#!/usr/bin/env python3
"""
AWS Lambda handler for Fulmine-Sparks API.
Serverless image generation with Replicate.
"""

import json
import os
import sys
import base64
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from fulmine_spark.services.image_generation import image_generation_service
from fulmine_spark.services.moderation import moderation_service

# Initialize services
import asyncio

def lambda_handler(event, context):
    """
    AWS Lambda handler for HTTP requests.
    
    Routes:
    - GET /health - Health check
    - POST /api/v1/moderation/check - Check content safety
    - POST /api/v1/services/image/generate - Generate image
    - GET /api/v1/services/image/models - List models
    """
    
    try:
        # Parse request
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('rawPath', '/')
        body = event.get('body', '{}')
        
        # Parse JSON body if present
        try:
            if isinstance(body, str):
                body_data = json.loads(body) if body else {}
            else:
                body_data = body
        except json.JSONDecodeError:
            body_data = {}
        
        print(f"Request: {http_method} {path}")
        
        # Route requests
        if path == '/health' and http_method == 'GET':
            return health_check()
        
        elif path == '/api/v1/moderation/check' and http_method == 'POST':
            return check_moderation(body_data)
        
        elif path == '/api/v1/services/image/generate' and http_method == 'POST':
            return generate_image(body_data)
        
        elif path == '/api/v1/services/image/models' and http_method == 'GET':
            return list_models()
        
        elif path == '/' and http_method == 'GET':
            return root_endpoint()
        
        else:
            return error_response(404, "Endpoint not found")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, str(e))


def health_check():
    """Health check endpoint."""
    return success_response({
        "status": "ok",
        "service": "Fulmine-Sparks Lambda",
        "timestamp": datetime.now().isoformat()
    })


def root_endpoint():
    """Root endpoint with API documentation."""
    return success_response({
        "service": "Fulmine-Sparks Serverless API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /api/v1/moderation/check": "Check if content is safe",
            "POST /api/v1/services/image/generate": "Generate an image",
            "GET /api/v1/services/image/models": "List available models"
        },
        "documentation": "https://github.com/Fulmine-Labs/Fulmine-Sparks"
    })


def check_moderation(body_data):
    """Check if content is safe."""
    try:
        prompt = body_data.get('prompt', '')
        threshold = body_data.get('threshold', 0.15)
        
        if not prompt:
            return error_response(400, "No prompt provided")
        
        print(f"Checking moderation for: {prompt}")
        
        # Check content (async)
        is_safe, score, reason = asyncio.run(
            moderation_service.check_content(prompt, threshold)
        )
        
        result = {
            "prompt": prompt,
            "is_safe": is_safe,
            "score": score,
            "reason": reason,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Result: safe={is_safe}, score={score:.2f}")
        return success_response(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, str(e))


def generate_image(body_data):
    """Generate an image."""
    try:
        prompt = body_data.get('prompt', '')
        model = body_data.get('model', 'stable-diffusion')
        num_outputs = body_data.get('num_outputs', 1)
        guidance_scale = body_data.get('guidance_scale', 7.5)
        num_inference_steps = body_data.get('num_inference_steps', 50)
        
        if not prompt:
            return error_response(400, "No prompt provided")
        
        print(f"Generating image for: {prompt}")
        
        # Check safety first
        is_safe, score, reason = asyncio.run(
            moderation_service.check_content(prompt)
        )
        
        if not is_safe:
            print(f"Prompt rejected: {reason}")
            return error_response(400, {
                "status": "rejected",
                "reason": reason,
                "score": score,
                "prompt": prompt
            })
        
        # Generate image
        import time
        start_time = time.time()
        
        image_urls, image_base64 = asyncio.run(
            image_generation_service.generate_image(
                prompt=prompt,
                model=model,
                num_outputs=num_outputs,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                return_base64=True
            )
        )
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "completed",
            "prompt": prompt,
            "model": model,
            "image_urls": image_urls,
            "image_base64": image_base64,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Image generated in {processing_time:.1f}s")
        return success_response(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, str(e))


def list_models():
    """List available models."""
    try:
        models = image_generation_service.get_available_models()
        return success_response({
            "models": models,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return error_response(500, str(e))


def success_response(data, status_code=200):
    """Format success response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data)
    }


def error_response(status_code, message):
    """Format error response."""
    if isinstance(message, dict):
        body = message
    else:
        body = {"error": message}
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
