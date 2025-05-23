"""
FastAPI application initialization.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api import auth_router, did_router, ad_router
from auth.auth_middleware import auth_middleware


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title="DID WBA Example",
        description="DID WBA Authentication Example with Client and Server capabilities",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add authentication middleware
    @app.middleware("http")
    async def auth_middleware_wrapper(request, call_next):
        return await auth_middleware(request, call_next)
    
    # Include routers
    app.include_router(auth_router.router)
    app.include_router(did_router.router)
    app.include_router(ad_router.router)
    
    return app
