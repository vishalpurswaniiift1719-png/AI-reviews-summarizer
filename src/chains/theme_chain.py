"""
LangChain chains for clustering themes and generating actions using Gemini.
"""

import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from fuzzywuzzy import fuzz

from src.config import GEMINI_API_KEY
from src.prompts.clustering_prompt import CLUSTERING_PROMPT, ACTION_PROMPT

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Pydantic Schemas for Structured Output
# -----------------------------------------------------------------------------
class Theme(BaseModel):
    theme_name: str = Field(description="Professional name of the theme")
    description: str = Field(description="Short description of what the theme encompasses")
    review_ids: List[str] = Field(description="List of review IDs assigned to this theme")
    representative_quote: str = Field(description="Exact verbatim quote from a review in this theme")

class ClusteringOutput(BaseModel):
    themes: List[Theme] = Field(description="List of 2 to 5 themes")

class Action(BaseModel):
    title: str = Field(description="Short title for the action item")
    description: str = Field(description="1-2 sentences describing the specific action to take")

class ActionOutput(BaseModel):
    actions: List[Action] = Field(description="Exactly 3 action items")


# -----------------------------------------------------------------------------
# LLM Initialization
# -----------------------------------------------------------------------------
def get_llm():
    """Initialize the Gemini LLM."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,  # Low temp for deterministic clustering
        api_key=GEMINI_API_KEY,
        max_retries=3
    )


# -----------------------------------------------------------------------------
# Validation Helpers
# -----------------------------------------------------------------------------
def verify_verbatim_quote(quote: str, reviews: List[Dict[str, Any]]) -> str:
    """Ensure the quote is verbatim. If not, find the closest matching review."""
    corpus = [r.get("text", "") for r in reviews]
    
    # Fast exact match check
    for text in corpus:
        if quote in text:
            return quote
            
    # Fuzzy match fallback
    logger.warning(f"Quote not found exactly verbatim. Falling back to fuzzy matching: {quote[:30]}...")
    best_match = ""
    best_score = 0
    
    for text in corpus:
        score = fuzz.partial_ratio(quote, text)
        if score > best_score:
            best_score = score
            best_match = text
            
    if best_score > 85:
        logger.info(f"Replaced with closest match (score {best_score})")
        # Use the whole review as fallback, or ideally just a sentence. 
        # For simplicity, if we have to fall back, use the matched text.
        return best_match
    
    # If no good match, just return the first review's text (fallback of fallback)
    logger.error("No suitable verbatim quote found. Falling back to first review.")
    return corpus[0] if corpus else quote


# -----------------------------------------------------------------------------
# Chains
# -----------------------------------------------------------------------------
def run_theme_clustering(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the clustering chain to group reviews into top themes."""
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=ClusteringOutput)
    
    chain = CLUSTERING_PROMPT | llm | parser
    
    # Simplify input to reduce tokens
    simplified_reviews = [
        {"id": r["id"], "text": r["text"]} for r in reviews
    ]
    
    logger.info("Invoking Gemini for theme clustering...")
    try:
        result = chain.invoke({
            "reviews_json": json.dumps(simplified_reviews, ensure_ascii=False),
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        logger.error(f"LLM clustering failed: {e}")
        raise
        
    themes = result.get("themes", [])
    
    # Post-process: calculate review counts
    for theme in themes:
        theme["review_count"] = len(theme.get("review_ids", []))
        
        # Verify verbatim quote
        raw_quote = theme.get("representative_quote", "")
        theme["representative_quote"] = verify_verbatim_quote(raw_quote, reviews)
        
    # Sort themes by review count descending
    themes = sorted(themes, key=lambda x: x["review_count"], reverse=True)
    
    return themes


def run_action_generation(top_themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the action generation chain based on top themes."""
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=ActionOutput)
    
    chain = ACTION_PROMPT | llm | parser
    
    # Extract only necessary info for the prompt
    themes_summary = [
        {"theme_name": t["theme_name"], "description": t["description"], "quote": t["representative_quote"]}
        for t in top_themes
    ]
    
    logger.info("Invoking Gemini for action generation...")
    try:
        result = chain.invoke({
            "themes_json": json.dumps(themes_summary, ensure_ascii=False),
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        logger.error(f"LLM action generation failed: {e}")
        raise
        
    actions = result.get("actions", [])
    
    # Enforce constraint: exactly 3 actions
    if len(actions) > 3:
        actions = actions[:3]
        
    return actions
