import asyncio
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from tools.weather import get_weather_data
from tools.search import web_search_data
from tools.wikipedia import wiki_search_data
from tools.summariser import summarise_text_data

load_dotenv()

# ── Initialise MCP Server ─────────────────────────────────────────────────────
server = Server("mcp-tools-server")


# ── List Tools ────────────────────────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Expose available tools to any MCP client."""
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for any city in the world.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name e.g. 'Gurgaon', 'London', 'New York'"
                    }
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="web_search",
            description="Search the web for current, real-time information using DuckDuckGo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query e.g. 'latest AI news 2026'"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="wiki_search",
            description="Search Wikipedia for factual information about people, places, concepts, history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term e.g. 'Sundar Pichai' or 'Quantum Computing'"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="summarise_text",
            description="Summarise a long piece of text into concise bullet points.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to summarise"
                    }
                },
                "required": ["text"]
            }
        )
    ]


# ── Call Tool ─────────────────────────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute the requested tool and return results."""

    try:
        if name == "get_weather":
            result = get_weather_data(arguments["city"])

        elif name == "web_search":
            result = web_search_data(arguments["query"])

        elif name == "wiki_search":
            result = wiki_search_data(arguments["query"])

        elif name == "summarise_text":
            result = summarise_text_data(arguments["text"])

        else:
            result = f"Unknown tool: {name}"

    except Exception as e:
        result = f"Error executing tool '{name}': {str(e)}"

    return [types.TextContent(type="text", text=result)]


# ── Run Server ────────────────────────────────────────────────────────────────
async def main():
    print("🚀 MCP Tools Server starting...")
    print("📡 Exposing tools: get_weather, web_search, wiki_search, summarise_text")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())