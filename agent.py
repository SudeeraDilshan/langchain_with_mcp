from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from agent_tools import inbuilt_tools
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant"),
        ("human", "{input}"),
        ("ai", "{agent_scratchpad}"),
    ]
)

class Agent:
    def __init__(self,mcp_tools:list,api_key=GOOGLE_API_KEY):
        self.tools = inbuilt_tools + mcp_tools  # Combine the tool lists properly
        self.prompt = prompt
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=api_key
        )
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
    
    async def process_input(self, user_input):
        """Process a single user input and return the agent's response"""
        response = await self.agent_executor.ainvoke({"input": user_input})
        return response["output"]
    
    async def run_interactive(self):
        """Run an interactive session with the agent"""
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                response = await self.process_input(user_input)
                print("AI:", response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")








