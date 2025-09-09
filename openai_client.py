#!/usr/bin/env python3

from openai import OpenAI
import mcp_client
import asyncio
import json

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
        self.history = []
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
    async def chat(self, user_message):
        messages = [self.system_message] + self.history + [{"role": "user", "content": user_message}]
        try: 
            response = self.openai.chat.completions.create(
                model="gpt-5",
                messages=messages,
                tools=self.openai_functions if self.openai_functions else None,
                tool_choice="auto" if self.openai_functions else None
            )
            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments or "{}")

                print(f"[*] Calling {function_name}")
                tool_result = await self.execute_tool(function_name, function_args)
                
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls
                })
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
                # Get final response with tool result
                final_response = self.openai.chat.completions.create(
                    model="gpt-5",
                    messages=messages,
                   # max_completion_tokens=1000
                )
                # extend history
                self.history.extend([
                    {"role": "user", "content": user_message},
                    {
                        "role": "assistant", 
                        "content": message.content,
                        "tool_calls": message.tool_calls
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    },
                    {"role": "assistant", "content": final_response.choices[0].message.content}
                ])
                
                return final_response.choices[0].message.content
            
            else:
                self.history.extend([
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": message.content}
                ])
                return message.content

        except Exception as e:
            print(f"error while communicating with GPT-5: {e}")   
            return "Something went wrong."
    def mcp_tool_to_openai_function(self, mcp_tool):
        return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description or f"Execute {mcp_tool.name} tool",
            "parameters": (
                mcp_tool.inputSchema
                if hasattr(mcp_tool, "inputSchema") and mcp_tool.inputSchema
                else {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        }
    }
    async def register_tools(self): 
        try:
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
        
        
