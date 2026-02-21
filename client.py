#!/usr/bin/env python3
"""
Fulmine-Sparks API Client
Simple client to interact with the Fulmine-Sparks serverless API
Uses SeeDream 4.5 model for image generation
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
        num_outputs: int = 1
    ) -> Dict[str, Any]:
        """Generate an image from a text prompt using SeeDream 4.5"""
        
        if not prompt:
            return {"error": "Prompt cannot be empty"}
        
        payload = {
            "prompt": prompt,
            "model": "seedream-4.5",
            "num_outputs": num_outputs
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
                print_header("Generate Image with SeeDream 4.5")
                
                prompt = input("Enter prompt: ").strip()
                if not prompt:
                    print("❌ Prompt cannot be empty!")
                    continue
                
                num_outputs_input = input("Number of outputs [default: 1]: ").strip() or "1"
                try:
                    num_outputs = int(num_outputs_input)
                except ValueError:
                    num_outputs = 1
                
                print(f"\n⏳ Generating image with SeeDream 4.5...")
                print("   (This may take 10-15 seconds...)\n")
                
                result = client.generate_image(prompt=prompt, num_outputs=num_outputs)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                elif "status" in result and result["status"] == "completed":
                    print("✅ Image generated successfully!")
                    print(f"\n📝 Prompt: {result['prompt']}")
                    print(f"🎨 Model: {result['model']}")
                    print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                    
                    image_base64_list = result.get("image_base64", [])
                    for i, base64_data in enumerate(image_base64_list, 1):
                        if base64_data:
                            print(f"\n🖼️  Image {i}:")
                            print(f"   Base64 length: {len(base64_data)} characters")
                            
                            # Automatically save the image
                            filepath = save_base64_image(base64_data)
                            if filepath:
                                print(f"   ✅ Saved to: {filepath}")
                                # Automatically open the image
                                open_image(filepath)
                        else:
                            print(f"\n❌ Image {i}: Failed to generate")
                    
                    # Display invoice if available
                    invoice = result.get("invoice")
                    if invoice:
                        print(f"\n{'='*80}")
                        print(f"💰 Payment Required (Bitcoin Lightning)")
                        print(f"{'='*80}")
                        print(f"Amount:        {invoice['amount_sats']:,} sats (${invoice['price_usd']:.4f})")
                        print(f"Expires:       {invoice['expires_at']}")
                        print(f"\n⚡ Lightning Invoice (BOLT11):")
                        print(f"{invoice['payment_request']}")
                        print(f"\n📱 Scan QR code or paste invoice into your Lightning wallet")
                        print(f"Payment Hash: {invoice['payment_hash'][:16]}...")
                        print(f"{'='*80}")
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
                print("Usage: python client.py generate '<prompt>' [num_outputs]")
                sys.exit(1)
            
            prompt = sys.argv[2]
            num_outputs = 1
            if len(sys.argv) > 3:
                try:
                    num_outputs = int(sys.argv[3])
                except ValueError:
                    num_outputs = 1
            
            print(f"⏳ Generating image with SeeDream 4.5: {prompt}")
            result = client.generate_image(prompt=prompt, num_outputs=num_outputs)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            elif "status" in result and result["status"] == "completed":
                print("✅ Image generated successfully!")
                print(f"📝 Prompt: {result['prompt']}")
                print(f"🎨 Model: {result['model']}")
                print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                
                image_base64_list = result.get("image_base64", [])
                for i, base64_data in enumerate(image_base64_list, 1):
                    if base64_data:
                        print(f"\n🖼️  Image {i}:")
                        print(f"   Base64 length: {len(base64_data)} characters")
                        
                        # Automatically save the image
                        filepath = save_base64_image(base64_data)
                        if filepath:
                            print(f"   ✅ Saved to: {filepath}")
                            # Automatically open the image
                            open_image(filepath)
                    else:
                        print(f"\n❌ Image {i}: Failed to generate")
                
                # Display invoice if available
                invoice = result.get("invoice")
                if invoice:
                    print(f"\n{'='*80}")
                    print(f"💰 Payment Required (Bitcoin Lightning)")
                    print(f"{'='*80}")
                    print(f"Amount:        {invoice['amount_sats']:,} sats (${invoice['price_usd']:.4f})")
                    print(f"Expires:       {invoice['expires_at']}")
                    print(f"\n⚡ Lightning Invoice (BOLT11):")
                    print(f"{invoice['payment_request']}")
                    print(f"\n📱 Scan QR code or paste invoice into your Lightning wallet")
                    print(f"Payment Hash: {invoice['payment_hash'][:16]}...")
                    print(f"{'='*80}")
            else:
                print_json(result)
        
        else:
            print("Usage: python client.py [health|models|generate '<prompt>' [num_outputs]]")
            sys.exit(1)
    else:
        # Interactive mode
        main()
