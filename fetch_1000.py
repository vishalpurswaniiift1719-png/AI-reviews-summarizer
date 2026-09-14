import json
import logging
from google_play_scraper import Sort, reviews

from src.config import GOOGLE_PLAY_APP_ID, RAW_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_1000_reviews():
    logger.info(f"Fetching 1000 latest reviews for {GOOGLE_PLAY_APP_ID}...")
    
    result, continuation_token = reviews(
        GOOGLE_PLAY_APP_ID,
        lang='en',
        country='ae',
        sort=Sort.NEWEST,
        count=1000
    )
    
    all_filtered_reviews = []
    
    for review in result:
        review_date = review.get("at")
        
        formatted_review = {
            "reviewId": review.get("reviewId"),
            "rating": review.get("score"),
            "title": review.get("userName"),
            "text": review.get("content"),
            "date": review_date.isoformat() if review_date else None,
            "source": "google_play"
        }
        all_filtered_reviews.append(formatted_review)
        
    logger.info(f"Successfully fetched and formatted {len(all_filtered_reviews)} reviews.")
    
    output_path = RAW_DIR / "google_play_reviews.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_filtered_reviews, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    fetch_1000_reviews()
