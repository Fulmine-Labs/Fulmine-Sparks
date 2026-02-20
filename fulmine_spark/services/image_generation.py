"""
Image generation service using Replicate API.
Supports multiple models: Stable Diffusion, Stable Diffusion XL, DALL-E.
"""

import replicate
import logging
from typing import Optional, List
from ..config import settings

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating images using Replicate API."""
    
    # Model configurations
    MODELS = {
        "stable-diffusion": {
            "model": "stability-ai/stable-diffusion",
            "cost": settings.STABLE_DIFFUSION_PRICE,
            "description": "Stable Diffusion v1.5",
        },
        "stable-diffusion-xl": {
            "model": "stability-ai/stable-diffusion-xl",
            "cost": settings.STABLE_DIFFUSION_XL_PRICE,
            "description": "Stable Diffusion XL",
        },
        "dall-e": {
            "model": "openai/dall-e-3",
            "cost": settings.DALLE_PRICE,
            "description": "DALL-E 3",
        },
    }
    
    def __init__(self):
        """Initialize the image generation service."""
        if not settings.REPLICATE_API_KEY:
            logger.warning("REPLICATE_API_KEY not set. Image generation will fail.")
        
        # Set Replicate API key
        replicate.api_token = settings.REPLICATE_API_KEY
    
    @staticmethod
    def get_model_info(model_name: str) -> dict:
        """
        Get information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model configuration dictionary
        """
        if model_name not in ImageGenerationService.MODELS:
            raise ValueError(f"Unknown model: {model_name}")
        
        return ImageGenerationService.MODELS[model_name]
    
    @staticmethod
    def list_models() -> dict:
        """
        List all available models.
        
        Returns:
            Dictionary of available models
        """
        return {
            name: {
                "description": config["description"],
                "cost": config["cost"],
            }
            for name, config in ImageGenerationService.MODELS.items()
        }
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "stable-diffusion",
        num_outputs: int = 1,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50,
    ) -> List[str]:
        """
        Generate an image using Replicate API.
        
        Args:
            prompt: Text description of the image to generate
            model: Model to use (stable-diffusion, stable-diffusion-xl, dall-e)
            num_outputs: Number of images to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            
        Returns:
            List of image URLs
            
        Raises:
            ValueError: If model is unknown or API key is not set
        """
        if not settings.REPLICATE_API_KEY:
            raise ValueError("REPLICATE_API_KEY not configured")
        
        model_info = self.get_model_info(model)
        model_path = model_info["model"]
        
        try:
            logger.info(f"Generating image with {model}: {prompt}")
            
            # Call Replicate API
            output = replicate.run(
                model_path,
                input={
                    "prompt": prompt,
                    "num_outputs": num_outputs,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps,
                }
            )
            
            # Output is a list of URLs
            if isinstance(output, list):
                urls = output
            else:
                urls = [output]
            
            logger.info(f"Successfully generated {len(urls)} image(s)")
            return urls
            
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise ValueError(f"Image generation failed: {str(e)}")
    
    @staticmethod
    def get_cost(model: str) -> float:
        """
        Get the cost of generating an image with a model.
        
        Args:
            model: Model name
            
        Returns:
            Cost in BTC
        """
        model_info = ImageGenerationService.get_model_info(model)
        return model_info["cost"]


# Global image generation service instance
image_generation_service = ImageGenerationService()
