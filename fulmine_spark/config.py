"""
Configuration management for Fulmine-Spark service.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    SERVICE_ENV: str = "development"  # development or production
    
    # Replicate API Configuration
    # The replicate library uses REPLICATE_API_TOKEN, but we support both for flexibility
    REPLICATE_API_TOKEN: Optional[str] = None
    REPLICATE_API_KEY: Optional[str] = None
    
    @property
    def replicate_api_key(self) -> Optional[str]:
        """Get Replicate API key, checking both TOKEN and KEY variants."""
        return self.REPLICATE_API_TOKEN or self.REPLICATE_API_KEY
    
    # BTCPay Server Configuration
    BTCPAY_SERVER_URL: Optional[str] = None
    BTCPAY_API_KEY: Optional[str] = None
    BTCPAY_STORE_ID: Optional[str] = None
    
    # Image Generation Models
    STABLE_DIFFUSION_MODEL: str = "stability-ai/stable-diffusion"
    STABLE_DIFFUSION_XL_MODEL: str = "stability-ai/stable-diffusion-xl"
    DALLE_MODEL: str = "openai/dall-e-3"
    
    # Pricing Configuration (in BTC)
    STABLE_DIFFUSION_PRICE: float = 0.00001  # ~$0.01 at current rates
    STABLE_DIFFUSION_XL_PRICE: float = 0.00002  # ~$0.02
    DALLE_PRICE: float = 0.00005  # ~$0.05
    
    # Moderation Configuration
    MODERATION_ENABLED: bool = True
    MODERATION_THRESHOLD: float = 0.15
    
    # Image Generation Configuration
    IMAGE_WIDTH: int = 512
    IMAGE_HEIGHT: int = 512
    NUM_INFERENCE_STEPS: int = 50
    GUIDANCE_SCALE: float = 7.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
