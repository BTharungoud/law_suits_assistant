"""
FastAPI application factory and initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import cases

app = FastAPI(
    title="Law Assistant API",
    description="AI-powered legal case prioritization system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(cases.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Law Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "openapi_schema": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    )
