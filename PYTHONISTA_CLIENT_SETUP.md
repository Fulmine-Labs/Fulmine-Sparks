# 📱 Pythonista Client Setup Guide

This guide will help you set up the Fulmine-Sparks client on your iPhone using Pythonista.

## What You'll Get

A beautiful iOS app that lets you:
- ✅ Enter positive and negative prompts
- ✅ Check content safety before generation
- ✅ Generate AI images
- ✅ Preview images on your iPhone
- ✅ Save images to Photos
- ✅ Test image-to-image (future)

## Prerequisites

1. **Pythonista 3** - Download from App Store ($9.99)
2. **Your Fulmine-Sparks server running** - With API accessible
3. **iPhone on same network** as server (or use ngrok for remote)

## Step 1: Get the Client File

### Option A: Copy from GitHub (Easiest)

1. Go to: https://github.com/Fulmine-Labs/Fulmine-Sparks
2. Click on `pythonista_client.py`
3. Click "Raw" button
4. Copy all the code

### Option B: Download Directly

```bash
# On your computer
curl -O https://raw.githubusercontent.com/Fulmine-Labs/Fulmine-Sparks/master/pythonista_client.py
```

## Step 2: Add to Pythonista

1. Open **Pythonista** on your iPhone
2. Tap the **"+"** button to create new script
3. Name it: `fulmine_client.py`
4. Paste the code you copied
5. Tap **"Done"**

## Step 3: Configure Server IP

The client needs to know where your server is.

**Find your server IP:**

On your computer (where the server is running):
```bash
# Linux/Mac
hostname -I

# Or use
ifconfig | grep "inet "
```

You should see something like: `10.2.38.143` or `192.168.1.100`

**Update the client:**

1. In Pythonista, open `fulmine_client.py`
2. Find this line (around line 20):
   ```python
   API_BASE_URL = "http://10.2.38.143:8000"
   ```
3. Replace `10.2.38.143` with your actual server IP
4. Save the file

## Step 4: Install Dependencies

Pythonista comes with most libraries, but you may need to install:

```bash
# In Pythonista, tap the "+" and create a new script
# Run this:
import pip
pip.main(['install', 'requests', 'pillow'])
```

Or use Pythonista's built-in package manager:
1. Tap **"⚙️"** (Settings)
2. Go to **"Packages"**
3. Search for and install:
   - `requests`
   - `pillow` (PIL)

## Step 5: Run the Client

1. Open `fulmine_client.py` in Pythonista
2. Tap the **"▶️"** (Play) button
3. The app should launch!

## Using the App

### Check Content Safety

1. Enter a prompt in the **"Positive Prompt"** field
2. Tap **"🛡️ Check Safety"**
3. See if the prompt is safe and the safety score

### Generate an Image

1. Enter a **positive prompt** (what you want)
   - Example: "a beautiful sunset over mountains"
2. Optionally enter a **negative prompt** (what to avoid)
   - Example: "blurry, low quality, distorted"
3. Tap **"🎨 Generate Image"**
4. Wait 30-60 seconds for generation
5. Image appears on screen!

### Save Image

1. After generating an image
2. Tap **"💾 Save Image"**
3. Image saves to your Photos app

## Testing Scenarios

### Test 1: Safe Prompt
```
Positive: "a cute cat playing with a ball"
Negative: "blurry, low quality"
```
Expected: ✅ Image generated

### Test 2: Unsafe Prompt
```
Positive: "violent content"
Negative: ""
```
Expected: ❌ Rejected by moderation

### Test 3: Negative Prompt
```
Positive: "a beautiful landscape"
Negative: "people, buildings, cars"
```
Expected: ✅ Image without those elements

## Troubleshooting

### "Connection refused" error
- Make sure your server is running
- Check the IP address is correct
- Make sure iPhone is on same network
- Try: `ping 10.2.38.143` from your computer

### "Module not found" error
- Install missing packages via Pythonista settings
- Required: `requests`, `pillow`

### Image doesn't display
- Make sure base64 decoding is working
- Check that `pillow` is installed
- Try generating a simpler prompt

### "Timeout" error
- Image generation takes 30-60 seconds
- Make sure you wait long enough
- Check server logs for errors

## Advanced: Remote Access

To access your server from outside your network:

### Option 1: ngrok (Easiest)

```bash
# On your computer
ngrok http 8000
```

This gives you a URL like: `https://abc123.ngrok.io`

Update the client:
```python
API_BASE_URL = "https://abc123.ngrok.io"
```

### Option 2: Port Forwarding

Forward port 8000 on your router to your computer.

### Option 3: Cloud Deployment

Deploy your server to AWS, Google Cloud, or Heroku.

## Features

### Current
- ✅ Positive prompts
- ✅ Negative prompts
- ✅ Content moderation check
- ✅ Image generation
- ✅ Image preview
- ✅ Save to Photos

### Coming Soon
- ⬜ Image-to-image generation
- ⬜ Multiple image outputs
- ⬜ Model selection
- ⬜ Guidance scale adjustment
- ⬜ History/favorites

## Code Structure

```python
FulmineClient
├── check_content()      # Check if prompt is safe
├── generate_image()     # Generate image
└── decode_base64_image() # Convert base64 to image

FulmineUI (Pythonista UI)
├── layout()            # Create UI elements
├── check_safety()      # Handle safety check
├── generate_image()    # Handle generation
└── save_image()        # Save to Photos
```

## API Endpoints Used

```
POST /api/v1/moderation/check
  - Check if content is safe
  - Input: prompt, threshold
  - Output: is_safe, score, reason

POST /api/v1/services/image/generate
  - Generate image
  - Input: prompt, model, num_outputs, etc.
  - Output: status, image_base64, processing_time
```

## Tips & Tricks

1. **Test with simple prompts first** - "a cat", "a sunset"
2. **Use negative prompts** - Improves quality significantly
3. **Wait for generation** - Takes 30-60 seconds
4. **Check safety first** - Saves time if prompt will be rejected
5. **Save good images** - Build a collection

## Example Prompts

### Good Prompts
- "a serene forest with a waterfall"
- "a futuristic city at night with neon lights"
- "a delicious pizza on a wooden table"
- "a golden retriever playing in the snow"

### Negative Prompts
- "blurry, low quality, distorted, ugly"
- "watermark, text, signature"
- "duplicate, repetitive, boring"

## Support

- **GitHub Issues:** https://github.com/Fulmine-Labs/Fulmine-Sparks/issues
- **Documentation:** https://github.com/Fulmine-Labs/Fulmine-Sparks
- **Pythonista Docs:** https://omz-software.com/pythonista/

---

**🎉 Your Pythonista client is ready!**

**Perfect for testing image generation and content filtering on your iPhone!**
