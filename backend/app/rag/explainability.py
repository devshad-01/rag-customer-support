"""Explainability module — source ranking, highlighting, and evidence assessment."""

import logging
import re

logger = logging.getLogger(__name__)

# Minimum score to consider a source as "sufficient evidence"
WEAK_SOURCE_THRESHOLD = 0.35


def rank_sources_by_relevance(sources: list[dict]) -> list[dict]:
    """Sort sources by relevance score descending.

    Adds a 'rank' field (1-based) and 'is_primary' flag to each source.

    Args:
        sources: List of source dicts, each with a 'score' key.

    Returns:
        Sorted list with added 'rank' and 'is_primary' fields.
    """
    sorted_sources = sorted(sources, key=lambda s: s.get("score", 0), reverse=True)
    for i, src in enumerate(sorted_sources):
        src["rank"] = i + 1
        src["is_primary"] = i == 0
    return sorted_sources


def highlight_relevant_passages(
    response_text: str,
    source_chunks: list[dict],
) -> list[dict]:
    """Identify which parts of the AI response map to source chunks.

    Uses a simple keyword-overlap approach: extracts key phrases from each
    source chunk and checks if they appear in the response text.

    Args:
        response_text: The AI-generated answer.
        source_chunks: List of source dicts with 'chunk_text' and 'chunk_id'.

    Returns:
        List of mappings: { chunk_id, matched_phrases, overlap_score }
    """
    if not response_text or not source_chunks:
        return []

    response_lower = response_text.lower()
    mappings = []

    for chunk in source_chunks:
        chunk_text = chunk.get("chunk_text", "")
        if not chunk_text:
            continue

        # Extract meaningful phrases (3+ word sequences)
        phrases = _extract_key_phrases(chunk_text)
        matched = [p for p in phrases if p.lower() in response_lower]

        # Calculate overlap: ratio of matched phrases to total
        overlap = len(matched) / max(len(phrases), 1)

        mappings.append({
            "chunk_id": chunk.get("chunk_id", ""),
            "document_id": chunk.get("document_id"),
            "matched_phrases": matched[:5],  # Cap to top 5 to keep response small
            "overlap_score": round(overlap, 4),
        })

    # Sort by overlap score descending
    mappings.sort(key=lambda m: m["overlap_score"], reverse=True)
    return mappings


def assess_evidence_sufficiency(
    sources: list[dict],
    confidence_score: float,
) -> dict:
    """Determine if the retrieved sources provide sufficient evidence.

    Args:
        sources: Ranked source list with 'score' fields.
        confidence_score: Overall confidence from confidence module.

    Returns:
        dict with:
          has_sufficient_evidence — bool
          evidence_quality — 'strong' | 'moderate' | 'weak' | 'none'
          disclaimer — str or None (message to prepend when evidence is weak)
    """
    if not sources:
        return {
            "has_sufficient_evidence": False,
            "evidence_quality": "none",
            "disclaimer": (
                "I could not find any relevant documents to answer your question. "
                "The following response is not backed by supporting evidence."
            ),
        }

    top_score = sources[0].get("score", 0) if sources else 0
    strong_count = sum(1 for s in sources if s.get("score", 0) >= 0.6)
    moderate_count = sum(1 for s in sources if s.get("score", 0) >= WEAK_SOURCE_THRESHOLD)

    if confidence_score >= 0.7 and strong_count >= 1:
        return {
            "has_sufficient_evidence": True,
            "evidence_quality": "strong",
            "disclaimer": None,
        }
    elif confidence_score >= 0.4 and moderate_count >= 1:
        return {
            "has_sufficient_evidence": True,
            "evidence_quality": "moderate",
            "disclaimer": None,
        }
    else:
        return {
            "has_sufficient_evidence": False,
            "evidence_quality": "weak",
            "disclaimer": (
                "Note: I could not find strong supporting documents for this answer. "
                "The following is based on limited context."
            ),
        }


def _extract_key_phrases(text: str, min_words: int = 3, max_phrases: int = 20) -> list[str]:
    """Extract key phrases from text for matching.

    Splits text into sentences, then extracts multi-word subsequences.
    """
    # Clean and split into sentences
    sentences = re.split(r'[.!?\n]+', text)
    phrases = []

    for sentence in sentences:
        words = sentence.strip().split()
        if len(words) < min_words:
            continue
        # Take the whole sentence if short enough, or sliding windows
        if len(words) <= 6:
            phrases.append(" ".join(words))
        else:
            # Sliding window of 4-5 words
            for i in range(0, len(words) - 3):
                phrase = " ".join(words[i : i + 4])
                phrases.append(phrase)
                if len(phrases) >= max_phrases:
                    return phrases

    return phrases[:max_phrases]
