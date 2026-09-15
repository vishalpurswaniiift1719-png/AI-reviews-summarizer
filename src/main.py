"""
AI Reviews Summarizer for Noon — Entry Point
=============================================

Usage:
    python src/main.py

Launches the LangChain agent that orchestrates the full pipeline:
  1. Fetch Google Play reviews
  2. Process and clean reviews
  3. Cluster into themes
  4. Generate weekly pulse note
  5. Publish to Google Docs (via MCP)
  6. Create Gmail draft (via MCP)
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src.*` imports work
# when running as `python src/main.py` from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    """Entry point for the AI Reviews Summarizer pipeline."""
    from src.config import print_config_summary
    from src.agent import get_agent_executor

    print()
    print_config_summary()
    print()
    print("Starting LangChain Agent Orchestrator...")
    
    agent_executor = get_agent_executor()
    
    try:
        result = agent_executor.invoke({
            "input": "Generate this week's Noon app review pulse."
        })
    except Exception as e:
        print(f"\nPipeline failed: {e}", flush=True)
        sys.exit(1)
    
    print("\n" + "="*50)
    print("Agent Execution Finished")
    print("="*50)
    
    # Safely print to Windows console which may have cp1252 encoding
    output_text = result.get("output", "")
    print(output_text.encode('ascii', 'replace').decode('ascii'))


if __name__ == "__main__":
    main()
