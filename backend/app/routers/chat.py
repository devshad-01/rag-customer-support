"""Chat router — conversation & message endpoints with RAG pipeline."""

import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.conversation import Conversation, ConversationStatus, Message, SenderRole
from app.models.query_log import QueryLog
from app.models.ticket import Ticket, TicketStatus
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
from app.services import ticket_service, ai_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

AUTO_ESCALATION_MESSAGE = (
    "I'm connecting you to a support agent now. "
    "They'll review your conversation and reply shortly."
)

# ── Greeting / vague message detection ────────────────────────

_GREETING_PATTERNS = re.compile(
    r"^(hi|hey|hello|howdy|yo|sup|hiya|good\s*(morning|afternoon|evening|day)|"
    r"thanks|thank\s*you|ok|okay|bye|goodbye|see\s*ya|cheers|"
    r"what'?s?\s*up|how\s*are\s*you|how'?s?\s*it\s*going|"
    r"help|help\s*me|i\s*need\s*help|"
    r"hmm+|umm+|ah+|oh+|huh|lol|haha|wow"
    r")[!?.,\s]*$",
    re.IGNORECASE,
)

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "than", "to", "of", "in", "on", "at", "for",
    "with", "from", "by", "is", "are", "was", "were", "be", "been", "being", "do", "does", "did",
    "can", "could", "should", "would", "will", "may", "might", "i", "you", "we", "they", "he", "she",
    "it", "my", "your", "our", "their", "me", "us", "them", "this", "that", "these", "those", "how",
    "what", "where", "when", "why", "which", "who", "whom", "about", "please", "help",
}


def _topic_tokens(text: str) -> set[str]:
    """Extract lightweight topic tokens for simple query-shift detection."""
    tokens = re.findall(r"[a-zA-Z0-9']+", (text or "").lower())
    return {token for token in tokens if len(token) > 2 and token not in _STOP_WORDS}


def _is_topic_shift(previous_query: str | None, current_query: str) -> bool:
    """Return True when the current query appears semantically different from previous."""
    if not previous_query:
        return True

    prev = _topic_tokens(previous_query)
    curr = _topic_tokens(current_query)
    if not prev or not curr:
        return False

    overlap = len(prev & curr)
    union = len(prev | curr)
    jaccard = overlap / union if union else 0.0
    return jaccard < 0.2

def _build_greeting_response(customer_name: str | None) -> str:
    """Return a personalized greeting for vague/hello messages."""
    first_name = (customer_name or "").strip().split(" ")[0]
    if first_name:
        return (
            f"Hello {first_name}, thank you for contacting SupportIQ. "
            "I can help with questions about our products and services. "
            "How can I help you today?"
        )
    return (
        "Hello, thank you for contacting SupportIQ. "
        "I can help with questions about our products and services. "
        "How can I help you today?"
    )

def _is_vague_message(content: str) -> bool:
    """Return True if the message is a greeting or too vague for RAG."""
    stripped = content.strip()
    if len(stripped) < 3:
        return True
    if _GREETING_PATTERNS.match(stripped):
        return True
    # Single-word messages that aren't meaningful queries
    if len(stripped.split()) <= 1 and len(stripped) < 15:
        return True
    return False


def _normalize_title(text: str, max_len: int = 80) -> str:
    """Convert a message into a concise conversation title."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + "\u2026"


def _is_generic_title(title: str | None) -> bool:
    """Return True when title is missing or too generic (e.g., 'hello')."""
    if not title:
        return True
    stripped = title.strip()
    if not stripped:
        return True
    if _is_vague_message(stripped):
        return True
    generic_values = {
        "new chat",
        "chat",
        "conversation",
        "support",
        "help",
    }
    return stripped.lower() in generic_values


def _update_conversation_title_if_needed(conv: Conversation, customer_message: str) -> None:
    """Set/update conversation title when current title is generic and message is meaningful."""
    if not _is_generic_title(conv.title):
        return
    if _is_vague_message(customer_message):
        return
    conv.title = _normalize_title(customer_message)


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

    # Block AI replies if conversation is already escalated
    if conv.status == ConversationStatus.escalated:
        # Check if there's an open/in-progress ticket
        open_ticket = (
            db.query(Ticket)
            .filter(
                Ticket.conversation_id == conversation_id,
                Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress]),
            )
            .first()
        )
        if open_ticket:
            # Save the customer message so the agent can see it,
            # but do NOT repeat an AI holding message each time.
            content = (body.content or "").strip()
            if not content:
                raise HTTPException(status_code=400, detail="Message cannot be empty")

            _update_conversation_title_if_needed(conv, content)

            user_msg = Message(
                conversation_id=conversation_id,
                sender_role=SenderRole.customer,
                content=content,
            )
            db.add(user_msg)
            db.commit()
            db.refresh(user_msg)
            return ChatResponse(
                message=_msg_to_response(user_msg),
                sources=[],
                confidence=ConfidenceInfo(
                    confidence_score=0.0,
                    has_sufficient_evidence=False,
                    escalation_action="none",
                ),
                evidence=EvidenceInfo(
                    has_sufficient_evidence=False,
                    evidence_quality="none",
                    disclaimer=None,
                ),
                highlights=[],
                total_sources_found=0,
            )

    # Validate message content
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Set/update title only when the message is meaningful (not generic greeting).
    _update_conversation_title_if_needed(conv, content)

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        sender_role=SenderRole.customer,
        content=content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Conversation-level context flags
    has_prior_ai_reply = (
        db.query(Message.id)
        .filter(
            Message.conversation_id == conversation_id,
            Message.sender_role == SenderRole.ai,
            Message.id != user_msg.id,
        )
        .first()
        is not None
    )

    prior_ai_metadata_rows = (
        db.query(Message.sources_json)
        .filter(
            Message.conversation_id == conversation_id,
            Message.sender_role == SenderRole.ai,
            Message.sources_json.isnot(None),
        )
        .all()
    )

    metadata_already_shown = False
    for (sources_json,) in prior_ai_metadata_rows:
        try:
            raw = json.loads(sources_json)
            if isinstance(raw, dict) and raw.get("sources"):
                metadata_already_shown = True
                break
            if isinstance(raw, list) and raw:
                metadata_already_shown = True
                break
        except (json.JSONDecodeError, TypeError):
            continue

    previous_customer_msg = (
        db.query(Message.content)
        .filter(
            Message.conversation_id == conversation_id,
            Message.sender_role == SenderRole.customer,
            Message.id != user_msg.id,
        )
        .order_by(Message.created_at.desc())
        .first()
    )
    previous_customer_query = previous_customer_msg[0] if previous_customer_msg else None
    topic_shift = _is_topic_shift(previous_customer_query, content)

    # Handle vague/greeting messages without RAG pipeline
    if _is_vague_message(content):
        ai_msg = Message(
            conversation_id=conversation_id,
            sender_role=SenderRole.ai,
            content=_build_greeting_response(current_user.name if not has_prior_ai_reply else None),
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)
        return ChatResponse(
            message=_msg_to_response(ai_msg),
            sources=[],
            confidence=ConfidenceInfo(
                confidence_score=1.0,
                has_sufficient_evidence=True,
                escalation_action="none",
            ),
            evidence=EvidenceInfo(
                has_sufficient_evidence=True,
                evidence_quality="strong",
                disclaimer=None,
            ),
            highlights=[],
            total_sources_found=0,
        )

    # Run RAG pipeline (with error recovery)
    try:
        cfg = ai_config_service.get_or_create_config(db)

        # Recent conversation context for better continuity
        recent = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(8)
            .all()
        )
        recent_messages = [
            {"sender_role": m.sender_role.value, "content": m.content}
            for m in reversed(recent)
        ]

        result = await process_query(
            content,
            ai_config={
                "system_template_extension": cfg.system_template_extension,
                "no_escalate_out_of_scope": cfg.no_escalate_out_of_scope,
            },
            customer_name=current_user.name if not has_prior_ai_reply else None,
            recent_messages=recent_messages,
        )
    except Exception as exc:
        logger.error("RAG pipeline crashed for conv=%d: %s", conversation_id, exc)
        result = {
            "response": (
                "I'm sorry, I encountered an error while processing your question. "
                "Please try again or ask to speak with a support agent."
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

    # Prepare sources + confidence + evidence JSON to store with AI message.
    # Show metadata only when we have references, and:
    # - first referenced answer in conversation, or
    # - user changed to a new topic.
    has_references = bool(result["sources"])
    include_metadata = has_references and (not metadata_already_shown or topic_shift)
    metadata = {
        "sources": result["sources"],
        "confidence": result["confidence"],
        "evidence": result["evidence"],
        "highlights": result["highlights"],
    }

    # Keep customer-facing response concise for auto-escalation.
    if result["confidence"]["escalation_action"] == "auto":
        result["response"] = AUTO_ESCALATION_MESSAGE

    # Save AI message
    ai_msg = Message(
        conversation_id=conversation_id,
        sender_role=SenderRole.ai,
        content=result["response"],
        sources_json=json.dumps(metadata, default=str) if include_metadata else None,
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
    if include_metadata:
        sources = [SourceReference(**s) for s in result["sources"]]
        confidence = ConfidenceInfo(**result["confidence"])
        evidence = EvidenceInfo(**result["evidence"])
        highlights = [HighlightMapping(**h) for h in result["highlights"]]
        total_sources_found = result["total_sources_found"]
    else:
        sources = []
        confidence = None
        evidence = None
        highlights = []
        total_sources_found = 0

    return ChatResponse(
        message=_msg_to_response(ai_msg),
        sources=sources,
        confidence=confidence,
        evidence=evidence,
        highlights=highlights,
        total_sources_found=total_sources_found,
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


@router.post("/{conversation_id}/escalate", response_model=EscalationResponse)
async def escalate_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually escalate a conversation to a support agent."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.customer_id != current_user.id and current_user.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Not your conversation")
    if conv.status == ConversationStatus.closed:
        raise HTTPException(status_code=400, detail="This conversation is closed")

    ticket = ticket_service.create_ticket(
        db,
        conversation_id=conversation_id,
        customer_id=current_user.id,
        reason="Customer requested support agent",
    )

    # Add a system-style message so the customer sees it in chat
    system_msg = Message(
        conversation_id=conversation_id,
        sender_role=SenderRole.ai,
        content=(
            "I'm connecting you to a support agent now. "
            "They'll review your conversation and reply shortly."
        ),
    )
    db.add(system_msg)
    db.commit()
    db.refresh(ticket)

    from app.schemas.ticket import TicketResponse
    from app.models.user import UserRole as _UR  # avoid shadowing

    # Build ticket response
    customer = db.query(User).filter(User.id == ticket.customer_id).first()
    agent_name = None
    if ticket.assigned_agent_id:
        agent = db.query(User).filter(User.id == ticket.assigned_agent_id).first()
        agent_name = agent.name if agent else None
    msg_count = (
        db.query(func.count(Message.id))
        .filter(Message.conversation_id == conversation_id)
        .scalar()
    ) or 0

    ticket_resp = TicketResponse(
        id=ticket.id,
        conversation_id=ticket.conversation_id,
        customer_id=ticket.customer_id,
        assigned_agent_id=ticket.assigned_agent_id,
        status=ticket.status.value,
        priority=ticket.priority.value,
        reason=ticket.reason,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        updated_at=ticket.updated_at,
        customer_name=customer.name if customer else None,
        agent_name=agent_name,
        conversation_title=conv.title,
        message_count=msg_count,
    )
    return EscalationResponse(
        ticket=ticket_resp,
        message="Conversation escalated to a support agent.",
    )


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
