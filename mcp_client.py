#!/usr/bin/env python3

from openai import OpenAI # to add modularity for different models
from contextlib import AsyncExitStack
from mcp import ClientSession,StdioServerParameters
from typing import Optional
from mcp.client.stdio import stdio_client
import asyncio

class Client:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        
    async def connect_local_server(self,config):
        server_params = StdioServerParameters(
            command=config["command"], args=config["args"], env=config["env"])
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        mcp_session = self.session
        return mcp_session
    # TODO: add implementation for connect_remote_server
    async def connect_remote_server(self):
        pass
    async def cleanup(self):  # Added cleanup method
        """Clean up resources"""
        await self.exit_stack.aclose()
        
        