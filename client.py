from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
import asyncio
from agent import Agent


server_params = StdioServerParameters(
    command="env\\Scripts\\python",
    args=["server.py"]
)

async def run_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            agent = Agent(mcp_tools=mcp_tools)  # Initialize the agent with MCP tools
            await agent.run_interactive()  # Start the interactive session
            
        
if __name__ == "__main__":
    asyncio.run(run_agent())
