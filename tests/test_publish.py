import asyncio
from src.tools.publish_mcp import publish_and_draft_pulse

def test():
    content = """# Noon App Pulse — Test
## 🔥 Top Themes
1. Test Theme
> "Test Quote"
💡 **Action:** Test Action
"""
    print("Testing publish_and_draft_pulse...")
    result = publish_and_draft_pulse.invoke({"pulse_content": content})
    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print("Result written to test_result.txt")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test()
