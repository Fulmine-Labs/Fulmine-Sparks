# Quick Fix Reference - 404 Status Endpoint Issue

## 🔴 Problem
```
❌ Error: 404 Client Error: Not Found for url: 
https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/{payment_hash}
```

**Root Cause:** Lambda in-memory cache is lost between invocations

---

## ✅ Solution in 5 Steps

### 1️⃣ Create DynamoDB Table (2 minutes)
```bash
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-2

aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-images \
  --time-to-live-specification AttributeName=ttl,Enabled=true \
  --region us-east-2
```

### 2️⃣ Update Lambda IAM Permissions (2 minutes)
```bash
ROLE_NAME=$(aws lambda get-function-configuration \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'Role' \
  --output text | awk -F'/' '{print $NF}')

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

### 3️⃣ Update 5 Functions in lambda_handler_simple.py (15 minutes)

**Function 1: `store_image()` - Add DynamoDB put_item**
```python
def store_image(payment_hash, image_base64):
    current_time = time.time()
    expires_at = current_time + CACHE_DURATION
    
    # Memory cache
    IMAGE_CACHE[payment_hash] = {
        'image_base64': image_base64,
        'status': 'pending',
        'created_at': current_time,
        'expires_at': expires_at,
        'polling_started': False,
        'polling_expires_at': current_time + POLLING_DURATION
    }
    
    # DynamoDB (NEW)
    if DYNAMODB_AVAILABLE:
        try:
            images_table.put_item(Item={
                'payment_hash': payment_hash,
                'image_base64': image_base64,
                'status': 'pending',
                'created_at': int(current_time),
                'expires_at': int(expires_at),
                'ttl': int(expires_at),
                'polling_started': False,
                'polling_expires_at': int(current_time + POLLING_DURATION)
            })
            print(f"✅ Image stored in DynamoDB: {payment_hash[:16]}...")
        except Exception as e:
            print(f"⚠️  Error storing in DynamoDB: {str(e)}")
```

**Function 2: `get_cached_image()` - Add DynamoDB get_item**
```python
def get_cached_image(payment_hash):
    cleanup_expired_images()
    
    # Check memory first
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        if time.time() <= item.get('expires_at', 0):
            return item.get('image_base64')
    
    # Check DynamoDB (NEW)
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                if time.time() <= item.get('expires_at', 0):
                    # Restore to memory cache
                    IMAGE_CACHE[payment_hash] = {
                        'image_base64': item.get('image_base64'),
                        'status': item.get('status', 'pending'),
                        'created_at': item.get('created_at', time.time()),
                        'expires_at': item.get('expires_at', time.time() + CACHE_DURATION),
                        'polling_started': item.get('polling_started', False),
                        'polling_expires_at': item.get('polling_expires_at', time.time() + POLLING_DURATION)
                    }
                    return item.get('image_base64')
        except Exception as e:
            print(f"⚠️  Error getting from DynamoDB: {str(e)}")
    
    return None
```

**Function 3: `get_image_status()` - Add DynamoDB get_item**
```python
def get_image_status(payment_hash):
    cleanup_expired_images()
    
    # Check memory first
    if payment_hash in IMAGE_CACHE:
        item = IMAGE_CACHE[payment_hash]
        if time.time() > item.get('expires_at', 0):
            return 'expired'
        return item.get('status', 'pending')
    
    # Check DynamoDB (NEW)
    if DYNAMODB_AVAILABLE:
        try:
            response = images_table.get_item(Key={'payment_hash': payment_hash})
            if 'Item' in response:
                item = response['Item']
                if time.time() > item.get('expires_at', 0):
                    return 'expired'
                return item.get('status', 'pending')
        except Exception as e:
            print(f"⚠️  Error getting status from DynamoDB: {str(e)}")
    
    return None
```

**Function 4: `mark_image_available()` - Add DynamoDB update_item**
```python
def mark_image_available(payment_hash):
    # Update memory
    if payment_hash in IMAGE_CACHE:
        IMAGE_CACHE[payment_hash]['status'] = 'available'
    
    # Update DynamoDB (NEW)
    if DYNAMODB_AVAILABLE:
        try:
            images_table.update_item(
                Key={'payment_hash': payment_hash},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'available'}
            )
        except Exception as e:
            print(f"⚠️  Error updating in DynamoDB: {str(e)}")
```

**Function 5: `delete_cached_image()` - Add DynamoDB delete_item**
```python
def delete_cached_image(payment_hash):
    # Delete from memory
    if payment_hash in IMAGE_CACHE:
        del IMAGE_CACHE[payment_hash]
    
    # Delete from DynamoDB (NEW)
    if DYNAMODB_AVAILABLE:
        try:
            images_table.delete_item(Key={'payment_hash': payment_hash})
        except Exception as e:
            print(f"⚠️  Error deleting from DynamoDB: {str(e)}")
```

### 4️⃣ Create & Upload Deployment Package (5 minutes)
```bash
cd /workspace/project

python3 << 'EOF'
import subprocess, os, zipfile, shutil

if os.path.exists('lambda_package'):
    shutil.rmtree('lambda_package')
os.makedirs('lambda_package')

subprocess.run(['pip', 'install', 'requests', '-t', 'lambda_package', '-q'], check=True)

shutil.copy('lambda_handler_simple.py', 'lambda_package/lambda_handler.py')
shutil.copy('billing.py', 'lambda_package/')
shutil.copy('configure_alby.py', 'lambda_package/')

with zipfile.ZipFile('fulmine-sparks.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('lambda_package'):
        for file in files:
            if not file.endswith(('.pyc', '.pyo')):
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, 'lambda_package')
                zipf.write(filepath, arcname)

shutil.rmtree('lambda_package')
print("✅ Package created")
EOF

# Upload
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip \
  --region us-east-2
```

### 5️⃣ Set Environment Variable (1 minute)
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

## 🧪 Test It

```bash
# Generate image
python3 client.py generate "A beautiful sunset"

# Check status (should NOT be 404)
python3 client.py status <payment_hash>

# Expected: ✅ Status check successful
# NOT: ❌ Error: 404 Client Error
```

---

## 📊 Before vs After

| Step | Before | After |
|------|--------|-------|
| Generate image | ✅ Works | ✅ Works |
| Poll status (same invocation) | ✅ Works | ✅ Works |
| Poll status (new invocation) | ❌ 404 | ✅ Works |
| After payment | ❌ 404 | ✅ Works |

---

## ⏱️ Total Time: ~25 minutes

- DynamoDB setup: 2 min
- IAM permissions: 2 min
- Code updates: 15 min
- Deploy: 5 min
- Test: 1 min

---

## 🔍 Verify It Worked

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/fulmine-sparks --follow

# Should see:
# ✅ Image stored in DynamoDB
# ✅ Image status found in DynamoDB
# (NOT: ❌ Image not found)

# Check DynamoDB table
aws dynamodb scan --table-name fulmine-sparks-images --region us-east-2

# Should show items with payment_hash
```

---

## 🆘 If Still Getting 404

1. **Check table exists:**
   ```bash
   aws dynamodb describe-table --table-name fulmine-sparks-images --region us-east-2
   ```

2. **Check permissions:**
   ```bash
   aws iam list-role-policies --role-name <lambda-role-name>
   ```

3. **Check environment variable:**
   ```bash
   aws lambda get-function-configuration --function-name fulmine-sparks --region us-east-2 | grep IMAGES_TABLE
   ```

4. **Check logs:**
   ```bash
   aws logs tail /aws/lambda/fulmine-sparks --follow
   ```

---

## 📝 Key Changes Summary

| Function | Change |
|----------|--------|
| `store_image()` | Add `images_table.put_item()` |
| `get_cached_image()` | Add `images_table.get_item()` fallback |
| `get_image_status()` | Add `images_table.get_item()` fallback |
| `mark_image_available()` | Add `images_table.update_item()` |
| `delete_cached_image()` | Add `images_table.delete_item()` |

**Total lines added:** ~80 lines of code

---

*Quick Reference for 404 Status Endpoint Fix - Fulmine-Sparks*
