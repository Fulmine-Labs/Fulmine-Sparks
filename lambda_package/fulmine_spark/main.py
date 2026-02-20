"""
Fulmine-Spark: Lightning-powered AI image generation service.

A stateless, serverless-ready service that accepts Lightning Network payments
and generates AI images using Replicate API.

Features:
- Lightning Network payments via BTCPay
- Multiple image generation models (Stable Diffusion, DALL-E)
- Content moderation and safety filtering
- Stateless architecture for horizontal scaling
- Production-ready error handling and logging
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Fulmine-Spark",
    description="Lightning-powered AI image generation service",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("Fulmine-Spark Starting Up")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.SERVICE_ENV}")
    logger.info(f"Host: {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
    logger.info(f"Replicate API: {'Configured' if settings.REPLICATE_API_KEY else 'Not configured'}")
    logger.info(f"BTCPay Server: {'Configured' if settings.BTCPAY_SERVER_URL else 'Not configured'}")
    logger.info(f"Moderation: {'Enabled' if settings.MODERATION_ENABLED else 'Disabled'}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info("Fulmine-Spark Shutting Down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Fulmine-Spark",
        "version": "1.0.0",
        "description": "Lightning-powered AI image generation",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        log_level="info",
    )
