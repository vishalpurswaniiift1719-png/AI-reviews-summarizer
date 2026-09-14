"""
LangChain tool to process raw reviews into a clean, deduplicated, and PII-stripped corpus.
"""

import json
import logging
from typing import List, Dict, Any

from langchain_core.tools import tool

from src.config import RAW_DIR, PROCESSED_DIR
from src.processing import normalizer, deduplicator, pii_stripper

logger = logging.getLogger(__name__)


def run_pipeline(raw_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the full data processing pipeline on raw reviews."""
    logger.info(f"Starting processing pipeline with {len(raw_reviews)} raw reviews.")
    
    # 1. Normalize and filter
    normalized_reviews = normalizer.normalize_all(raw_reviews)
    logger.info(f"After normalization & filtering: {len(normalized_reviews)} reviews.")
    
    # 2. Deduplicate
    deduped_reviews = deduplicator.deduplicate(normalized_reviews)
    logger.info(f"After deduplication: {len(deduped_reviews)} reviews.")
    
    # 3. Strip PII
    cleaned_reviews = pii_stripper.strip_all(deduped_reviews)
    logger.info(f"After PII stripping: {len(cleaned_reviews)} reviews.")
    
    return cleaned_reviews


@tool
def process_reviews() -> str:
    """Process raw Google Play reviews into a cleaned dataset.
    This tool normalizes schemas, removes duplicates, strips PII (like emails and phone numbers),
    and filters out meaningless or excessively long reviews.
    Reads from data/raw/google_play_reviews.json and saves to data/processed/cleaned_reviews.json.
    Run this after fetch_reviews.
    """
    input_path = RAW_DIR / "google_play_reviews.json"
    output_path = PROCESSED_DIR / "cleaned_reviews.json"
    
    if not input_path.exists():
        return f"Error: Raw reviews file not found at {input_path}. Please run fetch_reviews first."
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw_reviews = json.load(f)
    except json.JSONDecodeError as e:
        return f"Error: Failed to parse raw reviews JSON: {e}"
        
    cleaned_reviews = run_pipeline(raw_reviews)
    
    if len(cleaned_reviews) < 10:
        logger.warning(f"Only {len(cleaned_reviews)} unique reviews remain after processing.")
        if len(cleaned_reviews) == 0:
            return "Error: No valid reviews remained after processing. Pipeline cannot proceed."
            
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_reviews, f, indent=2, ensure_ascii=False)
        
    return f"Successfully processed {len(raw_reviews)} raw reviews into {len(cleaned_reviews)} cleaned reviews. Saved to data/processed/cleaned_reviews.json"
