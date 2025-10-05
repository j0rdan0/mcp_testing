#!/usr/bin/env python3

from pink_agent import PinkAgent
from termcolor import colored, cprint
from mcp_servers_loader import load_config
import logging
from aux import print_banner

class InteractiveAgent:
    def __init__(self,enhanced=False):
        self.client = PinkAgent()
        self.mcp_servers= load_config() if enhanced else []
        self.logger = logging.Logger(__name__)
    async def initialize(self):
        if self.mcp_servers:
            await self.client.load_mcp_servers(self.mcp_servers)
    async def run_chat(self):
        print_banner()
        while True:
            try:
                cprint("user>","red",end="")
                msg = input().strip()
                if msg.lower() in ['quit', 'exit', 'q']:
                    await self.client.cleanup()
                    break
                if not msg:
                    continue
                if msg.lower() == "/tools":
                    self.client.get_mcp_servers()
                    continue
                if msg.lower() == "/reload":
                    config = load_config()
                    await self.client.reload_mcp_servers(config)
                    continue
                response = await self.client.chat(msg)
                cprint("system>","blue",end="")
                print(response)
            except KeyboardInterrupt:
                cprint("\nExiting...","green")
                await self.client.cleanup()
                break
            except Exception as e:
                self.logger.error(f"[*]Chat error: {e}")
    