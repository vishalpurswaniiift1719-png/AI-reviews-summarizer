"""
Prompt template for generating the final weekly pulse note.
"""
from langchain_core.prompts import ChatPromptTemplate

PULSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert product manager and technical writer for the Noon App.
Your task is to generate a weekly pulse note based on user reviews.
The pulse note must strictly follow this exact markdown structure and be <= 250 words:

# Noon App Pulse — Week of [DATE_RANGE]

## 🔥 Top Themes This Week

### 1. [Theme 1 Name] ([Theme 1 Count] reviews)
> "[Theme 1 Verbatim Quote]"
💡 **Action:** [Theme 1 Action]

### 2. [Theme 2 Name] ([Theme 2 Count] reviews)
> "[Theme 2 Verbatim Quote]"
💡 **Action:** [Theme 2 Action]

### 3. [Theme 3 Name] ([Theme 3 Count] reviews)
> "[Theme 3 Verbatim Quote]"
💡 **Action:** [Theme 3 Action]

---
📊 Based on [TOTAL_REVIEWS] reviews from [DATE_START] – [DATE_END]
⭐ Average rating: [AVERAGE_RATING] / 5

RULES:
1. Do not include any PII (names, emails, phone numbers, etc.).
2. You must output exactly 3 themes, 3 quotes, and 3 actions based on the provided inputs.
3. Keep the entire response under 250 words. Be concise.
4. Do not output anything else other than the requested markdown."""),
    ("human", """Here is the data for this week's pulse:

Metadata:
- Date Range: {date_range}
- Date Start: {date_start}
- Date End: {date_end}
- Total Reviews Analyzed: {total_reviews}
- Average Rating: {average_rating}

Themes and Actions:
{themes_and_actions}

Generate the pulse note.""")
])

RE_PROMPT_WORD_COUNT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert product manager and technical writer for the Noon App.
You previously generated a pulse note, but it exceeded the strict 250-word limit.
Your task is to rewrite the pulse note to be strictly under 250 words while preserving the exact markdown structure and all information.
Be extremely concise. Cut unnecessary adjectives.

Structure to preserve:
# Noon App Pulse — Week of [DATE_RANGE]

## 🔥 Top Themes This Week
...
"""),
    ("human", "Original Draft ({word_count} words):\n\n{draft}\n\nPlease rewrite this draft to be under 250 words.")
])
