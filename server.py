import asyncio
import os
from mcp.server.fastmcp import FastMCP
from tools.weather import get_weather_data
from tools.search import web_search_data
from tools.wikipedia import wiki_search_data
from tools.summariser import summarise_text_data

# FastMCP is the modern way to build MCP servers in 1.x+
mcp = FastMCP("mcp-tools-server")


@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for any city. Input should be a city name like Gurgaon or London."""
    return get_weather_data(city)


@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for current real-time information using DuckDuckGo."""
    return web_search_data(query)


@mcp.tool()
def wiki_search(query: str) -> str:
    """Search Wikipedia for factual information about people, places, history or concepts."""
    return wiki_search_data(query)


@mcp.tool()
def summarise_text(text: str) -> str:
    """Summarise a long piece of text into concise bullet points."""
    return summarise_text_data(text)


if __name__ == "__main__":
    print("MCP Tools Server starting...")
    print("Exposing tools: get_weather, web_search, wiki_search, summarise_text")
    mcp.run(transport="stdio")