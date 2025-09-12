#!/usr/bin/env python3

from termcolor import colored, cprint
from openai_client import OpenAIChatClient

class Chat:
    def __init__(self,config):
        self.client = OpenAIChatClient(config)
    async def run_chat(self):
        await self.client.initialize()
        while True:
            try:
                cprint("user>","red",end="")
                msg = input().strip()
                if msg.lower() in ['quit', 'exit', 'q']:
                    await self.client.cleanup()
                    break
                if not msg:
                    continue
                # add handing of config reload
                
                if msg == "/reload":
                    await self.client.reload_tools()
                    continue
                response = await self.client.chat(msg)
                cprint("system>","blue",end="")
                print(response)
            except KeyboardInterrupt:
                cprint("\nExiting...","green")
                await self.client.cleanup()
                break
            except Exception as e:
                print(f"[*] Chat error: {e}")
    
    