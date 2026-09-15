import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_mcp_email():
    url = "https://google-workspace-mcp-production-c1aa.up.railway.app/sse"
    print(f"Connecting to {url}...")
    
    async with sse_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            print("Session established!")
            
            # Initialize the session
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            
            pulse_content = """# Noon App Pulse — Week of 2026-09-08 to 2026-09-15

## 🔥 Top Themes This Week

### 1. Delivery Failures & Unnotified Cancellations
Many users are extremely frustrated with delivery drivers failing to find their address and immediately canceling orders without attempting to contact them first.

### 2. Delayed Refunds & Unhelpful Customer Support
Users are experiencing prolonged delays (20+ days) in receiving their money back for canceled or returned items, and customer support is repeatedly described as unhelpful.

### 3. Search Engine Accuracy & Empty Packages
Following a recent app update, users are complaining that the search engine is broken or inaccurate.
"""
            
            # Call gmail_create_draft tool
            print("\nCalling gmail_create_draft...")
            try:
                result = await session.call_tool("gmail_create_draft", {
                    "to": ["team@example.com"],
                    "subject": "Weekly Noon App Pulse — 2026-09-15",
                    "body": pulse_content
                })
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_email())
