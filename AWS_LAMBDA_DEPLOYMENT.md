# 🚀 AWS Lambda Deployment Guide

Deploy Fulmine-Sparks to AWS Lambda serverless in 10 minutes!

## Why AWS Lambda?

- ✅ **Free tier:** 1M requests/month
- ✅ **Pay per use:** Only pay for what you use
- ✅ **No idle costs:** No charges when not in use
- ✅ **Auto-scaling:** Handles traffic automatically
- ✅ **Perfect for passthrough:** Ideal for API calls to Replicate

## Cost Comparison

| Usage | Railway | Lambda |
|-------|---------|--------|
| 100 requests/month | $5 | FREE ✅ |
| 1,000 requests/month | $5 | FREE ✅ |
| 10,000 requests/month | $5 | FREE ✅ |
| 100,000 requests/month | $5 | FREE ✅ |
| 1M requests/month | $5 | FREE ✅ |
| 2M requests/month | $5 | $0.20 |

## Prerequisites

1. **AWS Account** - Free tier available
2. **AWS CLI** - Command line tool
3. **Replicate API Token** - For image generation

## Step 1: Create AWS Account

1. Go to: https://aws.amazon.com
2. Click "Create an AWS Account"
3. Sign up (free tier available)
4. Verify email and set up payment method

## Step 2: Install AWS CLI

**On Mac:**
```bash
brew install awscli
```

**On Linux:**
```bash
sudo apt-get install awscli
```

**On Windows:**
- Download from: https://aws.amazon.com/cli/
- Or use: `pip install awscli`

## Step 3: Configure AWS CLI

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID** - Get from AWS console
- **AWS Secret Access Key** - Get from AWS console
- **Default region** - Use: `us-east-1`
- **Default output format** - Use: `json`

### How to get AWS credentials:

1. Go to: https://console.aws.amazon.com
2. Click your username (top right)
3. Go to "Security credentials"
4. Click "Create access key"
5. Copy the Access Key ID and Secret Access Key
6. Use them in `aws configure`

## Step 4: Deploy to Lambda

### Option A: Automatic Deployment (Easiest)

```bash
cd /workspace/Fulmine-Spark
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

The script will:
- ✅ Create IAM role
- ✅ Package your code
- ✅ Deploy to Lambda
- ✅ Set up API Gateway
- ✅ Give you a public URL

### Option B: Manual Deployment

If the script doesn't work, follow these steps:

**1. Create IAM Role**
```bash
aws iam create-role \
  --role-name fulmine-sparks-lambda-role \
  --assume-role-policy-document file://trust-policy.json
```

**2. Create Deployment Package**
```bash
mkdir lambda_package
cp lambda_handler.py lambda_package/
cp -r fulmine_spark lambda_package/
pip install -r requirements.txt -t lambda_package/
cd lambda_package
zip -r ../fulmine-sparks.zip .
cd ..
```

**3. Create Lambda Function**
```bash
aws lambda create-function \
  --function-name fulmine-sparks \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/fulmine-sparks-lambda-role \
  --handler lambda_handler.lambda_handler \
  --timeout 300 \
  --memory-size 512 \
  --zip-file fileb://fulmine-sparks.zip \
  --environment Variables="{REPLICATE_API_TOKEN=your_token_here}"
```

**4. Create API Gateway**
```bash
aws apigatewayv2 create-api \
  --name fulmine-sparks \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:fulmine-sparks
```

## Step 5: Get Your API URL

After deployment, you'll see:
```
🔗 Your API URL:
   https://abc123.execute-api.us-east-1.amazonaws.com
```

Copy this URL!

## Step 6: Update Pythonista Client

On your iPhone in Pythonista:

1. Open `pythonista_client.py`
2. Find line 20:
   ```python
   API_BASE_URL = "http://10.2.38.143:8000"
   ```
3. Replace with your Lambda URL:
   ```python
   API_BASE_URL = "https://abc123.execute-api.us-east-1.amazonaws.com"
   ```
4. Save

## Step 7: Test from iPhone

1. Open Pythonista
2. Run `pythonista_client.py`
3. Enter: "a beautiful sunset"
4. Tap "🎨 Generate Image"
5. Wait 30-60 seconds
6. Image appears! ✨

## Monitoring

### View Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

### Check Function Status

```bash
aws lambda get-function --function-name fulmine-sparks
```

### View Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=fulmine-sparks \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Updating Your Code

When you make changes:

```bash
# Rebuild package
mkdir lambda_package
cp lambda_handler.py lambda_package/
cp -r fulmine_spark lambda_package/
pip install -r requirements.txt -t lambda_package/
cd lambda_package
zip -r ../fulmine-sparks.zip .
cd ..

# Update Lambda
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip
```

Or use the deployment script:
```bash
./deploy_lambda.sh
```

## Troubleshooting

### "AWS CLI not found"
- Install AWS CLI: https://aws.amazon.com/cli/
- Or: `pip install awscli`

### "Not authenticated with AWS"
- Run: `aws configure`
- Enter your AWS credentials

### "Function timeout"
- Image generation takes 30-60 seconds
- Lambda timeout is set to 300 seconds (5 minutes)
- Should be fine

### "REPLICATE_API_TOKEN not set"
- Update environment variable:
  ```bash
  aws lambda update-function-configuration \
    --function-name fulmine-sparks \
    --environment Variables="{REPLICATE_API_TOKEN=your_token}"
  ```

### "API Gateway not working"
- Check that Lambda function is deployed
- Check that API Gateway is configured
- Check CloudWatch logs for errors

## Costs

### Free Tier
- 1M requests/month
- 400,000 GB-seconds/month
- Perfect for testing

### After Free Tier
- **Requests:** $0.20 per 1M requests
- **Compute:** $0.0000166667 per GB-second
- **Plus Replicate API costs**

### Example Monthly Costs

**100 requests/month:**
- Lambda: FREE
- Replicate: ~$1-5
- **Total: ~$1-5**

**1,000 requests/month:**
- Lambda: FREE
- Replicate: ~$10-50
- **Total: ~$10-50**

**10,000 requests/month:**
- Lambda: FREE
- Replicate: ~$100-500
- **Total: ~$100-500**

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

## Files

- `lambda_handler.py` - Lambda function code
- `deploy_lambda.sh` - Deployment script
- `requirements.txt` - Python dependencies

## Next Steps

1. ✅ Create AWS account
2. ✅ Install AWS CLI
3. ✅ Configure AWS CLI
4. ✅ Run deployment script
5. ✅ Get API URL
6. ✅ Update Pythonista client
7. ✅ Test from iPhone

## Support

- **AWS Lambda Docs:** https://docs.aws.amazon.com/lambda/
- **AWS CLI Docs:** https://docs.aws.amazon.com/cli/
- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues

---

**🎉 Your Fulmine-Sparks service is now serverless!**

**Pay only for what you use - perfect for testing and production!**
