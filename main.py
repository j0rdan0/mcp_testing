#!/usr/bin/env python3

import asyncio
from dotenv import load_dotenv
from interactive_agent import InteractiveAgent
from aux import parse_args

load_dotenv()

async def main():
    args = parse_args()
    agent = InteractiveAgent(enhanced=args.enhanced)
    await agent.initialize()
    await agent.run_chat()
    
if __name__ == "__main__":
    asyncio.run(main())
