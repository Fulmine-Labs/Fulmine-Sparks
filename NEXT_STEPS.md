# 📋 Next Steps - Deployment Checklist

## ✅ What's Been Done

- [x] **Identified the issue**: Rate limiting stored in-memory, lost between Lambda invocations
- [x] **Implemented the fix**: Moved rate limiting to DynamoDB for persistent tracking
- [x] **Updated Lambda handler**: `lambda_handler_simple.py` now uses DynamoDB for both images and rate limits
- [x] **Created documentation**: Comprehensive guides for deployment and troubleshooting
- [x] **Created test script**: `test_workflow.py` to validate the complete workflow

## 🚀 Deployment Steps (In Order)

### Phase 1: AWS Infrastructure Setup

#### Step 1.1: Create DynamoDB Tables
```bash
# Images table
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL on images table
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-images \
  --time-to-live-specification Enabled=true,AttributeName=ttl

# Rate limits table
aws dynamodb create-table \
  --table-name fulmine-sparks-rate-limits \
  --attribute-definitions AttributeName=client_ip,AttributeType=S \
  --key-schema AttributeName=client_ip,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL on rate limits table
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-rate-limits \
  --time-to-live-specification Enabled=true,AttributeName=ttl
```

**Verification**:
```bash
aws dynamodb list-tables
# Should show: fulmine-sparks-images, fulmine-sparks-rate-limits
```

#### Step 1.2: Create IAM Role
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

**Verification**:
```bash
aws iam get-role --role-name fulmine-sparks-lambda-role
aws iam list-role-policies --role-name fulmine-sparks-lambda-role
```

### Phase 2: Lambda Deployment

#### Step 2.1: Create Deployment Package
```bash
# Create package directory
mkdir -p lambda_package

# Install dependencies
pip install requests -t lambda_package -q

# Copy source files
cp lambda_handler_simple.py lambda_package/lambda_handler.py
cp billing.py lambda_package/
cp configure_alby.py lambda_package/

# Create zip file
cd lambda_package
zip -r ../fulmine-sparks.zip . -q
cd ..

# Verify zip contents
unzip -l fulmine-sparks.zip | head -20
```

**Verification**:
```bash
ls -lh fulmine-sparks.zip
# Should be ~50-100 KB
```

#### Step 2.2: Create Lambda Function
```bash
# Get your AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create function
aws lambda create-function \
  --function-name fulmine-sparks \
  --runtime python3.9 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/fulmine-sparks-lambda-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://fulmine-sparks.zip \
  --timeout 60 \
  --memory-size 512
```

**Verification**:
```bash
aws lambda get-function --function-name fulmine-sparks
# Should show function details
```

#### Step 2.3: Set Environment Variables
```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables="{
    REPLICATE_API_TOKEN=your_replicate_token_here,
    ALBY_NWC_URL=nostr+walletconnect://your_nwc_url_here,
    IMAGES_TABLE=fulmine-sparks-images,
    RATE_LIMITS_TABLE=fulmine-sparks-rate-limits
  }"
```

**Verification**:
```bash
aws lambda get-function-configuration --function-name fulmine-sparks | grep Environment
```

### Phase 3: API Gateway Setup

#### Step 3.1: Create REST API
```bash
API_ID=$(aws apigateway create-rest-api \
  --name fulmine-sparks-api \
  --description "Fulmine-Sparks Image Generation API" \
  --query 'id' --output text)

echo "API_ID=$API_ID" > api_config.sh
source api_config.sh
```

#### Step 3.2: Create Resources
```bash
# Get root resource
ROOT=$(aws apigateway get-resources --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Create resource hierarchy
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
STATUS=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $IMAGE --path-part status --query 'id' --output text)
STATUS_HASH=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $STATUS --path-part '{payment_hash}' --query 'id' --output text)
RETRIEVE=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $IMAGE --path-part retrieve --query 'id' --output text)
RETRIEVE_HASH=$(aws apigateway create-resource --rest-api-id $API_ID \
  --parent-id $RETRIEVE --path-part '{payment_hash}' --query 'id' --output text)
```

#### Step 3.3: Create Methods
```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name fulmine-sparks \
  --query 'Configuration.FunctionArn' --output text)

# POST /api/v1/services/image/generate
aws apigateway put-method \
  --rest-api-id $API_ID --resource-id $GENERATE \
  --http-method POST --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID --resource-id $GENERATE \
  --http-method POST --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations

# GET /api/v1/services/image/status/{payment_hash}
aws apigateway put-method \
  --rest-api-id $API_ID --resource-id $STATUS_HASH \
  --http-method GET --authorization-type NONE \
  --request-parameters method.request.path.payment_hash=true

aws apigateway put-integration \
  --rest-api-id $API_ID --resource-id $STATUS_HASH \
  --http-method GET --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations

# GET /api/v1/services/image/retrieve/{payment_hash}
aws apigateway put-method \
  --rest-api-id $API_ID --resource-id $RETRIEVE_HASH \
  --http-method GET --authorization-type NONE \
  --request-parameters method.request.path.payment_hash=true

aws apigateway put-integration \
  --rest-api-id $API_ID --resource-id $RETRIEVE_HASH \
  --http-method GET --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations
```

#### Step 3.4: Grant Lambda Permission
```bash
aws lambda add-permission \
  --function-name fulmine-sparks \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-2:*:${API_ID}/*/*"
```

#### Step 3.5: Deploy API
```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID --stage-name prod

# Get endpoint
API_ENDPOINT=$(aws apigateway get-stage \
  --rest-api-id $API_ID --stage-name prod \
  --query 'invokeUrl' --output text)

echo "API_ENDPOINT=$API_ENDPOINT" >> api_config.sh
echo "API Endpoint: $API_ENDPOINT"
```

### Phase 4: Testing

#### Step 4.1: Quick Test
```bash
# Test generate endpoint
curl -X POST ${API_ENDPOINT}/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset"}'

# Should return 200 with payment_hash and invoice
```

#### Step 4.2: Full Workflow Test
```bash
python3 test_workflow.py ${API_ENDPOINT}

# Should show all tests passing
```

#### Step 4.3: Check Logs
```bash
aws logs tail /aws/lambda/fulmine-sparks --follow

# Should show:
# ✅ Image stored in DynamoDB
# 📊 Image status from DynamoDB
# ✅ Image marked as available
```

#### Step 4.4: Verify DynamoDB
```bash
# Check images table
aws dynamodb scan --table-name fulmine-sparks-images

# Check rate limits table
aws dynamodb scan --table-name fulmine-sparks-rate-limits
```

## 📊 Verification Checklist

After deployment, verify:

- [ ] DynamoDB tables created and TTL enabled
- [ ] IAM role created with correct permissions
- [ ] Lambda function created and configured
- [ ] Environment variables set correctly
- [ ] API Gateway created with all resources
- [ ] Lambda has permission to be invoked by API Gateway
- [ ] API deployed to prod stage
- [ ] Health endpoint returns 200
- [ ] Generate endpoint returns 200 with payment_hash
- [ ] Status endpoint returns 200 or 404
- [ ] Retrieve endpoint returns 200, 402, or 404
- [ ] Rate limiting works (429 after limit)
- [ ] CloudWatch logs show no errors
- [ ] DynamoDB tables have items

## 🧪 Testing Commands

```bash
# Test health
curl ${API_ENDPOINT}/health

# Test generate
curl -X POST ${API_ENDPOINT}/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test"}'

# Test status (replace HASH with actual payment_hash)
curl ${API_ENDPOINT}/api/v1/services/image/status/HASH

# Test retrieve (replace HASH with actual payment_hash)
curl ${API_ENDPOINT}/api/v1/services/image/retrieve/HASH

# Run full workflow test
python3 test_workflow.py ${API_ENDPOINT}
```

## 🔍 Troubleshooting

### If tests fail:

1. **Check CloudWatch logs**:
   ```bash
   aws logs tail /aws/lambda/fulmine-sparks --follow
   ```

2. **Check DynamoDB tables**:
   ```bash
   aws dynamodb describe-table --table-name fulmine-sparks-images
   aws dynamodb describe-table --table-name fulmine-sparks-rate-limits
   ```

3. **Check Lambda configuration**:
   ```bash
   aws lambda get-function-configuration --function-name fulmine-sparks
   ```

4. **Check IAM permissions**:
   ```bash
   aws iam get-role-policy --role-name fulmine-sparks-lambda-role --policy-name dynamodb-policy
   ```

5. **Check API Gateway**:
   ```bash
   aws apigateway get-rest-api --rest-api-id $API_ID
   ```

## 📚 Documentation Reference

- **QUICKSTART.md** - 5-minute deployment guide
- **DEPLOYMENT_INSTRUCTIONS.md** - Detailed step-by-step guide
- **RATE_LIMITING_FIX.md** - Technical analysis of the fix
- **SOLUTION_SUMMARY.md** - Executive summary
- **README.md** - Complete project documentation

## 🎯 Success Criteria

✅ **Deployment is successful when**:
1. All DynamoDB tables created and TTL enabled
2. Lambda function deployed with correct environment variables
3. API Gateway deployed with all endpoints
4. Health endpoint returns 200
5. Generate endpoint returns 200 with payment_hash
6. Status endpoint works (returns 200 or 404)
7. Retrieve endpoint works (returns 200, 402, or 404)
8. Rate limiting works (returns 429 after limit)
9. CloudWatch logs show no errors
10. Full workflow test passes

## 🚀 Next Phase: Payment Integration

After deployment is verified:

1. **Integrate Alby Hub NWC** for actual Lightning payments
2. **Implement payment verification** in status endpoint
3. **Update rate limiting tiers** based on payment status
4. **Add payment webhook** for automatic status updates
5. **Monitor and optimize** based on usage patterns

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review CloudWatch logs
3. Verify all AWS resources are created
4. Check environment variables
5. Review RATE_LIMITING_FIX.md for technical details

---

**Status**: 🟢 Ready for Deployment

**Last Updated**: 2024
**Version**: 1.0.0

Made with ⚡ by Fulmine Labs
