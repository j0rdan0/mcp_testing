#!/usr/bin/python3

from agents import Agent,SQLiteSession,Runner
import uuid
import os
import logging
import asyncio
import time
from aux import get_tempdir

class PinkAgent:
    def __init__(self):
        # the agent that has access to tools
        self.logger = logging.Logger(__name__)
        session_id = str(uuid.uuid4())
        self.session_filepath = os.path.join(get_tempdir(),session_id + ".db")
        self.session = SQLiteSession(session_id,self.session_filepath)
        self.mcp_servers = []
        self.mcp_agent = Agent(
            name="MCP Enhanced Agent",
            instructions='''You an assistance that has access to various MCP Servers you can use to help the use with his queries. Always first check to see if you
            can gather information needed from a tool rather than responding directly''',
            handoff_description="A MCP Enhanced Agent",
            mcp_servers=self.mcp_servers# to be later fetched.
            )
        # main agent you interact with 
        self.triage_agent = Agent(
            name="Triage Agent",
            instructions="You are an assistance, if the user will address any questions for which MCP Server access is require you will handoff to tools_agent. The tools you have access include Time Server, to answer time related queries",
            handoffs=[self.mcp_agent],
        )
    async def load_mcp_servers(self, servers):
        if not servers:
            return
        connected_servers = []
        for server in servers:
            server_name = getattr(server, 'name', type(server).__name__)
            try:
                await server.__aenter__()
                connected_servers.append(server)
            except Exception as e:
                self.logger.error(f"[*]Failed to initialize {server_name},err: {e} ")
        self.mcp_servers = connected_servers
        self.mcp_agent.mcp_servers = self.mcp_servers
        
    async def reload_mcp_servers(self,config):
        if self.mcp_servers:
            for server in self.mcp_servers:
                try:
                    await server.__aexit__(None,None,None)
                except asyncio.CancelledError:
                    self.logger.info("MCP cleanup interrupted (normal during shutdown)")
                except Exception as e:
                    self.logger.error(f"MCP cleanup error: {e}")
        reloaded_servers = config
        if not reloaded_servers:
            print("[*] No MCP servers found in config.")
            self.mcp_servers = []
            self.mcp_agent.mcp_servers = []
            return
        await self.load_mcp_servers(reloaded_servers)
        print("[*]Reloaded MCP Servers")
        
    async def chat(self,input):
        result = await Runner.run(self.triage_agent,input=input,session=self.session)
        # need to add error handling
        return result.final_output
    
    async def cleanup(self):
        self.session.close()
        if self.mcp_servers:
            for server in self.mcp_servers:
                try:
                    await server.__aexit__(None,None,None)
                except asyncio.CancelledError:
                    self.logger.info("MCP cleanup interrupted (normal during shutdown)")
                except Exception as e:
                    self.logger.error(f"MCP cleanup error: {e}")
        time.sleep(0.2)
        os.unlink(self.session_filepath)
       
    def get_mcp_servers(self):
           if self.mcp_servers:
               for server in self.mcp_servers:
                   server_name = getattr(server, 'name', type(server).__name__)
                   print(f"Loaded: {server_name}")
           else:
                print("No MCP servers loaded")
        
        
        

