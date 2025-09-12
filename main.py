#!/usr/bin/env python3

import asyncio
import mcp_client
from interactive_chat import Chat
from dotenv import load_dotenv
import sys
from config_loader import load_tools_config

load_dotenv()

async def main():
    config_list =  None
    if len(sys.argv) > 1 and (sys.argv[1] == "--with-tools" or sys.argv[1] == "-tools"):
        config_list = load_tools_config()
    chat =  Chat(config_list)
    await chat.run_chat() 
    
if __name__ == "__main__":
    asyncio.run(main())
