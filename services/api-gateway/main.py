"""API Gateway for Course Creator."""

from fastapi import FastAPI

app = FastAPI(title="Course Creator API Gateway")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Course Creator API Gateway", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
