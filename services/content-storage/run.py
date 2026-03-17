#!/usr/bin/env python3
"""
Startup script for content-storage service
"""

import uvicorn
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        reload=config.service.debug,
        log_level=config.service.log_level.lower()
    )
