# Fulmine-Sparks: Recommended Code Improvements

This document provides specific code changes to address the issues identified in the analysis.

---

## 1. Remove Debug Logging (HIGH PRIORITY)

### Current Code (Lines 308-312, 330, 380-381)

```python
def lambda_handler(event, context):
    # ... code ...
    
    # Parse request
    body = event.get('body', '')
    
    # ... code ...
    
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
    
    # ... more code ...
    
    else:
        print(f"DEBUG: No route matched for {http_method} {path}")
        print(f"DEBUG: Full event: {json.dumps(event, default=str)[:1000]}")
        return error_response(404, f"Endpoint not found: {http_method} {path}")
```

### Recommended Fix

```python
import logging

# Add at module level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

        # Determine HTTP method
        http_method = 'POST' if body_data else 'GET'
        actual_method = event.get('requestContext', {}).get('http', {}).get('method')
        if not actual_method:
            actual_method = event.get('httpMethod')
        if actual_method:
            http_method = actual_method

        # Get path from proxy parameter
        path = '/'
        if 'proxy' in event.get('pathParameters', {}):
            path = '/' + event['pathParameters']['proxy']
        elif 'rawPath' in event:
            path = event['rawPath']
        elif 'path' in event.get('pathParameters', {}):
            path = event['pathParameters']['path']

        # Strip stage prefix if present
        for stage in ['prod', 'dev', 'staging', 'test', 'stage']:
            if path.startswith(f'/{stage}/'):
                path = path[len(f'/{stage}'):]
                break

        # Normalize path
        if path != '/' and path.endswith('/'):
            path = path[:-1]

        logger.info(f"Request: {http_method} {path}")

        # Route requests
        if path == '/health' and http_method == 'GET':
            return success_response({
                "status": "ok",
                "service": "Fulmine-Sparks Lambda",
                "timestamp": datetime.now().isoformat()
            })
        
        # ... rest of routing ...
        
        else:
            logger.warning(f"No route matched for {http_method} {path}")
            return error_response(404, f"Endpoint not found: {http_method} {path}")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return error_response(500, str(e))
```

---

## 2. Complete DynamoDB Integration (HIGH PRIORITY)

### Current Code Issues

The code initializes DynamoDB but never uses it:

```python
# Lines 249-264
try:
    import boto3
    DYNAMODB_AVAILABLE = True
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    IMAGES_TABLE = os.getenv('IMAGES_TABLE', 'fulmine-sparks-images')
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        images_table.table_status
    except Exception as e:
        print(f"Warning: Could not connect to DynamoDB table: {e}")
        DYNAMODB_AVAILABLE = False
except ImportError:
    DYNAMODB_AVAILABLE = False
```

But `store_image()` only uses memory cache:

```python
# Lines 47-58
def store_image(payment_hash, image_base64):
    """Store image in memory cache with pending status"""
    current_time = time.time()
    IMAGE_CACHE[payment_hash] = {
        'image_base64': image_base64,
        'status': 'pending',
        'created_at': current_time,
        'expires_at': current_time + CACHE_DURATION,
        'polling_started': False,
        'polling_expires_at': current_time + POLLING_DURATION
    }
    print(f"💾 Image stored in cache for {CACHE_DURATION}s: {payment_hash[:16]}...")
```

### Recommended Fix

```python
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
    logger.info(f"💾 Image stored in memory cache for {CACHE_DURATION}s: {payment_hash[:16]}...")
    
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
                    'ttl': int(expires_at),  # DynamoDB TTL attribute
                    'polling_started': False,
                    'polling_expires_at': int(current_time + POLLING_DURATION)
                }
            )
            logger.info(f"✅ Image stored in DynamoDB for {CACHE_DURATION}s: {payment_hash[:16]}...")
        except Exception as e:
            logger.error(f"⚠️  Error storing image in DynamoDB: {str(e)}")
            # Continue anyway - memory cache is still available


def get_cached_image(payment_hash):
    """Get image from cache (memory first, then DynamoDB)"""
    cleanup_expired_images()
    
    # Check memory cache first (fastest)
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        if time.time() <= item.get('expires_at', 0):
            logger.info(f"✅ Image found in memory cache: {payment_hash[:16]}...")
            return item.get('image_base64')
    
    # Check DynamoDB (fallback)
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                # Check if expired
                if time.time() <= item.get('expires_at', 0):
                    logger.info(f"✅ Image found in DynamoDB: {payment_hash[:16]}...")
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
                    logger.info(f"🗑️  Image expired in DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            logger.error(f"⚠️  Error retrieving image from DynamoDB: {str(e)}")
    
    return None


def get_image_status(payment_hash):
    """Get image status (checks memory first, then DynamoDB)"""
    cleanup_expired_images()
    
    # Check memory cache first
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        current_time = time.time()
        
        # Check if expired
        if current_time > item.get('expires_at', 0):
            logger.info(f"🗑️  Image expired in memory: {payment_hash[:16]}...")
            return 'expired'
        
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
                    logger.info(f"🗑️  Image expired in DynamoDB: {payment_hash[:16]}...")
                    return 'expired'
                
                logger.info(f"✅ Image status found in DynamoDB: {item.get('status')}")
                return item.get('status', 'pending')
        except Exception as e:
            logger.error(f"⚠️  Error getting image status from DynamoDB: {str(e)}")
    
    return None


def mark_image_available(payment_hash):
    """Mark image as available after payment confirmed"""
    # Update memory cache
    if payment_hash in IMAGE_CACHE:
        IMAGE_CACHE[payment_hash]['status'] = 'available'
        logger.info(f"✅ Image marked as available in memory: {payment_hash[:16]}...")
    
    # Update DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.update_item(
                Key={'payment_hash': payment_hash},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'available'}
            )
            logger.info(f"✅ Image marked as available in DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            logger.error(f"⚠️  Error updating image status in DynamoDB: {str(e)}")


def delete_cached_image(payment_hash):
    """Delete image from cache (memory and DynamoDB)"""
    # Delete from memory cache
    if payment_hash in IMAGE_CACHE:
        del IMAGE_CACHE[payment_hash]
        logger.info(f"🗑️  Deleted image from memory cache: {payment_hash[:16]}...")
    
    # Delete from DynamoDB
    if DYNAMODB_AVAILABLE:
        try:
            images_table.delete_item(Key={'payment_hash': payment_hash})
            logger.info(f"🗑️  Deleted image from DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            logger.error(f"⚠️  Error deleting image from DynamoDB: {str(e)}")
```

---

## 3. Improve Path Extraction (MEDIUM PRIORITY)

### Current Code Issues

The current path extraction is fragile and has been the subject of multiple recent commits:

```python
# Lines 305-320
path = '/'
if 'proxy' in event.get('pathParameters', {}):
    path = '/' + event['pathParameters']['proxy']
elif 'rawPath' in event:
    path = event['rawPath']
elif 'path' in event.get('pathParameters', {}):
    path = event['pathParameters']['path']

# Strip stage prefix if present
for stage in ['prod', 'dev', 'staging', 'test', 'stage']:
    if path.startswith(f'/{stage}/'):
        path = path[len(f'/{stage}'):]
        break
```

### Recommended Fix

```python
def extract_path_from_event(event):
    """
    Extract and normalize the request path from Lambda event.
    
    Handles multiple API Gateway formats:
    - HTTP API (rawPath)
    - REST API with proxy (pathParameters.proxy)
    - REST API with path (pathParameters.path)
    """
    path = '/'
    
    # Try different path sources in order of preference
    if 'rawPath' in event:
        # HTTP API format
        path = event['rawPath']
    elif 'pathParameters' in event and event['pathParameters']:
        if 'proxy' in event['pathParameters']:
            # REST API with proxy
            path = '/' + event['pathParameters']['proxy']
        elif 'path' in event['pathParameters']:
            # REST API with path parameter
            path = event['pathParameters']['path']
    
    # Strip stage prefix if present
    # API Gateway may include stage in path: /prod/api/v1/... -> /api/v1/...
    stage_prefixes = ['prod', 'dev', 'staging', 'test', 'stage']
    for stage in stage_prefixes:
        stage_prefix = f'/{stage}/'
        if path.startswith(stage_prefix):
            path = path[len(stage):]  # Remove stage but keep leading slash
            logger.debug(f"Stripped stage prefix '{stage}' from path")
            break
    
    # Normalize path - remove trailing slash except for root
    if path != '/' and path.endswith('/'):
        path = path[:-1]
    
    return path


def extract_http_method(event):
    """
    Extract HTTP method from Lambda event.
    
    Handles multiple API Gateway formats.
    """
    # Try different method sources
    method = event.get('requestContext', {}).get('http', {}).get('method')
    if not method:
        method = event.get('httpMethod')
    if not method:
        # Fallback: infer from body presence
        body = event.get('body', '')
        method = 'POST' if body else 'GET'
    
    return method.upper() if method else 'GET'


# In lambda_handler:
def lambda_handler(event, context):
    """AWS Lambda handler for HTTP requests."""
    try:
        # Parse request body
        body = event.get('body', '')
        try:
            if isinstance(body, str):
                body_data = json.loads(body) if body else {}
            else:
                body_data = body
        except json.JSONDecodeError:
            body_data = {}

        # Extract HTTP method and path
        http_method = extract_http_method(event)
        path = extract_path_from_event(event)

        logger.info(f"Request: {http_method} {path}")

        # Route requests
        if path == '/health' and http_method == 'GET':
            return success_response({
                "status": "ok",
                "service": "Fulmine-Sparks Lambda",
                "timestamp": datetime.now().isoformat()
            })
        
        # ... rest of routing ...
```

---

## 4. Add Request Signing (MEDIUM PRIORITY)

### Recommended Implementation

```python
import hmac
import hashlib
import base64
from typing import Tuple

class RequestValidator:
    """Validate requests using HMAC-SHA256 signing"""
    
    def __init__(self, secret_key: str = None):
        """
        Initialize validator with secret key.
        
        Args:
            secret_key: Secret key for HMAC (defaults to env var)
        """
        self.secret_key = secret_key or os.getenv('API_SECRET_KEY', '')
    
    def generate_signature(self, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            payload: Request payload (JSON string)
        
        Returns:
            Base64-encoded signature
        """
        if not self.secret_key:
            return None
        
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify HMAC-SHA256 signature.
        
        Args:
            payload: Request payload (JSON string)
            signature: Base64-encoded signature from header
        
        Returns:
            True if signature is valid
        """
        if not self.secret_key or not signature:
            return False
        
        expected_signature = self.generate_signature(payload)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)


# In lambda_handler:
def lambda_handler(event, context):
    """AWS Lambda handler for HTTP requests."""
    try:
        # Parse request body
        body = event.get('body', '')
        try:
            if isinstance(body, str):
                body_data = json.loads(body) if body else {}
            else:
                body_data = body
        except json.JSONDecodeError:
            body_data = {}

        # Extract HTTP method and path
        http_method = extract_http_method(event)
        path = extract_path_from_event(event)

        logger.info(f"Request: {http_method} {path}")

        # Verify signature for sensitive endpoints
        if path.startswith('/api/v1/services/image/retrieve/'):
            headers = event.get('headers', {})
            signature = headers.get('X-Signature') or headers.get('x-signature')
            
            if signature:
                validator = RequestValidator()
                if not validator.verify_signature(body, signature):
                    logger.warning(f"Invalid signature for {path}")
                    return error_response(401, "Invalid signature")
            else:
                logger.warning(f"Missing signature for {path}")
                # Optional: require signature
                # return error_response(401, "Missing signature")

        # Route requests
        if path == '/health' and http_method == 'GET':
            return success_response({
                "status": "ok",
                "service": "Fulmine-Sparks Lambda",
                "timestamp": datetime.now().isoformat()
            })
        
        # ... rest of routing ...
```

---

## 5. Implement Persistent Rate Limiting (MEDIUM PRIORITY)

### Recommended Implementation

```python
class PersistentRateLimiter:
    """Rate limiter with DynamoDB persistence"""
    
    def __init__(self, table_name: str = 'fulmine-sparks-rate-limits'):
        """Initialize rate limiter with DynamoDB table"""
        try:
            import boto3
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
            self.table = self.dynamodb.Table(table_name)
            self.available = True
        except Exception as e:
            logger.warning(f"DynamoDB rate limiter unavailable: {e}")
            self.available = False
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if IP is within rate limit.
        
        Returns:
            (allowed: bool, reason: str)
        """
        if not self.available:
            # Fallback to in-memory if DynamoDB unavailable
            return check_rate_limit_memory(ip)
        
        try:
            current_time = time.time()
            window_start = current_time - RATE_LIMIT_WINDOW
            
            # Get IP tracking data
            response = self.table.get_item(Key={'ip': ip})
            data = response.get('Item', {})
            
            # Clean up old requests
            requests = [t for t in data.get('requests', []) if t > window_start]
            unpaid_invoices = data.get('unpaid_invoices', 0)
            
            # Get rate limit for this IP
            rate_limit = get_rate_limit_for_ip_count(unpaid_invoices)
            max_requests = int(rate_limit['requests_per_minute'])
            
            # Check if at limit
            if max_requests == 0:
                return False, f"Rate limited: {rate_limit['description']}"
            
            if len(requests) >= max_requests:
                return False, f"Rate limited: {rate_limit['description']} ({len(requests)}/{max_requests} requests/min)"
            
            # Record this request
            requests.append(current_time)
            
            # Update DynamoDB
            self.table.put_item(
                Item={
                    'ip': ip,
                    'requests': requests,
                    'unpaid_invoices': unpaid_invoices,
                    'ttl': int(current_time + RATE_LIMIT_WINDOW + 3600)  # Keep for 1 hour after last request
                }
            )
            
            return True, f"Allowed: {rate_limit['description']}"
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fallback to in-memory
            return check_rate_limit_memory(ip)
    
    def track_invoice_created(self, payment_hash: str, ip: str):
        """Track that an invoice was created from this IP"""
        if not self.available:
            return
        
        try:
            current_time = time.time()
            response = self.table.get_item(Key={'ip': ip})
            data = response.get('Item', {})
            
            unpaid_invoices = data.get('unpaid_invoices', 0) + 1
            
            self.table.update_item(
                Key={'ip': ip},
                UpdateExpression='SET unpaid_invoices = :count, #ttl = :ttl',
                ExpressionAttributeNames={'#ttl': 'ttl'},
                ExpressionAttributeValues={
                    ':count': unpaid_invoices,
                    ':ttl': int(current_time + 86400)  # Keep for 24 hours
                }
            )
            
            logger.info(f"📊 Invoice created for {ip}: {unpaid_invoices} unpaid invoice(s)")
        except Exception as e:
            logger.error(f"Error tracking invoice: {e}")
    
    def track_payment_confirmed(self, payment_hash: str, ip: str):
        """Track that a payment was confirmed"""
        if not self.available:
            return
        
        try:
            response = self.table.get_item(Key={'ip': ip})
            data = response.get('Item', {})
            
            unpaid_invoices = max(0, data.get('unpaid_invoices', 1) - 1)
            
            self.table.update_item(
                Key={'ip': ip},
                UpdateExpression='SET unpaid_invoices = :count',
                ExpressionAttributeValues={':count': unpaid_invoices}
            )
            
            logger.info(f"✅ Payment confirmed for {ip}: {unpaid_invoices} unpaid invoice(s) remaining")
        except Exception as e:
            logger.error(f"Error tracking payment: {e}")
```

---

## 6. Add Proper Error Handling (MEDIUM PRIORITY)

### Recommended Implementation

```python
class APIError(Exception):
    """Base API error"""
    def __init__(self, status_code: int, message: str, details: str = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)


class RateLimitError(APIError):
    """Rate limit exceeded"""
    def __init__(self, message: str):
        super().__init__(429, message)


class PaymentRequiredError(APIError):
    """Payment required"""
    def __init__(self, message: str):
        super().__init__(402, message)


class NotFoundError(APIError):
    """Resource not found"""
    def __init__(self, message: str):
        super().__init__(404, message)


class ValidationError(APIError):
    """Invalid input"""
    def __init__(self, message: str):
        super().__init__(400, message)


# In lambda_handler:
def lambda_handler(event, context):
    """AWS Lambda handler for HTTP requests."""
    try:
        # ... existing code ...
        
        # Route requests
        if path == '/health' and http_method == 'GET':
            return success_response({
                "status": "ok",
                "service": "Fulmine-Sparks Lambda",
                "timestamp": datetime.now().isoformat()
            })

        elif path == '/api/v1/services/image/generate' and http_method == 'POST':
            try:
                # Check rate limit
                client_ip = get_client_ip(event)
                allowed, reason = check_rate_limit(client_ip)

                if not allowed:
                    logger.warning(f"⛔ Rate limit exceeded for {client_ip}: {reason}")
                    raise RateLimitError(reason)

                return generate_image(body_data, client_ip)
            
            except RateLimitError as e:
                return error_response(e.status_code, e.message)
            except ValidationError as e:
                return error_response(e.status_code, e.message)
            except Exception as e:
                logger.error(f"Error generating image: {e}", exc_info=True)
                return error_response(500, "Error generating image")

        elif path.startswith('/api/v1/services/image/retrieve/') and http_method == 'GET':
            try:
                payment_hash = path.split('/api/v1/services/image/retrieve/')[-1]
                if not payment_hash:
                    raise ValidationError("Payment hash is required")
                return retrieve_image(payment_hash)
            
            except NotFoundError as e:
                return error_response(e.status_code, e.message)
            except PaymentRequiredError as e:
                return error_response(e.status_code, e.message)
            except ValidationError as e:
                return error_response(e.status_code, e.message)
            except Exception as e:
                logger.error(f"Error retrieving image: {e}", exc_info=True)
                return error_response(500, "Error retrieving image")

        else:
            logger.warning(f"No route matched for {http_method} {path}")
            raise NotFoundError(f"Endpoint not found: {http_method} {path}")

    except APIError as e:
        return error_response(e.status_code, e.message)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return error_response(500, "Internal server error")
```

---

## 7. Add Monitoring & Metrics (LOW PRIORITY)

### Recommended Implementation

```python
import time
from functools import wraps

class MetricsCollector:
    """Collect and log metrics to CloudWatch"""
    
    @staticmethod
    def record_metric(metric_name: str, value: float, unit: str = 'Count'):
        """Record a metric to CloudWatch"""
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch')
            cloudwatch.put_metric_data(
                Namespace='Fulmine-Sparks',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.now()
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
    
    @staticmethod
    def time_operation(operation_name: str):
        """Decorator to time operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    MetricsCollector.record_metric(
                        f'{operation_name}_duration',
                        duration,
                        'Seconds'
                    )
                    MetricsCollector.record_metric(
                        f'{operation_name}_success',
                        1,
                        'Count'
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    MetricsCollector.record_metric(
                        f'{operation_name}_duration',
                        duration,
                        'Seconds'
                    )
                    MetricsCollector.record_metric(
                        f'{operation_name}_error',
                        1,
                        'Count'
                    )
                    raise
            return wrapper
        return decorator


# Usage:
@MetricsCollector.time_operation('image_generation')
def generate_image(body_data, client_ip=None):
    """Generate an image using Replicate API."""
    # ... existing code ...
```

---

## Summary of Changes

| Priority | Issue | Fix | Effort |
|----------|-------|-----|--------|
| HIGH | Debug logging in production | Remove DEBUG print statements, use logging module | 30 min |
| HIGH | DynamoDB not implemented | Complete DynamoDB integration in cache functions | 1 hour |
| MEDIUM | Path extraction issues | Extract to separate function, improve robustness | 45 min |
| MEDIUM | No request signing | Add HMAC-SHA256 signature verification | 1 hour |
| MEDIUM | Rate limiting not persistent | Implement DynamoDB-backed rate limiter | 1.5 hours |
| MEDIUM | Error handling | Create custom exception classes | 45 min |
| LOW | No monitoring | Add CloudWatch metrics collection | 1 hour |

**Total Estimated Effort:** 6-7 hours

---

## Testing Recommendations

After implementing these changes:

1. **Unit Tests**
   ```bash
   pytest tests/test_path_extraction.py
   pytest tests/test_rate_limiting.py
   pytest tests/test_dynamodb_cache.py
   ```

2. **Integration Tests**
   ```bash
   python3 client.py generate "Test image"
   python3 client.py status <payment_hash>
   python3 client.py retrieve <payment_hash>
   ```

3. **Load Tests**
   ```bash
   python3 test_rate_limiting.py
   ```

4. **Security Tests**
   - Test signature verification
   - Test rate limit bypass attempts
   - Test path traversal attempts

---

*Recommendations compiled: 2025-02-23*
