#!/usr/bin/env python3

from openai import OpenAI
import mcp_client
import asyncio
import json
from config_loader import load_tools_config

class OpenAIChatClient:
    def __init__(self, config):
        self.openai = OpenAI()
        self.system_message = {
            "role": "system",
            "content": """You are a helpful assistant with access to various tools through MCP (Model Context Protocol).
            You can automatically use available tools when needed to answer user questions.
            When a user asks about time, dates, or related queries, check if you have appropriate tools available and use them.
            Always use the available tools to provide real, current data rather than giving generic responses.
            Never tell users to visit GitHub manually when you have tools to fetch the information directly.
            Always try to call the relevant GitHub tool instead of refusing.
            For example, if a user asks to list repositories, call `search_repositories` with a query like 'user:<username>'.
            Always provide helpful, accurate responses using the most current information from your tools."""
        }
        
        self.available_tools = {}              # name → MCP tool
        self.openai_functions = []             # converted MCP tools → OpenAI tool schema
        self.mcp_sessions = {}                 # tool name → session
        self.config_list = config
        self.mcp_client = mcp_client.Client()

    async def initialize(self):
        """Initialize the client - must be called after __init__"""
        await self.register_tools()

    async def cleanup(self):
        await self.mcp_client.cleanup()
        
        # TODO: this is where the tools config should go, for dynamic usage (and use kafka to fetch the configs)
        # as the tools apparently are sent with the system prompt, registering all of them at once increases the context window
    async def chat(self, user_message):
        try:
            input_list = [{"role": "user", "content": user_message}]

            response = self.openai.responses.create(
                model="gpt-5",
                instructions=self.system_message["content"],
                tools=self.openai_functions if self.openai_functions else None,
                tool_choice="auto" if self.openai_functions else None,
                reasoning={"effort": "low"},
                input=input_list
            )
            input_list += response.output  

            for item in response.output:
                if item.type == "function_call":
                    function_name = item.name
                    function_args = json.loads(item.arguments or "{}")

                    print(f"[*] Calling {function_name} with {function_args}")

                    tool_result = await self.execute_tool(function_name, function_args)

                    input_list.append({
                        "type": "function_call_output",
                                "call_id": item.call_id,
                                "output": json.dumps({
                                    "tool_result": tool_result
                                })}
                    )
                    final_response = self.openai.responses.create(
                        model="gpt-5",
                        reasoning={"effort": "low"},
                        input=input_list
                    )
                    final_text = final_response.output_text

                    return final_text
                elif item.type == "message":
                    # No tools, just text
                    final_response = response.output_text

            return final_response

        except Exception as e:
            print(f"Error while communicating with GPT-5: {e}")
            return "Something went wrong"

    def mcp_tool_to_openai_function(self, mcp_tool):
        return {
            "type": "function",
            "name": mcp_tool.name,
            "description": (
                mcp_tool.description
                or f"Use this tool to execute {mcp_tool.name}."
            ),
            "parameters": (
                mcp_tool.inputSchema
                if hasattr(mcp_tool, "inputSchema") and isinstance(mcp_tool.inputSchema, dict)
                else {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )

        }

    async def register_tools(self):
        try:
            if not self.config_list:
                return
            for config in self.config_list:
                mcp_session = await self.mcp_client.connect_local_server(config)
                result = await mcp_session.list_tools()
                tools = result.tools if hasattr(result, 'tools') else []

                for tool in tools:
                    self.available_tools[tool.name] = tool
                    self.mcp_sessions[tool.name] = mcp_session
                    openai_function = self.mcp_tool_to_openai_function(tool)
                    self.openai_functions.append(openai_function)
                    print(f"[*] Registered {tool.name}")
        except Exception as e:
            print(f"Error registering tool: {e}")

    async def execute_tool(self, tool_name, arguments):
        try:
            print(f"[*] Executing {tool_name} with args {arguments}")
            mcp_session = self.mcp_sessions.get(tool_name)
            if not mcp_session:
                return f"No session found for tool {tool_name}"
            result = await mcp_session.call_tool(tool_name, arguments)
            if hasattr(result, 'content') and result.content:
                if getattr(result.content[0], "text", None):
                    return result.content[0].text
                else:
                    return str(result.content[0])
            else:
                return f"Tool {tool_name} executed but returned no content"
        except Exception as e:
            print(f"Error executing tool: {e}")
            return f"Execution error: {e}"
        
    async def reload_tools(self):
        for session in self.mcp_sessions.values():
                try:
                    await session.cleanup()
                except:
                    pass
        # clear existing tool lists     
        self.available_tools.clear()
        self.openai_functions.clear()
        self.mcp_sessions.clear()
        
        new_config = load_tools_config() # tbi
        if new_config:
            self.config_list = new_config
            await self.register_tools()
            print("[*] Reloaded tools")
            
        
