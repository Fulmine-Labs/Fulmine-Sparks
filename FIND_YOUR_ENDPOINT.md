# 🔍 Finding Your API Endpoint

The test script needs your actual API Gateway endpoint URL. Here's how to find it:

## 🚀 Quick Find (AWS CLI)

```bash
# Find your API Gateway endpoint
aws apigateway get-rest-apis --query 'items[?name==`fulmine-sparks`]' --output table
```

Look for the **Invoke URL** in the output. It should look like:
```
https://abc123def.execute-api.us-east-1.amazonaws.com/prod
```

## 📋 Step-by-Step (AWS Console)

1. **Go to AWS Console**
   - Search for "API Gateway"
   - Click on "API Gateway"

2. **Find Your API**
   - Look for "fulmine-sparks" in the list
   - Click on it

3. **Get the Endpoint**
   - Click "Stages" on the left sidebar
   - Click "prod" stage
   - Look at the top - you'll see "Invoke URL"
   - Copy this URL

4. **Example URL**
   ```
   https://abc123def.execute-api.us-east-1.amazonaws.com/prod
   ```

## 🧪 Test Your Endpoint

Once you have your endpoint, test it:

```bash
# Replace with your actual endpoint
curl https://abc123def.execute-api.us-east-1.amazonaws.com/prod/health
```

You should get:
```json
{"status": "ok"}
```

## ✅ Run the Test Workflow

Once you have your endpoint:

```bash
# Replace with your actual endpoint
python3 test_workflow.py https://abc123def.execute-api.us-east-1.amazonaws.com/prod
```

## 🔧 Troubleshooting

### "Connection refused"
- Check the endpoint URL is correct
- Make sure it includes `/prod` at the end
- Verify the API Gateway is deployed

### "404 Not Found"
- Check the endpoint URL is correct
- Make sure Lambda function is deployed
- Check API Gateway routes are configured

### "Timeout"
- Check your internet connection
- Verify the API Gateway is accessible
- Check AWS credentials are configured

## 📝 Example Endpoints

These are examples - yours will be different:

```
https://abc123def.execute-api.us-east-1.amazonaws.com/prod
https://xyz789uvw.execute-api.eu-west-1.amazonaws.com/prod
https://qwerty123.execute-api.ap-southeast-1.amazonaws.com/prod
```

The format is always:
```
https://<API-ID>.execute-api.<REGION>.amazonaws.com/prod
```

## 🎯 Once You Have It

Run the test:
```bash
python3 test_workflow.py https://YOUR-ACTUAL-ENDPOINT/prod
```

Then check CloudWatch logs:
```bash
aws logs tail /aws/lambda/fulmine-sparks --follow
```

---

Made with ⚡ by Fulmine Labs
