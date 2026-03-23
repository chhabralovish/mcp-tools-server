from duckduckgo_search import DDGS


def web_search_data(query: str) -> str:
    """Search the web using DuckDuckGo. Used by MCP server."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=4):
                results.append(f"📰 {r['title']}\n{r['body']}\n🔗 {r['href']}")

        return "\n\n---\n\n".join(results) if results else "No results found."

    except Exception as e:
        return f"Error performing web search: {str(e)}"