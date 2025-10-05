#!/usr/bin/env python3

from agents.mcp import MCPServerStdio
import json
import logging
import os

config_file = "mcp-servers.json"
logger = logging.Logger("debug")

def load_config():
    mcp_servers  = [] # list of MCPServerStdio
    try:
        with open(config_file,"r") as f:
            config_dict = json.load(f)
    except Exception as e:
        logger.error(f"[*]Failed reading config file for MCP servers,err: {e} ")
        return mcp_servers
    if not config_dict["mcp-servers"]:
        return mcp_servers
    for config  in config_dict["mcp-servers"]:
        # check if env vars is set
        env_vars = config["params"].get("env")
        if env_vars:
            for key, value in env_vars.items():
                if isinstance(value,str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    env_vars[key] = os.environ.get(env_var, value)
        mcp_server = MCPServerStdio(name=config["name"],params=config["params"],cache_tools_list=True,client_session_timeout_seconds=10)
        mcp_servers.append(mcp_server)
    return mcp_servers


    
    