# ⚡ Fulmine-Sparks Quick Start Guide

Get up and running with Fulmine-Sparks in 5 minutes!

## What's Fixed

✅ **Rate Limiting Issue Resolved**: Rate limiting now persists across Lambda invocations using DynamoDB
✅ **Image Generation Workflow**: Complete workflow (generate → status → retrieve) now works correctly
✅ **Persistent Storage**: Both images and rate limits stored in DynamoDB with automatic cleanup

## Prerequisites

- AWS Account
- AWS CLI configured
- Python 3.9+
- Replicate API token (get one at https://replicate.com/)
- Alby Hub NWC URL (get one at https://getalby.com/)

## Quick Deployment (5 minutes)

### 1. Create DynamoDB Tables

```bash
# Images table
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-images \
  --time-to-live-specification Enabled=true,AttributeName=ttl

# Rate limits table
aws dynamodb create-table \
  --table-name fulmine-sparks-rate-limits \
  --attribute-definitions AttributeName=client_ip,AttributeType=S \
  --key-schema AttributeName=client_ip,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-rate-limits \
  --time-to-live-specification Enabled=true,AttributeName=ttl
```

### 2. Create Lambda Execution Role

```bash
# Create role
aws iam create-role \
  --role-name fulmine-sparks-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Add DynamoDB permissions
aws iam put-role-policy \
  --role-name fulmine-sparks-lambda-role \
  --policy-name dynamodb-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/fulmine-sparks-images",
        "arn:aws:dynamodb:*:*:table/fulmine-sparks-rate-limits"
      ]
    }]
  }'

# Add CloudWatch Logs permissions
aws iam attach-role-policy \
  --role-name fulmine-sparks-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 3. Create Deployment Package

```bash
# Create package
mkdir -p lambda_package
pip install requests -t lambda_package -q

# Copy files
cp lambda_handler_simple.py lambda_package/lambda_handler.py
cp billing.py lambda_package/
cp configure_alby.py lambda_package/

# Create zip
cd lambda_package && zip -r ../fulmine-sparks.zip . -q && cd ..
```

### 4. Create Lambda Function

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws lambda create-function \
  --function-name fulmine-sparks \
  --runtime python3.9 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/fulmine-sparks-lambda-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://fulmine-sparks.zip \
  --timeout 60 \
  --memory-size 512
```

### 5. Set Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables="{
    REPLICATE_API_TOKEN=your_token_here,
    ALBY_NWC_URL=nostr+walletconnect://your_url_here,
    IMAGES_TABLE=fulmine-sparks-images,
    RATE_LIMITS_TABLE=fulmine-sparks-rate-limits
  }"
```

### 6. Create API Gateway

```bash
# Create API
API_ID=$(aws apigateway create-rest-api \
  --name fulmine-sparks-api \
  --query 'id' --output text)

# Get root resource
ROOT=$(aws apigateway get-resources --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Create resources
API=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $ROOT --path-part api --query 'id' --output text)
V1=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $API --path-part v1 --query 'id' --output text)
SERVICES=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $V1 --path-part services --query 'id' --output text)
IMAGE=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $SERVICES --path-part image --query 'id' --output text)
GENERATE=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $IMAGE --path-part generate --query 'id' --output text)

# Create POST method
LAMBDA_ARN=$(aws lambda get-function --function-name fulmine-sparks \
  --query 'Configuration.FunctionArn' --output text)

aws apigateway put-method \
  --rest-api-id $API_ID --resource-id $GENERATE \
  --http-method POST --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID --resource-id $GENERATE \
  --http-method POST --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations

# Grant permission
aws lambda add-permission \
  --function-name fulmine-sparks \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-2:*:${API_ID}/*/*"

# Deploy
aws apigateway create-deployment \
  --rest-api-id $API_ID --stage-name prod

# Get endpoint
API_ENDPOINT=$(aws apigateway get-stage \
  --rest-api-id $API_ID --stage-name prod \
  --query 'invokeUrl' --output text)

echo "API Endpoint: $API_ENDPOINT"
```

## Testing

### Test Generate Endpoint

```bash
curl -X POST ${API_ENDPOINT}/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset"}'
```

### Test with Python Client

```bash
python3 client.py generate "A beautiful sunset"
```

## What's New

### Rate Limiting Fix

**Before**: Rate limiting was stored in-memory and lost between Lambda invocations
**After**: Rate limiting is stored in DynamoDB and persists across invocations

```
Before (Broken):
  Invocation 1: count = 1 ✅
  Invocation 2: count = 1 (reset!) ❌
  Invocation 3: count = 1 (reset!) ❌

After (Fixed):
  Invocation 1: count = 1 ✅
  Invocation 2: count = 2 ✅
  Invocation 3: count = 3 ✅
```

### Image Persistence

Images are now stored in DynamoDB with:
- 24-hour TTL for automatic cleanup
- Fallback to in-memory cache for performance
- Persistent across Lambda invocations

### Rate Limiting Tiers

- **Default**: 10 requests/hour
- **Unpaid**: 3 requests/hour
- **Paid**: 100 requests/hour

## Monitoring

### View Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

### Check DynamoDB

```bash
# Images
aws dynamodb scan --table-name fulmine-sparks-images

# Rate limits
aws dynamodb scan --table-name fulmine-sparks-rate-limits
```

## Troubleshooting

### 404 on Status Endpoint

Check DynamoDB table exists:
```bash
aws dynamodb describe-table --table-name fulmine-sparks-images
```

### Rate Limit Errors

Check rate limits table:
```bash
aws dynamodb scan --table-name fulmine-sparks-rate-limits
```

### Lambda Errors

Check logs:
```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

## Next Steps

1. ✅ Deploy to AWS
2. ✅ Test the workflow
3. ✅ Monitor CloudWatch logs
4. ✅ Adjust rate limits as needed
5. ✅ Set up payment integration

## Documentation

- [README.md](README.md) - Full documentation
- [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md) - Detailed deployment guide
- [RATE_LIMITING_FIX.md](RATE_LIMITING_FIX.md) - Technical analysis of the fix

## Support

For issues, check:
1. CloudWatch logs
2. DynamoDB tables
3. Lambda function configuration
4. API Gateway setup

---

Made with ⚡ by Fulmine Labs
