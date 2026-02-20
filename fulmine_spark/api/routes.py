"""
API routes for Fulmine-Spark service.
Handles invoice creation, image generation, and payment verification.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from .models import (
    InvoiceRequest, InvoiceResponse,
    ImageGenerationRequest, ImageGenerationResponse,
    ModerationCheckRequest, ModerationCheckResponse,
    PaymentStatusRequest, PaymentStatusResponse,
    HealthCheckResponse,
    ErrorResponse,
)
from ..services.lightning_payment import payment_service
from ..services.image_generation import image_generation_service
from ..services.moderation import moderation_service
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status and component status
    """
    services = {
        "moderation": "operational",
        "image_generation": "operational" if settings.REPLICATE_API_KEY else "unconfigured",
        "lightning_payment": "operational" if settings.BTCPAY_SERVER_URL else "unconfigured",
    }
    
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        services=services,
    )


@router.post("/invoice", response_model=InvoiceResponse)
async def create_invoice(request: InvoiceRequest):
    """
    Create a Lightning invoice for image generation.
    
    Args:
        request: Invoice request with model and prompt
        
    Returns:
        Invoice with payment request (BOLT11)
        
    Raises:
        HTTPException: If invoice creation fails
    """
    try:
        # Check moderation
        is_safe, score, reason = moderation_service.is_safe(request.prompt)
        if not is_safe:
            logger.warning(f"Prompt rejected by moderation: {reason}")
            raise HTTPException(
                status_code=400,
                detail=f"Prompt rejected: {reason}",
            )
        
        # Get model cost
        cost = image_generation_service.get_cost(request.model.value)
        
        # Create invoice via BTCPay
        invoice_data = await payment_service.create_invoice(
            amount=cost,
            currency="BTC",
            description=f"Image generation: {request.prompt[:50]}",
            order_id=f"img-{int(time.time())}",
        )
        
        payment_request = payment_service.get_payment_request(invoice_data)
        
        return InvoiceResponse(
            invoice_id=invoice_data.get("id"),
            amount=cost,
            payment_request=payment_request or "",
            status=invoice_data.get("status", "pending"),
            model=request.model.value,
            prompt=request.prompt,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invoice creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invoice creation failed: {str(e)}",
        )


@router.get("/image/{invoice_id}", response_model=ImageGenerationResponse)
async def generate_image(
    invoice_id: str,
    prompt: str = Query(..., min_length=1, max_length=1000),
    model: str = Query(default="stable-diffusion"),
    num_outputs: int = Query(default=1, ge=1, le=4),
    guidance_scale: float = Query(default=7.5, ge=1.0, le=20.0),
    num_inference_steps: int = Query(default=50, ge=10, le=100),
):
    """
    Generate an image after payment is confirmed.
    
    Args:
        invoice_id: Invoice ID for payment verification
        prompt: Image generation prompt
        model: Model to use
        num_outputs: Number of images
        guidance_scale: Guidance scale
        num_inference_steps: Number of inference steps
        
    Returns:
        Generated image URLs or base64 encoded images
        
    Raises:
        HTTPException: If payment not confirmed or generation fails
    """
    try:
        # Check payment status
        is_confirmed = await payment_service.is_payment_confirmed(invoice_id)
        if not is_confirmed:
            raise HTTPException(
                status_code=402,
                detail="Payment not confirmed",
            )
        
        # Check moderation
        is_safe, score, reason = moderation_service.is_safe(prompt)
        if not is_safe:
            logger.warning(f"Prompt rejected by moderation: {reason}")
            raise HTTPException(
                status_code=400,
                detail=f"Prompt rejected: {reason}",
            )
        
        # Generate image
        start_time = time.time()
        image_urls = await image_generation_service.generate_image(
            prompt=prompt,
            model=model,
            num_outputs=num_outputs,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
        )
        processing_time = time.time() - start_time
        
        return ImageGenerationResponse(
            status="completed",
            image_urls=image_urls,
            error=None,
            processing_time=processing_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}",
        )


@router.post("/moderation/check", response_model=ModerationCheckResponse)
async def check_moderation(request: ModerationCheckRequest):
    """
    Check if a prompt passes content moderation.
    
    Args:
        request: Moderation check request
        
    Returns:
        Moderation check result
    """
    try:
        is_safe, score, reason = moderation_service.is_safe(
            request.prompt,
            threshold=request.threshold,
        )
        
        return ModerationCheckResponse(
            is_safe=is_safe,
            score=score,
            reason=reason,
        )
        
    except Exception as e:
        logger.error(f"Moderation check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Moderation check failed: {str(e)}",
        )


@router.post("/payment/status", response_model=PaymentStatusResponse)
async def check_payment_status(request: PaymentStatusRequest):
    """
    Check the status of a payment.
    
    Args:
        request: Payment status request
        
    Returns:
        Payment status
        
    Raises:
        HTTPException: If payment check fails
    """
    try:
        invoice = await payment_service.get_invoice(request.invoice_id)
        is_confirmed = await payment_service.is_payment_confirmed(request.invoice_id)
        
        return PaymentStatusResponse(
            invoice_id=request.invoice_id,
            status=invoice.get("status", "unknown"),
            amount=float(invoice.get("amount", 0)),
            confirmed=is_confirmed,
        )
        
    except Exception as e:
        logger.error(f"Payment status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Payment status check failed: {str(e)}",
        )


@router.get("/models")
async def list_models():
    """
    List available image generation models.
    
    Returns:
        Dictionary of available models with descriptions and costs
    """
    return image_generation_service.list_models()
