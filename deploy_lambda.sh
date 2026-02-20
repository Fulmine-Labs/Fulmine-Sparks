#!/bin/bash
# Deploy Fulmine-Sparks to AWS Lambda

set -e

echo "============================================================"
echo "🚀 Deploying Fulmine-Sparks to AWS Lambda"
echo "============================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if we're authenticated
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Not authenticated with AWS"
    echo "Run: aws configure"
    exit 1
fi

# Configuration
FUNCTION_NAME="fulmine-sparks"
RUNTIME="python3.11"
HANDLER="lambda_handler.lambda_handler"
ROLE_NAME="fulmine-sparks-lambda-role"
TIMEOUT=300  # 5 minutes for image generation
MEMORY=512

echo ""
echo "📋 Configuration:"
echo "   Function Name: $FUNCTION_NAME"
echo "   Runtime: $RUNTIME"
echo "   Handler: $HANDLER"
echo "   Timeout: ${TIMEOUT}s"
echo "   Memory: ${MEMORY}MB"
echo ""

# Create IAM role if it doesn't exist
echo "🔐 Checking IAM role..."
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "Creating IAM role..."
    ROLE_ARN=$(aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document '{
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
        }' \
        --query 'Role.Arn' \
        --output text)
    
    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    echo "✅ Role created: $ROLE_ARN"
    
    # Wait for role to be available
    sleep 10
else
    echo "✅ Role exists: $ROLE_ARN"
fi

# Create deployment package
echo ""
echo "📦 Creating deployment package..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy handler
cp lambda_handler.py lambda_package/

# Copy project code
cp -r fulmine_spark lambda_package/

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt -t lambda_package/

# Create zip file
echo "Creating zip file..."
cd lambda_package
zip -r -q ../fulmine-sparks.zip .
cd ..

echo "✅ Deployment package created: fulmine-sparks.zip"

# Check if function exists
echo ""
echo "🔍 Checking if Lambda function exists..."
FUNCTION_EXISTS=$(aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null || echo "")

if [ -z "$FUNCTION_EXISTS" ]; then
    echo "Creating Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --zip-file fileb://fulmine-sparks.zip \
        --environment Variables="{REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN}" \
        --description "Fulmine-Sparks serverless image generation API"
    
    echo "✅ Lambda function created"
else
    echo "Updating Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://fulmine-sparks.zip
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --environment Variables="{REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN}"
    
    echo "✅ Lambda function updated"
fi

# Create API Gateway
echo ""
echo "🌐 Setting up API Gateway..."

# Get or create API
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='fulmine-sparks'].ApiId" --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
    echo "Creating API Gateway..."
    API_ID=$(aws apigatewayv2 create-api \
        --name fulmine-sparks \
        --protocol-type HTTP \
        --target arn:aws:lambda:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME \
        --query 'ApiId' \
        --output text)
    
    echo "✅ API Gateway created: $API_ID"
else
    echo "✅ API Gateway exists: $API_ID"
fi

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-apis --query "Items[?Name=='fulmine-sparks'].ApiEndpoint" --output text)

echo ""
echo "============================================================"
echo "✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "🔗 Your API URL:"
echo "   $API_ENDPOINT"
echo ""
echo "📱 Update Pythonista client (line 20):"
echo "   API_BASE_URL = \"$API_ENDPOINT\""
echo ""
echo "💡 Next steps:"
echo "   1. Copy the API URL above"
echo "   2. Update pythonista_client.py with the URL"
echo "   3. Run the app on your iPhone"
echo "   4. Test image generation!"
echo ""
echo "📊 Monitor your function:"
echo "   aws lambda get-function --function-name $FUNCTION_NAME"
echo ""
echo "📋 View logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "💰 Costs:"
echo "   - Free tier: 1M requests/month"
echo "   - After: \$0.20 per 1M requests"
echo "   - Plus Replicate API costs"
echo ""
