"""Chat router — conversation & message endpoints with RAG pipeline."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.conversation import Conversation, ConversationStatus, Message, SenderRole
from app.models.query_log import QueryLog
from app.models.ticket import Ticket
from app.models.user import User
from app.rag.pipeline import process_query
from app.schemas.chat import (
    ChatResponse,
    ConfidenceInfo,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    EvidenceInfo,
    HighlightMapping,
    MessageCreate,
    MessageResponse,
    SourceReference,
)
from app.schemas.ticket import EscalationResponse
from app.services import ticket_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ── Helper ────────────────────────────────────────────────────

def _msg_to_response(msg: Message) -> MessageResponse:
    """Convert a Message ORM object to a MessageResponse schema."""
    sources: list[SourceReference] = []
    confidence: ConfidenceInfo | None = None
    evidence: EvidenceInfo | None = None
    highlights: list[HighlightMapping] = []

    if msg.sources_json:
        try:
            raw = json.loads(msg.sources_json)
            if isinstance(raw, dict):
                sources = [SourceReference(**s) for s in raw.get("sources", [])]
                if "confidence" in raw:
                    confidence = ConfidenceInfo(**raw["confidence"])
                if "evidence" in raw:
                    evidence = EvidenceInfo(**raw["evidence"])
                if "highlights" in raw:
                    highlights = [HighlightMapping(**h) for h in raw["highlights"]]
            elif isinstance(raw, list):
                sources = [SourceReference(**s) for s in raw]
        except (json.JSONDecodeError, Exception):
            pass

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_role=msg.sender_role.value,
        content=msg.content,
        sources=sources,
        confidence=confidence,
        evidence=evidence,
        highlights=highlights,
        created_at=msg.created_at,
    )


def _conv_to_response(conv: Conversation, db: Session) -> ConversationResponse:
    """Convert a Conversation ORM object to a ConversationResponse schema."""
    # Get last message preview
    last_msg = (
        db.query(Message.content)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .first()
    )
    msg_count = (
        db.query(func.count(Message.id))
        .filter(Message.conversation_id == conv.id)
        .scalar()
    )

    return ConversationResponse(
        id=conv.id,
        customer_id=conv.customer_id,
        title=conv.title,
        status=conv.status.value,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        last_message=last_msg[0] if last_msg else None,
        message_count=msg_count or 0,
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new conversation."""
    conv = Conversation(
        customer_id=current_user.id,
        title=body.title,
        status=ConversationStatus.active,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    logger.info("Conversation id=%d created by user=%d", conv.id, current_user.id)
    return _conv_to_response(conv, db)


@router.post("/{conversation_id}/message", response_model=ChatResponse)
async def send_message(
    conversation_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get an AI response via the RAG pipeline."""
    # Validate conversation
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.customer_id != current_user.id and current_user.role.value not in ("admin", "agent"):
        raise HTTPException(status_code=403, detail="Not your conversation")
    if conv.status in (ConversationStatus.closed,):
        raise HTTPException(status_code=400, detail="This conversation is closed")

    # Validate message content
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Auto-set conversation title from first message
    if not conv.title:
        conv.title = content[:80] + ("\u2026" if len(content) > 80 else "")

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        sender_role=SenderRole.customer,
        content=content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Run RAG pipeline (with error recovery)
    try:
        result = await process_query(content)
    except Exception as exc:
        logger.error("RAG pipeline crashed for conv=%d: %s", conversation_id, exc)
        result = {
            "response": (
                "I'm sorry, I encountered an error while processing your question. "
                "Please try again or ask to speak with a human agent."
            ),
            "sources": [],
            "confidence": {
                "confidence_score": 0.0,
                "has_sufficient_evidence": False,
                "escalation_action": "auto",
            },
            "evidence": {
                "evidence_quality": "none",
                "has_sufficient_evidence": False,
                "disclaimer": "An error occurred.",
            },
            "highlights": [],
            "total_sources_found": 0,
            "response_time_ms": 0,
        }

    # Prepare sources + confidence + evidence JSON to store with AI message
    metadata = {
        "sources": result["sources"],
        "confidence": result["confidence"],
        "evidence": result["evidence"],
        "highlights": result["highlights"],
    }

    # Save AI message
    ai_msg = Message(
        conversation_id=conversation_id,
        sender_role=SenderRole.ai,
        content=result["response"],
        sources_json=json.dumps(metadata, default=str),
        confidence_score=result["confidence"]["confidence_score"],
    )
    db.add(ai_msg)

    # Log to QueryLog for analytics
    query_log = QueryLog(
        conversation_id=conversation_id,
        customer_id=current_user.id,
        query_text=content,
        response_text=result["response"],
        confidence_score=result["confidence"]["confidence_score"],
        has_sufficient_evidence=result["confidence"]["has_sufficient_evidence"],
        sources_count=len(result["sources"]),
        primary_source_score=result["sources"][0]["score"] if result["sources"] else None,
        escalated=result["confidence"]["escalation_action"] == "auto",
        escalation_reason=(
            "Low confidence (auto-escalate)"
            if result["confidence"]["escalation_action"] == "auto"
            else None
        ),
        response_time_ms=result["response_time_ms"],
    )
    db.add(query_log)

    # Auto-escalate: create ticket when confidence is very low
    if result["confidence"]["escalation_action"] == "auto":
        try:
            ticket_service.create_ticket(
                db,
                conversation_id=conversation_id,
                customer_id=current_user.id,
                reason="Auto-escalated: low confidence response",
                confidence_score=result["confidence"]["confidence_score"],
            )
            logger.info("Auto-escalated conv=%d (confidence=%.2f)", conversation_id, result["confidence"]["confidence_score"])
        except Exception as esc_err:
            logger.error("Auto-escalation failed for conv=%d: %s", conversation_id, esc_err)

    db.commit()
    db.refresh(ai_msg)

    # Build response
    sources = [SourceReference(**s) for s in result["sources"]]
    confidence = ConfidenceInfo(**result["confidence"])
    evidence = EvidenceInfo(**result["evidence"])
    highlights = [HighlightMapping(**h) for h in result["highlights"]]

    return ChatResponse(
        message=_msg_to_response(ai_msg),
        sources=sources,
        confidence=confidence,
        evidence=evidence,
        highlights=highlights,
        total_sources_found=result["total_sources_found"],
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages in a conversation, ordered by time."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.customer_id != current_user.id and current_user.role.value not in ("admin", "agent"):
        raise HTTPException(status_code=403, detail="Not your conversation")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [_msg_to_response(m) for m in messages]


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations. Customers see only their own; admins/agents see all."""
    query = db.query(Conversation)
    if current_user.role.value == "customer":
        query = query.filter(Conversation.customer_id == current_user.id)

    total = query.count()
    convs = query.order_by(Conversation.created_at.desc()).all()

    return ConversationListResponse(
        items=[_conv_to_response(c, db) for c in convs],
        total=total,
    )


def _delete_conversation(conv: Conversation, db: Session) -> None:
    """Delete a conversation and clean up FK references."""
    # Nullify query_log FK (preserve analytics rows)
    db.query(QueryLog).filter(QueryLog.conversation_id == conv.id).update(
        {QueryLog.conversation_id: None}, synchronize_session=False
    )
    # Delete tickets tied to this conversation
    db.query(Ticket).filter(Ticket.conversation_id == conv.id).delete(
        synchronize_session=False
    )
    # Messages cascade-delete via ORM relationship
    db.delete(conv)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a single conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.customer_id != current_user.id and current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Not your conversation")

    _delete_conversation(conv, db)
    db.commit()
    logger.info("Deleted conversation id=%d by user=%d", conversation_id, current_user.id)


@router.delete("/", status_code=204)
async def clear_all_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all conversations for the current customer."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.customer_id == current_user.id)
        .all()
    )
    for conv in convs:
        _delete_conversation(conv, db)
    db.commit()
    logger.info("Cleared %d conversations for user=%d", len(convs), current_user.id)
