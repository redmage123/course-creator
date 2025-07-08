"""
Module entry point for running the software engineer agent
Allows execution via: python -m software_engineer_agent
"""

from .software_engineering_agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())