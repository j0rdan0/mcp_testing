#!/usr/bin/env python3

import json
import os

def load_tools_config():
    config_file = "tools.json"
    if os.path.exists(config_file):
        try:
            with open(config_file,"r") as f:
                config_data = json.load(f)
            config_list = [] # parsed config entries 
            for tool_config in config_data.get("tools",[]):
                if tool_config.get("enabled",True):
                    env_dict = tool_config.get('env')
                    if env_dict:
                        for key, value in env_dict.items():
                            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                                env_var = value[2:-1]
                                env_dict[key] = os.environ.get(env_var, value)
                    config_list.append({
                        'command': tool_config['command'],
                        'args': tool_config['args'],
                        'env': env_dict
                    })
            return config_list
        except Exception as e:
            print(f"Failed fetching config from file: {e}")
            return None