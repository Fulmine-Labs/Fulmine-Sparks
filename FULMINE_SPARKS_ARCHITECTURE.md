# Fulmine-Sparks: Architecture & Deployment Guide

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATIONS                             │
│  (Discord Bot, Web App, Mobile App, CLI Client)                             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   API Gateway (HTTP)    │
                    │  (Route 53 DNS)         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  AWS Lambda Function    │
                    │  (lambda_handler)       │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   ┌────▼─────┐          ┌──────▼──────┐         ┌───────▼────┐
   │ Replicate │          │ Alby Hub    │         │ DynamoDB   │
   │ API       │          │ (Lightning) │         │ (Cache)    │
   │ (Image    │          │ (Payments)  │         │            │
   │ Gen)      │          │             │         │            │
   └───────────┘          └─────────────┘         └────────────┘
```

### Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STEP 1: GENERATE IMAGE                              │
└─────────────────────────────────────────────────────────────────────────────┘

Client                          Lambda                      External Services
  │                               │                              │
  ├─ POST /api/v1/services/image/generate ──────────────────────>│
  │  {prompt: "..."}              │                              │
  │                               │                              │
  │                               ├─ Check rate limit ──────────>│ DynamoDB
  │                               │                              │
  │                               ├─ Call Replicate API ────────>│ Replicate
  │                               │  (poll for 10 min)           │
  │                               │                              │
  │                               ├─ Create Lightning invoice ──>│ Alby Hub
  │                               │                              │
  │                               ├─ Store image in cache ──────>│ DynamoDB
  │                               │                              │
  │<─ 200 OK (invoice only) ──────┤                              │
  │  {payment_hash, invoice}      │                              │
  │                               │                              │

┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 2: USER PAYS INVOICE (EXTERNAL)                     │
└─────────────────────────────────────────────────────────────────────────────┘

User                          Lightning Network
  │                                │
  ├─ Scan QR code ────────────────>│
  │                                │
  ├─ Pay invoice ─────────────────>│
  │  (1-5 seconds)                 │
  │                                │

┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 3: POLL FOR PAYMENT STATUS                          │
└─────────────────────────────────────────────────────────────────────────────┘

Client                          Lambda                      External Services
  │                               │                              │
  ├─ GET /api/v1/services/image/status/{payment_hash} ────────>│
  │                               │                              │
  │                               ├─ Check Alby for payment ───>│ Alby Hub
  │                               │                              │
  │                               ├─ Update cache status ──────>│ DynamoDB
  │                               │  (pending → available)       │
  │                               │                              │
  │<─ 200 OK (status: available) ──┤                              │
  │                               │                              │
  │ (repeat every 1 second until payment confirmed)              │

┌─────────────────────────────────────────────────────────────────────────────┐
│                      STEP 4: RETRIEVE IMAGE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Client                          Lambda                      External Services
  │                               │                              │
  ├─ GET /api/v1/services/image/retrieve/{payment_hash} ──────>│
  │                               │                              │
  │                               ├─ Get image from cache ──────>│ DynamoDB
  │                               │                              │
  │                               ├─ Delete from cache ────────>│ DynamoDB
  │                               │                              │
  │<─ 200 OK (base64 image) ──────┤                              │
  │  {image_base64: "..."}        │                              │
  │                               │                              │
```

---

## 📊 Data Flow & Storage

### Image Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE LIFECYCLE (15 seconds)                 │
└─────────────────────────────────────────────────────────────────┘

Time    Memory Cache          DynamoDB              Status
────────────────────────────────────────────────────────────────
0s      ✅ Created            ✅ Created            pending
        (fast access)         (persistent)

5s      ✅ Available          ✅ Available          available
        (payment confirmed)   (payment confirmed)   (after payment)

10s     ✅ Available          ✅ Available          available
        (ready to retrieve)   (ready to retrieve)

15s     ❌ Expired            ❌ Expired            expired
        (auto-deleted)        (TTL triggered)       (auto-deleted)
```

### Cache Strategy

```
┌──────────────────────────────────────────────────────────────────┐
│                    DUAL-LAYER CACHE STRATEGY                     │
└──────────────────────────────────────────────────────────────────┘

Layer 1: Memory Cache (IMAGE_CACHE dict)
├─ Speed: <1ms
├─ Capacity: Limited by Lambda memory (512MB)
├─ Persistence: Lost between invocations
├─ Use Case: Fast access within same invocation
└─ Fallback: Check DynamoDB if not found

Layer 2: DynamoDB (fulmine-sparks-images table)
├─ Speed: 10-50ms
├─ Capacity: Unlimited (on-demand billing)
├─ Persistence: Survives Lambda invocations
├─ Use Case: Persistent storage across invocations
└─ TTL: Automatic cleanup after 15 seconds
```

### Rate Limiting State

```
┌──────────────────────────────────────────────────────────────────┐
│                  RATE LIMITING STATE TRACKING                    │
└──────────────────────────────────────────────────────────────────┘

IP Address Tracking (IP_TRACKING dict)
├─ requests: [timestamp, timestamp, ...]  (last 60 seconds)
├─ unpaid_invoices: 3                      (count)
└─ blocked_until: 1708617600               (unix timestamp)

Rate Limit Tiers
├─ 0 unpaid invoices    → 3 requests/min   (normal)
├─ 1 unpaid invoice     → 2 requests/min   (warning)
├─ 2-3 unpaid invoices  → 1 request/min    (caution)
├─ 4-5 unpaid invoices  → 0.5 req/min      (restricted)
├─ 6-10 unpaid invoices → 0.2 req/min      (heavily restricted)
└─ 11+ unpaid invoices  → 0 requests/min   (blocked)
```

---

## 🚀 Deployment Architecture

### AWS Resources Required

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS RESOURCE DIAGRAM                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Route 53 (DNS)                                                  │
│ └─ fulmine-sparks.example.com → API Gateway                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│ API Gateway (HTTP API)                                        │
│ ├─ POST /api/v1/services/image/generate                      │
│ ├─ GET /api/v1/services/image/status/{payment_hash}          │
│ ├─ GET /api/v1/services/image/retrieve/{payment_hash}        │
│ ├─ GET /api/v1/services/image/models                         │
│ └─ GET /api/v1/workflow                                      │
└─────────────────────────────▬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│ Lambda Function (lambda_handler_simple.py)                    │
│ ├─ Memory: 512 MB                                             │
│ ├─ Timeout: 15 minutes                                        │
│ ├─ Runtime: Python 3.9+                                       │
│ └─ Layers: None required                                      │
└─────────────────────────────┬─────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│ DynamoDB       │  │ CloudWatch      │  │ IAM Role        │
│ (Cache)        │  │ (Logs)          │  │ (Permissions)   │
│                │  │                 │  │                 │
│ Table:         │  │ Log Group:      │  │ Permissions:    │
│ fulmine-sparks-│  │ /aws/lambda/    │  │ - DynamoDB      │
│ images         │  │ fulmine-sparks  │  │ - CloudWatch    │
│                │  │                 │  │ - Logs          │
│ TTL: 15s       │  │ Retention: 7d   │  │                 │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

### Deployment Options

#### Option 1: AWS Console (Manual)

```
1. Create DynamoDB Table
   ├─ Table Name: fulmine-sparks-images
   ├─ Primary Key: payment_hash (String)
   ├─ TTL Attribute: ttl
   └─ Billing: On-demand

2. Create Lambda Function
   ├─ Runtime: Python 3.9
   ├─ Memory: 512 MB
   ├─ Timeout: 900 seconds (15 min)
   └─ Handler: lambda_handler.lambda_handler

3. Upload Code
   ├─ Upload fulmine-sparks.zip
   └─ Set environment variables

4. Create API Gateway
   ├─ Type: HTTP API
   ├─ Integration: Lambda proxy
   └─ CORS: Enabled

5. Set IAM Permissions
   └─ Attach DynamoDB policy to Lambda role
```

#### Option 2: CloudFormation (IaC)

```yaml
# cloudformation-simple.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Fulmine-Sparks Serverless API'

Resources:
  # DynamoDB Table
  ImagesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: fulmine-sparks-images
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: payment_hash
          AttributeType: S
      KeySchema:
        - AttributeName: payment_hash
          KeyType: HASH
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true

  # Lambda Execution Role
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:PutItem
                  - dynamodb:UpdateItem
                  - dynamodb:DeleteItem
                Resource: !GetAtt ImagesTable.Arn

  # Lambda Function
  FulmineSparksFunctionRole:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: fulmine-sparks
      Runtime: python3.9
      Handler: lambda_handler.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: 900
      MemorySize: 512
      Code:
        S3Bucket: !Ref CodeBucket
        S3Key: fulmine-sparks.zip
      Environment:
        Variables:
          REPLICATE_API_TOKEN: !Ref ReplicateApiToken
          ALBY_NWC_URL: !Ref AlbyNwcUrl
          ALBY_API_TOKEN: !Ref AlbyApiToken
          IMAGES_TABLE: !Ref ImagesTable

  # API Gateway
  FulmineSparkApi:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: fulmine-sparks-api
      ProtocolType: HTTP
      CorsConfiguration:
        AllowOrigins:
          - '*'
        AllowMethods:
          - GET
          - POST
        AllowHeaders:
          - '*'

  # API Integration
  ApiIntegration:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref FulmineSparkApi
      IntegrationType: AWS_PROXY
      IntegrationUri: !Sub
        - arn:aws:apigatewayv2:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaArn}/invocations
        - LambdaArn: !GetAtt FulmineSparksFunctionRole.Arn

  # API Routes
  ApiRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref FulmineSparkApi
      RouteKey: '$default'
      Target: !Sub integrations/${ApiIntegration}

  # API Stage
  ApiStage:
    Type: AWS::ApiGatewayV2::Stage
    Properties:
      ApiId: !Ref FulmineSparkApi
      StageName: prod
      AutoDeploy: true

Parameters:
  ReplicateApiToken:
    Type: String
    NoEcho: true
    Description: Replicate API token
  
  AlbyNwcUrl:
    Type: String
    NoEcho: true
    Description: Alby Hub NWC connection string
  
  AlbyApiToken:
    Type: String
    NoEcho: true
    Description: Alby API token

Outputs:
  ApiEndpoint:
    Value: !Sub 'https://${FulmineSparkApi}.execute-api.${AWS::Region}.amazonaws.com/prod'
    Description: API Gateway endpoint
```

#### Option 3: Bash Script (Semi-automated)

```bash
#!/bin/bash
# deploy_lambda.sh

set -e

# Configuration
FUNCTION_NAME="fulmine-sparks"
REGION="us-east-2"
ROLE_NAME="fulmine-sparks-lambda-role"
TABLE_NAME="fulmine-sparks-images"

# Create DynamoDB table if it doesn't exist
echo "Creating DynamoDB table..."
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION \
  2>/dev/null || echo "Table already exists"

# Enable TTL
echo "Enabling TTL on DynamoDB table..."
aws dynamodb update-time-to-live \
  --table-name $TABLE_NAME \
  --time-to-live-specification AttributeName=ttl,Enabled=true \
  --region $REGION \
  2>/dev/null || echo "TTL already enabled"

# Create IAM role if it doesn't exist
echo "Creating IAM role..."
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  2>/dev/null || echo "Role already exists"

# Attach policies
echo "Attaching policies..."
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

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
      "Resource": "arn:aws:dynamodb:*:*:table/'$TABLE_NAME'"
    }]
  }'

# Create deployment package
echo "Creating deployment package..."
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
print("✅ Deployment package created")
EOF

# Update Lambda function
echo "Updating Lambda function..."
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://fulmine-sparks.zip \
  --region $REGION

# Set environment variables
echo "Setting environment variables..."
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --environment Variables="{
    REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN,
    ALBY_NWC_URL=$ALBY_NWC_URL,
    ALBY_API_TOKEN=$ALBY_API_TOKEN,
    IMAGES_TABLE=$TABLE_NAME
  }" \
  --region $REGION

echo "✅ Deployment complete!"
```

---

## 🔧 Configuration & Environment Variables

### Required Environment Variables

```bash
# Replicate API (for image generation)
REPLICATE_API_TOKEN=<your-replicate-api-token>

# Alby Hub (for Lightning payments)
ALBY_NWC_URL=nostr+walletconnect://pubkey?relay=wss://relay.getalby.com/v1&secret=...
ALBY_API_TOKEN=<your-alby-api-token>

# DynamoDB (optional, defaults to fulmine-sparks-images)
IMAGES_TABLE=fulmine-sparks-images
```

### Optional Environment Variables

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Rate Limiting
RATE_LIMIT_WINDOW=60  # seconds
CACHE_DURATION=15     # seconds
POLLING_DURATION=5    # seconds

# API Security
API_SECRET_KEY=<your-secret-key>  # For request signing
```

---

## 📈 Scaling & Performance

### Lambda Configuration

| Setting | Recommended | Notes |
|---------|-------------|-------|
| Memory | 512 MB | Sufficient for image processing |
| Timeout | 900 seconds (15 min) | For Replicate polling |
| Ephemeral Storage | 512 MB | Default, sufficient |
| Concurrency | Unlimited | Auto-scales |

### DynamoDB Configuration

| Setting | Recommended | Notes |
|---------|-------------|-------|
| Billing Mode | On-demand | Pay per request |
| Read Capacity | Auto | Scales automatically |
| Write Capacity | Auto | Scales automatically |
| TTL | Enabled | Auto-cleanup after 15s |

### Cost Estimation

**Per Image Generation:**
- Lambda: $0.0001 (512MB, 15s)
- Replicate: $0.04
- DynamoDB: $0.0001 (1 write, 1 read)
- **Total: ~$0.04**

**Monthly (1000 images):**
- Lambda: $0.10
- Replicate: $40.00
- DynamoDB: $0.10
- **Total: ~$40.20**

---

## 🔐 Security Best Practices

### 1. Secrets Management

```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret \
  --name fulmine-sparks/replicate-token \
  --secret-string $REPLICATE_API_TOKEN

# Reference in Lambda
import boto3
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='fulmine-sparks/replicate-token')
api_token = secret['SecretString']
```

### 2. VPC Configuration (Optional)

```yaml
# For additional security, run Lambda in VPC
VpcConfig:
  SecurityGroupIds:
    - sg-xxxxxxxx
  SubnetIds:
    - subnet-xxxxxxxx
    - subnet-xxxxxxxx
```

### 3. API Gateway Authentication

```yaml
# Add API key requirement
ApiKey:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Enabled: true
    StageKeys:
      - RestApiId: !Ref FulmineSparkApi
        StageName: prod

UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    ApiStages:
      - ApiId: !Ref FulmineSparkApi
        Stage: prod
    ApiKeyIds:
      - !Ref ApiKey
    Quota:
      Limit: 10000
      Period: DAY
    Throttle:
      BurstLimit: 100
      RateLimit: 50
```

### 4. CloudWatch Alarms

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Alarm for high error rate
cloudwatch.put_metric_alarm(
    AlarmName='fulmine-sparks-high-error-rate',
    MetricName='Errors',
    Namespace='AWS/Lambda',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-2:123456789:alerts']
)

# Alarm for high latency
cloudwatch.put_metric_alarm(
    AlarmName='fulmine-sparks-high-latency',
    MetricName='Duration',
    Namespace='AWS/Lambda',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=5000,  # 5 seconds
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-2:123456789:alerts']
)
```

---

## 🧪 Testing & Validation

### Health Check

```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health
```

### Generate Image

```bash
curl -X POST https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset", "model": "seedream-4.5", "num_outputs": 1}'
```

### Check Status

```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/{payment_hash}
```

### Retrieve Image

```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/retrieve/{payment_hash}
```

---

## 📊 Monitoring & Observability

### CloudWatch Metrics

```python
# Key metrics to monitor
metrics = {
    'ImageGenerationDuration': 'Average time to generate image',
    'PaymentConfirmationTime': 'Time from invoice to payment',
    'CacheHitRate': 'Percentage of cache hits',
    'ErrorRate': 'Percentage of failed requests',
    'RateLimitViolations': 'Number of rate limit violations',
    'DynamoDBLatency': 'DynamoDB read/write latency'
}
```

### CloudWatch Logs

```bash
# View logs
aws logs tail /aws/lambda/fulmine-sparks --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/fulmine-sparks \
  --filter-pattern "ERROR"

# Get metrics
aws logs get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time 2025-02-23T00:00:00Z \
  --end-time 2025-02-24T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

---

## 🚨 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Path extraction issue | Check API Gateway configuration |
| 429 Rate Limited | Too many requests | Wait or pay invoices |
| 402 Payment Required | Image not available | Wait for payment confirmation |
| 500 Server Error | Lambda error | Check CloudWatch logs |
| DynamoDB timeout | Table not accessible | Check IAM permissions |

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check Lambda environment
import os
print(f"REPLICATE_API_TOKEN: {os.getenv('REPLICATE_API_TOKEN', 'NOT SET')}")
print(f"ALBY_NWC_URL: {os.getenv('ALBY_NWC_URL', 'NOT SET')}")
print(f"IMAGES_TABLE: {os.getenv('IMAGES_TABLE', 'NOT SET')}")
```

---

## 📚 Additional Resources

- **AWS Lambda Documentation:** https://docs.aws.amazon.com/lambda/
- **API Gateway Documentation:** https://docs.aws.amazon.com/apigateway/
- **DynamoDB Documentation:** https://docs.aws.amazon.com/dynamodb/
- **Replicate API:** https://replicate.com/docs
- **Alby Hub:** https://getalby.com/docs
- **Lightning Network:** https://lightning.network/

---

*Architecture & Deployment Guide compiled: 2025-02-23*
