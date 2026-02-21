#!/usr/bin/env python3
"""
Simplified AWS Lambda handler for Fulmine-Sparks API.
No heavy dependencies - just what we need.
"""

import json
import os
import sys
import asyncio
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def lambda_handler(event, context):
    """
    AWS Lambda handler for HTTP requests.
    """
    
    try:
        # Parse request
        body = event.get('body', '')
        
        # Parse JSON body if present
        try:
            if isinstance(body, str):
                body_data = json.loads(body) if body else {}
            else:
                body_data = body
        except json.JSONDecodeError:
            body_data = {}
        
        # Determine HTTP method: if there's a body, it's POST; otherwise GET
        # (workaround for API Gateway not passing method correctly)
        http_method = 'POST' if body_data else 'GET'
        
        # Try to get actual method from event (in case it's available)
        actual_method = event.get('requestContext', {}).get('http', {}).get('method')
        if not actual_method:
            actual_method = event.get('httpMethod')
        if actual_method:
            http_method = actual_method
        
        # Get path from proxy parameter
        path = '/'
        if 'proxy' in event.get('pathParameters', {}):
            path = '/' + event['pathParameters']['proxy']
        
        # Normalize path - remove trailing slash except for root
        if path != '/' and path.endswith('/'):
            path = path[:-1]
        
        print(f"Request: {http_method} {path}")
        
        # Route requests
        if path == '/health' and http_method == 'GET':
            return success_response({
                "status": "ok",
                "service": "Fulmine-Sparks Lambda",
                "timestamp": datetime.now().isoformat()
            })
        
        elif path == '/' and http_method == 'GET':
            return success_response({
                "service": "Fulmine-Sparks Serverless API",
                "version": "1.0.0",
                "endpoints": {
                    "GET /health": "Health check",
                    "POST /api/v1/services/image/generate": "Generate an image",
                    "GET /api/v1/services/image/models": "List available models"
                },
                "documentation": "https://github.com/Fulmine-Labs/Fulmine-Sparks"
            })
        
        elif path == '/api/v1/services/image/generate' and http_method == 'POST':
            return generate_image(body_data)
        
        elif path == '/api/v1/services/image/models' and http_method == 'GET':
            return list_models()
        
        else:
            return error_response(404, "Endpoint not found")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def generate_image(body_data):
    """Generate an image using Replicate API."""
    try:
        prompt = body_data.get('prompt', '')
        model = body_data.get('model', 'stable-diffusion')
        num_outputs = body_data.get('num_outputs', 1)
        guidance_scale = body_data.get('guidance_scale', 7.5)
        num_inference_steps = body_data.get('num_inference_steps', 50)
        
        if not prompt:
            return error_response(400, "No prompt provided")
        
        print(f"Generating image for: {prompt}")
        
        # Get API token
        api_token = os.environ.get('REPLICATE_API_TOKEN')
        if not api_token:
            return error_response(500, "REPLICATE_API_TOKEN not set")
        
        # Map model names to Replicate versions
        # Versions verified from https://replicate.com
        model_map = {
            # Bytedance Seedream 4.5 (excellent quality, 4K support)
            'seedream-4.5': 'bytedance/seedream-4.5',
        }
        
        model_version = model_map.get(model, model)
        
        # Call Replicate API directly using requests
        import requests
        import time
        
        start_time = time.time()
        
        # Create prediction
        headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        prediction_data = {
            "version": model_version,
            "input": {
                "prompt": prompt,
                "num_outputs": num_outputs,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
            }
        }
        
        # Start prediction
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=prediction_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 201:
            return error_response(500, f"Replicate API error: {response.text}")
        
        prediction = response.json()
        prediction_id = prediction.get('id')
        
        # Poll for completion (with timeout)
        max_wait = 600  # 10 minutes
        poll_interval = 2
        elapsed = 0
        
        while elapsed < max_wait:
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return error_response(500, f"Replicate API error: {response.text}")
            
            prediction = response.json()
            status = prediction.get('status')
            
            if status == 'succeeded':
                output = prediction.get('output', [])
                image_urls = output if isinstance(output, list) else [output]
                
                processing_time = time.time() - start_time
                
                result = {
                    "status": "completed",
                    "prompt": prompt,
                    "model": model,
                    "image_urls": image_urls,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"Image generated in {processing_time:.1f}s")
                return success_response(result)
            
            elif status == 'failed':
                error_msg = prediction.get('error', 'Unknown error')
                return error_response(500, f"Image generation failed: {error_msg}")
            
            # Still processing
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        return error_response(500, "Image generation timed out")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def list_models():
    """List available models."""
    try:
        models = [
            # Bytedance Seedream 4.5 (excellent quality, 4K support)
            {
                "name": "seedream-4.5",
                "description": "Seedream 4.5 - Cinematic quality, 4K support, strong spatial reasoning",
                "category": "image",
                "quality": "excellent",
                "speed": "medium",
                "cost": "$0.04 per image",
                "max_resolution": "4K (4096px)"
            }
        ]
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
