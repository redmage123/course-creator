#!/usr/bin/env python3
"""Simple test FastAPI app to verify basic functionality"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Organization Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test")  
async def test():
    return {"message": "Test endpoint working"}

@app.post("/api/v1/organizations")
async def create_org():
    return {"message": "Organization creation endpoint working", "test": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)