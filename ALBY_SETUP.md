# Getting Your Alby Hub NWC Connection String

## 🎯 Quick Summary

**What You Need**:
- A **NWC Connection String** (Nostr Wallet Connect)
- This is what Alby Hub uses for API authentication

**Where to Find It**:
1. Go to your Alby Hub dashboard
2. Click **App Store** (in main menu)
3. Click **"Connect"** or **"Add New App"**
4. Name it: `Fulmine-Sparks`
5. Select permissions:
   - ✅ **Create invoices** (required)
   - ✅ **Look up Status of Invoices** (required)
6. Copy the **NWC Connection String** (shown only once!)
   - It looks like: `nostr+walletconnect://...`

---

## Step-by-Step Guide

### 1. Access Your Alby Hub Dashboard

1. Go to your Alby Hub instance
   - If self-hosted: `https://your-alby-hub-domain.com`
   - If using Alby's hosted: `https://hub.getalby.com`

2. Log in with your credentials

### 2. Navigate to App Store

1. Click on **App Store** (in the main menu)
2. Look for **"Connect"** or **"Add App"** button
3. You should see an option to create a new connection

### 3. Create a New App Connection

1. Click **"Connect"** or **"Add New App"**
2. Give it a name: `Fulmine-Sparks`
3. Select the required permissions:
   - ✅ **Create invoices** - To create Lightning invoices
   - ✅ **Look up Status of Invoices** - To check invoice status
   - ❌ Do NOT select: Isolate, Read balance, Read node info, Read transaction history, sign messages, receive wallet notifications, send payments

4. Click **"Create"** or **"Connect"**

### 4. Copy Your NWC Connection String

⚠️ **IMPORTANT**: The connection string will only be shown ONCE!

1. Copy the entire **NWC Connection String**
2. Save it somewhere safe (password manager, secure note, etc.)
3. Do NOT share this string with anyone

The NWC Connection String will look something like:
```
nostr+walletconnect://abc123def456...?relay=wss://relay.getalby.com/v1&secret=xyz789
```

**This is your API token** - it's what you'll use to authenticate with Alby Hub!

## Setting Up in AWS Lambda

### Option 1: AWS Console (Easiest)

1. Go to AWS Lambda Console
2. Find your `fulmine-sparks` function
3. Click on **Configuration** tab
4. Click on **Environment variables**
5. Click **Edit**
6. Click **Add environment variable**
7. Set:
   - **Key**: `ALBY_NWC_URL`
   - **Value**: `[paste your NWC Connection String here]`
   - Example: `nostr+walletconnect://abc123...?relay=wss://relay.getalby.com/v1&secret=xyz789`
8. Click **Save**

### Option 2: AWS CLI

```bash
aws lambda update-function-configuration \
  --function-name fulmine-sparks \
  --environment Variables={ALBY_NWC_URL=nostr+walletconnect://...} \
  --region us-east-2
```

### Option 3: Using AWS Secrets Manager (More Secure)

1. Go to AWS Secrets Manager
2. Click **Store a new secret**
3. Choose **Other type of secret**
4. Add key-value pair:
   - **Key**: `ALBY_API_TOKEN`
   - **Value**: `[paste your token]`
5. Name it: `fulmine-sparks/alby-token`
6. Update Lambda to read from Secrets Manager

## Testing Your Token

### Test Locally

```bash
# Set the environment variable
export ALBY_API_TOKEN="your_token_here"

# Test the billing module
python3 << 'EOF'
from billing import AlbyBillingClient, calculate_image_price

# Test connection
client = AlbyBillingClient()
print("✅ Connected to Alby Hub!")

# Test pricing calculation
pricing = calculate_image_price(1)
print(f"Price for 1 image: {pricing['total_sats']} sats")

# Test invoice creation
invoice = client.create_invoice(
    amount_sats=100,
    description="Test invoice"
)
print(f"Invoice created: {invoice.get('payment_hash', 'error')}")
EOF
```

### Test in Lambda

1. Deploy the updated zip file
2. Go to Lambda Console
3. Click **Test**
4. Create a test event:
```json
{
  "httpMethod": "POST",
  "path": "/api/v1/services/image/generate",
  "body": "{\"prompt\": \"test\", \"model\": \"seedream-4.5\", \"num_outputs\": 1}"
}
```
5. Click **Test**
6. Check the response for invoice data

## Troubleshooting

### "ALBY_API_TOKEN not set"

**Solution**: Make sure the environment variable is set in Lambda:
1. Go to Lambda Configuration → Environment variables
2. Verify `ALBY_API_TOKEN` is there
3. Verify the value is not empty
4. Redeploy the function

### "Invalid token"

**Solution**: Token may be expired or incorrect:
1. Go back to Alby Hub Settings
2. Check if the token is still valid
3. Create a new token if needed
4. Update Lambda environment variable

### "Connection refused"

**Solution**: Alby Hub URL may be wrong:
1. Check your Alby Hub URL is correct
2. Make sure it's accessible from Lambda
3. If self-hosted, verify firewall rules
4. Set `ALBY_HUB_URL` environment variable if using custom URL

### "Permission error"

**Solution**: Token doesn't have required permissions:
1. Go to Alby Hub App Store
2. Delete the old connection
3. Create a new connection with both permissions:
   - ✅ **Create invoices**
   - ✅ **Look up Status of Invoices**

## Security Best Practices

✅ **DO**:
- Store token in Lambda environment variables or Secrets Manager
- Use minimal required scopes
- Rotate tokens periodically
- Monitor token usage

❌ **DON'T**:
- Commit token to GitHub
- Share token with others
- Use in client-side code
- Log the token in CloudWatch

## Environment Variables Reference

```bash
# Required - Your NWC Connection String from Alby Hub
ALBY_NWC_URL="nostr+walletconnect://abc123...?relay=wss://relay.getalby.com/v1&secret=xyz789"

# Optional (for custom BTC price)
BTC_PRICE_USD="67000"
```

## Alby Hub Resources

- **Alby Hub Docs**: https://docs.getalby.com/
- **Alby API Reference**: https://guides.getalby.com/developer-guide/
- **Alby GitHub**: https://github.com/getAlby

## Next Steps

1. ✅ Get your API token from Alby Hub
2. ✅ Set `ALBY_API_TOKEN` in Lambda environment
3. ✅ Deploy updated zip file
4. ✅ Test with `python3 client.py generate "test" 1`
5. ✅ Verify invoice appears in response

---

**Need Help?**
- Check Alby Hub documentation: https://docs.getalby.com/
- Check Lambda logs in CloudWatch
- Verify token has correct scopes
