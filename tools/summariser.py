from langchain_groq import ChatGroq
import os


def summarise_text_data(text: str) -> str:
    """Summarise text into bullet points using Groq LLM. Used by MCP server."""
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return "GROQ_API_KEY not found in environment."

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            groq_api_key=api_key
        )

        response = llm.invoke(
            f"Summarise the following text into 5 clear bullet points:\n\n{text}\n\nSummary:"
        )
        return f"📝 **Summary:**\n\n{response.content}"

    except Exception as e:
        return f"Error summarising text: {str(e)}"