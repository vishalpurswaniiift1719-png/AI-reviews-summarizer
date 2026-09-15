"""
LangChain agent definition for the AI Reviews Summarizer.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from src.config import GEMINI_API_KEY
from src.tools import (
    fetch_reviews,
    process_reviews,
    cluster_themes,
    generate_pulse,
    publish_and_draft_pulse
)

def get_agent_executor() -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0.0,
        api_key=GEMINI_API_KEY
    )
    
    tools = [
        fetch_reviews,
        process_reviews,
        cluster_themes,
        generate_pulse,
        publish_and_draft_pulse,
    ]
    
    # ReAct prompt template
    template = """You are a Review Pulse Agent for the Noon app. Execute these steps in strict order:
1. Fetch Google Play reviews using fetch_reviews
2. Process and clean reviews using process_reviews
3. Cluster into themes and extract insights using cluster_themes
4. Generate the weekly pulse note using generate_pulse
5. Publish to Google Docs and Gmail using publish_and_draft_pulse

Report the final status. Ensure each step succeeds before proceeding to the next.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)
    
    agent = create_react_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )
