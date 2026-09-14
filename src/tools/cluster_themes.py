"""
LangChain tool to cluster processed reviews into top themes and generate actions.
"""

import json
import logging
from langchain_core.tools import tool

from src.config import PROCESSED_DIR, DATA_DIR
from src.chains.theme_chain import run_theme_clustering, run_action_generation

logger = logging.getLogger(__name__)


@tool
def cluster_themes() -> str:
    """Cluster processed reviews into themes and extract insights.
    Reads from data/processed/cleaned_reviews.json.
    Generates top 3 themes, representative quotes, and 3 action items.
    Saves the result to data/processed/themes_and_actions.json.
    Run this after process_reviews.
    """
    input_path = PROCESSED_DIR / "cleaned_reviews.json"
    output_path = PROCESSED_DIR / "themes_and_actions.json"
    
    if not input_path.exists():
        return f"Error: Cleaned reviews file not found at {input_path}. Please run process_reviews first."
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            cleaned_reviews = json.load(f)
    except json.JSONDecodeError as e:
        return f"Error: Failed to parse cleaned reviews JSON: {e}"
        
    if len(cleaned_reviews) < 2:
        return "Error: Not enough reviews to cluster (minimum 2 required)."
        
    logger.info(f"Starting theme clustering on {len(cleaned_reviews)} reviews.")
    
    # 1. Cluster reviews into themes (top 5 max, sorted by count)
    try:
        themes = run_theme_clustering(cleaned_reviews)
    except Exception as e:
        return f"Error during clustering: {e}"
        
    if not themes:
        return "Error: No themes generated."
        
    # 2. Select top 3 themes
    top_3_themes = themes[:3]
    logger.info(f"Selected top {len(top_3_themes)} themes for action generation.")
    
    # 3. Generate actions based on top themes
    try:
        actions = run_action_generation(top_3_themes)
    except Exception as e:
        return f"Error during action generation: {e}"
        
    # 4. Save results
    result_data = {
        "themes": top_3_themes,
        "actions": actions,
        "metadata": {
            "total_reviews_analyzed": len(cleaned_reviews)
        }
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
        
    return f"Successfully generated {len(top_3_themes)} themes and {len(actions)} actions. Saved to data/processed/themes_and_actions.json"
