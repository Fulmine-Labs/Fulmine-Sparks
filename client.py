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

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

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
    
    def retrieve_image(self, payment_hash: str) -> Dict[str, Any]:
        """Retrieve image after payment is confirmed"""
        
        if not payment_hash:
            return {"error": "Payment hash cannot be empty"}
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/retrieve/{payment_hash}"
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


def display_qr_code(invoice_string: str, description: str = "Lightning Invoice"):
    """Generate and display QR code for Lightning invoice"""
    if not QRCODE_AVAILABLE:
        print(f"⚠️  QR code module not available. Install with: pip install qrcode[pil]")
        return
    
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(invoice_string)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_filename = f"qr_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        qr_path = Path("fulmine_images") / qr_filename
        qr_path.parent.mkdir(exist_ok=True)
        img.save(qr_path)
        
        print(f"\n📱 QR Code saved to: {qr_path}")
        print(f"   Scan with your Lightning wallet to pay")
        
        # Try to open the QR code
        try:
            import subprocess
            subprocess.Popen(['open', str(qr_path)])  # macOS
        except:
            try:
                import subprocess
                subprocess.Popen(['xdg-open', str(qr_path)])  # Linux
            except:
                pass  # Windows or other
        
        # Also display ASCII QR code in terminal
        print(f"\n📲 ASCII QR Code (scan with your phone):")
        print()
        qr_ascii = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr_ascii.add_data(invoice_string)
        qr_ascii.make(fit=True)
        qr_ascii.print_ascii(invert=True)
        print()
        
    except Exception as e:
        print(f"❌ Error generating QR code: {str(e)}")


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
                elif "status" in result and result["status"] == "payment_required":
                    print("✅ Image generated successfully!")
                    print(f"\n📝 Prompt: {result['prompt']}")
                    print(f"🎨 Model: {result['model']}")
                    print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                    
                    # Display invoice FIRST
                    invoice = result.get("invoice")
                    if invoice:
                        print(f"\n{'='*80}")
                        print(f"💰 Payment Required (Bitcoin Lightning)")
                        print(f"{'='*80}")
                        print(f"Amount:        {invoice['amount_sats']:,} sats (${invoice['price_usd']:.4f})")
                        print(f"Expires:       {invoice['expires_at']}")
                        print(f"\n⚡ Lightning Invoice (BOLT11):")
                        print(f"{invoice['payment_request']}")
                        print(f"\nPayment Hash: {invoice['payment_hash'][:16]}...")
                        print(f"{'='*80}")
                        
                        # Display QR code
                        display_qr_code(invoice['payment_request'])
                        
                        print(f"\n📱 Scan the QR code above with your Lightning wallet")
                        print(f"💰 Send {invoice['amount_sats']} sats to unlock the image")
                        print(f"⚡ Lightning settles instantly!")
                    else:
                        print(f"\n⚠️  No invoice generated - this should not happen")
                        return
                    
                    # Image will be available after payment is confirmed
                    print(f"\n📝 Next steps:")
                    print(f"1. Scan the QR code with your Lightning wallet")
                    print(f"2. Send {invoice['amount_sats']} sats")
                    print(f"3. After payment settles, retrieve your image with:")
                    print(f"   python3 client.py retrieve {invoice['payment_hash']}")
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
            elif "status" in result and result["status"] == "payment_required":
                print("✅ Image generated successfully!")
                print(f"📝 Prompt: {result['prompt']}")
                print(f"🎨 Model: {result['model']}")
                print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
                print(f"📝 Message: {result.get('message', 'Payment required')}")
                
                # Display invoice
                invoice = result.get("invoice")
                if invoice:
                    print(f"\n{'='*80}")
                    print(f"💰 Payment Required (Bitcoin Lightning)")
                    print(f"{'='*80}")
                    print(f"Amount:        {invoice['amount_sats']:,} sats (${invoice['price_usd']:.4f})")
                    print(f"Expires:       {invoice['expires_at']}")
                    print(f"\n⚡ Lightning Invoice (BOLT11):")
                    print(f"{invoice['payment_request']}")
                    print(f"\nPayment Hash: {invoice['payment_hash'][:16]}...")
                    print(f"{'='*80}")
                    
                    # Display QR code
                    display_qr_code(invoice['payment_request'])
                    
                    # Show next steps
                    print(f"\n📝 Next steps:")
                    print(f"1. Scan the QR code with your Lightning wallet")
                    print(f"2. Send {invoice['amount_sats']} sats")
                    print(f"3. After payment settles, retrieve your image with:")
                    print(f"   python3 client.py retrieve {invoice['payment_hash']}")
                else:
                    print(f"\n⚠️  No invoice generated - this should not happen")
                    sys.exit(1)
            else:
                print_json(result)
        
        elif sys.argv[1] == "retrieve":
            if len(sys.argv) < 3:
                print("Usage: python client.py retrieve <payment_hash>")
                sys.exit(1)
            
            payment_hash = sys.argv[2]
            max_wait_time = 300  # 5 minutes max wait
            poll_interval = 2  # Check every 2 seconds
            elapsed = 0
            
            print(f"⏳ Retrieving image for payment hash: {payment_hash[:16]}...")
            print(f"📱 Waiting for payment confirmation and image retrieval...")
            print(f"⏱️  This may take a few seconds...\n")
            
            while elapsed < max_wait_time:
                result = client.retrieve_image(payment_hash=payment_hash)
                
                if "error" in result:
                    # Check if it's a payment not confirmed error
                    if "402" in str(result.get('error', '')) or "not confirmed" in str(result.get('error', '')).lower():
                        print(f"⏳ Payment not yet confirmed... ({elapsed}s elapsed)", end='\r')
                        import time
                        time.sleep(poll_interval)
                        elapsed += poll_interval
                        continue
                    else:
                        print(f"\n❌ Error: {result['error']}")
                        sys.exit(1)
                
                elif "status" in result and result["status"] == "success":
                    image_base64_list = result.get("image_base64", [])
                    
                    # Check if images are available
                    if image_base64_list and any(image_base64_list):
                        print(f"\n✅ Payment confirmed!")
                        print(f"🖼️  Image retrieved successfully!")
                        
                        for i, base64_data in enumerate(image_base64_list, 1):
                            if base64_data:
                                print(f"\n🖼️  Image {i}:")
                                print(f"   Base64 length: {len(base64_data)} characters")
                                
                                # Save the image
                                filepath = save_base64_image(base64_data)
                                if filepath:
                                    print(f"   ✅ Saved to: {filepath}")
                                    # Open the image
                                    open_image(filepath)
                            else:
                                print(f"\n❌ Image {i}: Failed to retrieve")
                        break
                    else:
                        # Payment confirmed but image not ready yet
                        print(f"⏳ Payment confirmed, waiting for image... ({elapsed}s elapsed)", end='\r')
                        import time
                        time.sleep(poll_interval)
                        elapsed += poll_interval
                        continue
                else:
                    print(f"\n❌ Unexpected response: {result}")
                    sys.exit(1)
            
            if elapsed >= max_wait_time:
                print(f"\n⏱️  Timeout: Image not retrieved within {max_wait_time} seconds")
                print(f"💡 Try again later with: python3 client.py retrieve {payment_hash}")
                sys.exit(1)
        
        else:
            print("Usage: python client.py [health|models|generate '<prompt>' [num_outputs]|retrieve <payment_hash>]")
            sys.exit(1)
    else:
        # Interactive mode
        main()
