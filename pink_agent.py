#!/usr/bin/python3

from agents import Agent,SQLiteSession,Runner
import uuid
import os
import logging
import asyncio
import time
from aux import get_tempdir,system_prompt


class PinkAgent:
    def __init__(self):
        self.logger = logging.Logger(__name__)
        
        self.session = None # can further implement multiple session for agent, adding /session option to cli; using a current_session to keep track of the one to use
        self.session_filepath = None
        
        self.mcp_servers = []
        self.mcp_agent = None
        
        # main agent you interact with 
        self.triage_agent = Agent(
            name="Triage Agent",
            instructions= system_prompt,
            handoffs=[],
        )
    # create session only when chat is sent
    async def init_session(self):
        session_id = str(uuid.uuid4())
        self.session_filepath = os.path.join(get_tempdir(),session_id + ".db")
        self.session = SQLiteSession(session_id,self.session_filepath)
    
    # need to handle situations when config exists for a mcp server, but the process cant be started(e.g.Docker not up), this messes up the cleanup method
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
       
        # lazy instantiation of MCP Agent
        if not self.mcp_agent:
            self.mcp_agent = Agent(
            name="MCP Enhanced Agent",
            instructions='''You an assistance that has access to various MCP Servers you can use to help the use with his queries. Always first check to see if you
            can gather information needed from a tool rather than responding directly''',
            handoff_description="MCP Enhanced Agent",
            mcp_servers=self.mcp_servers
            )
            self.triage_agent.handoffs = [self.mcp_agent]
        else:
             self.mcp_agent.mcp_servers = self.mcp_servers
        
    async def reload_mcp_servers(self,config):
        if self.mcp_servers:
            self._close_mcp_servers()
        reloaded_servers = config
        if not reloaded_servers:
            print("[*]No MCP servers found in config.")
            self.mcp_servers = []
            if self.mcp_agent:
                self.mcp_agent.mcp_servers = []
            return
        await self.load_mcp_servers(reloaded_servers)
        print("[*]Reloaded MCP Servers")
        
    async def chat(self,input):
        if not self.session:
            await self.init_session()
        try:
            result = await Runner.run(self.triage_agent,input=input,session=self.session)
            return result.final_output
        
        except Exception as e:
                self.logger.error(f"[!] MCP Chat error: {repr(e)}", exc_info=True)
                return f"Internal error: {e}"
    
    async def cleanup(self):
        # this should also handle stuff like gracefully stopping containers when MCP servers are run using Docker
        if self.session:
            self.session.close()
        if self.mcp_servers:
            await self._close_mcp_servers()
        if self.session_filepath:
            time.sleep(0.2)
            os.unlink(self.session_filepath)
            
    async def _close_mcp_servers(self):
        for server in self.mcp_servers:
            try:
                await server.__aexit__(None, None, None)
            except asyncio.CancelledError:
                self.logger.info("MCP cleanup interrupted.")
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")

        self.mcp_servers.clear()
       
    def get_mcp_servers(self):
           if self.mcp_servers:
               for server in self.mcp_servers:
                   server_name = getattr(server, 'name', type(server).__name__)
                   print(f"Loaded: {server_name}")
           else:
                print("[*]No MCP servers loaded")
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.cleanup()
        
        
        

