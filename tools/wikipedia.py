import wikipedia


def wiki_search_data(query: str) -> str:
    """Search Wikipedia for factual information. Used by MCP server."""
    try:
        results = wikipedia.search(query, results=3)
        if not results:
            return f"No Wikipedia results found for '{query}'."

        page = wikipedia.page(results[0], auto_suggest=False)
        summary = wikipedia.summary(results[0], sentences=5, auto_suggest=False)

        return f"📖 **{page.title}**\n\n{summary}\n\n🔗 {page.url}"

    except wikipedia.exceptions.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=5)
            return f"📖 **{e.options[0]}**\n\n{summary}"
        except:
            return f"Multiple results for '{query}'. Try: {', '.join(e.options[:5])}"

    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."

    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"