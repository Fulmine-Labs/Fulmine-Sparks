# Fulmine-Sparks: Serverless AI Image Generation with Lightning Payments

**Status:** ✅ Production Ready
**Version:** 1.0.0 - Rate Limiting Implementation Complete
**Date:** February 28, 2026

## Quick Start

### For Users
Generate images by paying with Bitcoin Lightning:
```bash
python client.py
# Command: 7 (Generate Image)
# Enter prompt, get BOLT11 invoice, pay with Lightning wallet
```

### For Testing Rate Limiting
```bash
python client.py test-rate-manual
# Automated test: blocks at 3 unpaid invoices, unblocks after payment
```

## What This Is

Fulmine-Sparks is a serverless API that:
- ✅ Generates high-quality images using AI models (SeeDream 4.5)
- ✅ Requires Bitcoin Lightning Network payments
- ✅ Implements simple, fair rate limiting (blocks at 3 unpaid invoices)
- ✅ Uses AWS Lambda, DynamoDB, and Alby Wallet API
- ✅ Runs completely serverless with no infrastructure management

## Key Features

### Rate Limiting
- **Simple Rule:** Block users with 3+ unpaid invoices
- **Fair:** Paying customers have unlimited access
- **Transparent:** Users know exactly what's blocking them
- **Persistent:** Tracked in DynamoDB, survives Lambda restarts
- **Automatic Clearing:** Counter decrements when invoices are paid

### Payment System
- Bitcoin Lightning Network via Alby Wallet
- BOLT11 invoice generation per image request
- Automatic payment detection
- Immediate unblocking after payment

### Image Generation
- SeeDream 4.5 model for high-quality output
- Configurable prompts and parameters
- Base64 encoding for API response
- 2-minute cache for payment confirmation period

### Testing
- Automated rate limiting test
- Payment flow verification
- API compliance checker
- Bot simulator for load testing

## Architecture

```
Client (CLI)
    ↓
API Gateway
    ↓
Lambda Handler
├── Rate Limit Check (DynamoDB)
├── Invoice Generation
├── Image Generation (Replicate)
└── Payment Status Checking (Alby)
    ↓
DynamoDB
├── fulmine-sparks-rate-limits (IP tracking)
└── fulmine-sparks-images (cache)
    ↓
External APIs
├── Alby Wallet (Lightning payments)
└── Replicate (Image generation)
```

## Database Schema

### rate-limits Table
```json
{
  "client_ip": "203.0.113.42",
  "unpaid_invoices": 2,
  "ttl": 1708881234
}
```

### images Table
```json
{
  "payment_hash": "abc123def456...",
  "status": "pending|available|expired",
  "image_base64": "[large base64 string]",
  "created_at": 1708880034,
  "expires_at": 1708880154,
  "ttl": 1708880154
}
```

## Rate Limiting Flow

```
Generate Image Request
    ↓
Extract Client IP
    ↓
Query DynamoDB: unpaid_invoices count
    ↓
IF count >= 3:
    RETURN 429 error
    "You have 3 unpaid invoices. Please pay before requesting more images."
    ↓
ELSE:
    Generate invoice
    Increment counter: unpaid_invoices += 1
    RETURN BOLT11 payment request
    ↓
    [User pays via Alby]
    ↓
    Status check → Payment detected
    ↓
    Decrement counter: unpaid_invoices -= 1
    User unblocked
```

## API Endpoints

### `POST /api/v1/services/image/generate`
Generate an image (requires payment)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "seedream-4.5",
    "num_outputs": 1
  }' \
  https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/generate
```

**Response (Success):**
```json
{
  "status": "payment_required",
  "invoice": {
    "payment_hash": "...",
    "payment_request": "lnbc...",
    "amount_sats": 77,
    "price_usd": 0.05
  }
}
```

**Response (Rate Limited):**
```json
{
  "status": 429,
  "error": "Rate limited: You have 3 unpaid invoices. Please pay before requesting more images."
}
```

### `GET /api/v1/services/image/status/{payment_hash}`
Check image generation status
```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/abc123...
```

### `GET /api/v1/services/image/retrieve/{payment_hash}`
Retrieve generated image after payment

### `GET /health`
Health check endpoint

## Configuration

### Environment Variables (Lambda)
```bash
RATE_LIMITS_TABLE=fulmine-sparks-rate-limits
IMAGES_TABLE=fulmine-sparks-images
ALBY_NWC_URL=nwc://...
REPLICATE_API_TOKEN=...
```

### Environment Variables (Client)
```bash
ALBY_API_TOKEN=your_alby_token
```

## Bot Integration

### Simple Bot Example
```python
from fulmine_spark_client import FulmineSparkClient
from alby import Alby

# Initialize client
client = FulmineSparkClient()
alby = Alby(token=os.getenv("ALBY_API_TOKEN"))

# Generate image
result = client.generate_image(prompt="sunset over mountains")
invoice = result["invoice"]["payment_request"]
payment_hash = result["invoice"]["payment_hash"]

# Pay invoice
alby.pay_invoice(invoice)

# Poll for completion
status = client.poll_status(payment_hash, timeout=30)
if status["status"] == "available":
    image_base64 = client.retrieve_image(payment_hash)
    # Save or process image
```

### Rate Limit Handling
```python
# Generate image - might hit rate limit
try:
    result = client.generate_image(prompt="...")
except Exception as e:
    if "429" in str(e):
        print("Rate limited: You have 3 unpaid invoices")
        print("Pay one invoice to unblock")
    else:
        raise
```

### Full Workflow with Error Handling
```bash
# See client.py for complete production-ready implementation
python client.py              # Interactive menu
python client.py test-rate-manual  # Full workflow test
```

## Testing

### Automated Rate Limiting Test
```bash
python client.py test-rate-manual
```

**What it does:**
1. Generates 3 unpaid invoices (all succeed)
2. Blocks on 4th attempt (429 error)
3. Automatically pays one invoice
4. Generates 4th image (unblocked)

**Expected Duration:** ~30 seconds

### Manual Testing
```bash
# Test health
python client.py health

# Generate single image
python client.py
# Menu: 7 (generate-image)

# Interactive menu
python client.py
```

### Verify DynamoDB State
```bash
# Check rate limits
aws dynamodb scan --table-name fulmine-sparks-rate-limits --region us-east-2

# Check image cache
aws dynamodb scan --table-name fulmine-sparks-images --region us-east-2
```

## Deployment

### Prerequisite Setup
1. Create DynamoDB tables (see FINAL_WORKING_VERSION.md)
2. Set Lambda environment variables
3. Configure IAM role permissions
4. Deploy lambda_handler_simple.py to AWS Lambda

### Deploy Command
```bash
# Build deployment package
python3 -c "
import zipfile, os
with zipfile.ZipFile('fulmine-sparks.zip', 'w') as z:
    z.write('lambda_handler_simple.py')
    z.write('billing.py')
"

# Upload to Lambda
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip
```

### Post-Deploy Verification
```bash
# Health check
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health

# Rate limiting test
python client.py test-rate-manual
```

## Documentation

- **FINAL_WORKING_VERSION.md** - Complete working features and testing guide
- **FULMINE_SPARKS_ANALYSIS.md** - Architecture and design analysis
- **DEPLOYMENT_STEPS.md** - Detailed deployment instructions
- **QUICKSTART.md** - Getting started guide

## Troubleshooting

### "Rate limited: You have 3 unpaid invoices"
✅ This is working correctly! You've created 3 invoices without paying. Pay one to unblock.

### Status check returns "pending" instead of "available"
- Payment may not have settled yet (Lightning can take a few seconds)
- Check Alby wallet to confirm payment was received
- Try status check again after 5 seconds

### DynamoDB errors in CloudWatch
- Verify tables exist: `fulmine-sparks-rate-limits` and `fulmine-sparks-images`
- Check TTL is enabled on both tables
- Verify Lambda IAM role has GetItem/PutItem permissions

### Lambda logs show "BILLING_ENABLED=False"
- Set ALBY_NWC_URL environment variable
- Check that billing.py is deployed

## Features Implemented

✅ Simple rate limiting (block at 3 unpaid)
✅ DynamoDB-backed persistent tracking
✅ Payment detection via Alby
✅ Automatic counter decrement
✅ In-memory fallback
✅ Automated testing
✅ Comprehensive documentation
✅ CloudWatch logging
✅ TTL auto-cleanup

## Performance

| Metric | Value |
|--------|-------|
| Rate Limit Check | <5ms |
| Image Generation | 30-60 seconds |
| Payment Detection | <1 second |
| DynamoDB Operations | 1-2 per request |
| Monthly Cost | ~$0.25 (DynamoDB) |

## Known Limitations

- Rate limit threshold is fixed at 3 (can be adjusted in code)
- No per-user whitelist (all users equal)
- No analytics dashboard
- Payment confirmation is polling-based (not webhook)

## Future Enhancements

- [ ] Webhook-based payment confirmation
- [ ] Per-IP analytics dashboard
- [ ] Configurable rate limit tiers
- [ ] Email notifications
- [ ] Automatic retry with exponential backoff

## Support

For issues or questions:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/fulmine-sparks`
2. Review FINAL_WORKING_VERSION.md troubleshooting section
3. Run test: `python client.py test-rate-manual`
4. Check DynamoDB tables exist and are properly configured

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines including:
- How to report issues and security vulnerabilities
- Development setup and testing procedures
- Code standards and best practices
- How to submit pull requests

---

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** February 28, 2026
**Rate Limiting:** Simple, Fair, Effective ⚡
