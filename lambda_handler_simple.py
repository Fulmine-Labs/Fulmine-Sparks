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
        # Parse request - try multiple fields for HTTP method
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        if not http_method:
            http_method = event.get('httpMethod', 'GET')
        if not http_method:
            http_method = event.get('requestContext', {}).get('httpMethod', 'GET')
        if not http_method:
            http_method = 'GET'
        
        # Try different path fields
        path = event.get('rawPath', '/')
        if not path or path == '/':
            path = event.get('requestContext', {}).get('http', {}).get('path', '/')
        
        # Also try path parameter from proxy
        if 'proxy' in event.get('pathParameters', {}):
            path = '/' + event['pathParameters']['proxy']
        
        # Debug: print raw event
        print(f"DEBUG: httpMethod={event.get('httpMethod')}")
        print(f"DEBUG: requestContext.httpMethod={event.get('requestContext', {}).get('httpMethod')}")
        print(f"DEBUG: requestContext.http.method={event.get('requestContext', {}).get('http', {}).get('method')}")
        print(f"DEBUG: Final http_method={http_method}")
        print(f"DEBUG: pathParameters={event.get('pathParameters')}")
        
        # Normalize path - remove trailing slash except for root
        if path != '/' and path.endswith('/'):
            path = path[:-1]
        
        print(f"DEBUG: Final path after normalization={path}")
        
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
    """Generate an image using Replicate."""
    try:
        prompt = body_data.get('prompt', '')
        model = body_data.get('model', 'stable-diffusion')
        num_outputs = body_data.get('num_outputs', 1)
        guidance_scale = body_data.get('guidance_scale', 7.5)
        num_inference_steps = body_data.get('num_inference_steps', 50)
        
        if not prompt:
            return error_response(400, "No prompt provided")
        
        print(f"Generating image for: {prompt}")
        
        # Import replicate here to avoid import errors
        import replicate
        
        # Get API token
        api_token = os.environ.get('REPLICATE_API_TOKEN')
        if not api_token:
            return error_response(500, "REPLICATE_API_TOKEN not set")
        
        # Map model names
        model_map = {
            'stable-diffusion': 'stability-ai/stable-diffusion:db21e45d3f7023abc9f30f5cc29eee38d2d9c0c7',
            'stable-diffusion-xl': 'stability-ai/stable-diffusion-xl:39ed52f2a60c3b36b4fe38b18e56f1f66a14e8925afd339bab9d1260cbe5eca6',
        }
        
        model_version = model_map.get(model, model)
        
        # Call Replicate
        import time
        start_time = time.time()
        
        output = replicate.run(
            model_version,
            input={
                "prompt": prompt,
                "num_outputs": num_outputs,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
            },
            api_token=api_token
        )
        
        processing_time = time.time() - start_time
        
        # Convert output to list if needed
        if isinstance(output, str):
            image_urls = [output]
        else:
            image_urls = list(output) if output else []
        
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
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def list_models():
    """List available models."""
    try:
        models = [
            {
                "name": "stable-diffusion",
                "description": "Stable Diffusion v1.5",
                "version": "db21e45d3f7023abc9f30f5cc29eee38d2d9c0c7"
            },
            {
                "name": "stable-diffusion-xl",
                "description": "Stable Diffusion XL",
                "version": "39ed52f2a60c3b36b4fe38b18e56f1f66a14e8925afd339bab9d1260cbe5eca6"
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
