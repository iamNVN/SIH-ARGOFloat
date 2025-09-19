import os
import traceback
from typing import Optional
from dotenv import load_dotenv
from utils.logger import logger
from anthropic import Anthropic
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = Anthropic()
        self.tools = []
        self.messages = []
        self.logger = logger

    async def connect_to_server(self, server_script_path: str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server script must be a Python or JavaScript file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(command=command, args=[server_script_path],env=None)

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()

            self.logger.info(f"Connected to MCP server")

            mcp_tools = await self.get_mcp_tools()

            self.tools = [
                {
                    "name":tool.name,
                    "description":tool.description,
                    "input_schema":tool.inputSchema,
                }
                for tool in mcp_tools
            ]

            self.logger.info(f"Available MCP tools: {[tool['name'] for tool in self.tools]}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            traceback.print_exc()
            raise e

    async def get_mcp_tools(self):
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            self.logger.error(f"Failed to get MCP tools: {e}")
            raise e
        
    async def get_table_schema(self):
        try:
            response = await self.session.call_tool("get_schema", {})
            return response
        except Exception as e:
            self.logger.error(f"Failed to get table schema: {e}")
            raise e

    async def process_query(self, query: str):
        try:
            self.logger.info(f"Processing query: {query}")
            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)

            while True:
                response = await self.call_llm()

                if response.content[0].type == "text" and len(response.content) == 1:
                    assistant_message = {"role": "assistant", "content": response.content[0].text}
                    self.messages.append(assistant_message)
                    break

                assistant_message = {
                    "role": "assistant",
                    "content": response.to_dict()["content"]                    
                }
                self.messages.append(assistant_message)

                for content in response.content:
                    if content.type == "tool_use":
                        tool_name = content.name
                        tool_args = content.input
                        tool_use_id = content.id
                        self.logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                        try:
                            result = await self.session.call_tool(tool_name, tool_args)
                            self.logger.info(f"Tool {tool_name} result: {result}...")
                            self.messages.append({
                                "role":"user",
                                "content": [
                                    {
                                        "type":"tool_result",
                                        "tool_use_id":tool_use_id,
                                        "content":result.content,
                                    }
                                ]
                            })
                    
                        except Exception as e:
                            self.logger.error(f"Tool call failed: {e}")
                            raise e
            return self.messages    
        except Exception as e:
            self.logger.error(f"Failed to process query: {e}")
            traceback.print_exc()
            raise e

    async def call_llm(self):
        try:
            self.logger.info("Calling LLM")
            response = self.llm.messages.create(
                model="claude-3-5-haiku-20241022",
                temperature=0,
                max_tokens=3000,
                messages=self.messages,
                tools=self.tools,
            )
            return response
        except Exception as e:
            self.logger.error(f"Failed to call LLM: {e}")
            raise e
        
    async def get_sql_query(self, query: str):
        try:
            response = await self.session.call_tool("get_sql_query", {"query": query})
            return response
        except Exception as e:
            self.logger.error(f"Failed to get SQL query: {e}")
            raise e

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info(f"Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            traceback.print_exc()
            raise e
