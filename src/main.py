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

    # 1. Load and validate configuration (this also creates data dirs)
    from src.config import print_config_summary  # noqa: E402

    print()
    print_config_summary()
    print()
    print("Setup OK -- all dependencies loaded, config validated, directories created.")
    print()
    print("Next steps:")
    print("  • Phase 2: Implement review ingestion  (src/tools/fetch_reviews.py)")
    print("  • Phase 3: Implement data processing   (src/processing/)")
    print("  • Phase 4: Implement theme clustering   (src/chains/theme_chain.py)")
    print("  • Phase 5: Implement pulse generation   (src/tools/generate_pulse.py)")
    print("  • Phase 6: Implement MCP delivery       (src/delivery/)")
    print("  • Phase 7: Wire up the LangChain agent  (src/agent.py)")
    print()


if __name__ == "__main__":
    main()
