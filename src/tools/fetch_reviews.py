"""
Google Play review fetching tool for the AI Reviews Summarizer.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from google_play_scraper import Sort, reviews
from langchain_core.tools import tool

from src.config import GOOGLE_PLAY_APP_ID, REVIEW_WEEKS, RAW_DIR

logger = logging.getLogger(__name__)


def _fetch_with_retry(app_id: str, count: int, continuation_token: Any = None) -> tuple:
    """Fetch reviews with exponential backoff for rate limits."""
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries + 1):
        try:
            return reviews(
                app_id,
                lang='en',
                country='ae',
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token
            )
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Failed to fetch reviews after {max_retries} retries: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Fetch failed, retrying in {delay}s: {e}")
            time.sleep(delay)


def fetch_and_filter_reviews(app_id: str, weeks: int) -> List[Dict[str, Any]]:
    """Fetch reviews and filter by the specified time window."""
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    logger.info(f"Fetching reviews for {app_id} since {cutoff_date.isoformat()}")

    all_filtered_reviews = []
    continuation_token = None
    batch_size = 199  # google_play_scraper standard max count
    
    # We loop to fetch pages until we hit reviews older than our cutoff date
    # or we exhaust all reviews.
    while True:
        try:
            result, continuation_token = _fetch_with_retry(app_id, batch_size, continuation_token)
        except Exception as e:
            logger.error(f"Error during fetching: {e}")
            break

        if not result:
            break

        reached_cutoff = False
        
        for review in result:
            review_date = review.get("at")
            if not review_date:
                continue
                
            if review_date < cutoff_date:
                reached_cutoff = True
                continue
                
            # Filter and format to our required schema fields
            formatted_review = {
                "reviewId": review.get("reviewId"),
                "rating": review.get("score"),
                "title": review.get("userName"),  # Play store doesn't have review titles, use username as proxy or leave null
                "text": review.get("content"),
                "date": review_date.isoformat(),
                "source": "google_play"
            }
            all_filtered_reviews.append(formatted_review)

        # Stop fetching if we've seen reviews older than our cutoff date
        if reached_cutoff or not continuation_token:
            break
            
    return all_filtered_reviews


@tool
def fetch_reviews() -> str:
    """Fetch recent Google Play reviews for the Noon Buyer App.
    Run this to download the latest reviews within the configured time window.
    Saves the output to data/raw/google_play_reviews.json.
    """
    try:
        filtered_reviews = fetch_and_filter_reviews(GOOGLE_PLAY_APP_ID, REVIEW_WEEKS)
    except Exception as e:
        return f"Error: Failed to fetch reviews: {str(e)}"
        
    if not filtered_reviews:
        # Fallback: widen window if 0 reviews
        logger.warning(f"No reviews found in the last {REVIEW_WEEKS} weeks. Widening window by 2 weeks.")
        try:
            filtered_reviews = fetch_and_filter_reviews(GOOGLE_PLAY_APP_ID, REVIEW_WEEKS + 2)
        except Exception as e:
            return f"Error: Failed to fetch reviews on retry: {str(e)}"
            
        if not filtered_reviews:
            return f"Error: No reviews found for {GOOGLE_PLAY_APP_ID} even after widening the window."
            
    output_path = RAW_DIR / "google_play_reviews.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered_reviews, f, indent=2, ensure_ascii=False)
        
    return f"Fetched {len(filtered_reviews)} reviews and saved to data/raw/google_play_reviews.json"
