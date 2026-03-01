# Fulmine-Sparks: Serverless AI Image Generation with Lightning Payments

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Date:** February 28, 2026

## Quick Start

### Generate an Image in 3 Steps
```bash
python client.py
# 1. Enter your image prompt
# 2. Scan the Lightning invoice with your wallet to pay
# 3. Get your generated image
```

### Automated Workflow Test
Watch the full workflow: generate image → pay → retrieve result:
```bash
python client.py
# Menu: 7 (Bot Simulator)
#   - Option 2 (Payment Bot): Auto-generates image, pays invoice, retrieves result
#   - Expected duration: ~30 seconds
```

## How It Works: The Main Workflow

```
┌─────────────────────────────────────────┐
│ 1. Request Image Generation             │
│    POST /api/v1/services/image/generate │
│    payload: { "prompt": "..." }         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. Receive Lightning Invoice             │
│    BOLT11: lnbc77...                    │
│    Amount: 77 sats (~$0.05)             │
│    payment_hash: abc123...              │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. Pay with Lightning Wallet             │
│    Scan QR code with Alby or other      │
│    (instant payment - less than 1 sec)  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Poll for Image Status                │
│    GET /api/v1/services/image/status/.. │
│    Returns: "pending" or "available"    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. Retrieve Generated Image              │
│    GET /api/v1/services/image/retrieve/.│
│    Returns: base64-encoded image        │
└─────────────────────────────────────────┘
```

## What This Is

Fulmine-Sparks is a serverless image generation API that combines AI with cryptocurrency payments:
- ✅ **Generates high-quality images** using AI models (SeeDream 4.5)
- ✅ **Pays with Bitcoin Lightning** - instant, low-fee payments
- ✅ **Runs completely serverless** - AWS Lambda + DynamoDB, no servers to manage
- ✅ **Fair rate limiting** - honest users have unlimited access

## Key Features

### Image Generation
- **SeeDream 4.5** model for high-quality, stunning images
- **Custom prompts** - describe what you want to see
- **Quick generation** - 30-60 seconds per image
- **Cached results** - 2-minute window for payment confirmation

### Payments with Lightning
- **Bitcoin Lightning Network** - instant, low-fee payments via Alby Wallet
- **BOLT11 invoices** - industry-standard format, QR code ready
- **Micro-payments** - typical image costs only ~$0.05 (77 sats)
- **Automatic detection** - payment confirmed in <1 second

### Rate Limiting (Fair Use)
- **Simple rule:** Users with 3+ unpaid invoices are temporarily blocked
- **Paying customers:** Have unlimited access
- **Transparent:** Always know your status
- **Auto-clearing:** Counter resets when you pay


## Using the API

### Step 1: Request Image Generation
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

**Success Response:**
```json
{
  "status": "payment_required",
  "invoice": {
    "payment_hash": "abc123def456",
    "payment_request": "lnbc77...",
    "amount_sats": 77,
    "price_usd": 0.05
  }
}
```

Save the `payment_hash` - you'll need it later.

### Step 2: Pay the Invoice
Scan the QR code from `payment_request` (BOLT11 format) with your Lightning wallet:
- **Alby Wallet** (recommended): https://getalby.com
- **Wallet of Satoshi**: Mobile app
- Any Lightning-compatible wallet

Payment is instant and non-reversible.

### Step 3: Check Image Status
Poll the status endpoint after paying:
```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/abc123def456
```

**Response When Ready:**
```json
{
  "status": "available",
  "created_at": 1708880034,
  "expires_at": 1708880154
}
```

### Step 4: Retrieve Your Image
```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/retrieve/abc123def456
```

**Response:**
```json
{
  "status": "available",
  "image_base64": "[large base64 encoded image]"
}
```

### Other Endpoints

**Health Check:**
```bash
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health
```

**Rate Limit Hit?**
```json
{
  "status": 429,
  "error": "Rate limited: You have 3 unpaid invoices. Please pay before requesting more images."
}
```
If you see this, pay one of your outstanding invoices to unblock.

## Setup & Configuration

### Quick Setup Checklist
- [ ] Create DynamoDB tables (`fulmine-sparks-rate-limits`, `fulmine-sparks-images`)
- [ ] Enable TTL on both tables
- [ ] Deploy `lambda_handler_simple.py` to AWS Lambda
- [ ] Set Lambda environment variables (see below)
- [ ] Test with `python client.py health`

### Lambda Environment Variables
```bash
RATE_LIMITS_TABLE=fulmine-sparks-rate-limits
IMAGES_TABLE=fulmine-sparks-images
ALBY_NWC_URL=nwc://...              # Lightning Network Connect URL
REPLICATE_API_TOKEN=...              # Image generation API key
```

### Client Environment Variables
```bash
ALBY_API_TOKEN=your_alby_token       # For automatic payment in tests
```

### IAM Role Permissions
Your Lambda execution role needs:
```json
{
  "Effect": "Allow",
  "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
  "Resource": [
    "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-rate-limits",
    "arn:aws:dynamodb:us-east-2:*:table/fulmine-sparks-images"
  ]
}
```

## Programmatic Usage

### Python Example: Full Workflow
```python
import requests
import time
import json

# Step 1: Request image
response = requests.post(
    'https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/generate',
    json={'prompt': 'sunset over mountains', 'model': 'seedream-4.5'}
)
invoice_data = response.json()['invoice']
payment_hash = invoice_data['payment_hash']
invoice_bolt11 = invoice_data['payment_request']

print(f"Pay this invoice: {invoice_bolt11}")
# User scans QR and pays...

# Step 2: Wait for payment + image
time.sleep(5)  # Give payment/generation time
while True:
    status = requests.get(
        f'https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/status/{payment_hash}'
    ).json()

    if status['status'] == 'available':
        break
    time.sleep(2)

# Step 3: Retrieve image
image_response = requests.get(
    f'https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/api/v1/services/image/retrieve/{payment_hash}'
)
image_base64 = image_response.json()['image_base64']

# Save to file
import base64
with open('generated_image.png', 'wb') as f:
    f.write(base64.b64decode(image_base64))
```

### Handling Rate Limits
```python
try:
    response = requests.post(endpoint, json=payload)
    if response.status_code == 429:
        error = response.json()
        print(f"Blocked: {error['error']}")
        print("Pay one of your outstanding invoices to unblock")
except Exception as e:
    print(f"Error: {e}")
```

## Testing & Examples

### Watch the Full Workflow (Recommended)
```bash
python client.py
# Menu: 7 (Bot Simulator)
#   - Option 2 (Payment Bot): Generates image → pays → retrieves result
#   - Expected duration: ~30 seconds
#   - Watch the console to see each step in action
```

### Manual Workflow Test
```bash
python client.py
# Menu: 7 (Generate Image or Bot Simulator)
# Follow the prompts to:
# 1. Enter your prompt
# 2. Get invoice (scan with Lightning wallet)
# 3. Pay with Alby or other wallet
# 4. Poll status until image is ready
# 5. Retrieve your image
```

### Test Rate Limiting
```bash
python client.py test-rate-manual
```
This generates 3 invoices, gets blocked on the 4th, pays one, then generates again successfully.

### Health Check
```bash
python client.py health
```

### Advanced: Check Database State
```bash
# View all rate limit entries
aws dynamodb scan --table-name fulmine-sparks-rate-limits --region us-east-2

# View all cached images
aws dynamodb scan --table-name fulmine-sparks-images --region us-east-2
```

## Technical Details

### Architecture Overview
```
Client/Bot (HTTP)
        ↓
API Gateway (route /api/v1/services/image/*)
        ↓
Lambda Handler (rate limit check → invoice gen → image gen → payment check)
        ↓
       ┌─────────────┬──────────────────┬──────────────┐
       ↓             ↓                  ↓              ↓
   DynamoDB      Replicate API      Alby Wallet    Alby NWC
(rate limits,   (image gen)      (payment check)  (payment detection)
  image cache)
```

### Database Schema

**fulmine-sparks-rate-limits table:**
```json
{
  "client_ip": "203.0.113.42",
  "unpaid_invoices": 2,
  "ttl": 1708881234
}
```

**fulmine-sparks-images table:**
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

### Rate Limiting Logic
The system enforces a simple, transparent rule:
1. Each request checks: *"How many unpaid invoices does this IP have?"*
2. If **≥3 unpaid invoices**: Return 429 error (blocked)
3. If **<3 unpaid invoices**: Generate invoice and increment counter
4. When payment detected: Decrement counter (unblock)
5. Auto-cleanup: TTL deletes entries after 1 hour

This means paying users have unlimited access.

### Performance Characteristics
| Metric | Value |
|--------|-------|
| Rate Limit Check | <5ms |
| Image Generation | 30-60 seconds |
| Payment Detection | <1 second |
| DynamoDB Operations | 1-2 per request |
| Monthly Cost | ~$0.25 (DynamoDB) |

## Deployment

### Build & Deploy
```bash
# Package code
python3 -c "
import zipfile
with zipfile.ZipFile('fulmine-sparks.zip', 'w') as z:
    z.write('lambda_handler_simple.py')
    z.write('billing.py')
"

# Upload to Lambda
aws lambda update-function-code \
  --function-name fulmine-sparks \
  --zip-file fileb://fulmine-sparks.zip
```

### Verify Deployment
```bash
# Health check
curl https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health

# Full workflow test
python client.py test-rate-manual
```

### See Also
- **FINAL_WORKING_VERSION.md** - Complete feature list and troubleshooting
- **DEPLOYMENT_STATUS.md** - Pre-deployment checklist

## Troubleshooting

### Image Test Fails Immediately
**Problem:** First request returns 429 (rate limited)
- **Cause:** Old test data in DynamoDB from previous tests
- **Fix:** Scan the `fulmine-sparks-rate-limits` table and delete old entries, or wait 1 hour for TTL cleanup

### Status Stays "Pending" After Paying
**Problem:** You paid, but image status never changes to "available"
- **Cause:** Usually means ALBY_NWC_URL is not set
- **Fix:** Verify Lambda env var: `aws lambda get-function-configuration --function-name fulmine-sparks | grep ALBY_NWC_URL`
- **Workaround:** Try again after 5 seconds, or check CloudWatch logs

### "Rate Limited" Block
**This is expected behavior!** You've created 3 unpaid invoices:
- Pay one of your existing invoices to decrement the counter
- Or wait 1 hour for TTL to auto-clear

### DynamoDB Errors in CloudWatch
- Check tables exist: `aws dynamodb list-tables --region us-east-2`
- Enable TTL on both tables (AWS Console → Tables → TTL)
- Verify Lambda IAM permissions (GetItem, PutItem)

## Documentation

- **FINAL_WORKING_VERSION.md** - Complete feature reference and testing guide
- **DEPLOYMENT_STATUS.md** - Pre-deployment checklist
- **aws-troubleshooting.md** - AWS CLI debugging commands

## What's Implemented

✅ **Image Generation** - SeeDream 4.5 via Replicate
✅ **Lightning Payments** - BOLT11 invoices via Alby
✅ **Rate Limiting** - Fair use (3 unpaid invoice max)
✅ **Payment Detection** - Auto-confirm in <1 second
✅ **Persistent Tracking** - DynamoDB with TTL auto-cleanup
✅ **Automated Testing** - Full workflow tests included
✅ **CloudWatch Logging** - Complete audit trail

## Known Limitations

- Rate limit threshold is fixed at 3 (editable in code)
- No per-user accounts (IP-based rate limiting)
- No analytics dashboard
- Payment confirmation is polling (not webhook)

## Roadmap

- [ ] Webhook-based payment confirmation
- [ ] Per-user accounts and dashboards
- [ ] Configurable rate limit tiers
- [ ] Email receipt notifications
- [ ] Automatic retry with backoff

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
