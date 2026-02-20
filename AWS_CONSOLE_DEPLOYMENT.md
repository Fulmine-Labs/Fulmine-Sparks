# 🚀 AWS Lambda Deployment via Console (No CLI Needed!)

Deploy Fulmine-Sparks to AWS Lambda using just the AWS Console - no terminal commands needed!

## Prerequisites

- ✅ AWS Account (created)
- ✅ Replicate API Token
- ✅ `fulmine-sparks.zip` file (ready to upload)

## Step 1: Download the ZIP File

The ZIP file is ready at:
```
/workspace/Fulmine-Spark/fulmine-sparks.zip
```

**Download it to your computer:**
1. Go to: https://github.com/Fulmine-Labs/Fulmine-Sparks
2. Click "Code" → "Download ZIP"
3. Or download directly: `fulmine-sparks.zip`

## Step 2: Go to AWS Lambda Console

1. Go to: https://console.aws.amazon.com/lambda
2. Make sure you're in region: **us-east-1** (top right)
3. Click "Create function"

## Step 3: Create Lambda Function

Fill in the form:

**Function name:** `fulmine-sparks`

**Runtime:** `Python 3.11`

**Architecture:** `x86_64`

**Permissions:** 
- Select "Create a new role with basic Lambda permissions"
- Role name: `fulmine-sparks-lambda-role`

Click "Create function"

## Step 4: Upload Your Code

1. In the Lambda console, scroll down to "Code source"
2. Click "Upload from" → ".zip file"
3. Click "Upload"
4. Select the `fulmine-sparks.zip` file from your computer
5. Click "Save"

Wait for upload to complete (may take 1-2 minutes)

## Step 5: Configure Handler

1. Scroll down to "Runtime settings"
2. Click "Edit"
3. Change **Handler** to: `lambda_handler.lambda_handler`
4. Click "Save"

## Step 6: Increase Timeout

Image generation takes 30-60 seconds, so we need more time:

1. Click "Configuration" tab
2. Click "General configuration"
3. Click "Edit"
4. Change **Timeout** to: `300` seconds (5 minutes)
5. Change **Memory** to: `512` MB
6. Click "Save"

## Step 7: Add Environment Variables

1. Click "Configuration" tab
2. Click "Environment variables"
3. Click "Edit"
4. Click "Add environment variable"
5. Fill in:
   - **Key:** `REPLICATE_API_TOKEN`
   - **Value:** Your Replicate API token
6. Click "Save"

## Step 8: Create API Gateway

Now we need to make your Lambda function accessible via a public URL.

1. Go to: https://console.aws.amazon.com/apigateway
2. Click "Create API"
3. Select "HTTP API"
4. Click "Build"

**Create API:**
- **API name:** `fulmine-sparks`
- Click "Next"

**Configure routes:**
- **Resource path:** `$default` (keep as is)
- **Method:** `ANY`
- **Integration:** Select your `fulmine-sparks` Lambda function
- Click "Next"

**Review and create:**
- Click "Create"

## Step 9: Get Your Public URL

After API Gateway is created:

1. Go to "APIs" in API Gateway console
2. Click on `fulmine-sparks`
3. Look for **Invoke URL** (something like: `https://abc123.execute-api.us-east-1.amazonaws.com`)
4. **Copy this URL!**

## Step 10: Update Pythonista Client

On your iPhone in Pythonista:

1. Open `pythonista_client.py`
2. Find line 20:
   ```python
   API_BASE_URL = "http://10.2.38.143:8000"
   ```
3. Replace with your API Gateway URL:
   ```python
   API_BASE_URL = "https://abc123.execute-api.us-east-1.amazonaws.com"
   ```
4. Save the file

## Step 11: Test from iPhone

1. Open Pythonista
2. Run `pythonista_client.py`
3. Enter a prompt: "a beautiful sunset"
4. Tap "🎨 Generate Image"
5. Wait 30-60 seconds
6. Image appears! ✨

## Troubleshooting

### "Upload failed"
- Make sure ZIP file is not corrupted
- Try downloading again
- Check file size is ~12 MB

### "Handler not found"
- Make sure handler is: `lambda_handler.lambda_handler`
- Make sure ZIP file was uploaded successfully

### "Timeout"
- Image generation takes 30-60 seconds
- Make sure timeout is set to 300 seconds
- Check CloudWatch logs for errors

### "REPLICATE_API_TOKEN not set"
- Go to Configuration → Environment variables
- Make sure token is added correctly
- Save changes

### "API Gateway not working"
- Make sure Lambda function is deployed
- Check that API Gateway is configured correctly
- Try accessing the health endpoint: `https://your-url/health`

## Monitoring

### View Logs

1. Go to Lambda console
2. Click your function
3. Click "Monitor" tab
4. Click "View CloudWatch logs"
5. You'll see real-time logs

### Check Invocations

1. Go to Lambda console
2. Click your function
3. Click "Monitor" tab
4. See number of invocations, errors, duration

## Updating Your Code

When you make changes:

1. Create new `fulmine-sparks.zip` file
2. Go to Lambda console
3. Click "Upload from" → ".zip file"
4. Select new ZIP file
5. Click "Save"

## Costs

### Free Tier
- 1M requests/month
- 400,000 GB-seconds/month
- Perfect for testing

### After Free Tier
- **Requests:** $0.20 per 1M requests
- **Compute:** $0.0000166667 per GB-second
- **Plus Replicate API costs**

## Architecture

```
iPhone (Pythonista)
    ↓
HTTPS Request
    ↓
API Gateway
    ↓
AWS Lambda
    ↓
Replicate API
    ↓
Image Generation
    ↓
Base64 Response
    ↓
iPhone displays image ✨
```

## Summary

✅ Create Lambda function
✅ Upload ZIP file
✅ Configure handler
✅ Increase timeout
✅ Add environment variables
✅ Create API Gateway
✅ Get public URL
✅ Update Pythonista client
✅ Test from iPhone

## Support

- **AWS Lambda Docs:** https://docs.aws.amazon.com/lambda/
- **AWS API Gateway Docs:** https://docs.aws.amazon.com/apigateway/
- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues

---

**🎉 Your Fulmine-Sparks service is now live on AWS Lambda!**

**No CLI needed - just click through the AWS Console!**
