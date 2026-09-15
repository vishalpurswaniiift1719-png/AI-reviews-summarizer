"""
LangChain tool to generate the weekly pulse note markdown document.
"""

import json
import logging
from datetime import datetime
from langchain_core.tools import tool

from src.config import PROCESSED_DIR, DATA_DIR, PULSES_DIR
from src.chains.pulse_chain import run_pulse_generation
from src.processing.pii_stripper import strip

logger = logging.getLogger(__name__)


@tool
def generate_pulse() -> str:
    """Generate the weekly pulse note based on clustered themes and actions.
    Reads themes_and_actions.json and cleaned_reviews.json from data/processed.
    Calculates metadata and generates a markdown document.
    Saves the pulse note to data/pulses/pulse_YYYY-MM-DD.md.
    Run this after cluster_themes.
    """
    themes_path = PROCESSED_DIR / "themes_and_actions.json"
    reviews_path = PROCESSED_DIR / "cleaned_reviews.json"
    
    if not themes_path.exists():
        return f"Error: Themes and actions file not found at {themes_path}. Please run cluster_themes first."
    if not reviews_path.exists():
        return f"Error: Cleaned reviews file not found at {reviews_path}. Please run process_reviews first."
        
    try:
        with open(themes_path, "r", encoding="utf-8") as f:
            themes_data = json.load(f)
        with open(reviews_path, "r", encoding="utf-8") as f:
            reviews_data = json.load(f)
    except json.JSONDecodeError as e:
        return f"Error: Failed to parse JSON files: {e}"
        
    logger.info("Calculating metadata for the pulse note.")
    
    # Calculate metadata
    total_reviews = len(reviews_data)
    
    # Calculate average rating
    total_rating = sum(r.get("rating", 0) for r in reviews_data if isinstance(r.get("rating"), (int, float)))
    average_rating = round(total_rating / total_reviews, 1) if total_reviews > 0 else 0.0
    
    # Calculate date range
    dates = []
    for r in reviews_data:
        date_str = r.get("date")
        if date_str:
            try:
                # Try to parse the ISO format or other formats if needed
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dates.append(dt)
            except ValueError:
                pass
                
    if dates:
        start_date = min(dates).strftime("%Y-%m-%d")
        end_date = max(dates).strftime("%Y-%m-%d")
        date_range = f"{start_date} to {end_date}"
    else:
        start_date = "Unknown"
        end_date = "Unknown"
        date_range = "Unknown"
        
    metadata = {
        "date_range": date_range,
        "date_start": start_date,
        "date_end": end_date,
        "total_reviews": total_reviews,
        "average_rating": f"{average_rating:.1f}"
    }
    
    # Format themes and actions as a string for the prompt
    themes_and_actions_str = json.dumps(themes_data, indent=2, ensure_ascii=False)
    
    logger.info("Starting pulse generation.")
    try:
        pulse_content = run_pulse_generation(metadata, themes_and_actions_str)
    except Exception as e:
        return f"Error during pulse generation: {e}"
        
    # Final PII scan
    logger.info("Running final PII scan on the generated pulse.")
    clean_pulse = strip(pulse_content)
    
    # Save the pulse document
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"pulse_{today_str}.md"
    output_path = PULSES_DIR / output_filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_pulse)
        
    # Calculate Sentiment CSAT
    pos_count = sum(1 for r in reviews_data if r.get("rating", 0) >= 4)
    neu_count = sum(1 for r in reviews_data if r.get("rating", 0) == 3)
    neg_count = sum(1 for r in reviews_data if r.get("rating", 0) <= 2)
    
    pos_percent = round((pos_count / total_reviews * 100)) if total_reviews > 0 else 0
    neu_percent = round((neu_count / total_reviews * 100)) if total_reviews > 0 else 0
    neg_percent = round((neg_count / total_reviews * 100)) if total_reviews > 0 else 0

    # Calculate Week Number
    week_number = datetime.now().isocalendar()[1]
    metadata["week_number"] = week_number
    metadata["csat"] = {
        "positive": pos_percent,
        "neutral": neu_percent,
        "negative": neg_percent
    }
    
    # Calculate Theme Share
    for theme, data in themes_data.items():
        count = data.get("count", 0)
        data["share"] = round((count / total_reviews * 100)) if total_reviews > 0 else 0

    # Extract Executive Synthesis (first paragraph of pulse)
    synthesis = "No executive synthesis available."
    for line in clean_pulse.split('\n'):
        if line.strip() and not line.startswith('#'):
            synthesis = line.strip()
            break
            
    # Also save the structured payload for the Vercel dashboard
    from src.config import PROJECT_ROOT
    dashboard_data_path = PROJECT_ROOT / "dashboard" / "data" / "latest_pulse.json"
    dashboard_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    dashboard_payload = {
        "metadata": metadata,
        "themes": themes_data,
        "markdown_pulse": clean_pulse,
        "executive_synthesis": synthesis,
        "generated_at": datetime.now().isoformat()
    }
    
    with open(dashboard_data_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_payload, f, indent=2, ensure_ascii=False)
        
    return f"Successfully generated pulse note ({len(clean_pulse.split())} words). Saved to data/pulses/{output_filename} and dashboard/data/latest_pulse.json"
