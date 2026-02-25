# 🚀 Fulmine-Sparks Deployment Instructions

Complete step-by-step guide to deploy the Fulmine-Sparks API to AWS.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Python 3.9+
- Replicate API token (https://replicate.com/)
- Alby Hub NWC connection string (https://getalby.com/)

## Step 1: Create DynamoDB Tables

### 1.1 Create Images Table

```bash
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-2
```

### 1.2 Enable TTL on Images Table

```bash
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-images \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-2
```

### 1.3 Create Rate Limits Table

```bash
aws dynamodb create-table \
  --table-name fulmine-sparks-rate-limits \
  --attribute-definitions AttributeName=client_ip,AttributeType=S \
  --key-schema AttributeName=client_ip,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-2
```

### 1.4 Enable TTL on Rate Limits Table

```bash
aws dynamodb update-time-to-live \
  --table-name fulmine-sparks-rate-limits \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-2
```

## Step 2: Create IAM Role for Lambda

### 2.1 Create Trust Policy

Create a file `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 2.2 Create Role

```bash
aws iam create-role \
  --role-name fulmine-sparks-lambda-role \
  --assume-role-policy-document file://trust-policy.json
```

### 2.3 Create DynamoDB Policy

Create a file `dynamodb-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-images",
        "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-rate-limits"
      ]
    }
  ]
}
```

### 2.4 Attach Policy to Role

```bash
aws iam put-role-policy \
  --role-name fulmine-sparks-lambda-role \
  --policy-name fulmine-sparks-dynamodb-policy \
  --policy-document file://dynamodb-policy.json
```

### 2.5 Attach CloudWatch Logs Policy

```bash
aws iam attach-role-policy \
  --role-name fulmine-sparks-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## Step 3: Create Deployment Package

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

## Step 4: Create Lambda Function

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
  --memory-size 512 \
  --region us-east-2
```

## Step 5: Set Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables="{
    REPLICATE_API_TOKEN=your_replicate_token_here,
    ALBY_NWC_URL=nostr+walletconnect://your_nwc_url_here,
    IMAGES_TABLE=fulmine-sparks-images,
    RATE_LIMITS_TABLE=fulmine-sparks-rate-limits
  }" \
  --region us-east-2
```

## Step 6: Create API Gateway

### 6.1 Create REST API

```bash
API_ID=$(aws apigateway create-rest-api \
  --name fulmine-sparks-api \
  --description "Fulmine-Sparks Image Generation API" \
  --region us-east-2 \
  --query 'id' \
  --output text)

echo "API ID: $API_ID"
```

### 6.2 Get Root Resource

```bash
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region us-east-2 \
  --query 'items[0].id' \
  --output text)

echo "Root Resource ID: $ROOT_ID"
```

### 6.3 Create Resources

```bash
# Create /api resource
API_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part api \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1 resource
V1_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $API_RESOURCE \
  --path-part v1 \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services resource
SERVICES_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $V1_RESOURCE \
  --path-part services \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image resource
IMAGE_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $SERVICES_RESOURCE \
  --path-part image \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image/generate resource
GENERATE_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $IMAGE_RESOURCE \
  --path-part generate \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image/status resource
STATUS_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $IMAGE_RESOURCE \
  --path-part status \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image/status/{payment_hash} resource
STATUS_HASH_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $STATUS_RESOURCE \
  --path-part '{payment_hash}' \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image/retrieve resource
RETRIEVE_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $IMAGE_RESOURCE \
  --path-part retrieve \
  --region us-east-2 \
  --query 'id' \
  --output text)

# Create /api/v1/services/image/retrieve/{payment_hash} resource
RETRIEVE_HASH_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $RETRIEVE_RESOURCE \
  --path-part '{payment_hash}' \
  --region us-east-2 \
  --query 'id' \
  --output text)
```

### 6.4 Create Methods

```bash
# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name fulmine-sparks \
  --region us-east-2 \
  --query 'Configuration.FunctionArn' \
  --output text)

# POST /api/v1/services/image/generate
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $GENERATE_RESOURCE \
  --http-method POST \
  --authorization-type NONE \
  --region us-east-2

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $GENERATE_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations \
  --region us-east-2

# GET /api/v1/services/image/status/{payment_hash}
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $STATUS_HASH_RESOURCE \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters method.request.path.payment_hash=true \
  --region us-east-2

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $STATUS_HASH_RESOURCE \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations \
  --region us-east-2

# GET /api/v1/services/image/retrieve/{payment_hash}
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RETRIEVE_HASH_RESOURCE \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters method.request.path.payment_hash=true \
  --region us-east-2

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RETRIEVE_HASH_RESOURCE \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations \
  --region us-east-2
```

### 6.5 Grant API Gateway Permission to Invoke Lambda

```bash
aws lambda add-permission \
  --function-name fulmine-sparks \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-2:*:${API_ID}/*/*" \
  --region us-east-2
```

### 6.6 Deploy API

```bash
DEPLOYMENT_ID=$(aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region us-east-2 \
  --query 'id' \
  --output text)

echo "Deployment ID: $DEPLOYMENT_ID"

# Get API endpoint
API_ENDPOINT=$(aws apigateway get-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region us-east-2 \
  --query 'invokeUrl' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"
```

## Step 7: Test the API

### 7.1 Test Generate Endpoint

```bash
curl -X POST ${API_ENDPOINT}/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset over the ocean"}'
```

### 7.2 Test Status Endpoint

```bash
# Replace PAYMENT_HASH with the hash from the generate response
curl ${API_ENDPOINT}/api/v1/services/image/status/PAYMENT_HASH
```

### 7.3 Test with Python Client

```bash
python3 client.py generate "A beautiful sunset"
```

## Step 8: Monitor and Debug

### 8.1 View CloudWatch Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow --region us-east-2
```

### 8.2 Check DynamoDB Items

```bash
# Check images table
aws dynamodb scan --table-name fulmine-sparks-images --region us-east-2

# Check rate limits table
aws dynamodb scan --table-name fulmine-sparks-rate-limits --region us-east-2
```

### 8.3 Check Lambda Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=fulmine-sparks \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-2
```

## Troubleshooting

### Lambda Function Not Found

```bash
# List all Lambda functions
aws lambda list-functions --region us-east-2
```

### DynamoDB Table Not Found

```bash
# List all DynamoDB tables
aws dynamodb list-tables --region us-east-2
```

### API Gateway Not Working

```bash
# Check API Gateway status
aws apigateway get-rest-api --rest-api-id $API_ID --region us-east-2
```

### Permission Denied Errors

```bash
# Check Lambda execution role
aws iam get-role --role-name fulmine-sparks-lambda-role

# Check role policies
aws iam list-role-policies --role-name fulmine-sparks-lambda-role
```

## Cleanup

To remove all resources:

```bash
# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id $API_ID --region us-east-2

# Delete Lambda function
aws lambda delete-function --function-name fulmine-sparks --region us-east-2

# Delete IAM role
aws iam delete-role-policy --role-name fulmine-sparks-lambda-role --policy-name fulmine-sparks-dynamodb-policy
aws iam detach-role-policy --role-name fulmine-sparks-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name fulmine-sparks-lambda-role

# Delete DynamoDB tables
aws dynamodb delete-table --table-name fulmine-sparks-images --region us-east-2
aws dynamodb delete-table --table-name fulmine-sparks-rate-limits --region us-east-2
```

---

Made with ⚡ by Fulmine Labs
