"""
LangChain chains for generating the weekly pulse note.
"""

import logging
from typing import Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import GEMINI_API_KEY
from src.prompts.pulse_prompt import PULSE_PROMPT, RE_PROMPT_WORD_COUNT

logger = logging.getLogger(__name__)


def get_llm():
    """Initialize the Gemini LLM for pulse generation."""
    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0.2,
        api_key=GEMINI_API_KEY,
        max_retries=3
    )


def enforce_word_limit(pulse_text: str, max_words: int = 250) -> str:
    """Check if pulse_text exceeds max_words, re-prompt if necessary."""
    word_count = len(pulse_text.split())
    if word_count <= max_words:
        return pulse_text
        
    logger.warning(f"Pulse note exceeded {max_words} words ({word_count} words). Re-prompting to condense.")
    llm = get_llm()
    chain = RE_PROMPT_WORD_COUNT | llm | StrOutputParser()
    
    condensed_text = chain.invoke({
        "word_count": word_count,
        "draft": pulse_text
    })
    
    new_word_count = len(condensed_text.split())
    logger.info(f"Condensed pulse note to {new_word_count} words.")
    
    return condensed_text


def run_pulse_generation(metadata: Dict[str, Any], themes_and_actions: str) -> str:
    """Run the chain to generate the pulse note markdown."""
    llm = get_llm()
    chain = PULSE_PROMPT | llm | StrOutputParser()
    
    logger.info("Invoking Gemini for pulse generation...")
    try:
        pulse_text = chain.invoke({
            "date_range": metadata.get("date_range", ""),
            "date_start": metadata.get("date_start", ""),
            "date_end": metadata.get("date_end", ""),
            "total_reviews": metadata.get("total_reviews", 0),
            "average_rating": metadata.get("average_rating", "0.0"),
            "themes_and_actions": themes_and_actions
        })
        
        # Enforce word limit
        final_pulse = enforce_word_limit(pulse_text)
        return final_pulse
        
    except Exception as e:
        logger.error(f"LLM pulse generation failed: {e}")
        raise
