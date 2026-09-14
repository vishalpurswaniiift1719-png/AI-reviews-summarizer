"""
Prompt templates for theme clustering and action generation.
"""

from langchain_core.prompts import ChatPromptTemplate

# -----------------------------------------------------------------------------
# Clustering Prompt
# -----------------------------------------------------------------------------
CLUSTERING_PROMPT_TEMPLATE = """You are an expert Product Manager analyzing app reviews for the Noon Buyer App.
Your goal is to cluster the following user reviews into distinct, professional themes.

CONSTRAINTS:
1. Group the reviews into AT LEAST 2 and AT MOST 5 distinct themes.
2. Use professional, executive-friendly names for the themes (e.g., "Checkout & Payments", "Delivery Speed", "App Performance").
3. Ensure the themes do not heavily overlap.
4. For each theme, select exactly ONE representative quote from the reviews provided. 
   - The quote MUST BE VERBATIM (a direct, exact copy-paste from a review text). Do NOT paraphrase.
   - The quote must not contain any inappropriate language.
5. Assign every review to exactly one theme.

REVIEWS:
{reviews_json}

Return ONLY valid JSON matching the schema below. Do not include markdown code blocks.
"""

CLUSTERING_PROMPT = ChatPromptTemplate.from_template(CLUSTERING_PROMPT_TEMPLATE)


# -----------------------------------------------------------------------------
# Action Prompt
# -----------------------------------------------------------------------------
ACTION_PROMPT_TEMPLATE = """You are a strategic Product Manager for the Noon Buyer App.
Based on the top user feedback themes identified this week, generate exactly 3 concrete, actionable product/engineering recommendations.

CONSTRAINTS:
1. Generate exactly 3 actions.
2. Each action must be specific, feasible, and directly tied to the provided themes. Avoid generic advice like "improve the app".
3. Provide a short description (1-2 sentences) for how to implement the action.
4. Ensure no Personal Identifiable Information (PII) is included in the actions.

THEMES:
{themes_json}

Return ONLY valid JSON matching the schema below. Do not include markdown code blocks.
"""

ACTION_PROMPT = ChatPromptTemplate.from_template(ACTION_PROMPT_TEMPLATE)
