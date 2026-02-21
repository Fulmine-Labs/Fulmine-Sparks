#!/usr/bin/env python3
"""
Fulmine-Sparks API Client
Simple client to interact with the Fulmine-Sparks serverless API
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

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
                if "models" in models_result:
                    for i, model in enumerate(models_result["models"], 1):
                        print(f"  {i}. {model['name']} - {model['description']}")
                
                model_choice = input("\nSelect model (1-2) [default: 1]: ").strip() or "1"
                
                models_list = models_result.get("models", [])
                if model_choice == "1" or model_choice == "stable-diffusion":
                    model = "stable-diffusion"
                elif model_choice == "2" or model_choice == "stable-diffusion-xl":
                    model = "stable-diffusion-xl"
                else:
                    model = "stable-diffusion"
                
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
                    print(f"\n🖼️  Image URL:")
                    for url in result.get("image_urls", []):
                        print(f"   {url}")
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
