import asyncio
import os
import sys
import threading
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from pydantic import create_model

load_dotenv()

SYSTEM_PROMPT = """You are AgentX, a smart AI assistant connected to an MCP server.
You have access to tools: get_weather, web_search, wiki_search, summarise_text.
Always use the right tool for the job. Be concise, accurate and helpful.
If a tool fails, let the user know and try an alternative approach.
"""


class MCPClient:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self._agent = None
        self._loop = None
        self._thread = None
        self._ready = threading.Event()
        self._error = None

    def start(self):
        """Start MCP session in background thread and wait until ready."""
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=30)
        if self._error:
            raise self._error

    def _run_forever(self):
        """Run async event loop forever in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_and_stay())
        except Exception as e:
            self._error = e
            self._ready.set()

    async def _connect_and_stay(self):
        """Connect to MCP server and keep session alive."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
        server_path = os.path.join(base_dir, "server.py")

        if not os.path.exists(venv_python):
            venv_python = sys.executable

        server_params = StdioServerParameters(
            command=venv_python,
            args=[server_path],
            env=dict(os.environ)
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected to MCP server!")

                tools_response = await session.list_tools()
                print(f"Found {len(tools_response.tools)} tools:")
                for t in tools_response.tools:
                    print(f"  - {t.name}")

                # Build LangChain tools that call MCP via this session
                lc_tools = self._build_lc_tools(session, tools_response.tools)

                # Build agent
                self._agent = self._build_agent(lc_tools)
                print("Agent ready!")

                # Signal ready
                self._ready.set()

                # Keep session alive forever (until app closes)
                await asyncio.Event().wait()

    def _build_lc_tools(self, session, mcp_tools):
        """Convert MCP tools to LangChain tools using the live session."""
        lc_tools = []
        for mcp_tool in mcp_tools:
            props = mcp_tool.inputSchema.get("properties", {}) if mcp_tool.inputSchema else {}
            fields = {k: (str, ...) for k in props} if props else {}
            schema = create_model(f"{mcp_tool.name}_schema", **fields) if fields else None

            tool_name = mcp_tool.name

            # Call MCP tool via the persistent session
            def make_tool_func(name):
                def func(**kwargs):
                    # Submit to background event loop and wait for result
                    future = asyncio.run_coroutine_threadsafe(
                        session.call_tool(name, kwargs),
                        self._loop
                    )
                    result = future.result(timeout=30)
                    return result.content[0].text if result.content else "No result"
                return func

            tool_kwargs = dict(
                name=mcp_tool.name,
                description=mcp_tool.description or f"Tool: {mcp_tool.name}",
                func=make_tool_func(tool_name)
            )
            if schema:
                tool_kwargs["args_schema"] = schema

            lc_tools.append(StructuredTool(**tool_kwargs))

        return lc_tools

    def _build_agent(self, tools):
        """Build LangGraph react agent."""
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=self.groq_api_key
        )
        return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

    def run_agent(self, question: str, chat_history: list) -> str:
        """Run the agent synchronously."""
        messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=question))

        result = self._agent.invoke({"messages": messages})
        return result["messages"][-1].content


def run_agent(agent_or_client, question: str, chat_history: list) -> str:
    """Wrapper for Streamlit app compatibility."""
    if isinstance(agent_or_client, MCPClient):
        return agent_or_client.run_agent(question, chat_history)
    # fallback for direct agent
    messages = [HumanMessage(content=msg["content"]) if msg["role"] == "user"
                else AIMessage(content=msg["content"]) for msg in chat_history]
    messages.append(HumanMessage(content=question))
    result = agent_or_client.invoke({"messages": messages})
    return result["messages"][-1].content


# ── Standalone terminal test ──────────────────────────────────────────────────
if __name__ == "__main__":
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("GROQ_API_KEY not found in .env")
        exit(1)

    client = MCPClient(groq_key)
    print("Starting MCP client...")
    client.start()

    print("\nAgentX MCP Client ready! (type exit to quit)\n")
    history = []
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit"]:
            break
        if not question:
            continue
        response = client.run_agent(question, history)
        print(f"\nAgentX: {response}\n")
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})