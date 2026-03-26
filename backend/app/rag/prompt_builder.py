"""Prompt builder — construct LLM prompts from retrieved chunks and a user query."""

import logging

logger = logging.getLogger(__name__)

CONTEXT_HEADER = "Context (retrieved documents):"
CONTEXT_SEPARATOR = "---"
HISTORY_HEADER = "Recent conversation context:"


def _format_chunk(chunk: dict, index: int) -> str:
    """Format a single chunk for inclusion in the prompt context block."""
    title = chunk.get("source_title") or f"Document {chunk.get('document_id', '?')}"
    page = chunk.get("page_number", "?")
    score = chunk.get("score", 0)
    text = chunk.get("chunk_text", "").strip()
    return (
        f"[Source {index + 1}: {title}, Page {page} "
        f"(relevance {score:.2f})]\n{text}"
    )


def _format_history(messages: list[dict], max_messages: int = 8) -> str:
    """Format recent conversation messages for continuity in prompting."""
    if not messages:
        return "No prior messages."

    trimmed = messages[-max_messages:]
    lines: list[str] = []
    for msg in trimmed:
        role = (msg.get("sender_role") or "unknown").lower()
        if role == "customer":
            label = "Customer"
        elif role == "agent":
            label = "Support Agent"
        else:
            label = "Assistant"

        content = (msg.get("content") or "").strip().replace("\n", " ")
        if len(content) > 240:
            content = content[:240].rstrip() + "…"
        lines.append(f"- {label}: {content}")

    return "\n".join(lines)


def build_prompt(
    query: str,
    chunks: list[dict],
    system_template_extension: str = "",
    recent_messages: list[dict] | None = None,
) -> str:
    """Build a full prompt string from the user query and retrieved chunks.

    Args:
        query: The customer's question.
        chunks: Retrieved document chunks from the retriever, each a dict with
                chunk_text, source_title, page_number, document_id, score.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    # Format context block
    if chunks:
        formatted_chunks = "\n\n".join(
            _format_chunk(c, i) for i, c in enumerate(chunks)
        )
        context_block = (
            f"{CONTEXT_HEADER}\n{CONTEXT_SEPARATOR}\n"
            f"{formatted_chunks}\n{CONTEXT_SEPARATOR}"
        )
    else:
        context_block = (
            f"{CONTEXT_HEADER}\n{CONTEXT_SEPARATOR}\n"
            "No relevant documents were found.\n"
            f"{CONTEXT_SEPARATOR}"
        )

    instruction_block = (
        (system_template_extension or "").strip()
        or "Respond as a professional support agent. Be concise and accurate."
    )

    history_block = (
        f"{HISTORY_HEADER}\n{_format_history(recent_messages or [])}\n\n"
    )

    prompt = (
        f"Instructions:\n{instruction_block}\n"
        "Response style rules:\n"
        "- Sound natural and conversational, like a real support agent.\n"
        "- For informational questions, give a fuller answer in 2-4 short paragraphs.\n"
        "- Include key conditions/limits and practical next steps when relevant.\n"
        "- Avoid one-line answers unless the question is truly simple.\n\n"
        f"{history_block}"
        f"{context_block}\n\n"
        f"Customer question: {query}\n\n"
        "Answer:"
    )

    logger.debug("Built prompt (%d chars, %d sources)", len(prompt), len(chunks))
    return prompt


def build_out_of_scope_prompt(
    query: str,
    customer_name: str | None = None,
    system_template_extension: str = "",
    recent_messages: list[dict] | None = None,
) -> str:
    """Build a prompt for dynamic out-of-scope responses.

    The model should respond naturally (not rigid template text), while
    following organization policy and avoiding escalation.
    """
    name_line = f"Customer name: {customer_name}\n" if customer_name else ""

    base_instructions = (
        (system_template_extension or "").strip()
        or "Respond as a professional support agent. Be concise and helpful."
    )

    prompt = (
        f"Instructions:\n{base_instructions}\n\n"
        "Out-of-scope handling rules:\n"
        "- The customer question is outside current company operations/content.\n"
        "- Do NOT escalate this conversation.\n"
        "- Respond naturally in 2-4 short sentences.\n"
        "- Avoid rigid or canned wording; sound conversational and human.\n"
        "- If customer name is provided, greet them once by first name.\n"
        "- Do not mention internal systems, confidence, retrieval, or knowledge base.\n"
        "- Politely guide the user back to company-related topics.\n"
        "- Invite the user to share a bit more context so you can help with relevant products or services.\n"
        "\n"
        f"{HISTORY_HEADER}\n{_format_history(recent_messages or [])}\n\n"
        f"{name_line}"
        f"Customer question: {query}\n\n"
        "Reply:"
    )

    logger.debug("Built out-of-scope prompt (%d chars)", len(prompt))
    return prompt
