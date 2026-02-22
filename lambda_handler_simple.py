#!/usr/bin/env python3
"""
Simplified AWS Lambda handler for Fulmine-Sparks API.
No heavy dependencies - just what we need.
"""

import json
import os
import sys
import asyncio
import base64
from datetime import datetime

# Try to import boto3 for DynamoDB storage
try:
    import boto3
    DYNAMODB_AVAILABLE = True
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    IMAGES_TABLE = os.getenv('IMAGES_TABLE', 'fulmine-sparks-images')
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        # Test connection
        images_table.table_status
    except Exception as e:
        print(f"Warning: Could not connect to DynamoDB table: {e}")
        DYNAMODB_AVAILABLE = False
except ImportError:
    DYNAMODB_AVAILABLE = False
    print("Warning: boto3 not available, DynamoDB storage disabled")

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Import billing module
try:
    from billing import AlbyBillingClient, calculate_image_price
    BILLING_ENABLED = True
except ImportError:
    BILLING_ENABLED = False
    print("Warning: Billing module not available")

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
        
        elif path.startswith('/api/v1/services/image/retrieve/') and http_method == 'GET':
            payment_hash = path.split('/api/v1/services/image/retrieve/')[-1]
            return retrieve_image(payment_hash)
        
        elif path == '/api/v1/services/image/models' and http_method == 'GET':
            return list_models()
        
        else:
            return error_response(404, "Endpoint not found")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def retrieve_image(payment_hash):
    """Retrieve image after payment is confirmed."""
    try:
        print(f"🔍 Retrieving image for payment hash: {payment_hash[:16]}...")
        
        # Check if payment was received
        if BILLING_ENABLED:
            try:
                alby_nwc_url = os.getenv('ALBY_NWC_URL')
                if not alby_nwc_url:
                    return error_response(500, "Payment system not configured")
                
                billing_client = AlbyBillingClient(nwc_url=alby_nwc_url)
                invoice_status = billing_client.get_invoice(payment_hash)
                
                if "error" in invoice_status:
                    print(f"❌ Invoice lookup failed: {invoice_status.get('error')}")
                    return error_response(404, f"Invoice not found: {invoice_status.get('error')}")
                
                # Check if payment was settled
                if invoice_status.get('settled') or invoice_status.get('state') == 'SETTLED':
                    print(f"✅ Payment confirmed for hash: {payment_hash[:16]}...")
                    
                    # Retrieve the stored image for this payment hash
                    image_base64_list = []
                    if DYNAMODB_AVAILABLE:
                        try:
                            # Try to fetch image from DynamoDB
                            response = images_table.get_item(Key={'payment_hash': payment_hash})
                            if 'Item' in response:
                                item = response['Item']
                                image_base64_list = item.get('image_base64', [])
                                print(f"✅ Image retrieved from DynamoDB: {len(image_base64_list)} image(s)")
                            else:
                                print(f"⚠️  Image not found in DynamoDB for payment_hash: {payment_hash[:16]}...")
                        except Exception as e:
                            print(f"⚠️  Could not retrieve image from DynamoDB: {str(e)}")
                            # Image not found in DynamoDB, but payment is confirmed
                            # This could happen if image generation failed or was deleted
                    
                    result = {
                        "status": "success",
                        "payment_hash": payment_hash,
                        "message": "Payment confirmed. Image retrieved.",
                        "image_base64": image_base64_list,
                        "timestamp": datetime.now().isoformat()
                    }
                    return success_response(result)
                else:
                    print(f"⏳ Payment not yet confirmed for hash: {payment_hash[:16]}...")
                    return error_response(402, "Payment not confirmed yet. Please wait for Lightning settlement.")
            
            except Exception as e:
                print(f"❌ Error checking payment: {str(e)}")
                import traceback
                traceback.print_exc()
                return error_response(500, f"Error checking payment: {str(e)}")
        else:
            return error_response(500, "Billing system not enabled")
    
    except Exception as e:
        print(f"❌ Error retrieving image: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f"Error retrieving image: {str(e)}")


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
                
                # Convert URLs to base64
                image_base64 = []
                for url in image_urls:
                    try:
                        img_response = requests.get(url, timeout=30)
                        img_response.raise_for_status()
                        b64_data = base64.b64encode(img_response.content).decode('utf-8')
                        image_base64.append(b64_data)
                    except Exception as e:
                        print(f"Error converting image to base64: {str(e)}")
                        image_base64.append(None)
                
                processing_time = time.time() - start_time
                
                # Create Lightning invoice FIRST
                invoice_result = None
                if BILLING_ENABLED:
                    try:
                        # Check if ALBY_NWC_URL is set
                        alby_nwc_url = os.getenv('ALBY_NWC_URL')
                        if not alby_nwc_url:
                            print("⚠️  ALBY_NWC_URL environment variable not set")
                            return error_response(500, "Payment system not configured")
                        
                        # Calculate pricing with 25% markup
                        pricing = calculate_image_price(num_outputs)
                        print(f"💰 Pricing calculated: {pricing['total_sats']} sats")
                        
                        # Create invoice
                        billing_client = AlbyBillingClient(nwc_url=alby_nwc_url)
                        invoice_result = billing_client.create_invoice(
                            amount_sats=pricing['total_sats'],
                            description=f"SeeDream 4.5 - {num_outputs} image(s): {prompt[:50]}",
                            metadata={
                                "prompt": prompt,
                                "model": "seedream-4.5",
                                "num_images": num_outputs,
                                "price_usd": pricing['your_price_usd']
                            }
                        )
                        
                        if "error" in invoice_result:
                            print(f"❌ Invoice creation failed: {invoice_result.get('error')}")
                            return error_response(500, f"Invoice creation failed: {invoice_result.get('error')}")
                        
                        print(f"✅ Invoice created: {pricing['total_sats']} sats")
                        
                        # Store image in DynamoDB with payment_hash as key
                        payment_hash = invoice_result.get("payment_hash")
                        if DYNAMODB_AVAILABLE and payment_hash and image_base64:
                            try:
                                images_table.put_item(
                                    Item={
                                        'payment_hash': payment_hash,
                                        'image_base64': image_base64,
                                        'prompt': prompt,
                                        'model': model,
                                        'timestamp': datetime.now().isoformat(),
                                        'ttl': int(datetime.now().timestamp()) + (7 * 24 * 60 * 60)  # 7 days
                                    }
                                )
                                print(f"✅ Image stored in DynamoDB for payment_hash: {payment_hash[:16]}...")
                            except Exception as e:
                                print(f"⚠️  Could not store image in DynamoDB: {str(e)}")
                                # Continue anyway - image is generated, just not stored
                        
                    except Exception as e:
                        print(f"❌ Error creating invoice: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        return error_response(500, f"Error creating invoice: {str(e)}")
                else:
                    return error_response(500, "Billing system not enabled")
                
                # Return invoice ONLY (no image yet)
                # Image will be returned after payment is confirmed
                result = {
                    "status": "payment_required",
                    "prompt": prompt,
                    "model": model,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Image generated. Payment required to retrieve.",
                    "invoice": {
                        "payment_request": invoice_result.get("payment_request"),
                        "payment_hash": invoice_result.get("payment_hash"),
                        "amount_sats": pricing['total_sats'],
                        "price_usd": pricing['your_price_usd'],
                        "expires_at": invoice_result.get("expires_at"),
                        "qr_code_png": invoice_result.get("qr_code_png"),
                        "qr_code_svg": invoice_result.get("qr_code_svg")
                    }
                }
                
                print(f"Image generated in {processing_time:.1f}s (invoice returned, image held in S3)")
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
