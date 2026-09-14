"""
PII Stripper for reviews.
Redacts emails, phone numbers, and common device IDs using regex.
"""

import re
from typing import List, Dict, Any

# Common PII Regex Patterns
EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
# UAE/General phone numbers (e.g. +971501234567, 0501234567, +971-50-123-4567)
PHONE_PATTERN = r'(?:\+971|00971|0)?[-\s]?(?:5[024568])[-\s]?\d{3}[-\s]?\d{4}\b'
# Order IDs, tracking numbers, IMEI patterns
DEVICE_ID_PATTERN = r'(?i)(imei|device id|device|order)[\s#:]*[A-Za-z0-9-]{6,}'


def strip(text: str) -> str:
    """Strip known PII patterns from text and replace with [REDACTED]."""
    if not text:
        return ""
        
    text = re.sub(EMAIL_PATTERN, '[REDACTED]', text)
    text = re.sub(PHONE_PATTERN, '[REDACTED]', text)
    text = re.sub(DEVICE_ID_PATTERN, r'\1 [REDACTED]', text)
    
    return text


def contains_pii(text: str) -> bool:
    """Check if the text contains any known PII patterns."""
    if not text:
        return False
        
    if re.search(EMAIL_PATTERN, text):
        return True
    if re.search(PHONE_PATTERN, text):
        return True
    if re.search(DEVICE_ID_PATTERN, text):
        return True
        
    return False


def strip_all(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run PII stripping on a list of reviews."""
    stripped_reviews = []
    
    for review in reviews:
        # Create a copy so we don't mutate original
        cleaned_review = review.copy()
        
        cleaned_review["text"] = strip(review.get("text", ""))
        
        # Strip title as well, as users sometimes put phone numbers there
        if cleaned_review.get("title"):
            cleaned_review["title"] = strip(cleaned_review.get("title", ""))
            
        stripped_reviews.append(cleaned_review)
        
    return stripped_reviews
