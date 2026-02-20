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
    # Using specific model versions from Replicate
    MODELS = {
        "stable-diffusion": {
            "model": "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            "cost": settings.STABLE_DIFFUSION_PRICE,
            "description": "Stable Diffusion v1.5",
        },
        "dall-e": {
            "model": "openai/dall-e-3:3711283151f5835402c01332a54cc16809921fc0d9fe9e9a65ce5967f1685a00",
            "cost": settings.DALLE_PRICE,
            "description": "DALL-E 3",
        },
        "nano-banana": {
            "model": "google/nano-banana-pro:9f57615b766710492f0887bec039aed69178c6db88839fca425ce6b78d858999",
            "cost": settings.STABLE_DIFFUSION_PRICE,
            "description": "Google Nano Banana Pro",
        },
    }
    
    def __init__(self):
        """Initialize the image generation service."""
        if not settings.replicate_api_key:
            logger.warning("REPLICATE_API_TOKEN or REPLICATE_API_KEY not set. Image generation will fail.")
    
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
        if not settings.replicate_api_key:
            raise ValueError("REPLICATE_API_TOKEN or REPLICATE_API_KEY not configured")
        
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
