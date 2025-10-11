#!/usr/bin/env python3

from argparse import ArgumentParser
import tempfile
import sys
import logfire
import os

system_prompt_triage_agent = '''You are a triage assistant, if the user will address any questions for which MCP Server access is require you will handoff to MCP Enhanced Agent.
The tools you have access include Time Server, Github MCP server, Azure MCP server, DeepWiki MCP Server. Always check first if a MCP server is available when unable to answer a user question. If so
always perform the handover, do not try to respond directly to the user. Never ask the user confirmation for doing handover to Enhanced MCP Agent.'''

system_prompt_mcp_agent = '''You an assistance that has access to various MCP Servers you can use to help the use with his queries. Always first check to see if you
can gather information needed from a tool rather than responding directly'''           

def print_banner():
    RED = "\033[31m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    banner = rf'''
    {CYAN}
      _____ _       _                               _   
 |  __ (_)     | |        /\\                   | |  
 | |__) | _ __ | | __    /  \   __ _  ___ _ __ | |_ 
 |  ___/ | '_ \| |/ /   / /\ \ / _` |/ _ \ '_ \| __|
 | |   | | | | |   <   / ____ \ (_| |  __/ | | | |_ 
 |_|   |_|_| |_|_|\_\ /_/    \_\__, |\___|_| |_|\__|
                                __/ |               
                               |___/     {RESET}           
    '''
    print(banner)
    print("Available commands:")
    print("/reload - reload MCP tools configuration") # to implement
    print("/tools - list loaded MCP Servers") # to implement
    
def parse_args():
    parser = ArgumentParser(prog="PinkAI Agent",description="Simple GPT Agent with MCP server enhancement options")
    parser.add_argument("-e","--enhanced",type=bool,help="enable MCP Servers")
    parser.add_argument("-t","--trace",type=bool,help="enable Logfire tracing")
    args = parser.parse_args()
    return args

def get_tempdir():
    if sys.platform == "darwin": # where TMPDIR if fucked up anyway
        return "/tmp"
    # on rest of OSes it behaves fine
    return tempfile.gettempdir()
def enable_tracing():
    logfire.configure(token=os.environ["LOGFIRE_TOKEN"],console=False)
    logfire.instrument_openai_agents()