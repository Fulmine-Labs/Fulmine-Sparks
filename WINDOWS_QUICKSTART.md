# Fulmine-Sparks API Client - Windows Quick Start

## 🚀 Fastest Way to Get Started (2 minutes)

### Step 1: Download the Files

Download these 2 files from GitHub:
- `client.py`
- `run_client.bat`

Save them in the same folder.

### Step 2: Double-Click `run_client.bat`

That's it! A command window will open with an interactive menu.

```
============================================================
  Fulmine-Sparks API Client
============================================================

Available commands:
  1. health     - Check API health
  2. models     - List available models
  3. generate   - Generate an image
  4. exit       - Exit the client

Enter command (1-4): 
```

### Step 3: Try It Out

**Check if API is working:**
```
Enter command (1-4): 1
```

**See available models:**
```
Enter command (1-4): 2
```

**Generate an image:**
```
Enter command (1-4): 3
Enter prompt: a beautiful sunset over mountains
Select model (1-2) [default: 1]: 1
```

Wait 4-5 seconds and you'll get a link to your generated image! 🎨

## 💻 Command Line Usage

You can also use the client from Command Prompt or PowerShell:

```bash
# Check health
python client.py health

# List models
python client.py models

# Generate image
python client.py generate "a cat wearing sunglasses"

# Generate with SDXL (higher quality)
python client.py generate "a cat wearing sunglasses" stable-diffusion-xl
```

## 🎨 Example Prompts to Try

```bash
python client.py generate "a futuristic city at night"
python client.py generate "a dragon flying over mountains"
python client.py generate "a cozy coffee shop interior"
python client.py generate "an astronaut on the moon"
python client.py generate "a magical forest with glowing trees"
```

## 📋 Requirements

- **Python 3.7+** (download from https://www.python.org/downloads/)
  - ⚠️ **IMPORTANT:** Check "Add Python to PATH" during installation!
- Internet connection
- That's it!

## ❓ Troubleshooting

### "Python is not installed"
1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **CHECK THE BOX:** "Add Python to PATH"
4. Click Install
5. Restart your computer
6. Try again

### "ModuleNotFoundError: No module named 'requests'"
- Just run `run_client.bat` - it will install it automatically
- Or manually: Open Command Prompt and type: `pip install requests`

### "Connection refused" or "Cannot connect"
- Check your internet connection
- The API might be temporarily down
- Try: https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health in your browser

### Image generation is slow
- This is normal! Takes 4-5 seconds per image
- The API is generating the image on a remote server
- Larger models (SDXL) may take longer

## 🎯 What You Can Do

✅ Generate images from text prompts
✅ Choose between Stable Diffusion v1.5 and XL
✅ Customize quality settings
✅ Get direct links to generated images
✅ Use in your own Python scripts

## 📚 More Information

- Full documentation: `CLIENT_README.md`
- API details: `API_DEPLOYMENT_SUMMARY.md`
- GitHub: https://github.com/Fulmine-Labs/Fulmine-Sparks

## 🎓 Using in Your Own Python Code

```python
from client import FulmineSparkClient

client = FulmineSparkClient()

# Generate an image
result = client.generate_image("a beautiful sunset")

if "error" not in result:
    print(f"✅ Image generated!")
    print(f"URL: {result['image_urls'][0]}")
    print(f"Time: {result['processing_time']:.2f}s")
```

## 🚀 Next Steps

1. Try the interactive client: `run_client.bat`
2. Experiment with different prompts
3. Try both models (Stable Diffusion and SDXL)
4. Integrate into your own projects

Enjoy! 🎨
