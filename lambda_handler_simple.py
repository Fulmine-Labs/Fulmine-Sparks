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
import time
from datetime import datetime

# In-memory cache for generated images
# Format: {payment_hash: {'image_base64': [...], 'status': 'pending'|'available'|'expired', 'created_at': timestamp, 'expires_at': timestamp, 'polling_started': bool}}
IMAGE_CACHE = {}
CACHE_DURATION = 15  # Keep images for 15 seconds (Lightning payments settle in ~1-5 seconds)
POLLING_DURATION = 5  # Poll for payment for 5 seconds (quick check, don't block response)

# IP-based rate limiting with progressive penalties
# Format: {ip: {'requests': [timestamp, ...], 'unpaid_invoices': count, 'blocked_until': timestamp}}
IP_TRACKING = {}
RATE_LIMIT_WINDOW = 60  # 1 minute window for tracking requests

# Progressive rate limiting based on unpaid invoices
RATE_LIMITS = {
    0: {"requests_per_minute": 3, "description": "normal"},
    1: {"requests_per_minute": 2, "description": "1 unpaid invoice"},
    3: {"requests_per_minute": 1, "description": "2-3 unpaid invoices"},
    5: {"requests_per_minute": 0.5, "description": "4-5 unpaid invoices"},
    10: {"requests_per_minute": 0.2, "description": "6-10 unpaid invoices"},
    float('inf'): {"requests_per_minute": 0, "description": "11+ unpaid invoices - blocked"}
}

# Mapping of payment_hash to IP for tracking
PAYMENT_HASH_TO_IP = {}

def cleanup_expired_images():
    """Remove expired images from cache"""
    current_time = time.time()
    expired = [k for k, v in IMAGE_CACHE.items() if current_time > v.get('expires_at', 0)]
    for k in expired:
        del IMAGE_CACHE[k]
        print(f"🗑️  Cleaned up expired image: {k[:16]}...")

def store_image(payment_hash, image_base64):
    """Store image in memory cache AND DynamoDB with pending status"""
    current_time = time.time()
    expires_at = current_time + CACHE_DURATION
    
    # Store in memory cache (fast access)
    IMAGE_CACHE[payment_hash] = {
        'image_base64': image_base64,
        'status': 'pending',
        'created_at': current_time,
        'expires_at': expires_at,
        'polling_started': False,
        'polling_expires_at': current_time + POLLING_DURATION
    }
    print(f"💾 Image stored in memory cache for {CACHE_DURATION}s: {payment_hash[:16]}...")
    
    # Store in DynamoDB (persistent storage)
    if DYNAMODB_AVAILABLE:
        try:
            images_table.put_item(
                Item={
                    'payment_hash': payment_hash,
                    'image_base64': image_base64,
                    'status': 'pending',
                    'created_at': int(current_time),
                    'expires_at': int(expires_at),
                    'ttl': int(expires_at),
                    'polling_started': False,
                    'polling_expires_at': int(current_time + POLLING_DURATION)
                }
            )
            print(f"✅ Image stored in DynamoDB for {CACHE_DURATION}s: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error storing image in DynamoDB: {str(e)}")

def get_cached_image(payment_hash):
    """Get image from cache (memory first, then DynamoDB)"""
    cleanup_expired_images()
    
    # Check memory cache first (fastest)
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        if time.time() <= item.get('expires_at', 0):
            print(f"✅ Image found in memory cache: {payment_hash[:16]}...")
            return item.get('image_base64')
    
    # Check DynamoDB (fallback)
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                # Check if expired
                if time.time() <= item.get('expires_at', 0):
                    print(f"✅ Image found in DynamoDB: {payment_hash[:16]}...")
                    # Restore to memory cache for faster access
                    IMAGE_CACHE[payment_hash] = {
                        'image_base64': item.get('image_base64'),
                        'status': item.get('status', 'pending'),
                        'created_at': item.get('created_at', time.time()),
                        'expires_at': item.get('expires_at', time.time() + CACHE_DURATION),
                        'polling_started': item.get('polling_started', False),
                        'polling_expires_at': item.get('polling_expires_at', time.time() + POLLING_DURATION)
                    }
                    return item.get('image_base64')
                else:
                    print(f"🗑️  Image expired in DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error retrieving image from DynamoDB: {str(e)}")
    
    return None

def get_client_ip(event):
    """Extract client IP from Lambda event"""
    try:
        # Try CloudFront header first
        if 'headers' in event:
            headers = event.get('headers', {})
            if 'CloudFront-Viewer-Address' in headers:
                return headers['CloudFront-Viewer-Address'].split(':')[0]
            if 'X-Forwarded-For' in headers:
                return headers['X-Forwarded-For'].split(',')[0].strip()
            if 'x-forwarded-for' in headers:
                return headers['x-forwarded-for'].split(',')[0].strip()
        
        # Try requestContext
        if 'requestContext' in event:
            return event['requestContext'].get('identity', {}).get('sourceIp', '0.0.0.0')
        
        return '0.0.0.0'
    except Exception as e:
        print(f"Error extracting IP: {str(e)}")
        return '0.0.0.0'


def cleanup_old_tracking():
    """Remove old tracking data"""
    current_time = time.time()
    ips_to_delete = []
    
    for ip, data in IP_TRACKING.items():
        # Remove requests older than rate limit window
        data['requests'] = [t for t in data.get('requests', []) if current_time - t < RATE_LIMIT_WINDOW]
        
        # Delete IP if no recent activity and no unpaid invoices
        if not data['requests'] and data.get('unpaid_invoices', 0) == 0:
            ips_to_delete.append(ip)
    
    for ip in ips_to_delete:
        del IP_TRACKING[ip]
        print(f"🗑️  Cleaned up tracking for IP: {ip}")


def get_rate_limit_for_ip(ip):
    """Get rate limit based on unpaid invoices"""
    if ip not in IP_TRACKING:
        return RATE_LIMITS[0]
    
    unpaid_count = IP_TRACKING[ip].get('unpaid_invoices', 0)
    
    # Find the appropriate rate limit
    for threshold in sorted(RATE_LIMITS.keys()):
        if unpaid_count <= threshold:
            return RATE_LIMITS[threshold]
    
    return RATE_LIMITS[float('inf')]


def check_rate_limit(ip):
    """Check if IP is within rate limit. Returns (allowed, reason)"""
    cleanup_old_tracking()
    current_time = time.time()
    
    # Initialize IP tracking if needed
    if ip not in IP_TRACKING:
        IP_TRACKING[ip] = {
            'requests': [],
            'unpaid_invoices': 0,
            'blocked_until': None
        }
    
    data = IP_TRACKING[ip]
    
    # Check if IP is blocked
    if data.get('blocked_until') and current_time < data['blocked_until']:
        return False, f"IP blocked until {datetime.fromtimestamp(data['blocked_until']).isoformat()}"
    
    # Clean up old requests
    data['requests'] = [t for t in data.get('requests', []) if current_time - t < RATE_LIMIT_WINDOW]
    
    # Get rate limit for this IP
    rate_limit = get_rate_limit_for_ip(ip)
    max_requests = int(rate_limit['requests_per_minute'])
    
    # Check if at limit (0 means blocked)
    if max_requests == 0:
        return False, f"Rate limited: {rate_limit['description']}"
    
    if len(data['requests']) >= max_requests:
        return False, f"Rate limited: {rate_limit['description']} ({len(data['requests'])}/{max_requests} requests/min)"
    
    # Record this request
    data['requests'].append(current_time)
    
    return True, f"Allowed: {rate_limit['description']}"


def track_invoice_created(payment_hash, ip):
    """Track that an invoice was created from this IP"""
    if ip not in IP_TRACKING:
        IP_TRACKING[ip] = {
            'requests': [],
            'unpaid_invoices': 0,
            'blocked_until': None
        }
    
    IP_TRACKING[ip]['unpaid_invoices'] += 1
    PAYMENT_HASH_TO_IP[payment_hash] = ip
    
    unpaid = IP_TRACKING[ip]['unpaid_invoices']
    print(f"📊 Invoice created for {ip}: {unpaid} unpaid invoice(s)")


def track_payment_confirmed(payment_hash):
    """Track that a payment was confirmed"""
    if payment_hash not in PAYMENT_HASH_TO_IP:
        return
    
    ip = PAYMENT_HASH_TO_IP[payment_hash]
    
    if ip in IP_TRACKING and IP_TRACKING[ip]['unpaid_invoices'] > 0:
        IP_TRACKING[ip]['unpaid_invoices'] -= 1
        unpaid = IP_TRACKING[ip]['unpaid_invoices']
        print(f"✅ Payment confirmed for {ip}: {unpaid} unpaid invoice(s) remaining")
    
    del PAYMENT_HASH_TO_IP[payment_hash]


def get_image_status(payment_hash):
    """Get image status (checks memory first, then DynamoDB)"""
    cleanup_expired_images()
    
    # Check memory cache first
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        current_time = time.time()
        
        # Check if expired
        if current_time > item.get('expires_at', 0):
            print(f"🗑️  Image expired in memory: {payment_hash[:16]}...")
            return 'expired'
        
        print(f"✅ Image status found in memory: {item.get('status')}")
        return item.get('status', 'pending')
    
    # Check DynamoDB (fallback)
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                current_time = time.time()
                
                # Check if expired
                if current_time > item.get('expires_at', 0):
                    print(f"🗑️  Image expired in DynamoDB: {payment_hash[:16]}...")
                    return 'expired'
                
                print(f"✅ Image status found in DynamoDB: {item.get('status')}")
                return item.get('status', 'pending')
        except Exception as e:
            print(f"⚠️  Error getting image status from DynamoDB: {str(e)}")
    
    print(f"❌ Image not found: {payment_hash[:16]}...")
    return None

def mark_image_available(payment_hash):
    """Mark image as available after payment confirmed"""
    # Update memory cache
    if payment_hash in IMAGE_CACHE:
        IMAGE_CACHE[payment_hash]['status'] = 'available'
        print(f"✅ Image marked as available in memory: {payment_hash[:16]}...")
    
    # Update DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.update_item(
                Key={'payment_hash': payment_hash},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'available'}
            )
            print(f"✅ Image marked as available in DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error updating image status in DynamoDB: {str(e)}")

def delete_cached_image(payment_hash):
    """Delete image from cache (memory and DynamoDB)"""
    # Delete from memory cache
    if payment_hash in IMAGE_CACHE:
        del IMAGE_CACHE[payment_hash]
        print(f"🗑️  Deleted image from memory cache: {payment_hash[:16]}...")
    
    # Delete from DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.delete_item(Key={'payment_hash': payment_hash})
            print(f"🗑️  Deleted image from DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error deleting image from DynamoDB: {str(e)}")

def poll_for_payment(payment_hash, billing_client):
    """Poll Alby for payment confirmation (runs in Lambda execution)"""
    print(f"🔄 Starting payment polling for {POLLING_DURATION}s: {payment_hash[:16]}...")
    
    start_time = time.time()
    poll_interval = 1  # Check every 1 second
    check_count = 0
    
    while time.time() - start_time < POLLING_DURATION:
        try:
            check_count += 1
            invoice_status = billing_client.get_invoice(payment_hash)
            
            if "error" not in invoice_status:
                if invoice_status.get('settled') or invoice_status.get('state') == 'SETTLED':
                    elapsed = int(time.time() - start_time)
                    print(f"✅ Payment confirmed via polling after {elapsed}s (check #{check_count}): {payment_hash[:16]}...")
                    mark_image_available(payment_hash)
                    return True
        except Exception as e:
            print(f"⚠️  Error polling payment (check #{check_count}): {str(e)}")
        
        time.sleep(poll_interval)
    
    print(f"⏱️  Polling timeout for {payment_hash[:16]}... (payment not received after {check_count} checks)")
    return False

# Try to import boto3 for DynamoDB storage (fallback only)
try:
    import boto3
    DYNAMODB_AVAILABLE = True
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    IMAGES_TABLE = os.getenv('IMAGES_TABLE', 'fulmine-sparks-images')
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        print(f"✅ DynamoDB initialized: {IMAGES_TABLE}")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize DynamoDB table: {e}")
        DYNAMODB_AVAILABLE = False
except ImportError as e:
    DYNAMODB_AVAILABLE = False
    print(f"⚠️  Warning: boto3 not available: {e}")

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
        print(f"DEBUG: pathParameters = {event.get('pathParameters', {})}")
        print(f"DEBUG: rawPath = {event.get('rawPath', 'NOT SET')}")
        print(f"DEBUG: path = {event.get('path', 'NOT SET')}")
        
        if 'proxy' in event.get('pathParameters', {}):
            path = '/' + event['pathParameters']['proxy']
        elif 'rawPath' in event:
            path = event['rawPath']
        elif 'path' in event.get('pathParameters', {}):
            path = event['pathParameters']['path']
        
        print(f"DEBUG: path before stage strip = {path}")
        
        # Strip stage prefix if present (e.g., /prod/api/v1/... -> /api/v1/...)
        for stage in ['prod', 'dev', 'staging', 'test', 'stage']:
            if path.startswith(f'/{stage}/'):
                path = path[len(f'/{stage}'):]
                print(f"DEBUG: stripped stage {stage}, path now = {path}")
                break
        
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
            # Check rate limit
            client_ip = get_client_ip(event)
            allowed, reason = check_rate_limit(client_ip)
            
            if not allowed:
                print(f"⛔ Rate limit exceeded for {client_ip}: {reason}")
                return error_response(429, f"Rate limited: {reason}")
            
            return generate_image(body_data, client_ip)
        
        elif path.startswith('/api/v1/services/image/status/') and http_method == 'GET':
            payment_hash = path.split('/api/v1/services/image/status/')[-1]
            # Create billing client for payment check
            billing_client = None
            if BILLING_ENABLED:
                try:
                    alby_nwc_url = os.getenv('ALBY_NWC_URL')
                    if alby_nwc_url:
                        billing_client = AlbyBillingClient(nwc_url=alby_nwc_url)
                except Exception as e:
                    print(f"⚠️  Could not create billing client: {str(e)}")
            return get_image_status_endpoint(payment_hash, billing_client)
        
        elif path.startswith('/api/v1/services/image/retrieve/') and http_method == 'GET':
            payment_hash = path.split('/api/v1/services/image/retrieve/')[-1]
            return retrieve_image(payment_hash)
        
        elif path == '/api/v1/services/image/models' and http_method == 'GET':
            return list_models()
        
        elif path == '/api/v1/workflow' and http_method == 'GET':
            return get_workflow()
        
        else:
            print(f"DEBUG: No route matched for {http_method} {path}")
            print(f"DEBUG: Full event: {json.dumps(event, default=str)[:1000]}")
            return error_response(404, f"Endpoint not found: {http_method} {path}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def get_image_status_endpoint(payment_hash, billing_client=None):
    """Get image status endpoint for polling"""
    try:
        print(f"📊 Checking image status: {payment_hash[:16]}...")
        
        status = get_image_status(payment_hash)
        
        if status is None:
            # Image not found - return pending status instead of 404
            # This allows clients to keep polling
            print(f"⏳ Image not yet generated or expired: {payment_hash[:16]}...")
            result = {
                "status": "pending",
                "payment_hash": payment_hash,
                "timestamp": datetime.now().isoformat(),
                "message": "Image generation in progress or not found"
            }
            return success_response(result)
        
        # If image is still pending, do a quick payment check
        if status == "pending" and billing_client:
            print(f"🔄 Quick payment check for pending image: {payment_hash[:16]}...")
            try:
                invoice_status = billing_client.get_invoice(payment_hash)
                if "error" not in invoice_status:
                    if invoice_status.get('settled') or invoice_status.get('state') == 'SETTLED':
                        print(f"✅ Payment detected on status check: {payment_hash[:16]}...")
                        mark_image_available(payment_hash)
                        status = "available"
                        
                        # Track payment for rate limiting
                        track_payment_confirmed(payment_hash)
            except Exception as e:
                print(f"⚠️  Error checking payment on status endpoint: {str(e)}")
        
        result = {
            "status": status,
            "payment_hash": payment_hash,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 Image status: {status}")
        return success_response(result)
    
    except Exception as e:
        print(f"❌ Error getting image status: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f"Error getting image status: {str(e)}")


def retrieve_image(payment_hash):
    """Retrieve image after payment is confirmed."""
    try:
        print(f"🔍 Retrieving image for payment hash: {payment_hash[:16]}...")
        
        # Check image status
        status = get_image_status(payment_hash)
        
        if status is None:
            # Image not found - return pending status instead of 404
            # This allows clients to keep polling
            print(f"⏳ Image not yet generated or expired: {payment_hash[:16]}...")
            result = {
                "status": "pending",
                "payment_hash": payment_hash,
                "timestamp": datetime.now().isoformat(),
                "message": "Image generation in progress or not found"
            }
            return success_response(result)
        
        if status == 'expired':
            print(f"❌ Image expired for hash: {payment_hash[:16]}...")
            return error_response(410, "Image expired. Please generate a new image.")
        
        if status == 'pending':
            print(f"⏳ Image still pending for hash: {payment_hash[:16]}...")
            return error_response(402, "Payment not confirmed yet. Please wait for Lightning settlement.")
        
        if status == 'available':
            print(f"✅ Image available for hash: {payment_hash[:16]}...")
            
            # Retrieve the stored image from cache
            image_base64_list = get_cached_image(payment_hash)
            if image_base64_list:
                print(f"✅ Image retrieved from cache: {len(image_base64_list)} image(s)")
                # Delete from cache after retrieval
                delete_cached_image(payment_hash)
            else:
                print(f"⚠️  Image not found in cache for payment_hash: {payment_hash[:16]}...")
                image_base64_list = []
            
            result = {
                "status": "success",
                "payment_hash": payment_hash,
                "message": "Payment confirmed. Image retrieved.",
                "image_base64": image_base64_list if image_base64_list else [],
                "timestamp": datetime.now().isoformat()
            }
            return success_response(result)
        
        return error_response(500, f"Unknown image status: {status}")
    
    except Exception as e:
        print(f"❌ Error retrieving image: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f"Error retrieving image: {str(e)}")


def generate_image(body_data, client_ip=None):
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
                        
                        # Store image in memory cache with payment_hash as key
                        payment_hash = invoice_result.get("payment_hash")
                        if payment_hash and image_base64:
                            store_image(payment_hash, image_base64)
                            print(f"✅ Image stored in cache for {CACHE_DURATION}s")
                            print(f"💡 Client will poll status endpoint for payment updates")
                            
                            # Track invoice for rate limiting
                            if client_ip:
                                track_invoice_created(payment_hash, client_ip)
                        
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
        # Calculate actual user cost (with 25% markup)
        from billing import calculate_image_price
        pricing = calculate_image_price(num_images=1)
        user_cost_per_image = pricing['your_price_usd']
        
        models = [
            # Bytedance Seedream 4.5 (excellent quality, 4K support)
            {
                "name": "seedream-4.5",
                "description": "Seedream 4.5 - Cinematic quality, 4K support, strong spatial reasoning",
                "category": "image",
                "quality": "excellent",
                "speed": "medium",
                "cost": f"${user_cost_per_image:.2f} per image",
                "max_resolution": "4K (4096px)"
            }
        ]
        return success_response({
            "models": models,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return error_response(500, str(e))


def get_workflow():
    """Get the complete bot integration workflow."""
    try:
        workflow = {
            "title": "Fulmine-Sparks Bot Integration Workflow",
            "description": "Complete 5-step workflow for integrating with Fulmine-Sparks API",
            "steps": [
                {
                    "step": 1,
                    "name": "Check Available Models and Pricing",
                    "endpoint": "GET /api/v1/services/image/models",
                    "purpose": "Discover available models and their current pricing",
                    "what_to_do": [
                        "Display available models to user",
                        "Show pricing for each model",
                        "Let user select model and enter prompt"
                    ]
                },
                {
                    "step": 2,
                    "name": "Generate Image and Get Invoice",
                    "endpoint": "POST /api/v1/services/image/generate",
                    "purpose": "Generate image and create Lightning invoice",
                    "request": {
                        "prompt": "A beautiful sunset over the ocean",
                        "num_outputs": 1
                    },
                    "what_to_do": [
                        "Save payment_hash for later retrieval",
                        "Display invoice to user (QR code or text)",
                        "Show amount in sats and USD",
                        "Show expiration time",
                        "Instruct user to pay with Lightning wallet"
                    ],
                    "important": [
                        "Image is generated but NOT returned yet",
                        "User must pay invoice to retrieve image",
                        "Invoice expires in 1 hour"
                    ]
                },
                {
                    "step": 3,
                    "name": "User Pays Invoice",
                    "endpoint": "User Action",
                    "purpose": "User scans QR code or pastes invoice into Lightning wallet",
                    "timeline": [
                        "User initiates payment",
                        "Lightning Network processes payment",
                        "Payment settles in 1-5 seconds",
                        "Bot can now retrieve the image"
                    ],
                    "what_to_do": [
                        "Wait for user to pay",
                        "Optionally show payment instructions",
                        "Proceed to Step 4 after payment"
                    ]
                },
                {
                    "step": 4,
                    "name": "Check Payment Status",
                    "endpoint": "GET /api/v1/services/image/status/{payment_hash}",
                    "purpose": "Check if payment has been received",
                    "what_to_do": [
                        "Poll this endpoint every 1-2 seconds",
                        "Stop polling after payment is received",
                        "Proceed to Step 5 when status is 'paid'"
                    ],
                    "polling_strategy": "Check every 1 second, timeout after 5 minutes"
                },
                {
                    "step": 5,
                    "name": "Retrieve Image",
                    "endpoint": "GET /api/v1/services/image/retrieve/{payment_hash}",
                    "purpose": "Get the generated image after payment is confirmed",
                    "what_to_do": [
                        "Decode base64 image data",
                        "Save image to file or display",
                        "Send to user",
                        "Handle errors gracefully"
                    ]
                }
            ],
            "rate_limiting": {
                "status": "Guidelines only - not enforced by API",
                "recommended": "1 request per 20 seconds",
                "maximum": "10 requests per minute",
                "burst_limit": "5 concurrent requests",
                "note": "Bots should respect these limits. Enforcement may be added in future versions."
            },
            "error_handling": {
                "payment_not_received": "Wait longer or check payment status",
                "image_expired": "Generate image again (cache is 15 seconds)",
                "invoice_expired": "Generate new image (invoice expires in 1 hour)",
                "server_error": "Retry after delay"
            },
            "best_practices": [
                "Always check models endpoint for pricing",
                "Respect rate limits",
                "Handle errors gracefully",
                "Provide user feedback at each step",
                "Cache models to reduce API calls"
            ],
            "documentation": {
                "full_guide": "https://github.com/Fulmine-Labs/Fulmine-Sparks/blob/master/BOT_INTEGRATION_GUIDE.md",
                "api_design": "https://github.com/Fulmine-Labs/Fulmine-Sparks/blob/master/API_DESIGN.md",
                "terms_of_service": "https://github.com/Fulmine-Labs/Fulmine-Sparks/blob/master/TERMS_OF_SERVICE.md",
                "privacy_policy": "https://github.com/Fulmine-Labs/Fulmine-Sparks/blob/master/PRIVACY_POLICY.md",
                "acceptable_use_policy": "https://github.com/Fulmine-Labs/Fulmine-Sparks/blob/master/ACCEPTABLE_USE_POLICY.md"
            }
        }
        return success_response(workflow)
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
