import streamlit as st
import asyncio
import os
import threading
from dotenv import load_dotenv
from client import MCPClient
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentX — MCP Powered",
    page_icon="🔌",
    layout="centered"
)


def run_async_in_thread(coro):
    """Run async coroutine in a separate thread with its own event loop."""
    result = {"value": None, "error": None}

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result["value"] = loop.run_until_complete(coro)
        except Exception as e:
            import traceback
            result["error"] = traceback.format_exc()
        finally:
            loop.close()

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()

    if result["error"]:
        raise Exception(result["error"])
    return result["value"]

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentX — MCP Powered",
    page_icon="🔌",
    layout="centered"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔌 AgentX — MCP Edition")
st.caption("AI Agent powered by Model Context Protocol (MCP) — tools served via MCP server, consumed by LangChain agent.")

with st.expander("ℹ️ What is MCP?"):
    st.markdown("""
    **Model Context Protocol (MCP)** is an open standard by Anthropic that allows AI models
    to connect to external tools and data sources in a standardised way.

    In this app:
    - 🖥️ **MCP Server** (`server.py`) — exposes Weather, Search, Wikipedia & Summariser as MCP tools
    - 🤖 **MCP Client** (`client.py`) — connects to server, discovers tools, builds AI agent
    - 💬 **This UI** — chat interface on top of the MCP-powered agent

    This is the same architecture used in production AI systems at enterprises worldwide.
    """)

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="Enter your Groq API key",
        value=os.getenv("GROQ_API_KEY", "")
    )

    weather_api_key = st.text_input(
        "OpenWeather API Key (optional)",
        type="password",
        placeholder="For weather queries",
        value=os.getenv("OPENWEATHER_API_KEY", "")
    )

    if weather_api_key:
        os.environ["OPENWEATHER_API_KEY"] = weather_api_key

    st.divider()
    st.markdown("**🔌 MCP Server Tools:**")
    st.markdown("- 🌤️ `get_weather`")
    st.markdown("- 🔍 `web_search`")
    st.markdown("- 📖 `wiki_search`")
    st.markdown("- 📝 `summarise_text`")

    st.divider()
    st.markdown("**💡 Try asking:**")
    st.markdown("- *What's the weather in Delhi?*")
    st.markdown("- *Search latest LLM news*")
    st.markdown("- *Who is Jensen Huang?*")
    st.markdown("- *Summarise: [paste text]*")

    st.divider()
    st.markdown("Built by [Lovish Chhabra](https://www.linkedin.com/in/lovish-chhabra/)")

# ── Initialise MCP Agent ──────────────────────────────────────────────────────
if groq_api_key:
    if "mcp_agent" not in st.session_state or st.session_state.get("mcp_key") != groq_api_key:
        with st.spinner("🔌 Connecting to MCP server and discovering tools..."):
            try:
                os.environ["GROQ_API_KEY"] = groq_api_key
                client = MCPClient(groq_api_key)
                client.start()
                st.session_state["mcp_agent"] = client
                st.session_state["mcp_key"] = groq_api_key
                st.session_state["messages"] = []
                st.success("✅ Connected to MCP server! Agent ready.")
            except Exception as e:
                st.error(f"❌ Failed to connect to MCP server: {str(e)}")
                st.stop()
else:
    st.info("👈 Enter your Groq API key in the sidebar to get started.")
    st.stop()

# ── Chat Interface ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask AgentX (MCP Edition) anything..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔌 MCP Agent thinking and calling tools..."):
            try:
                from client import run_agent
                response = run_agent(
                    st.session_state["mcp_agent"],
                    prompt,
                    st.session_state["messages"][:-1]
                )
                st.markdown(response)
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": response
                })
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if st.session_state.get("messages"):
    if st.button("🗑️ Clear Chat"):
        st.session_state["messages"] = []
        st.rerun()