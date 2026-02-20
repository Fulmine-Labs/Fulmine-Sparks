# 🚀 Railway.app Deployment Guide

Deploy Fulmine-Sparks to Railway.app in 5 minutes!

## What is Railway?

Railway is a simple cloud platform that:
- ✅ Deploys Python apps in seconds
- ✅ Provides free tier ($5/month credit)
- ✅ Gives you a public URL immediately
- ✅ Handles environment variables
- ✅ Perfect for testing

## Step 1: Create Railway Account

1. Go to: https://railway.app
2. Click "Start Project"
3. Sign up with GitHub (easiest) or email
4. Verify your email

## Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub"
3. Connect your GitHub account
4. Select: `Fulmine-Labs/Fulmine-Sparks` repository
5. Click "Deploy"

**OR** - If you don't have it on GitHub yet:

1. Click "New Project"
2. Select "GitHub Repo"
3. Paste: `https://github.com/Fulmine-Labs/Fulmine-Sparks`
4. Click "Deploy"

## Step 3: Add Environment Variables

Railway needs your Replicate API token:

1. In Railway dashboard, go to your project
2. Click "Variables"
3. Add:
   ```
   REPLICATE_API_TOKEN=your_token_here
   ```
4. Replace `your_token_here` with your actual Replicate token
5. Click "Save"

## Step 4: Deploy

1. Railway automatically deploys when you push to GitHub
2. Or click "Deploy" button manually
3. Wait 2-3 minutes for deployment
4. You'll see a green checkmark when done

## Step 5: Get Your Public URL

1. In Railway dashboard, click your project
2. Go to "Settings"
3. Look for "Domain" or "Public URL"
4. You'll see something like: `https://fulmine-sparks-production.up.railway.app`
5. **Copy this URL!**

## Step 6: Update Pythonista Client

On your iPhone in Pythonista:

1. Open `pythonista_client.py`
2. Find line 20:
   ```python
   API_BASE_URL = "http://10.2.38.143:8000"
   ```
3. Replace with your Railway URL:
   ```python
   API_BASE_URL = "https://fulmine-sparks-production.up.railway.app"
   ```
4. Save the file

## Step 7: Test from iPhone

1. Open Pythonista
2. Run `pythonista_client.py`
3. Enter a prompt: "a beautiful sunset"
4. Tap "🎨 Generate Image"
5. Wait 30-60 seconds
6. Image appears! ✨

## Troubleshooting

### "Deployment failed"
- Check that `requirements.txt` has all dependencies
- Check that `Procfile` exists
- Check Railway logs for errors

### "Connection refused"
- Make sure deployment is complete (green checkmark)
- Wait a few minutes for Railway to fully start
- Check that URL is correct

### "REPLICATE_API_TOKEN not set"
- Go to Railway dashboard
- Click "Variables"
- Add `REPLICATE_API_TOKEN=your_token`
- Redeploy

### "Image generation timeout"
- Generation takes 30-60 seconds
- Make sure you wait long enough
- Check Railway logs for errors

## Viewing Logs

To see what's happening:

1. In Railway dashboard, click your project
2. Click "Logs"
3. You'll see real-time server logs
4. Useful for debugging

## Updating Your Code

When you make changes:

1. Commit to GitHub:
   ```bash
   git add -A
   git commit -m "Update message"
   git push origin master
   ```

2. Railway automatically redeploys
3. Or manually click "Deploy" in Railway dashboard

## Costs

**Free Tier:**
- $5/month credit
- Enough for testing
- No credit card needed

**After free tier:**
- Pay-as-you-go
- Usually $5-20/month for small projects
- Can set spending limits

## Next Steps

1. ✅ Create Railway account
2. ✅ Deploy Fulmine-Sparks
3. ✅ Add environment variables
4. ✅ Get public URL
5. ✅ Update Pythonista client
6. ✅ Test from iPhone

## Support

- **Railway Docs:** https://docs.railway.app
- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues
- **Railway Support:** https://railway.app/support

---

**🎉 Your Fulmine-Sparks service is now live on the internet!**

**Access it from anywhere on your iPhone!**
