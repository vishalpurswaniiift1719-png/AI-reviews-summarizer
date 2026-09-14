"""
Data normalizer for reviews.
Formats raw review data into a unified schema and filters out meaningless content.
"""

import hashlib
import re
from typing import Dict, Any, List


def is_meaningful(text: str) -> bool:
    """Check if the review has at least 5 alphanumeric characters."""
    if not text:
        return False
    # Strip everything except alphanumeric
    alphanumeric_only = re.sub(r'[^\w\s]', '', text).strip()
    # Check if we have at least 5 alphanumeric characters (not just spaces)
    alphanumeric_chars = text_no_spaces = re.sub(r'\s+', '', alphanumeric_only)
    return len(alphanumeric_chars) >= 5


def truncate_long_text(text: str, max_words: int = 500) -> str:
    """Truncate reviews that are excessively long."""
    if not text:
        return ""
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + " [truncated]"
    return text


def normalize_review(raw_review: Dict[str, Any]) -> Dict[str, Any]:
    """Map fields to the unified schema and generate deterministic ID."""
    raw_id = str(raw_review.get("reviewId", ""))
    
    # Generate deterministic ID
    hashed_id = hashlib.sha256(raw_id.encode('utf-8')).hexdigest()[:16]
    
    text = raw_review.get("text", "")
    text = truncate_long_text(text)
    
    return {
        "id": hashed_id,
        "source": raw_review.get("source", "unknown"),
        "rating": raw_review.get("rating"),
        "title": raw_review.get("title"),
        "text": text,
        "date": raw_review.get("date"),
        "language": "en"  # For now assuming en or handling mixed via LLM
    }


def normalize_all(raw_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of reviews, filtering out invalid/meaningless ones."""
    normalized = []
    
    for r in raw_reviews:
        text = r.get("text", "")
        if not is_meaningful(text):
            continue
            
        # Needs date and rating to be valid
        if r.get("date") is None or r.get("rating") is None:
            continue
            
        normalized.append(normalize_review(r))
        
    return normalized
