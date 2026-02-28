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
            
            # Handle rate limiting
            if response.status_code == 429:
                try:
                    error_data = response.json()
                    return {
                        "error": "Rate limited",
                        "status": 429,
                        "message": error_data.get("error", "Too many requests"),
                        "details": "You have too many unpaid invoices. Please pay for previous images or wait."
                    }
                except:
                    return {
                        "error": "Rate limited",
                        "status": 429,
                        "message": "Too many requests"
                    }
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_image_status(self, payment_hash: str) -> Dict[str, Any]:
        """Check image status (pending, available, or expired)"""
        
        if not payment_hash:
            return {"error": "Payment hash cannot be empty"}
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/status/{payment_hash}"
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
    
    def pay_invoice(self, payment_request: str) -> Dict[str, Any]:
        """Pay a Lightning invoice using Alby Wallet API"""
        if not payment_request:
            return {"error": "Payment request cannot be empty"}
        
        try:
            alby_token = os.getenv('ALBY_API_TOKEN')
            if not alby_token:
                return {"error": "ALBY_API_TOKEN not set. Cannot pay invoice."}
            
            headers = {
                "Authorization": f"Bearer {alby_token}",
                "Content-Type": "application/json"
            }
            
            # Send payment request to Alby Wallet
            response = requests.post(
                "https://api.getalby.com/payments/bolt11",
                headers=headers,
                json={"invoice": payment_request},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "payment": result,
                "message": "Payment sent successfully!"
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Payment failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Error paying invoice: {str(e)}"}

    
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


def run_bot_simulator():
    """Run bot simulator to test API compliance"""
    import json
    from datetime import datetime
    
    print("📋 Bot Simulator - Testing API Compliance\n")
    
    # Step 1: Health Check
    print("="*80)
    print("  1. Health Check")
    print("="*80)
    print("✅ API is healthy and running\n")
    
    # Step 2: Read llms.txt
    print("="*80)
    print("  2. Reading llms.txt Guidelines")
    print("="*80)
    print("""
✅ PERMITTED USES:
   - Generate images for personal use
   - Generate images for commercial use
   - Integrate into applications
   - Use in research and development
   - Educational purposes

❌ PROHIBITED USES:
   - Illegal content generation
   - Hateful or discriminatory content
   - Sexual or adult content
   - Deceptive or fraudulent use
   - Intellectual property violations
   - Harassment or abuse
   - Reverse engineering
   - Service circumvention

📊 RATE LIMITS:
   - Recommended: 1 request per 20 seconds
   - Maximum: 10 requests per minute
   - Burst limit: 5 concurrent requests

💰 PRICING:
   - Cost: $0.05 USD per image
   - Payment method: Bitcoin Lightning Network only

📝 ATTRIBUTION:
   - Attribution appreciated but not required
   - If attributing: "Image generated by Fulmine-Sparks"
    """)
    
    # Step 3: Read robots.txt
    print("="*80)
    print("  3. Reading robots.txt Directives")
    print("="*80)
    print("""
User-agent: *
Allow: /

Disallow: /api/
Disallow: /invoices/
Disallow: /payments/
Disallow: /admin/
Disallow: /internal/
Disallow: /debug/

Crawl-delay: 1
    """)
    print("✅ Bot respecting robots.txt directives\n")
    
    # Step 4: Read Terms of Service
    print("="*80)
    print("  4. Reading Terms of Service")
    print("="*80)
    print("""
✅ PAYMENT TERMS:
   - Price: $0.05 USD per image
   - Payment method: Bitcoin Lightning Network
   - Payment is final and irreversible
   - Invoice expiration: 1 hour

❌ REFUND POLICY:
   - NO REFUNDS - All payments are final
   - Images are digital goods delivered immediately
   - No refunds for any reason

⚖️  LIABILITY:
   - Service provided "as is"
   - No warranty of any kind
   - No liability for service interruptions
   - Maximum liability: Amount paid in past 30 days
    """)
    
    # Step 5: Read Privacy Policy
    print("="*80)
    print("  5. Reading Privacy Policy")
    print("="*80)
    print("""
📊 DATA COLLECTION:
   - Prompts are NOT stored
   - Generated images cached for 1 minute only
   - Payment info handled by Alby Wallet
   - No user tracking

🗑️  DATA RETENTION:
   - Prompts: Not stored
   - Images: Deleted after 1 minute
   - Logs: Retained for 30 days
   - Payment records: Per Alby policy

✅ COMPLIANCE:
   - GDPR compliant (EU users)
   - CCPA compliant (California users)
   - User rights: Access, deletion, portability
    """)
    
    # Step 6: Read Acceptable Use Policy
    print("="*80)
    print("  6. Reading Acceptable Use Policy")
    print("="*80)
    print("""
❌ PROHIBITED CONTENT:
   - Illegal content
   - Hateful or discriminatory content
   - Sexual or adult content
   - Deceptive or fraudulent content
   - IP violations
   - Privacy violations
   - Harassment or abuse

❌ PROHIBITED ACTIVITIES:
   - Service abuse (circumventing rate limits)
   - Reverse engineering
   - Unauthorized access
   - Resale or redistribution

⚖️  ENFORCEMENT:
   - First violation: Warning
   - Repeated violations: Suspension (7-30 days)
   - Severe violations: Permanent termination
   - Legal action may be pursued
    """)
    
    # Summary
    print("="*80)
    print("  Bot Simulation Summary")
    print("="*80)
    print(f"""
🤖 Bot Name: FulmineBot/1.0
📊 Total Checks: 6
⏱️  Timestamp: {datetime.now().isoformat()}

✅ Bot successfully:
   - Read llms.txt guidelines
   - Read robots.txt directives
   - Respected rate limiting
   - Accessed all public endpoints
   - Read all legal documentation
   - Followed Acceptable Use Policy

🎯 Bot is compliant with Fulmine-Sparks API guidelines!
    """)


def test_rate_limiting():
    """Test progressive rate limiting by creating unpaid invoices"""
    print_header("Progressive Rate Limiting Test")
    
    client = FulmineSparkClient()
    
    print("This test demonstrates progressive rate limiting based on unpaid invoices.")
    print("We'll create invoices WITHOUT paying them to show how limits get stricter.\n")
    
    prompt = input("Enter a test prompt (or press Enter for default): ").strip()
    if not prompt:
        prompt = "A beautiful sunset over mountains"
    
    print(f"\n📝 Using prompt: {prompt}\n")
    
    unpaid_invoices = []
    results = []
    
    # Phase 1: Create unpaid invoices
    print("="*80)
    print("  Phase 1: Creating Unpaid Invoices")
    print("="*80)
    print()
    
    for i in range(1, 4):
        print(f"Request {i} (creating unpaid invoice):")
        result = client.generate_image(prompt=prompt, num_outputs=1)
        
        if "error" in result:
            if result.get("status") == 429:
                print(f"  ⛔ Rate Limited!")
                print(f"     {result.get('message', 'Too many requests')}")
                results.append({"phase": 1, "request": i, "status": "rate_limited"})
            else:
                print(f"  ❌ Error: {result['error']}")
                results.append({"phase": 1, "request": i, "status": "error"})
        elif "status" in result and result["status"] == "payment_required":
            print(f"  ✅ Invoice created (NOT paying)")
            print(f"     Amount: {result['invoice']['amount_sats']} sats (${result['invoice']['price_usd']:.4f})")
            print(f"     Payment Hash: {result['invoice']['payment_hash'][:16]}...")
            unpaid_invoices.append(result['invoice']['payment_hash'])
            results.append({"phase": 1, "request": i, "status": "allowed"})
        else:
            print(f"  ⚠️  Unexpected response")
            results.append({"phase": 1, "request": i, "status": "unexpected"})
        
        print()
    
    # Phase 2: Try more requests with unpaid invoices
    print("="*80)
    print(f"  Phase 2: Trying More Requests ({len(unpaid_invoices)} Unpaid Invoices)")
    print("="*80)
    print()
    
    if len(unpaid_invoices) > 0:
        print(f"⚠️  You now have {len(unpaid_invoices)} unpaid invoice(s)")
        print("   Rate limits should be MUCH stricter now!\n")
        
        for i in range(1, 6):
            print(f"Request {i}:")
            result = client.generate_image(prompt=prompt, num_outputs=1)
            
            if "error" in result:
                if result.get("status") == 429:
                    print(f"  ⛔ Rate Limited!")
                    print(f"     {result.get('message', 'Too many requests')}")
                    print(f"     {result.get('details', '')}")
                    results.append({"phase": 2, "request": i, "status": "rate_limited"})
                else:
                    print(f"  ❌ Error: {result['error']}")
                    results.append({"phase": 2, "request": i, "status": "error"})
            elif "status" in result and result["status"] == "payment_required":
                print(f"  ✅ Allowed (but you have unpaid invoices!)")
                print(f"     Amount: {result['invoice']['amount_sats']} sats (${result['invoice']['price_usd']:.4f})")
                unpaid_invoices.append(result['invoice']['payment_hash'])
                results.append({"phase": 2, "request": i, "status": "allowed"})
            else:
                print(f"  ⚠️  Unexpected response")
                results.append({"phase": 2, "request": i, "status": "unexpected"})
            
            print()
    
    # Summary
    print("="*80)
    print("  Test Summary")
    print("="*80)
    print()
    
    phase1_allowed = sum(1 for r in results if r["phase"] == 1 and r["status"] == "allowed")
    phase1_limited = sum(1 for r in results if r["phase"] == 1 and r["status"] == "rate_limited")
    phase2_allowed = sum(1 for r in results if r["phase"] == 2 and r["status"] == "allowed")
    phase2_limited = sum(1 for r in results if r["phase"] == 2 and r["status"] == "rate_limited")
    
    print("Phase 1 (Creating Unpaid Invoices):")
    print(f"  ✅ Allowed:      {phase1_allowed}")
    print(f"  ⛔ Rate limited: {phase1_limited}")
    print()
    
    print(f"Phase 2 (With {len(unpaid_invoices)} Unpaid Invoices):")
    print(f"  ✅ Allowed:      {phase2_allowed}")
    print(f"  ⛔ Rate limited: {phase2_limited}")
    print()
    
    if phase2_limited > phase1_limited or (phase2_limited > 0 and phase1_limited == 0):
        print("✅ Progressive rate limiting is working!")
        print("   - Phase 1: Could create invoices normally")
        print("   - Phase 2: Got rate limited with unpaid invoices")
        print("   - Limits got STRICTER as unpaid invoices accumulated")
    elif phase2_allowed > 0 and phase2_limited == 0:
        print("⚠️  Rate limiting may not be active")
        print("   - Still allowing requests with unpaid invoices")
    else:
        print("⚠️  Unexpected test results")
    
    print()
    print("💡 How Progressive Rate Limiting Works:")
    print("   - 0 unpaid invoices:    3 requests per minute (normal)")
    print("   - 1 unpaid invoice:     2 requests per minute")
    print("   - 2-3 unpaid invoices:  1 request per minute")
    print("   - 4-5 unpaid invoices:  1 request per 2 minutes")
    print("   - 6-10 unpaid invoices: 1 request per 5 minutes")
    print("   - 11+ unpaid invoices:  Blocked completely")
    print()
    print("💡 To Restore Normal Limits:")
    print("   - Pay your unpaid invoices")
    print("   - Unpaid count decreases immediately")
    print("   - Rate limits loosen right away")
    print()


def run_payment_bot():
    """Bot that automatically generates images and pays for them"""
    import time

    client = FulmineSparkClient()

    print_header("Payment Bot - Automated Image Generation & Payment")

    # Get prompt
    prompt = input("Enter prompt: ").strip()
    if not prompt:
        print("❌ Prompt cannot be empty!")
        return

    # Step 1: Generate image
    print(f"\n⏳ Step 1/4: Generating image with SeeDream 4.5...")
    print("   (This may take 10-15 seconds...)\n")

    result = client.generate_image(prompt=prompt, num_outputs=1)

    if "error" in result:
        print(f"❌ Error generating image: {result['error']}")
        return

    if "status" not in result or result["status"] != "payment_required":
        print(f"❌ Unexpected response: {result}")
        return

    print("✅ Image generated successfully!")

    # Get invoice
    invoice = result.get("invoice")
    if not invoice:
        print(f"❌ No invoice generated - this should not happen")
        return

    payment_hash = invoice['payment_hash']
    payment_request = invoice['payment_request']

    print(f"📝 Payment Hash: {payment_hash[:16]}...")
    print(f"💰 Amount: {invoice['amount_sats']:,} sats (${invoice['price_usd']:.4f})")

    # Step 2: Pay invoice
    print(f"\n⏳ Step 2/4: Submitting payment...")

    pay_result = client.pay_invoice(payment_request)

    if "error" in pay_result:
        print(f"❌ Error paying invoice: {pay_result['error']}")
        return

    print(f"✅ Payment submitted!")
    print(f"   {pay_result.get('message', 'Payment sent')}")

    # Step 3: Poll for image availability
    print(f"\n⏳ Step 3/4: Polling for payment confirmation...")

    max_wait_time = 300  # 5 minutes max wait
    poll_interval = 2  # Check every 2 seconds
    elapsed = 0

    while elapsed < max_wait_time:
        status_result = client.get_image_status(payment_hash=payment_hash)

        if "error" in status_result:
            print(f"\n❌ Error: {status_result['error']}")
            return

        status = status_result.get("status")

        if status == "pending":
            print(f"⏳ Waiting for payment confirmation... ({elapsed}s elapsed)", end='\r')
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        elif status == "available":
            print(f"\n✅ Payment confirmed! Image is available.")
            break

        elif status == "expired":
            print(f"\n❌ Image expired! Please generate a new image.")
            return

        else:
            print(f"\n❌ Unknown status: {status}")
            return

    if elapsed >= max_wait_time:
        print(f"\n⏱️  Timeout: Payment not confirmed within {max_wait_time} seconds")
        print(f"💡 Try again later with: python3 client.py retrieve {payment_hash}")
        return

    # Step 4: Retrieve image
    print(f"\n⏳ Step 4/4: Retrieving image...")

    retrieve_result = client.retrieve_image(payment_hash=payment_hash)

    if "error" in retrieve_result:
        print(f"❌ Error retrieving image: {retrieve_result['error']}")
        return

    if retrieve_result.get("status") == "success":
        image_base64_list = retrieve_result.get("image_base64", [])

        if image_base64_list and any(image_base64_list):
            print(f"✅ Image retrieved successfully!")

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
        else:
            print(f"❌ No images in response")
    else:
        print(f"❌ Unexpected response: {retrieve_result}")

    print(f"\n{'='*80}")
    print(f"✅ Bot workflow completed successfully!")
    print(f"{'='*80}\n")


def main():
    """Main CLI interface"""
    
    client = FulmineSparkClient()
    
    print_header("Fulmine-Sparks API Client")
    print("\nAvailable commands:")
    print("  1. health     - Check API health")
    print("  2. models     - List available models")
    print("  3. generate   - Generate an image")
    print("  4. status     - Check image status")
    print("  5. retrieve   - Retrieve image")
    print("  6. pay        - Pay an invoice")
    print("  7. bot-sim    - Run bot simulator (mock)")
    print("  8. test-rate  - Test rate limiting")
    print("  9. exit       - Exit the client")
    print()
    
    while True:
        try:
            command = input("Enter command (1-9): ").strip().lower()
            
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
                    # Check if it's a rate limiting error
                    if result.get("status") == 429:
                        print(f"⛔ Rate Limited!")
                        print(f"   {result.get('message', 'Too many requests')}")
                        print(f"   {result.get('details', '')}")
                        print(f"\n💡 Tip: Pay for your unpaid invoices to restore normal rate limits")
                    else:
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
                        
                        # Show payment instructions
                        print(f"\n📝 Payment Instructions:")
                        print(f"1. Scan the QR code with your Lightning wallet")
                        print(f"2. Send {invoice['amount_sats']} sats")
                        print(f"3. Payment will be detected automatically")
                    else:
                        print(f"\n⚠️  No invoice generated - this should not happen")
                        return
                    
                    print(f"\n⏳ Polling for payment confirmation...")
                    
                    payment_hash = invoice['payment_hash']
                    max_wait_time = 300  # 5 minutes max wait
                    poll_interval = 1  # Check every 1 second
                    elapsed = 0
                    
                    while elapsed < max_wait_time:
                        # Check status
                        status_result = client.get_image_status(payment_hash=payment_hash)
                        
                        if "error" in status_result:
                            print(f"\n❌ Error: {status_result['error']}")
                            break
                        
                        status = status_result.get("status")
                        
                        if status == "pending":
                            print(f"⏳ Payment pending... ({elapsed}s elapsed)", end='\r')
                            import time
                            time.sleep(poll_interval)
                            elapsed += poll_interval
                            continue
                        
                        elif status == "available":
                            print(f"\n✅ Image available! Retrieving...")
                            
                            # Now retrieve the actual image
                            result = client.retrieve_image(payment_hash=payment_hash)
                            
                            if "error" in result:
                                print(f"❌ Error retrieving image: {result['error']}")
                                break
                            
                            if result.get("status") == "success":
                                image_base64_list = result.get("image_base64", [])
                                
                                if image_base64_list and any(image_base64_list):
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
                                else:
                                    print(f"❌ No images in response")
                            else:
                                print(f"❌ Unexpected response: {result}")
                            break
                        
                        elif status == "expired":
                            print(f"\n❌ Image expired! Please generate a new image.")
                            break
                        
                        else:
                            print(f"\n❌ Unknown status: {status}")
                            break
                    
                    if elapsed >= max_wait_time:
                        print(f"\n⏱️  Timeout: Image not retrieved within {max_wait_time} seconds")
                        print(f"💡 Try again later with: python3 client.py retrieve {payment_hash}")
                else:
                    print_json(result)
            
            elif command in ["4", "status"]:
                print_header("Check Image Status")
                payment_hash = input("Enter payment hash: ").strip()
                if not payment_hash:
                    print("❌ Payment hash cannot be empty!")
                    continue
                result = client.get_image_status(payment_hash)
                print_json(result)
            
            elif command in ["5", "retrieve"]:
                print_header("Retrieve Image")
                payment_hash = input("Enter payment hash: ").strip()
                if not payment_hash:
                    print("❌ Payment hash cannot be empty!")
                    continue
                result = client.retrieve_image(payment_hash)
                print_json(result)
            
            elif command in ["6", "pay"]:
                print_header("Pay Invoice")
                payment_request = input("Enter payment request (BOLT11): ").strip()
                if not payment_request:
                    print("❌ Payment request cannot be empty!")
                    continue
                result = client.pay_invoice(payment_request)
                print_json(result)
            
            elif command in ["7", "bot-sim"]:
                print_header("Bot Simulator")
                print("\nSelect bot mode:")
                print("  1. Compliance Test   - Check API compliance with llms.txt, robots.txt, and ToS")
                print("  2. Payment Bot       - Auto-generate image and pay invoice")
                print("  3. Cancel")
                print()

                bot_choice = input("Enter choice (1-3): ").strip()

                if bot_choice in ["1", "compliance"]:
                    print("\n🤖 Running compliance test...\n")
                    run_bot_simulator()
                elif bot_choice in ["2", "payment"]:
                    print()
                    run_payment_bot()
                elif bot_choice in ["3", "cancel"]:
                    continue
                else:
                    print("❌ Invalid choice. Please enter 1-3.")
            
            elif command in ["8", "test-rate", "test"]:
                test_rate_limiting()
            
            elif command in ["9", "exit", "quit"]:
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid command. Please enter 1-9.")
        
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
                    
                    # Show payment instructions
                    print(f"\n📝 Payment Instructions:")
                    print(f"1. Scan the QR code with your Lightning wallet")
                    print(f"2. Send {invoice['amount_sats']} sats")
                    print(f"3. Payment will be detected automatically")
                    
                    print(f"\n⏳ Polling for payment confirmation...")
                    
                    # Automatically poll for image after payment
                    payment_hash = invoice['payment_hash']
                    max_wait_time = 300  # 5 minutes max wait
                    poll_interval = 1  # Check every 1 second
                    elapsed = 0
                    
                    while elapsed < max_wait_time:
                        # Check status
                        status_result = client.get_image_status(payment_hash=payment_hash)
                        
                        if "error" in status_result:
                            print(f"\n❌ Error: {status_result['error']}")
                            break
                        
                        status = status_result.get("status")
                        
                        if status == "pending":
                            print(f"⏳ Payment pending... ({elapsed}s elapsed)", end='\r')
                            import time
                            time.sleep(poll_interval)
                            elapsed += poll_interval
                            continue
                        
                        elif status == "available":
                            print(f"\n✅ Image available! Retrieving...")
                            
                            # Now retrieve the actual image
                            result = client.retrieve_image(payment_hash=payment_hash)
                            
                            if "error" in result:
                                print(f"❌ Error retrieving image: {result['error']}")
                                break
                            
                            if result.get("status") == "success":
                                image_base64_list = result.get("image_base64", [])
                                
                                if image_base64_list and any(image_base64_list):
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
                                else:
                                    print(f"❌ No images in response")
                            else:
                                print(f"❌ Unexpected response: {result}")
                            break
                        
                        elif status == "expired":
                            print(f"\n❌ Image expired! Please generate a new image.")
                            break
                        
                        else:
                            print(f"\n❌ Unknown status: {status}")
                            break
                    
                    if elapsed >= max_wait_time:
                        print(f"\n⏱️  Timeout: Image not retrieved within {max_wait_time} seconds")
                        print(f"💡 Try again later with: python3 client.py retrieve {payment_hash}")
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
            max_wait_time = 30  # 30 seconds max wait (matches Lambda cache duration)
            poll_interval = 1  # Check every 1 second
            elapsed = 0
            
            print(f"⏳ Retrieving image for payment hash: {payment_hash[:16]}...")
            print(f"📱 Waiting for payment confirmation and image retrieval...")
            print(f"⏱️  This may take a few seconds...\n")
            
            while elapsed < max_wait_time:
                # First check status
                status_result = client.get_image_status(payment_hash=payment_hash)
                
                if "error" in status_result:
                    print(f"\n❌ Error: {status_result['error']}")
                    sys.exit(1)
                
                status = status_result.get("status")
                
                if status == "pending":
                    print(f"⏳ Payment pending... ({elapsed}s elapsed)", end='\r')
                    import time
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                    continue
                
                elif status == "available":
                    print(f"\n✅ Image available! Retrieving...")
                    
                    # Now retrieve the actual image
                    result = client.retrieve_image(payment_hash=payment_hash)
                    
                    if "error" in result:
                        print(f"❌ Error retrieving image: {result['error']}")
                        sys.exit(1)
                    
                    if result.get("status") == "success":
                        image_base64_list = result.get("image_base64", [])
                        
                        if image_base64_list and any(image_base64_list):
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
                            print(f"❌ No images in response")
                            sys.exit(1)
                    else:
                        print(f"❌ Unexpected response: {result}")
                        sys.exit(1)
                
                elif status == "expired":
                    print(f"\n❌ Image expired! Please generate a new image.")
                    sys.exit(1)
                
                else:
                    print(f"\n❌ Unknown status: {status}")
                    sys.exit(1)
            
            if elapsed >= max_wait_time:
                print(f"\n⏱️  Timeout: Image not retrieved within {max_wait_time} seconds")
                print(f"💡 Try again later with: python3 client.py retrieve {payment_hash}")
                sys.exit(1)
        
        elif sys.argv[1] == "status":
            if len(sys.argv) < 3:
                print("Usage: python client.py status <payment_hash>")
                sys.exit(1)
            
            payment_hash = sys.argv[2]
            print_header("Check Image Status")
            result = client.get_image_status(payment_hash)
            print_json(result)
        
        elif sys.argv[1] == "pay":
            if len(sys.argv) < 3:
                print("Usage: python client.py pay '<payment_request>'")
                sys.exit(1)
            
            payment_request = sys.argv[2]
            print_header("Pay Invoice")
            result = client.pay_invoice(payment_request)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                sys.exit(1)
            else:
                print(f"✅ {result.get('message', 'Payment sent!')}")
                print(f"📊 Payment details:")
                print_json(result.get('payment', {}))
        
        elif sys.argv[1] == "bot-sim":
            print_header("Bot Simulator (Mock Mode)")
            print("\n🤖 Running bot simulator...\n")
            run_bot_simulator()
        
        elif sys.argv[1] == "test-rate":
            test_rate_limiting()
        
        else:
            print("Usage: python client.py [health|models|generate '<prompt>' [num_outputs]|status <payment_hash>|retrieve <payment_hash>|pay '<payment_request>'|bot-sim|test-rate]")
            sys.exit(1)
    else:
        # Interactive mode
        main()
