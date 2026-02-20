# 🧪 Testing Guide - Fulmine-Sparks

Complete guide to test your Fulmine-Sparks service on your iPhone using Pythonista.

## Current Status

✅ **Test Server Running** - API server is ready at `http://localhost:8000`
✅ **Pythonista Client Ready** - iOS app is ready to use
✅ **All Dependencies Installed** - Flask, Replicate, etc.

## Option 1: Test on Same Network (Easiest) ✅

If your iPhone and computer are on the **same WiFi network**:

### Step 1: Find Your Computer's IP

**On Mac/Linux:**
```bash
hostname -I
# or
ifconfig | grep "inet " | grep -v 127.0.0.1
```

You'll see something like: `192.168.1.100` or `10.0.0.50`

**On Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
```

### Step 2: Update Pythonista Client

In Pythonista, edit `pythonista_client.py`:

Find line 20:
```python
API_BASE_URL = "http://10.2.38.143:8000"
```

Replace with your actual IP:
```python
API_BASE_URL = "http://192.168.1.100:8000"  # Use YOUR IP
```

### Step 3: Make Sure Server is Running

```bash
# On your computer
cd /workspace/Fulmine-Spark
python test_server.py
```

You should see:
```
============================================================
🎨 Fulmine-Sparks Test Server
============================================================

✅ Starting server...
✅ Endpoints:
   GET  /health
   POST /api/v1/moderation/check
   POST /api/v1/services/image/generate
   GET  /api/v1/services/image/models
```

### Step 4: Test from iPhone

1. Open Pythonista
2. Run `pythonista_client.py`
3. Try: `!generate a beautiful sunset`
4. Image should appear! ✨

---

## Option 2: Use ngrok (Remote Access) 🌐

If you want to access from outside your network:

### Step 1: Create ngrok Account

1. Go to: https://dashboard.ngrok.com/signup
2. Sign up (free account)
3. Go to: https://dashboard.ngrok.com/get-started/your-authtoken
4. Copy your authtoken

### Step 2: Install ngrok

```bash
pip install pyngrok
```

### Step 3: Set Authtoken

```bash
python -c "from pyngrok import ngrok; ngrok.set_auth_token('YOUR_TOKEN_HERE')"
```

Replace `YOUR_TOKEN_HERE` with your actual token.

### Step 4: Start ngrok Tunnel

```bash
cd /workspace/Fulmine-Spark
python start_ngrok.py
```

You'll see:
```
✅ Tunnel created!

🔗 Public URL: https://abc123.ngrok.io

📱 Use this URL in your Pythonista client:

   API_BASE_URL = "https://abc123.ngrok.io"
```

### Step 5: Update Pythonista Client

In Pythonista, edit line 20:
```python
API_BASE_URL = "https://abc123.ngrok.io"  # Use the URL from ngrok
```

### Step 6: Test from iPhone

1. Open Pythonista
2. Run `pythonista_client.py`
3. Try: `!generate a beautiful sunset`
4. Image should appear! ✨

---

## Option 3: Deploy to Cloud ☁️

For permanent hosting:

### AWS Lambda
```bash
# Deploy to AWS Lambda
# Takes 15-30 minutes
# See: AWS Lambda deployment guide
```

### Google Cloud Run
```bash
# Deploy to Google Cloud Run
# Takes 15-30 minutes
# See: Google Cloud Run deployment guide
```

### Heroku
```bash
# Deploy to Heroku
# Takes 10-15 minutes
# See: Heroku deployment guide
```

---

## Testing Checklist

### ✅ Server Running
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "ok",
  "service": "Fulmine-Sparks Test Server"
}
```

### ✅ Moderation Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/moderation/check \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset"}'
```

Should return:
```json
{
  "is_safe": true,
  "score": 0.05,
  "reason": "Content is safe"
}
```

### ✅ Image Generation Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/services/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset"}'
```

Should return:
```json
{
  "status": "completed",
  "image_base64": ["data:image/png;base64,..."],
  "processing_time": 45.2
}
```

---

## Test Scenarios

### Scenario 1: Safe Prompt ✅
```
Prompt: "a beautiful sunset over mountains"
Expected: Image generated successfully
```

### Scenario 2: Unsafe Prompt ❌
```
Prompt: "violent content"
Expected: Rejected by moderation
```

### Scenario 3: Negative Prompt ✅
```
Positive: "a cat"
Negative: "blurry, low quality"
Expected: High-quality cat image
```

### Scenario 4: Save to Photos ✅
```
1. Generate image
2. Tap "Save Image"
3. Check Photos app
Expected: Image appears in Photos
```

---

## Troubleshooting

### "Connection refused"
- Make sure server is running: `python test_server.py`
- Check IP address is correct
- Make sure iPhone is on same network
- Try: `ping 192.168.1.100` (use your IP)

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`
- Or: `pip install flask flask-cors replicate pydantic pydantic-settings`

### "Image generation timeout"
- Generation takes 30-60 seconds
- Make sure you wait long enough
- Check server logs for errors

### "ngrok authentication failed"
- Create free account at: https://dashboard.ngrok.com/signup
- Get authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
- Set token: `python -c "from pyngrok import ngrok; ngrok.set_auth_token('TOKEN')"`

### "Pythonista can't connect"
- Check IP address in client
- Make sure server is running
- Try: `curl http://YOUR_IP:8000/health`
- Check firewall settings

---

## Quick Commands

### Start Server
```bash
cd /workspace/Fulmine-Spark
python test_server.py
```

### Start ngrok Tunnel
```bash
cd /workspace/Fulmine-Spark
python start_ngrok.py
```

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Moderation
```bash
curl -X POST http://localhost:8000/api/v1/moderation/check \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

### View Server Logs
```bash
tail -f /tmp/test_server.log
```

---

## Infrastructure Summary

### For Testing (What You're Doing Now)
- ✅ Local test server (Flask)
- ✅ Same network access (iPhone + Computer)
- ✅ No external dependencies
- ✅ Perfect for development

### For Production
- ⬜ Cloud deployment (AWS, Google Cloud, Heroku)
- ⬜ Domain name (example.com)
- ⬜ SSL certificate (HTTPS)
- ⬜ Monitoring and logging
- ⬜ Auto-scaling
- ⬜ Payment integration (BTCPay)

---

## Next Steps

1. ✅ **Start test server** - `python test_server.py`
2. ✅ **Find your IP** - `hostname -I`
3. ✅ **Update Pythonista client** - Change API_BASE_URL
4. ✅ **Run Pythonista app** - Test on iPhone
5. ✅ **Generate images** - Try different prompts
6. ✅ **Test filtering** - Try unsafe prompts
7. ⬜ **Deploy to production** - When ready

---

## Support

- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues
- **Documentation:** https://github.com/Fulmine-Labs/Fulmine-Sparks
- **Pythonista Docs:** https://omz-software.com/pythonista/

---

**🎉 You're ready to test!**

**Start the server and test from your iPhone!**
