# 🚀 Deployment Steps

The code has been fixed and pushed to GitHub, but you need to upload the new ZIP file to Lambda for the changes to take effect.

## 📋 Quick Deployment

### Step 1: Download the Latest ZIP

```bash
# Download from GitHub
wget https://raw.githubusercontent.com/Fulmine-Labs/Fulmine-Sparks/master/fulmine-sparks.zip

# Or if you have the file locally
# Just use the fulmine-sparks.zip from the project
```

### Step 2: Upload to Lambda

**Option A: Using AWS CLI**
```bash
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip
```

**Option B: Using AWS Console**
1. Go to AWS Console → Lambda
2. Find "fulmine-sparks" function
3. Click "Upload from" → ".zip file"
4. Select `fulmine-sparks.zip`
5. Click "Save"

### Step 3: Verify Deployment

Wait 30 seconds for Lambda to update, then test:

```bash
python3 test_workflow.py https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod
```

## 🔍 What Changed

### Latest Fixes (Commit 3f7775d)

**Fixed Replicate Model Identifier**:
- ❌ Before: `bytedance/seedream:latest` (invalid)
- ✅ After: `bytedance/seedream-4.5` (correct)

### Previous Fixes

1. **Payment Detection** (Commit 4320ee0)
   - Added detailed logging
   - Uses ALBY_API_TOKEN for authentication
   - Checks Alby API for payment status

2. **Debugging** (Commit 4320ee0)
   - Logs all Alby API responses
   - Shows invoice structure
   - Helps identify payment hash matching issues

## 📊 Expected Behavior After Deployment

### Successful Flow

```
1. Health Check
   ✅ GET /health → 200 OK

2. Generate Image
   ✅ POST /api/v1/services/image/generate → 201 Created
   📋 Response includes:
      - payment_hash: ac990488d0fc0d76...
      - invoice: lnbc760n1p5eazzadp...
      - amount_msats: 76000

3. Create Lightning Invoice
   ✅ Invoice created via Alby NWC
   ✅ Image generated and stored in cache

4. Poll for Payment
   ⏳ GET /api/v1/services/image/status/{payment_hash}
   ⏳ Waiting for payment...

5. Payment Detected
   ✅ Payment received on Lightning Network
   ✅ Status changes to "available"

6. Retrieve Image
   ✅ GET /api/v1/services/image/retrieve/{payment_hash}
   ✅ Image returned as base64
```

## 🧪 Testing After Deployment

### 1. Quick Health Check

```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health
```

Expected response:
```json
{"status": "ok", "service": "Fulmine-Sparks Lambda", "timestamp": "..."}
```

### 2. Full Workflow Test

```bash
python3 test_workflow.py https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod
```

Expected output:
```
✅ PASS: Health endpoint returns 200
✅ PASS: Generate endpoint returns 200
✅ Invoice created: ac990488d0fc0d7...
⏳ Polling for payment...
✅ Payment detected!
🎨 Image retrieved successfully
```

### 3. Check CloudWatch Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

Look for:
- `🎨 Using model: bytedance/seedream-4.5` (new code)
- `✅ Real invoice created via Alby API`
- `📋 Invoice response keys: [...]`
- `✅ Invoice found: ... settled=true`

## ⚠️ Troubleshooting

### Still Getting "Invalid version" Error

**Cause**: Lambda hasn't been updated yet

**Solution**:
1. Verify you uploaded the correct ZIP file
2. Wait 30 seconds for Lambda to update
3. Check the Lambda function code in AWS Console
4. Look for `bytedance/seedream-4.5` in the code

### Getting "REPLICATE_API_TOKEN not set"

**Cause**: Environment variable not configured

**Solution**:
1. Go to Lambda → fulmine-sparks → Configuration
2. Click "Environment variables"
3. Add: `REPLICATE_API_TOKEN` = your token
4. Save and test again

### Getting "ALBY_NWC_URL not set"

**Cause**: Alby configuration missing

**Solution**:
1. Go to Lambda → fulmine-sparks → Configuration
2. Click "Environment variables"
3. Add: `ALBY_NWC_URL` = your NWC connection string
4. Save and test again

## 📝 Deployment Checklist

- [ ] Downloaded latest `fulmine-sparks.zip` from GitHub
- [ ] Uploaded ZIP to Lambda function
- [ ] Waited 30 seconds for update
- [ ] Verified health endpoint works
- [ ] Ran full workflow test
- [ ] Checked CloudWatch logs
- [ ] Confirmed "bytedance/seedream-4.5" in logs
- [ ] Payment detection working

## 🎯 Next Steps

1. **Deploy the ZIP file** to Lambda
2. **Wait 30 seconds** for update
3. **Run the test workflow**
4. **Check CloudWatch logs** for debugging info
5. **Share any errors** if issues persist

---

Made with ⚡ by Fulmine Labs
