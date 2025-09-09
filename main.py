#!/usr/bin/env python3

import asyncio
import mcp_client
from interactive_chat import Chat
from dotenv import load_dotenv
from os import environ

load_dotenv()

# TODO: add a loop for instantiating the MCP client from a list of configs using Kafka producers
config = {
    "command": "uvx",
    "args":["mcp-server-time"],
    "env": None
}
config_github = {
    "command": "/Users/j0rdan0/mcp-servers/github-mcp-server/main",
    "args": ["stdio"],
    "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    }
}

async def main():
    config_list= [config,config_github]
    chat =  Chat(config_list)
    await chat.run_chat() 
    
if __name__ == "__main__":
    asyncio.run(main())
