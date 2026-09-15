"""
LangChain tool to publish the pulse note via the deployed MCP server.
"""

import logging
import asyncio
from datetime import datetime
from langchain_core.tools import tool

from src.config import TARGET_GOOGLE_DOC_ID, EMAIL_RECIPIENT, EMAIL_SUBJECT
from src.delivery.mcp_client import append_to_doc, draft_email

logger = logging.getLogger(__name__)


@tool
def publish_and_draft_pulse(pulse_content: str) -> str:
    """
    Appends the pulse to the rolling Google Doc and creates a Gmail draft 
    using the deployed MCP server.
    """
    # Create event loop if not running since this is an async operation inside a sync tool
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # In a real async agent, we'd use an async tool. 
        # For simplicity in this sync tool, we use asyncio.run in a separate thread or just run it if no loop
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(_run_mcp_delivery(pulse_content))
    else:
        return asyncio.run(_run_mcp_delivery(pulse_content))


async def _run_mcp_delivery(pulse_content: str) -> str:
    results = []
    
    # 1. Append to Google Docs
    if TARGET_GOOGLE_DOC_ID:
        try:
            doc_res = await append_to_doc(TARGET_GOOGLE_DOC_ID, "\n\n" + pulse_content)
            if doc_res.get("success"):
                results.append("✅ Appended to Google Doc successfully.")
            else:
                results.append(f"❌ Google Doc Error: {doc_res.get('error')}")
        except Exception as e:
            logger.error(f"Failed to append to doc: {e}")
            results.append(f"❌ Google Doc Exception: {e}")
    else:
        results.append("⚠️ Skipped Google Docs (TARGET_GOOGLE_DOC_ID not set).")
        
    # 2. Draft Email
    if EMAIL_RECIPIENT:
        today = datetime.now().strftime("%Y-%m-%d")
        subject = EMAIL_SUBJECT.format(date=today)
        
        # Ensure recipient is a list
        recipients = [r.strip() for r in EMAIL_RECIPIENT.split(',')]
        
        try:
            email_res = await draft_email(recipients, subject, pulse_content)
            if email_res.get("success"):
                results.append(f"✅ Drafted email to {EMAIL_RECIPIENT} successfully (Draft ID: {email_res.get('draft_id')}).")
            else:
                results.append(f"❌ Email Draft Error: {email_res.get('error')}")
        except Exception as e:
            logger.error(f"Failed to draft email: {e}")
            results.append(f"❌ Email Draft Exception: {e}")
    else:
        results.append("⚠️ Skipped Email Draft (EMAIL_RECIPIENT not set).")
        
    # 3. Save IDs to dashboard for UI linking
    mcp_meta = {
        "document_id": TARGET_GOOGLE_DOC_ID if TARGET_GOOGLE_DOC_ID else None,
        "draft_id": email_res.get('draft_id') if ('email_res' in locals() and email_res.get("success")) else None
    }
    try:
        import json
        from pathlib import Path
        meta_path = Path("dashboard/data/mcp_sync.json")
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w") as f:
            json.dump(mcp_meta, f)
    except Exception as e:
        logger.error(f"Failed to save mcp_sync.json: {e}")

    return "\n".join(results)
