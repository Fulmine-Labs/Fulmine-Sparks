#!/usr/bin/env python3
"""
Fulmine-Sparks API Client
Simple client to interact with the Fulmine-Sparks serverless API
"""

import requests
import json
import sys
import os
import webbrowser
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# API Configuration
API_BASE_URL = "https://c2f4z5jyqj.execute-api.us-east-2.amazonaws.com/prod"

class FulmineSparkClient:
    """Client for Fulmine-Sparks API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_models(self) -> Dict[str, Any]:
        """List available image generation models"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/services/image/models")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def generate_image(
        self,
        prompt: str,
        model: str = "stable-diffusion",
        num_outputs: int = 1,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50
    ) -> Dict[str, Any]:
        """Generate an image from a text prompt"""
        
        if not prompt:
            return {"error": "Prompt cannot be empty"}
        
        payload = {
            "prompt": prompt,
            "model": model,
            "num_outputs": num_outputs,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/services/image/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_json(data: Dict[str, Any]):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


def save_image(url: str, filename: Optional[str] = None) -> Optional[str]:
    """Download and save image from URL"""
    try:
        # Create images directory if it doesn't exist
        images_dir = Path("fulmine_images")
        images_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
        
        filepath = images_dir / filename
        
        # Download image
        print(f"⏳ Downloading image...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Image saved to: {filepath}")
        return str(filepath)
    
    except Exception as e:
        print(f"❌ Error saving image: {str(e)}")
        return None


def open_image(filepath: str):
    """Open image in default viewer"""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            return
        
        # Windows
        if sys.platform == "win32":
            os.startfile(filepath)
        # macOS
        elif sys.platform == "darwin":
            os.system(f"open '{filepath}'")
        # Linux
        else:
            os.system(f"xdg-open '{filepath}'")
        
        print(f"🖼️  Opening image...")
    except Exception as e:
        print(f"❌ Error opening image: {str(e)}")


def open_in_browser(url: str):
    """Open image URL in default browser"""
    try:
        print(f"🌐 Opening in browser...")
        webbrowser.open(url)
    except Exception as e:
        print(f"❌ Error opening browser: {str(e)}")


def url_to_base64(url: str) -> Optional[str]:
    """Download image from URL and convert to base64"""
    try:
        print(f"⏳ Downloading image...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Convert to base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        print(f"✅ Image converted to base64 ({len(image_data)} characters)")
        return image_data
    
    except Exception as e:
        print(f"❌ Error converting to base64: {str(e)}")
        return None


def save_base64_image(base64_data: str, filename: Optional[str] = None) -> Optional[str]:
    """Save base64-encoded image to file"""
    try:
        # Create images directory if it doesn't exist
        images_dir = Path("fulmine_images")
        images_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
        
        filepath = images_dir / filename
        
        # Decode base64 and save
        image_data = base64.b64decode(base64_data)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ Image saved to: {filepath}")
        return str(filepath)
    
    except Exception as e:
        print(f"❌ Error saving base64 image: {str(e)}")
        return None


def main():
    """Main CLI interface"""
    
    client = FulmineSparkClient()
    
    print_header("Fulmine-Sparks API Client")
    print("\nAvailable commands:")
    print("  1. health     - Check API health")
    print("  2. models     - List available models")
    print("  3. generate   - Generate an image")
    print("  4. exit       - Exit the client")
    print()
    
    while True:
        try:
            command = input("Enter command (1-4): ").strip().lower()
            
            if command in ["1", "health"]:
                print_header("Health Check")
                result = client.health_check()
                print_json(result)
            
            elif command in ["2", "models"]:
                print_header("Available Models")
                result = client.list_models()
                print_json(result)
            
            elif command in ["3", "generate"]:
                print_header("Generate Image")
                
                prompt = input("Enter prompt: ").strip()
                if not prompt:
                    print("❌ Prompt cannot be empty!")
                    continue
                
                print("\nAvailable models:")
                models_result = client.list_models()
                models_list = models_result.get("models", [])
                
                if models_list:
                    for i, model in enumerate(models_list, 1):
                        print(f"  {i}. {model['name']} - {model['description']}")
                
                num_models = len(models_list)
                model_choice = input(f"\nSelect model (1-{num_models}) [default: 1]: ").strip() or "1"
                
                # Try to parse as number first
                try:
                    choice_idx = int(model_choice) - 1
                    if 0 <= choice_idx < len(models_list):
                        model = models_list[choice_idx]['name']
                    else:
                        # Invalid number, try as model name
                        model = model_choice if model_choice in [m['name'] for m in models_list] else models_list[0]['name']
                except ValueError:
                    # Not a number, try as model name
                    model = model_choice if model_choice in [m['name'] for m in models_list] else models_list[0]['name']
                
                print(f"\n⏳ Generating image with '{model}'...")
                print("   (This may take 4-5 seconds...)\n")
                
                result = client.generate_image(prompt=prompt, model=model)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                elif "status" in result and result["status"] == "completed":
                    print("✅ Image generated successfully!")
                    print(f"\n📝 Prompt: {result['prompt']}")
                    print(f"🎨 Model: {result['model']}")
                    print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                    
                    image_urls = result.get("image_urls", [])
                    for i, url in enumerate(image_urls, 1):
                        print(f"\n🖼️  Image {i} URL:")
                        print(f"   {url}")
                        
                        # Ask what to do with the image
                        print("\nWhat would you like to do?")
                        print("  1. Save image locally (from URL)")
                        print("  2. Open in browser")
                        print("  3. Both (save and open)")
                        print("  4. Convert to base64")
                        print("  5. Base64 + Save")
                        print("  6. Skip")
                        
                        choice = input("Select (1-6) [default: 1]: ").strip() or "1"
                        
                        if choice in ["1", "3"]:
                            filepath = save_image(url)
                            if filepath and choice == "3":
                                open_image(filepath)
                        elif choice == "2":
                            open_in_browser(url)
                        elif choice in ["4", "5"]:
                            base64_data = url_to_base64(url)
                            if base64_data:
                                print(f"\n📋 Base64 Data (first 100 chars):")
                                print(f"   {base64_data[:100]}...")
                                print(f"\n💾 Full base64 data is {len(base64_data)} characters")
                                
                                if choice == "5":
                                    filepath = save_base64_image(base64_data)
                                    if filepath:
                                        open_image(filepath)
                else:
                    print_json(result)
            
            elif command in ["4", "exit", "quit"]:
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid command. Please enter 1-4.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        client = FulmineSparkClient()
        
        if sys.argv[1] == "health":
            print_json(client.health_check())
        
        elif sys.argv[1] == "models":
            print_json(client.list_models())
        
        elif sys.argv[1] == "generate":
            if len(sys.argv) < 3:
                print("Usage: python client.py generate '<prompt>' [model]")
                sys.exit(1)
            
            prompt = sys.argv[2]
            model = sys.argv[3] if len(sys.argv) > 3 else "stable-diffusion"
            
            print(f"⏳ Generating image: {prompt}")
            result = client.generate_image(prompt=prompt, model=model)
            print_json(result)
        
        else:
            print("Usage: python client.py [health|models|generate '<prompt>' [model]]")
            sys.exit(1)
    else:
        # Interactive mode
        main()
