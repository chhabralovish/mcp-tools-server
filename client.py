import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from dotenv import load_dotenv

load_dotenv()


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are AgentX, a smart AI assistant connected to an MCP (Model Context Protocol) server.

You have access to tools exposed by the MCP server:
- get_weather: Get current weather for any city
- web_search: Search the web for real-time information
- wiki_search: Search Wikipedia for factual knowledge
- summarise_text: Summarise any long text into bullet points

Always use the right tool for the job. Be concise, accurate and helpful.
If a tool fails, let the user know and try an alternative approach.
"""


class MCPClient:
    """Client that connects to MCP server and exposes tools to LangChain agent."""

    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.tools = []
        self.agent_executor = None

    async def connect_and_build(self):
        """Connect to MCP server, discover tools, build LangChain agent."""
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=dict(os.environ)
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialise connection
                await session.initialize()
                print("✅ Connected to MCP server")

                # Discover available tools
                tools_response = await session.list_tools()
                print(f"🔧 Discovered {len(tools_response.tools)} tools:")
                for t in tools_response.tools:
                    print(f"   - {t.name}: {t.description}")

                # Convert MCP tools to LangChain tools
                lc_tools = []
                for mcp_tool in tools_response.tools:
                    tool = self._mcp_to_langchain_tool(session, mcp_tool)
                    lc_tools.append(tool)

                # Build LangChain agent with discovered tools
                self.agent_executor = self._build_agent(lc_tools)
                return self.agent_executor

    def _mcp_to_langchain_tool(self, session, mcp_tool) -> StructuredTool:
        """Convert an MCP tool definition to a LangChain StructuredTool."""
        tool_name = mcp_tool.name

        async def tool_func(**kwargs):
            result = await session.call_tool(tool_name, kwargs)
            return result.content[0].text if result.content else "No result"

        def sync_tool_func(**kwargs):
            return asyncio.get_event_loop().run_until_complete(tool_func(**kwargs))

        # Build args schema from MCP inputSchema
        props = mcp_tool.inputSchema.get("properties", {})
        required = mcp_tool.inputSchema.get("required", [])

        from pydantic import create_model
        field_definitions = {}
        for prop_name, prop_def in props.items():
            field_definitions[prop_name] = (str, ...)

        schema = create_model(f"{tool_name}_schema", **field_definitions)

        return StructuredTool(
            name=tool_name,
            description=mcp_tool.description,
            func=sync_tool_func,
            args_schema=schema
        )

    def _build_agent(self, tools) -> AgentExecutor:
        """Build LangChain agent with MCP tools."""
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=self.groq_api_key
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )


# ── Standalone Test ───────────────────────────────────────────────────────────
async def test_client():
    """Test the MCP client directly from terminal."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY not found in .env")
        return

    client = MCPClient(groq_key)
    agent = await client.connect_and_build()

    print("\n🤖 AgentX MCP Client ready! Type your questions (or 'exit' to quit)\n")
    history = []

    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit"]:
            break
        if not question:
            continue

        result = agent.invoke({
            "input": question,
            "chat_history": history
        })
        answer = result["output"]
        print(f"\nAgentX: {answer}\n")

        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=answer))


if __name__ == "__main__":
    asyncio.run(test_client())