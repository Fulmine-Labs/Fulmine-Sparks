"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ModelEnum(str, Enum):
    """Available image generation models."""
    STABLE_DIFFUSION = "stable-diffusion"
    STABLE_DIFFUSION_XL = "stable-diffusion-xl"
    DALLE = "dall-e"


class InvoiceRequest(BaseModel):
    """Request model for creating an invoice."""
    model: ModelEnum = Field(..., description="Image generation model")
    prompt: str = Field(..., min_length=1, max_length=1000, description="Image prompt")
    num_outputs: int = Field(default=1, ge=1, le=4, description="Number of images")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    num_inference_steps: int = Field(default=50, ge=10, le=100, description="Inference steps")


class InvoiceResponse(BaseModel):
    """Response model for invoice creation."""
    invoice_id: str = Field(..., description="Unique invoice ID")
    amount: float = Field(..., description="Amount in BTC")
    payment_request: str = Field(..., description="BOLT11 payment request")
    status: str = Field(default="pending", description="Invoice status")
    model: str = Field(..., description="Image generation model")
    prompt: str = Field(..., description="Image prompt")


class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    invoice_id: str = Field(..., description="Invoice ID for payment verification")
    prompt: str = Field(..., description="Image prompt")
    model: ModelEnum = Field(default=ModelEnum.STABLE_DIFFUSION, description="Model to use")
    num_outputs: int = Field(default=1, ge=1, le=4, description="Number of images")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    num_inference_steps: int = Field(default=50, ge=10, le=100, description="Inference steps")


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    status: str = Field(..., description="Generation status (pending, completed, failed)")
    image_urls: Optional[List[str]] = Field(default=None, description="Generated image URLs")
    image_base64: Optional[List[str]] = Field(default=None, description="Base64 encoded images")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")


class ModerationCheckRequest(BaseModel):
    """Request model for content moderation check."""
    prompt: str = Field(..., min_length=1, max_length=1000, description="Text to check")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Safety threshold")


class ModerationCheckResponse(BaseModel):
    """Response model for moderation check."""
    is_safe: bool = Field(..., description="Whether content is safe")
    score: float = Field(..., ge=0.0, le=1.0, description="Safety score")
    reason: str = Field(..., description="Explanation of the result")


class PaymentStatusRequest(BaseModel):
    """Request model for checking payment status."""
    invoice_id: str = Field(..., description="Invoice ID")


class PaymentStatusResponse(BaseModel):
    """Response model for payment status."""
    invoice_id: str = Field(..., description="Invoice ID")
    status: str = Field(..., description="Payment status")
    amount: float = Field(..., description="Amount in BTC")
    confirmed: bool = Field(..., description="Whether payment is confirmed")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="1.0.0", description="API version")
    services: dict = Field(..., description="Status of individual services")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    code: Optional[str] = Field(default=None, description="Error code")
