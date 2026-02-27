"""Prompt builder — construct LLM prompts from retrieved chunks and a user query."""

import logging

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """\
You are a helpful, professional customer support assistant called SupportIQ.
Answer the user's question based ONLY on the provided context documents below.
If the context does not contain enough information to answer, say:
"I don't have enough information in our knowledge base to answer this question. \
Would you like me to escalate this to a human agent?"

Rules:
- Be concise, clear, and friendly.
- Do NOT make up information that is not in the context.
- When relevant, mention which source document your answer comes from.
- If multiple sources are relevant, synthesise them into a coherent answer.
"""

CONTEXT_HEADER = "Context (retrieved documents):"
CONTEXT_SEPARATOR = "---"


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


def build_prompt(query: str, chunks: list[dict]) -> str:
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

    prompt = (
        f"{SYSTEM_TEMPLATE}\n\n"
        f"{context_block}\n\n"
        f"Customer question: {query}\n\n"
        "Answer:"
    )

    logger.debug("Built prompt (%d chars, %d sources)", len(prompt), len(chunks))
    return prompt
