# 🚀 CloudFormation One-Click Deployment

Deploy Fulmine-Sparks with **ONE CLICK** - no manual configuration needed!

## What is CloudFormation?

CloudFormation is AWS's way of automating infrastructure setup. Instead of clicking through the console, you upload a template and it creates everything automatically.

## Prerequisites

- ✅ AWS Account
- ✅ Replicate API Token
- ✅ `fulmine-sparks.zip` file (already uploaded to Lambda)

## Step 1: Upload ZIP to S3

First, we need to upload the ZIP file to S3 so CloudFormation can access it.

1. Go to: https://console.aws.amazon.com/s3
2. Click **"Create bucket"**
3. **Bucket name:** `fulmine-sparks-YOUR_ACCOUNT_ID`
   - Replace `YOUR_ACCOUNT_ID` with your AWS Account ID
   - To find it: Go to https://console.aws.amazon.com/billing/home#/account
   - Look for "Account ID" (12 digits)
4. Click **"Create bucket"**

5. Click on your new bucket
6. Click **"Upload"**
7. Select `fulmine-sparks.zip`
8. Click **"Upload"**

## Step 2: Delete Current Resources (Optional)

If you want to start fresh and delete the current setup:

1. Go to Lambda: https://console.aws.amazon.com/lambda
2. Click `fulmine-sparks` function
3. Click **"Delete"**
4. Confirm

5. Go to API Gateway: https://console.aws.amazon.com/apigateway
6. Click `fulmine-sparks` API
7. Click **"Delete"**
8. Confirm

This is optional - CloudFormation can work with existing resources too.

## Step 3: Deploy with CloudFormation

1. Go to: https://console.aws.amazon.com/cloudformation
2. Click **"Create stack"**
3. Select **"Upload a template file"**
4. Click **"Choose file"**
5. Select `cloudformation-template.yaml`
6. Click **"Next"**

**Specify stack details:**
- **Stack name:** `fulmine-sparks-stack`
- **ReplicateApiToken:** Paste your Replicate API token
- Click **"Next"**

**Configure stack options:**
- Leave everything as default
- Click **"Next"**

**Review:**
- Check everything looks good
- Click **"Create stack"**

## Step 4: Wait for Deployment

CloudFormation will now create everything automatically:
- ✅ Lambda function
- ✅ API Gateway
- ✅ IAM roles
- ✅ Environment variables
- ✅ Integrations

This takes about 2-3 minutes. You'll see the status change from "CREATE_IN_PROGRESS" to "CREATE_COMPLETE".

## Step 5: Get Your API URL

Once deployment is complete:

1. In CloudFormation console, click on `fulmine-sparks-stack`
2. Click **"Outputs"** tab
3. Look for **"ApiEndpoint"**
4. Copy the URL (looks like: `https://abc123.execute-api.us-east-2.amazonaws.com`)

## Step 6: Update Pythonista Client

On your iPhone in Pythonista:

1. Open `pythonista_client.py`
2. Find line 20:
   ```python
   API_BASE_URL = "http://10.2.38.143:8000"
   ```
3. Replace with your API URL:
   ```python
   API_BASE_URL = "https://abc123.execute-api.us-east-2.amazonaws.com"
   ```
4. Save

## Step 7: Test from iPhone

1. Run Pythonista app
2. Enter: "a beautiful sunset"
3. Tap "🎨 Generate Image"
4. Wait 30-60 seconds
5. Image appears! ✨

## Troubleshooting

### "Stack creation failed"
- Check that you entered your Replicate token correctly
- Check that the S3 bucket name is correct
- Check that the ZIP file is in S3

### "Lambda function not found"
- Make sure the ZIP file is uploaded to S3
- Make sure the bucket name matches in the template

### "API not working"
- Wait a few minutes for everything to fully deploy
- Check CloudWatch logs in Lambda console

### "Internal Server Error"
- Check that REPLICATE_API_TOKEN is set correctly
- Check CloudWatch logs for errors

## Monitoring

### View Logs

1. Go to Lambda console
2. Click `fulmine-sparks` function
3. Click "Monitor" tab
4. Click "View CloudWatch logs"

### Check Stack Status

1. Go to CloudFormation console
2. Click `fulmine-sparks-stack`
3. See the status and events

## Updating Your Code

To update the Lambda function:

1. Create new `fulmine-sparks.zip`
2. Upload to S3
3. Go to CloudFormation
4. Click `fulmine-sparks-stack`
5. Click "Update"
6. Upload new template
7. Click "Next" through the steps
8. Click "Update stack"

## Deleting Everything

To delete all resources:

1. Go to CloudFormation console
2. Click `fulmine-sparks-stack`
3. Click "Delete"
4. Confirm

This will delete:
- ✅ Lambda function
- ✅ API Gateway
- ✅ IAM roles
- ✅ Everything else

## Costs

**Free Tier:**
- 1M Lambda requests/month
- 400,000 GB-seconds/month

**After Free Tier:**
- $0.20 per 1M requests
- Plus Replicate API costs

## Support

- **AWS CloudFormation Docs:** https://docs.aws.amazon.com/cloudformation/
- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues

---

**🎉 One-click deployment - no more manual configuration!**

**Just upload the template and watch it deploy automatically!**
