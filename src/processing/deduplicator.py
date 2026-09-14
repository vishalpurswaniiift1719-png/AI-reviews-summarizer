"""
Deduplicator for reviews.
Removes duplicate reviews based on exact text and date matches.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def deduplicate(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate reviews based on exact match of (text, date)."""
    seen = set()
    unique_reviews = []
    
    for review in reviews:
        # Use a combination of text and date as the unique signature
        text = review.get("text", "")
        # Standardize date to day level to avoid timezone/second jitter 
        # causing duplicates to slip through
        date_str = review.get("date", "")
        day = date_str[:10] if len(date_str) >= 10 else date_str
        
        signature = f"{text}|{day}"
        
        if signature not in seen:
            seen.add(signature)
            unique_reviews.append(review)
            
    duplicates_removed = len(reviews) - len(unique_reviews)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate reviews.")
        
    return unique_reviews
