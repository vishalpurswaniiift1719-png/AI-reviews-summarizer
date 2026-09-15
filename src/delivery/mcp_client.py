"""
Centralized MCP client to connect to the deployed Google Workspace MCP server.
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.sse import sse_client

from src.config import MCP_SERVER_SSE_URL, MCP_AUTH_TOKEN

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_mcp_session():
    """Establish an SSE connection to the MCP Server."""
    if not MCP_SERVER_SSE_URL:
        raise ValueError("MCP_SERVER_SSE_URL is not configured.")
        
    url_with_auth = f"{MCP_SERVER_SSE_URL}?token={MCP_AUTH_TOKEN}"
        
    logger.info(f"Connecting to MCP Server at {MCP_SERVER_SSE_URL}")
    async with sse_client(url_with_auth) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


async def append_to_doc(document_id: str, text: str) -> dict:
    """Appends text to a Google Doc using the MCP server."""
    async with get_mcp_session() as session:
        result = await session.call_tool("google_doc_append", {
            "document_id": document_id,
            "content": text
        })
        
        # Result content is usually a TextContent object
        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return {"success": False, "error": "No response content"}


async def draft_email(to: list, subject: str, body: str) -> dict:
    """Creates a Gmail draft using the MCP server."""
    async with get_mcp_session() as session:
        result = await session.call_tool("gmail_create_draft", {
            "to": to,
            "subject": subject,
            "body": body
        })
        
        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return {"success": False, "error": "No response content"}
