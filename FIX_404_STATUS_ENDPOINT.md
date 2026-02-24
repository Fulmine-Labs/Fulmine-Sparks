# Fix: 404 Error on Status Endpoint - Complete Implementation Guide

## 🔴 The Problem

When the client polls the status endpoint, it gets a **404 Not Found** error:

```
❌ Error: 404 Client Error: Not Found for url: 
https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/b4db0ffe4895fe18...
```

### Root Cause

**Lambda invocations are stateless.** Each time the Lambda function is invoked:
1. A new process starts with fresh memory
2. The in-memory `IMAGE_CACHE` dictionary is empty
3. The image stored in the previous invocation is lost
4. The status endpoint can't find the image → returns 404

### Timeline of the Problem

```
Invocation 1 (02:07:31):
├─ POST /api/v1/services/image/generate
├─ Generate image (10-15 seconds)
├─ Store in IMAGE_CACHE ✅
├─ Return invoice with payment_hash
└─ Lambda execution ends

Invocation 2 (02:07:32):
├─ GET /api/v1/services/image/status/{payment_hash}
├─ Check IMAGE_CACHE (empty!) ❌
├─ Image not found
└─ Return 404 ❌

Invocation 3 (02:07:33):
├─ GET /api/v1/services/image/status/{payment_hash}
├─ Check IMAGE_CACHE (still empty!) ❌
└─ Return 404 ❌
```

---

## ✅ The Solution

Use **DynamoDB for persistent storage** instead of just in-memory cache.

### Architecture Change

```
BEFORE (Broken):
┌─────────────────────────────────────────┐
│ Lambda Invocation 1                     │
├─────────────────────────────────────────┤
│ IMAGE_CACHE = {                         │
│   "payment_hash": {image_data}          │
│ }                                       │
└─────────────────────────────────────────┘
         ↓ (memory lost)
┌─────────────────────────────────────────┐
│ Lambda Invocation 2                     │
├─────────────────────────────────────────┤
│ IMAGE_CACHE = {} (empty!)               │
│ → 404 Not Found                         │
└─────────────────────────────────────────┘

AFTER (Fixed):
┌─────────────────────────────────────────┐
│ Lambda Invocation 1                     │
├─────────────────────────────────────────┤
│ IMAGE_CACHE = {payment_hash: data}      │
│ DynamoDB = {payment_hash: data} ✅      │
└─────────────────────────────────────────┘
         ↓ (memory lost, but data persists)
┌─────────────────────────────────────────┐
│ Lambda Invocation 2                     │
├─────────────────────────────────────────┤
│ IMAGE_CACHE = {} (empty)                │
│ DynamoDB = {payment_hash: data} ✅      │
│ → Read from DynamoDB ✅                 │
│ → Return status ✅                      │
└─────────────────────────────────────────┘
```

---

## 🔧 Implementation Steps

### Step 1: Verify DynamoDB Table Exists

First, check if the DynamoDB table is created:

```bash
# List DynamoDB tables
aws dynamodb list-tables --region us-east-2

# Should see: fulmine-sparks-images
```

If the table doesn't exist, create it:

```bash
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-2

# Enable TTL (auto-cleanup after 15 seconds)
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-images \
  --time-to-live-specification AttributeName=ttl,Enabled=true \
  --region us-east-2
```

### Step 2: Update Lambda IAM Permissions

The Lambda execution role needs DynamoDB permissions:

```bash
# Get the Lambda execution role name
ROLE_NAME=$(aws lambda get-function-configuration \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'Role' \
  --output text | awk -F'/' '{print $NF}')

echo "Lambda Role: $ROLE_NAME"

# Create inline policy for DynamoDB
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name DynamoDBAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-images"
    }]
  }'
```

### Step 3: Update Lambda Code

Replace the cache functions in `lambda_handler_simple.py`:

#### Function 1: `store_image()` - Store in Both Memory AND DynamoDB

**BEFORE (Lines 47-58):**
```python
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

**AFTER:**
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
                    'ttl': int(expires_at),  # DynamoDB TTL attribute
                    'polling_started': False,
                    'polling_expires_at': int(current_time + POLLING_DURATION)
                }
            )
            print(f"✅ Image stored in DynamoDB for {CACHE_DURATION}s: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error storing image in DynamoDB: {str(e)}")
            # Continue anyway - memory cache is still available
```

#### Function 2: `get_cached_image()` - Check Memory First, Then DynamoDB

**BEFORE (Lines 60-67):**
```python
def get_cached_image(payment_hash):
    """Get image from cache if it exists and hasn't expired"""
    cleanup_expired_images()
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        if time.time() <= item.get('expires_at', 0):
            return item.get('image_base64')
    return None
```

**AFTER:**
```python
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
```

#### Function 3: `get_image_status()` - Check Memory First, Then DynamoDB

**BEFORE (Lines 195-208):**
```python
def get_image_status(payment_hash):
    """Get image status"""
    cleanup_expired_images()
    if payment_hash not in IMAGE_CACHE:
        return None
    
    item = IMAGE_CACHE[payment_hash]
    current_time = time.time()
    
    # Check if expired
    if current_time > item.get('expires_at', 0):
        return 'expired'
    
    return item.get('status', 'pending')
```

**AFTER:**
```python
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
```

#### Function 4: `mark_image_available()` - Update Both Memory AND DynamoDB

**BEFORE (Lines 210-214):**
```python
def mark_image_available(payment_hash):
    """Mark image as available after payment confirmed"""
    if payment_hash in IMAGE_CACHE:
        IMAGE_CACHE[payment_hash]['status'] = 'available'
        print(f"✅ Image marked as available: {payment_hash[:16]}...")
```

**AFTER:**
```python
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
```

#### Function 5: `delete_cached_image()` - Delete from Both Memory AND DynamoDB

**BEFORE (Lines 216-220):**
```python
def delete_cached_image(payment_hash):
    """Delete image from cache"""
    if payment_hash in IMAGE_CACHE:
        del IMAGE_CACHE[payment_hash]
        print(f"🗑️  Deleted image from cache: {payment_hash[:16]}...")
```

**AFTER:**
```python
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
```

### Step 4: Create Deployment Package

```bash
cd /workspace/project

python3 << 'EOF'
import subprocess, os, zipfile, shutil

# Clean up old package
if os.path.exists('lambda_package'):
    shutil.rmtree('lambda_package')
os.makedirs('lambda_package')

# Install dependencies
subprocess.run(['pip', 'install', 'requests', '-t', 'lambda_package', '-q'], check=True)

# Copy files
shutil.copy('lambda_handler_simple.py', 'lambda_package/lambda_handler.py')
shutil.copy('billing.py', 'lambda_package/')
shutil.copy('configure_alby.py', 'lambda_package/')
shutil.copy('client.py', 'lambda_package/')

# Create zip
with zipfile.ZipFile('fulmine-sparks.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('lambda_package'):
        for file in files:
            if not file.endswith(('.pyc', '.pyo')):
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, 'lambda_package')
                zipf.write(filepath, arcname)

shutil.rmtree('lambda_package')
print("✅ Deployment package created: fulmine-sparks.zip")
EOF
```

### Step 5: Upload to Lambda

```bash
# Update Lambda function code
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip \
  --region us-east-2

# Wait for update to complete
sleep 5

# Verify update
aws lambda get-function-configuration \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'LastModified'
```

### Step 6: Set Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables="{
    REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN,
    ALBY_NWC_URL=$ALBY_NWC_URL,
    ALBY_API_TOKEN=$ALBY_API_TOKEN,
    IMAGES_TABLE=fulmine-sparks-images
  }" \
  --region us-east-2
```

---

## 🧪 Testing the Fix

### Test 1: Generate Image

```bash
python3 client.py generate "A beautiful sunset over the ocean"
```

**Expected Output:**
```
✅ Image generated successfully
💰 Payment Required
Amount: 78 sats ($0.0050)
Payment Hash: b4db0ffe4895fe18...

⚡ Lightning Invoice (BOLT11):
lnbc780n1p5e6p74...

📝 Payment Instructions:
1. Scan the QR code with your Lightning wallet
2. Send 78 sats
3. Payment will be detected automatically

⏳ Polling for payment confirmation...
```

### Test 2: Check Status (Before Payment)

```bash
python3 client.py status b4db0ffe4895fe18...
```

**Expected Output:**
```
✅ Status check successful
Status: pending
Payment Hash: b4db0ffe4895fe18...
```

**NOT:**
```
❌ Error: 404 Client Error: Not Found
```

### Test 3: Check CloudWatch Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

**Expected Log Output:**
```
💾 Image stored in memory cache for 15s: b4db0ffe4895fe18...
✅ Image stored in DynamoDB for 15s: b4db0ffe4895fe18...
📊 Image status: pending
✅ Image status found in DynamoDB: pending
```

### Test 4: Verify DynamoDB

```bash
# Scan the table
aws dynamodb scan \
  --table-name fulmine-sparks-images \
  --region us-east-2

# Should show items with payment_hash as key
```

---

## 🔍 Troubleshooting

### Issue: Still Getting 404

**Check 1: DynamoDB Table Exists**
```bash
aws dynamodb describe-table \
  --table-name fulmine-sparks-images \
  --region us-east-2
```

**Check 2: Lambda Has DynamoDB Permissions**
```bash
# Get role name
ROLE_NAME=$(aws lambda get-function-configuration \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'Role' \
  --output text | awk -F'/' '{print $NF}')

# Check inline policies
aws iam list-role-policies --role-name $ROLE_NAME
```

**Check 3: CloudWatch Logs**
```bash
aws logs tail /aws/lambda/fulmine-sparks --follow

# Look for errors like:
# "Error storing image in DynamoDB"
# "Error getting image status from DynamoDB"
```

**Check 4: Environment Variable Set**
```bash
aws lambda get-function-configuration \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'Environment.Variables.IMAGES_TABLE'

# Should return: fulmine-sparks-images
```

### Issue: DynamoDB Timeout

If you see "DynamoDB timeout" errors:

1. Check table status:
```bash
aws dynamodb describe-table \
  --table-name fulmine-sparks-images \
  --region us-east-2 \
  --query 'Table.TableStatus'
```

2. Check if Lambda is in VPC (shouldn't be for DynamoDB access)
3. Increase Lambda timeout to 30 seconds

### Issue: Items Not Persisting

Check TTL is enabled:
```bash
aws dynamodb describe-time-to-live \
  --table-name fulmine-sparks-images \
  --region us-east-2
```

Should show:
```json
{
  "TimeToLiveDescription": {
    "AttributeName": "ttl",
    "TimeToLiveStatus": "ENABLED"
  }
}
```

---

## 📊 Expected Behavior After Fix

### Before (Broken)
```
Invocation 1: Generate image → Store in memory ✅
Invocation 2: Poll status → 404 ❌
Invocation 3: Poll status → 404 ❌
```

### After (Fixed)
```
Invocation 1: Generate image → Store in memory + DynamoDB ✅
Invocation 2: Poll status → Read from DynamoDB ✅
Invocation 3: Poll status → Read from DynamoDB ✅
Invocation 4: After payment → Update in DynamoDB ✅
Invocation 5: Retrieve image → Read from DynamoDB ✅
```

---

## 📈 Performance Impact

| Operation | Before | After | Impact |
|-----------|--------|-------|--------|
| Store image | <1ms | 10-50ms | +10-50ms (acceptable) |
| Get status | <1ms | 10-50ms | +10-50ms (acceptable) |
| Retrieve image | <1ms | 10-50ms | +10-50ms (acceptable) |
| **Total latency** | 15-20s | 15-20s | **No change** |

The DynamoDB latency is negligible compared to image generation time (10-15 seconds).

---

## ✅ Verification Checklist

- [ ] DynamoDB table created
- [ ] TTL enabled on table
- [ ] Lambda IAM permissions updated
- [ ] Code updated with DynamoDB calls
- [ ] Deployment package created
- [ ] Lambda function updated
- [ ] Environment variables set
- [ ] Test: Generate image
- [ ] Test: Check status (should NOT be 404)
- [ ] Test: CloudWatch logs show DynamoDB operations
- [ ] Test: DynamoDB table has items
- [ ] Test: Items expire after 15 seconds

---

## 🎯 Summary

**The Fix:**
1. Create DynamoDB table for persistent storage
2. Update cache functions to use DynamoDB
3. Check memory first (fast), then DynamoDB (persistent)
4. Update Lambda code and redeploy

**Result:**
- ✅ Status endpoint returns correct status (not 404)
- ✅ Images persist across Lambda invocations
- ✅ Payment polling works correctly
- ✅ Image retrieval works after payment

**Time to Implement:** 30-45 minutes

---

*Implementation Guide for Fulmine-Sparks 404 Status Endpoint Fix*
