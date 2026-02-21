# Fulmine-Sparks API Client

A simple Python client to interact with the Fulmine-Sparks serverless image generation API.

## 🚀 Quick Start (Windows)

### Option 1: Interactive Mode (Easiest)

1. **Download the client files:**
   - `client.py`
   - `run_client.bat`

2. **Double-click `run_client.bat`**
   - The script will automatically install dependencies
   - You'll see an interactive menu

3. **Follow the prompts:**
   ```
   Enter command (1-4): 1
   ```

### Option 2: Command Line Mode

```bash
# Check API health
python client.py health

# List available models
python client.py models

# Generate an image
python client.py generate "a beautiful sunset over mountains"

# Generate with specific model
python client.py generate "a cat wearing sunglasses" stable-diffusion-xl
```

## 📋 Requirements

- Python 3.7+
- `requests` library (automatically installed by `run_client.bat`)

### Manual Installation

If you prefer to install manually:

```bash
pip install requests
```

## 🎮 Interactive Mode

Run the client without arguments:

```bash
python client.py
```

You'll see a menu:

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

### Example Session

```
Enter command (1-4): 1

============================================================
  Health Check
============================================================

{
  "status": "ok",
  "service": "Fulmine-Sparks Lambda",
  "timestamp": "2026-02-21T05:51:07.654827"
}

Enter command (1-4): 2

============================================================
  Available Models
============================================================

{
  "models": [
    {
      "name": "stable-diffusion",
      "description": "Stable Diffusion v1.5",
      "version": "db21e45d3f7023abc9f30f5cc29eee38d2d9c0c7"
    },
    {
      "name": "stable-diffusion-xl",
      "description": "Stable Diffusion XL",
      "version": "39ed52f2a60c3b36b4fe38b18e56f1f66a14e8925afd339bab9d1260cbe5eca6"
    }
  ],
  "timestamp": "2026-02-21T05:51:07.750094"
}

Enter command (1-4): 3

============================================================
  Generate Image
============================================================

Enter prompt: a beautiful sunset over mountains

Available models:
  1. stable-diffusion - Stable Diffusion v1.5
  2. stable-diffusion-xl - Stable Diffusion XL

Select model (1-2) [default: 1]: 1

⏳ Generating image with 'stable-diffusion'...
   (This may take 4-5 seconds...)

✅ Image generated successfully!

📝 Prompt: a beautiful sunset over mountains
🎨 Model: stable-diffusion
⏱️  Processing time: 4.63s

🖼️  Image URL:
   https://replicate.delivery/yhqm/NGhMaARAeHSEJaYLsAxh7Un76mMaVLIFEWfpUIhSuKVDnvJWA/out-0.png
```

## 💻 Python API Usage

You can also use the client as a library in your own Python code:

```python
from client import FulmineSparkClient

# Create client
client = FulmineSparkClient()

# Check health
health = client.health_check()
print(health)

# List models
models = client.list_models()
print(models)

# Generate image
result = client.generate_image(
    prompt="a beautiful sunset over mountains",
    model="stable-diffusion",
    num_outputs=1,
    guidance_scale=7.5,
    num_inference_steps=50
)

if "error" not in result:
    print(f"Image URL: {result['image_urls'][0]}")
    print(f"Processing time: {result['processing_time']:.2f}s")
```

## 🎨 Image Generation Parameters

When generating images, you can customize:

- **prompt** (required): Text description of the image
- **model** (optional): `stable-diffusion` or `stable-diffusion-xl` (default: `stable-diffusion`)
- **num_outputs** (optional): Number of images to generate, 1-4 (default: 1)
- **guidance_scale** (optional): How closely to follow the prompt, 1-20 (default: 7.5)
- **num_inference_steps** (optional): Quality vs speed tradeoff, 1-500 (default: 50)

### Example with Custom Parameters

```bash
python client.py generate "a futuristic city" stable-diffusion-xl
```

Or in Python:

```python
result = client.generate_image(
    prompt="a futuristic city",
    model="stable-diffusion-xl",
    num_outputs=1,
    guidance_scale=10.0,  # Higher = more prompt adherence
    num_inference_steps=75  # Higher = better quality but slower
)
```

## 📊 Response Format

### Health Check Response
```json
{
    "status": "ok",
    "service": "Fulmine-Sparks Lambda",
    "timestamp": "2026-02-21T05:51:07.654827"
}
```

### Models List Response
```json
{
    "models": [
        {
            "name": "stable-diffusion",
            "description": "Stable Diffusion v1.5",
            "version": "db21e45d3f7023abc9f30f5cc29eee38d2d9c0c7"
        },
        {
            "name": "stable-diffusion-xl",
            "description": "Stable Diffusion XL",
            "version": "39ed52f2a60c3b36b4fe38b18e56f1f66a14e8925afd339bab9d1260cbe5eca6"
        }
    ],
    "timestamp": "2026-02-21T05:51:07.750094"
}
```

### Image Generation Response
```json
{
    "status": "completed",
    "prompt": "a beautiful sunset over mountains",
    "model": "stable-diffusion",
    "image_urls": [
        "https://replicate.delivery/yhqm/NGhMaARAeHSEJaYLsAxh7Un76mMaVLIFEWfpUIhSuKVDnvJWA/out-0.png"
    ],
    "processing_time": 4.625061511993408,
    "timestamp": "2026-02-21T05:51:01.126138"
}
```

## ⚙️ Configuration

To use a different API endpoint, modify the `API_BASE_URL` in `client.py`:

```python
API_BASE_URL = "https://your-api-endpoint.com/prod"
```

Or pass it when creating the client:

```python
client = FulmineSparkClient(base_url="https://your-api-endpoint.com/prod")
```

## 🐛 Troubleshooting

### "Python is not installed"
- Download Python from https://www.python.org/downloads/
- **Important:** Check "Add Python to PATH" during installation
- Restart your computer after installation

### "ModuleNotFoundError: No module named 'requests'"
- Run: `pip install requests`
- Or just run `run_client.bat` which does this automatically

### "Connection refused" or "Cannot connect to API"
- Check your internet connection
- Verify the API is running: https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod/health
- Check if the API endpoint is correct in `client.py`

### Image generation is slow
- This is normal! Image generation takes 4-5 seconds
- The API is waiting for the Replicate service to generate the image
- Larger models (SDXL) may take longer

### "Invalid version or not permitted" error
- This means the Replicate API token doesn't have permission for that model
- Contact the API administrator

## 📝 Examples

### Generate a simple image
```bash
python client.py generate "a red apple on a table"
```

### Generate with SDXL (higher quality)
```bash
python client.py generate "a red apple on a table" stable-diffusion-xl
```

### Use in a Python script
```python
from client import FulmineSparkClient
import webbrowser

client = FulmineSparkClient()

# Generate image
result = client.generate_image("a beautiful landscape")

if "error" not in result:
    # Open image in browser
    image_url = result['image_urls'][0]
    webbrowser.open(image_url)
    print(f"Generated in {result['processing_time']:.2f} seconds")
```

## 🔗 API Documentation

For more details about the API, see: `API_DEPLOYMENT_SUMMARY.md`

## 📄 License

MIT License - Feel free to use and modify!

## 🤝 Support

For issues or questions, check the GitHub repository:
https://github.com/Fulmine-Labs/Fulmine-Sparks
