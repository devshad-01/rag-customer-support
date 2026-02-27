"""Confidence scoring — evaluate retrieval quality and decide escalation."""

import logging

logger = logging.getLogger(__name__)

# Thresholds (from proposal: < 0.4 auto-escalate, 0.4-0.7 offer, > 0.7 deliver)
AUTO_ESCALATE_THRESHOLD = 0.4
OFFER_ESCALATION_THRESHOLD = 0.7


def calculate_confidence(chunks: list[dict]) -> dict:
    """Compute a confidence score from the retrieved chunks.

    The score is the weighted average of the chunk similarity scores,
    giving more weight to the top-ranked results.

    Args:
        chunks: Retrieved chunks, each containing a 'score' key.

    Returns:
        dict with:
          confidence_score  — float 0-1
          has_sufficient_evidence — bool
          escalation_action — 'none' | 'offer' | 'auto'
    """
    if not chunks:
        return {
            "confidence_score": 0.0,
            "has_sufficient_evidence": False,
            "escalation_action": "auto",
        }

    scores = [c["score"] for c in chunks]

    # Weighted average: first chunk weighted most (rank-weighted)
    weights = [1.0 / (i + 1) for i in range(len(scores))]
    total_weight = sum(weights)
    confidence = sum(s * w for s, w in zip(scores, weights)) / total_weight

    # Clamp to [0, 1]
    confidence = max(0.0, min(1.0, confidence))

    # Determine escalation action
    if confidence < AUTO_ESCALATE_THRESHOLD:
        action = "auto"
        sufficient = False
    elif confidence < OFFER_ESCALATION_THRESHOLD:
        action = "offer"
        sufficient = True
    else:
        action = "none"
        sufficient = True

    logger.info(
        "Confidence=%.4f  action=%s  chunks=%d  top_score=%.4f",
        confidence,
        action,
        len(chunks),
        scores[0],
    )

    return {
        "confidence_score": round(confidence, 4),
        "has_sufficient_evidence": sufficient,
        "escalation_action": action,
    }
