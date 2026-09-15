"""
LangChain agent definition for the AI Reviews Summarizer.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from src.config import GEMINI_API_KEY
from src.tools import (
    fetch_reviews,
    process_reviews,
    cluster_themes,
    generate_pulse,
    publish_and_draft_pulse
)

def get_agent_executor():
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
    
    system_prompt = """You are a Review Pulse Agent for the Noon app. Execute these steps in strict order:
1. Fetch Google Play reviews using fetch_reviews
2. Process and clean reviews using process_reviews
3. Cluster into themes and extract insights using cluster_themes
4. Generate the weekly pulse note using generate_pulse
5. Publish to Google Docs and Gmail using publish_and_draft_pulse

Report the final status. Ensure each step succeeds before proceeding to the next."""
    
    # create_react_agent in langgraph acts as the executor
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    # We return an object that mimics the old AgentExecutor interface for main.py
    class AgentExecutorWrapper:
        def __init__(self, agent):
            self.agent = agent
            
        def invoke(self, inputs):
            result = self.agent.invoke(
                {"messages": [("user", inputs["input"])]}
            )
            # The last message is the AI response
            return {"output": result["messages"][-1].content}
            
    return AgentExecutorWrapper(agent)
