import json
import base64
import os
import time
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
import boto3
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
images_table = dynamodb.Table(os.environ.get('IMAGES_TABLE', 'fulmine-sparks-images'))
rate_limits_table = dynamodb.Table(os.environ.get('RATE_LIMITS_TABLE', 'fulmine-sparks-rate-limits'))

# In-memory cache for quick access
IMAGE_CACHE = {}

# Configuration
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN')
ALBY_NWC_URL = os.environ.get('ALBY_NWC_URL')
DYNAMODB_AVAILABLE = True

# Rate limiting configuration
RATE_LIMITS = {
    'unpaid': {'requests': 3, 'window': 3600},      # 3 requests per hour for unpaid
    'paid': {'requests': 100, 'window': 3600},      # 100 requests per hour for paid
    'default': {'requests': 10, 'window': 3600}     # 10 requests per hour default
}

def get_client_ip(event):
    """Extract client IP from API Gateway event"""
    if 'x-forwarded-for' in event.get('headers', {}):
        return event['headers']['x-forwarded-for'].split(',')[0].strip()
    return event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')

def check_rate_limit(client_ip, payment_status='default'):
    """
    Check if client has exceeded rate limit.
    Uses DynamoDB for persistent rate limit tracking across Lambda invocations.
    Returns: (allowed: bool, remaining: int, reset_time: int)
    """
    current_time = int(time.time())
    limit_config = RATE_LIMITS.get(payment_status, RATE_LIMITS['default'])
    
    # Try to get rate limit data from DynamoDB
    try:
        response = rate_limits_table.get_item(Key={'client_ip': client_ip})
        
        if 'Item' in response:
            client_data = response['Item']
            window_start = int(client_data['window_start'])
            count = int(client_data['count'])
        else:
            # First request from this IP
            window_start = current_time
            count = 0
    except Exception as e:
        print(f"⚠️ Failed to get rate limit from DynamoDB: {str(e)}")
        # Fallback: allow the request but don't track it
        return True, limit_config['requests'], current_time + limit_config['window']
    
    window_elapsed = current_time - window_start
    
    # Reset window if expired
    if window_elapsed > limit_config['window']:
        window_start = current_time
        count = 0
    
    # Check if limit exceeded
    if count >= limit_config['requests']:
        reset_time = window_start + limit_config['window']
        remaining = 0
        allowed = False
        print(f"⛔ Rate limit exceeded for {client_ip}: {count}/{limit_config['requests']}")
    else:
        # Increment counter
        count += 1
        remaining = limit_config['requests'] - count
        reset_time = window_start + limit_config['window']
        allowed = True
        
        # Update DynamoDB
        try:
            rate_limits_table.put_item(Item={
                'client_ip': client_ip,
                'count': Decimal(str(count)),
                'window_start': Decimal(str(window_start)),
                'payment_status': payment_status,
                'ttl': Decimal(str(current_time + limit_config['window'] + 3600))  # Extra hour for safety
            })
        except Exception as e:
            print(f"⚠️ Failed to update rate limit in DynamoDB: {str(e)}")
    
    return allowed, remaining, reset_time

def store_image(payment_hash, image_base64, status='pending'):
    """Store image in both memory cache and DynamoDB"""
    image_data = {
        'payment_hash': payment_hash,
        'image_base64': image_base64,
        'status': status,
        'timestamp': int(time.time()),
        'ttl': int(time.time()) + 86400  # 24 hour TTL
    }
    
    # Store in memory cache
    IMAGE_CACHE[payment_hash] = image_data
    
    # Store in DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.put_item(Item={
                'payment_hash': payment_hash,
                'image_base64': image_base64,
                'status': status,
                'timestamp': Decimal(str(int(time.time()))),
                'ttl': Decimal(str(int(time.time()) + 86400))
            })
            print(f"✅ Image stored in DynamoDB for 24h: {payment_hash[:8]}...")
        except Exception as e:
            print(f"⚠️ Failed to store in DynamoDB: {str(e)}")

def get_cached_image(payment_hash):
    """Get image from cache (memory first, then DynamoDB)"""
    # Check memory cache first
    if payment_hash in IMAGE_CACHE:
        return IMAGE_CACHE[payment_hash]
    
    # Check DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                # Restore to memory cache
                IMAGE_CACHE[payment_hash] = {
                    'payment_hash': item['payment_hash'],
                    'image_base64': item['image_base64'],
                    'status': item['status'],
                    'timestamp': int(item['timestamp']),
                    'ttl': int(item['ttl'])
                }
                return IMAGE_CACHE[payment_hash]
        except Exception as e:
            print(f"⚠️ Failed to retrieve from DynamoDB: {str(e)}")
    
    return None

def get_image_status(payment_hash):
    """Get image status from cache or DynamoDB"""
    # Check memory cache first
    if payment_hash in IMAGE_CACHE:
        return IMAGE_CACHE[payment_hash]['status']
    
    # Check DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                status = response['Item']['status']
                print(f"📊 Image status from DynamoDB: {status}")
                return status
        except Exception as e:
            print(f"⚠️ Failed to get status from DynamoDB: {str(e)}")
    
    return None

def mark_image_available(payment_hash):
    """Mark image as available in both cache and DynamoDB"""
    # Update memory cache
    if payment_hash in IMAGE_CACHE:
        IMAGE_CACHE[payment_hash]['status'] = 'available'
    
    # Update DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.update_item(
                Key={'payment_hash': payment_hash},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'available'}
            )
            print(f"✅ Image marked as available: {payment_hash[:8]}...")
        except Exception as e:
            print(f"⚠️ Failed to update status in DynamoDB: {str(e)}")

def generate_image(prompt):
    """Generate image using Replicate API"""
    try:
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'version': '0a9ed0c3b4c5c89c516265a878c0550ba742404434368a86332538c88cccddc',  # SeeDream 4.5
            'input': {
                'prompt': prompt,
                'num_outputs': 1,
                'num_inference_steps': 25,
                'guidance_scale': 7.5
            }
        }
        
        response = requests.post(
            'https://api.replicate.com/v1/predictions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 201:
            prediction = response.json()
            return {
                'success': True,
                'prediction_id': prediction['id'],
                'status': prediction['status']
            }
        else:
            return {
                'success': False,
                'error': f'Replicate API error: {response.status_code}'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_prediction_status(prediction_id):
    """Get prediction status from Replicate"""
    try:
        headers = {
            'Authorization': f'Token {REPLICATE_API_TOKEN}'
        }
        
        response = requests.get(
            f'https://api.replicate.com/v1/predictions/{prediction_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            prediction = response.json()
            return {
                'status': prediction['status'],
                'output': prediction.get('output'),
                'error': prediction.get('error')
            }
        else:
            return {
                'status': 'error',
                'error': f'Failed to get prediction: {response.status_code}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def create_invoice(amount_msats, description):
    """Create Lightning invoice using Alby Hub NWC"""
    try:
        # Parse NWC URL
        nwc_url = ALBY_NWC_URL
        if not nwc_url:
            return {'success': False, 'error': 'NWC URL not configured'}
        
        # For now, return a mock invoice
        # In production, this would call the Alby Hub NWC API
        payment_hash = hashlib.sha256(f"{int(time.time())}{description}".encode()).hexdigest()
        
        return {
            'success': True,
            'payment_hash': payment_hash,
            'invoice': f'lnbc{amount_msats}n1p...',  # Mock invoice
            'amount_msats': amount_msats,
            'description': description
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def lambda_handler(event, context):
    """Main Lambda handler"""
    print(f"📨 Received event: {json.dumps(event)}")
    
    # Extract path and method
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    # Strip API Gateway stage prefix if present
    if path.startswith('/'):
        parts = path.split('/')
        if len(parts) > 1 and parts[1] in ['dev', 'prod', 'staging']:
            path = '/' + '/'.join(parts[2:])
    
    print(f"🔍 Path: {path}, Method: {method}")
    
    # Get client IP for rate limiting
    client_ip = get_client_ip(event)
    print(f"👤 Client IP: {client_ip}")
    
    try:
        # Route: POST /api/v1/services/image/generate
        if method == 'POST' and path == '/api/v1/services/image/generate':
            # Check rate limit (default tier)
            allowed, remaining, reset_time = check_rate_limit(client_ip, 'default')
            
            if not allowed:
                print(f"⛔ Rate limit exceeded for {client_ip}")
                return {
                    'statusCode': 429,
                    'headers': {
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(reset_time),
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Rate limit exceeded',
                        'retry_after': reset_time - int(time.time())
                    })
                }
            
            # Parse request body
            body = json.loads(event.get('body', '{}'))
            prompt = body.get('prompt', '')
            
            if not prompt:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Prompt is required'})
                }
            
            print(f"🎨 Generating image for prompt: {prompt[:50]}...")
            
            # Generate image
            result = generate_image(prompt)
            
            if not result['success']:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': result['error']})
                }
            
            # Create invoice
            amount_msats = 1000  # 1 sat
            invoice_result = create_invoice(amount_msats, f"Image generation: {prompt[:30]}")
            
            if not invoice_result['success']:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': invoice_result['error']})
                }
            
            payment_hash = invoice_result['payment_hash']
            
            # Store image metadata (not the full image yet, just the prediction ID)
            store_image(payment_hash, result['prediction_id'], status='pending')
            
            print(f"✅ Image generation started: {payment_hash[:8]}...")
            
            return {
                'statusCode': 200,
                'headers': {
                    'X-RateLimit-Remaining': str(remaining),
                    'X-RateLimit-Reset': str(reset_time),
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'payment_hash': payment_hash,
                    'invoice': invoice_result['invoice'],
                    'amount_msats': amount_msats,
                    'prediction_id': result['prediction_id']
                })
            }
        
        # Route: GET /api/v1/services/image/status/{payment_hash}
        elif method == 'GET' and '/api/v1/services/image/status/' in path:
            payment_hash = path.split('/api/v1/services/image/status/')[-1]
            
            print(f"📊 Checking image status: {payment_hash[:8]}...")
            
            # Get image status
            status = get_image_status(payment_hash)
            
            if status is None:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Image not found'})
                }
            
            # If pending, check Replicate API
            if status == 'pending':
                image_data = get_cached_image(payment_hash)
                if image_data:
                    prediction_id = image_data['image_base64']  # We stored prediction_id here
                    pred_status = get_prediction_status(prediction_id)
                    
                    if pred_status['status'] == 'succeeded' and pred_status['output']:
                        # Image is ready
                        mark_image_available(payment_hash)
                        status = 'available'
                        print(f"✅ Image is now available: {payment_hash[:8]}...")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'payment_hash': payment_hash,
                    'status': status
                })
            }
        
        # Route: GET /api/v1/services/image/retrieve/{payment_hash}
        elif method == 'GET' and '/api/v1/services/image/retrieve/' in path:
            payment_hash = path.split('/api/v1/services/image/retrieve/')[-1]
            
            print(f"🖼️ Retrieving image: {payment_hash[:8]}...")
            
            # Get image
            image_data = get_cached_image(payment_hash)
            
            if image_data is None:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Image not found'})
                }
            
            if image_data['status'] != 'available':
                return {
                    'statusCode': 402,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Payment not confirmed or image not ready'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'payment_hash': payment_hash,
                    'image_base64': image_data['image_base64'],
                    'status': 'available'
                })
            }
        
        # Route: GET /health
        elif method == 'GET' and path == '/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'healthy'})
            }
        
        # Default: 404
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
