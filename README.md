# ⚡ Fulmine-Sparks - Serverless AI Image Generation with Lightning Payments

A serverless API for generating AI images and accepting Lightning Network payments, built on AWS Lambda and Alby Hub NWC.

## 🎯 Features

- **AI Image Generation**: Generate images using Replicate API (SeeDream 4.5 model)
- **Lightning Payments**: Accept payments via Alby Hub NWC (Nostr Wallet Connect)
- **Serverless Architecture**: Runs on AWS Lambda with API Gateway
- **Persistent Storage**: Uses DynamoDB for image metadata and status tracking
- **Rate Limiting**: Progressive IP-based rate limiting to prevent abuse
- **Status Polling**: Real-time image generation status updates

## 🏗️ Architecture

```
Client
  ↓
API Gateway
  ↓
Lambda Handler
  ├→ Replicate API (image generation)
  ├→ Alby Hub NWC (Lightning payments)
  └→ DynamoDB (persistent storage)
```

## 📋 Prerequisites

- AWS Account with Lambda, API Gateway, and DynamoDB access
- Replicate API token (https://replicate.com/)
- Alby Hub NWC connection string (https://getalby.com/)
- Python 3.9+

## 🚀 Deployment

### 1. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name fulmine-sparks-images \
  --attribute-definitions AttributeName=payment_hash,AttributeType=S \
  --key-schema AttributeName=payment_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --ttl-specification Enabled=true,AttributeName=ttl
```

### 2. Create Lambda Function

```bash
# Create deployment package
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
print("✅ Zip created!")
EOF

# Upload to Lambda
aws lambda create-function \
  --function-name fulmine-sparks \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://fulmine-sparks.zip \
  --timeout 60 \
  --memory-size 512
```

### 3. Set Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables="{
    REPLICATE_API_TOKEN=your_token_here,
    ALBY_NWC_URL=nostr+walletconnect://...,
    IMAGES_TABLE=fulmine-sparks-images
  }"
```

### 4. Set IAM Permissions

Add this policy to your Lambda execution role:

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
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-images"
    }
  ]
}
```

### 5. Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name fulmine-sparks-api \
  --description "Fulmine-Sparks Image Generation API"

# Create resources and methods
# (See DEPLOYMENT_INSTRUCTIONS.md for detailed steps)
```

## 📡 API Endpoints

### Generate Image

```bash
POST /api/v1/services/image/generate
Content-Type: application/json

{
  "prompt": "A beautiful sunset over the ocean"
}
```

**Response:**
```json
{
  "payment_hash": "abc123...",
  "invoice": "lnbc1000n1p...",
  "amount_msats": 1000,
  "prediction_id": "pred_123..."
}
```

### Check Status

```bash
GET /api/v1/services/image/status/{payment_hash}
```

**Response:**
```json
{
  "payment_hash": "abc123...",
  "status": "pending|available|expired"
}
```

### Retrieve Image

```bash
GET /api/v1/services/image/retrieve/{payment_hash}
```

**Response:**
```json
{
  "payment_hash": "abc123...",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "status": "available"
}
```

## 🧪 Testing

### Using the Python Client

```bash
# Generate image
python3 client.py generate "A beautiful sunset"

# Check status
python3 client.py status abc123...

# Retrieve image
python3 client.py retrieve abc123...
```

### Using curl

```bash
# Generate image
curl -X POST http://localhost:3000/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset"}'

# Check status
curl http://localhost:3000/api/v1/services/image/status/abc123...

# Retrieve image
curl http://localhost:3000/api/v1/services/image/retrieve/abc123...
```

## 🔧 Rate Limiting

The API implements progressive rate limiting:

- **Default tier**: 10 requests/hour
- **Unpaid invoices**: 3 requests/hour (stricter)
- **Paid invoices**: 100 requests/hour (generous)

Rate limit headers are included in responses:
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## 📊 Monitoring

### CloudWatch Logs

```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

### DynamoDB Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=fulmine-sparks-images \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 🐛 Troubleshooting

### 404 on Status Endpoint

**Problem**: Status endpoint returns 404 when polling for payment confirmation.

**Solution**: Ensure DynamoDB table exists and Lambda has proper IAM permissions.

```bash
# Check table exists
aws dynamodb describe-table --table-name fulmine-sparks-images

# Check Lambda permissions
aws iam get-role-policy --role-name lambda-role --policy-name dynamodb-policy
```

### Images Not Persisting

**Problem**: Images disappear between Lambda invocations.

**Solution**: Verify DynamoDB put_item is succeeding and TTL is configured.

```bash
# Check DynamoDB items
aws dynamodb scan --table-name fulmine-sparks-images

# Verify TTL
aws dynamodb describe-time-to-live --table-name fulmine-sparks-images
```

### Rate Limit Errors

**Problem**: Getting 429 Too Many Requests.

**Solution**: Wait for the reset time or use a different IP address.

```bash
# Check rate limit headers
curl -v http://localhost:3000/api/v1/services/image/generate
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `REPLICATE_API_TOKEN` | Replicate API token | Yes |
| `ALBY_NWC_URL` | Alby Hub NWC connection string | Yes |
| `IMAGES_TABLE` | DynamoDB table name | No (default: fulmine-sparks-images) |

## 🔐 Security

- All API calls use HTTPS
- Sensitive data (tokens, keys) stored in AWS Secrets Manager
- DynamoDB items encrypted at rest
- Rate limiting prevents abuse
- Input validation on all endpoints

## 📚 Resources

- [Replicate API Documentation](https://replicate.com/docs)
- [Alby Hub Documentation](https://getalby.com/docs)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)

## 📄 License

MIT License - See LICENSE file for details

## 👥 Support

For issues and questions, please open an issue on GitHub.

---

Made with ⚡ by Fulmine Labs
