#!/usr/bin/env python3
"""
Fulmine-Sparks Client - Test client for image generation API
"""
import requests
import json
import time
import sys
import qrcode
from io import StringIO
from typing import Optional, Dict

class FulmineClient:
    """Client for Fulmine-Sparks API"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize client
        
        Args:
            base_url: API base URL
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def generate_image(self, prompt: str) -> Optional[Dict]:
        """
        Generate an image
        
        Args:
            prompt: Image generation prompt
        
        Returns:
            Response dict with payment_hash and invoice
        """
        try:
            print(f"🎨 Generating image: {prompt}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/services/image/generate",
                json={"prompt": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Image generation started")
                print(f"   Payment Hash: {data['payment_hash'][:16]}...")
                print(f"   Prediction ID: {data['prediction_id'][:16]}...")
                return data
            elif response.status_code == 429:
                print(f"⛔ Rate limit exceeded")
                print(f"   Retry after: {response.json().get('retry_after')} seconds")
                return None
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def get_status(self, payment_hash: str) -> Optional[str]:
        """
        Get image status
        
        Args:
            payment_hash: Payment hash
        
        Returns:
            Status string (pending/available/expired)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/status/{payment_hash}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['status']
            elif response.status_code == 404:
                return None
            else:
                print(f"❌ Error getting status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def retrieve_image(self, payment_hash: str) -> Optional[str]:
        """
        Retrieve generated image
        
        Args:
            payment_hash: Payment hash
        
        Returns:
            Base64-encoded image
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/retrieve/{payment_hash}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['image_base64']
            elif response.status_code == 402:
                print("⚠️ Payment not confirmed yet")
                return None
            elif response.status_code == 404:
                print("❌ Image not found")
                return None
            else:
                print(f"❌ Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def poll_status(self, payment_hash: str, max_attempts: int = 10, interval: int = 1) -> Optional[str]:
        """
        Poll image status until available or timeout
        
        Args:
            payment_hash: Payment hash
            max_attempts: Maximum polling attempts
            interval: Polling interval in seconds
        
        Returns:
            Final status or None if timeout
        """
        print(f"\n📊 Polling status (max {max_attempts} attempts)...")
        
        for attempt in range(max_attempts):
            status = self.get_status(payment_hash)
            
            if status is None:
                print(f"   Attempt {attempt + 1}/{max_attempts}: ❌ Not found")
            else:
                print(f"   Attempt {attempt + 1}/{max_attempts}: {status}")
                
                if status == 'available':
                    print(f"✅ Image is ready!")
                    return status
                elif status == 'expired':
                    print(f"❌ Image expired")
                    return status
            
            if attempt < max_attempts - 1:
                time.sleep(interval)
        
        print(f"⏱️ Polling timeout")
        return None
    
    def display_qr_code(self, invoice: str):
        """
        Display QR code for invoice
        
        Args:
            invoice: Lightning invoice
        """
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(invoice)
            qr.make(fit=True)
            
            print("\n📱 QR Code for payment:")
            qr.print_ascii(invert=True)
        except Exception as e:
            print(f"⚠️ Could not display QR code: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <command> [args]")
        print("\nCommands:")
        print("  generate <prompt>     - Generate an image")
        print("  status <payment_hash> - Get image status")
        print("  retrieve <payment_hash> - Retrieve image")
        print("\nExample:")
        print("  python3 client.py generate 'A beautiful sunset'")
        sys.exit(1)
    
    command = sys.argv[1]
    client = FulmineClient()
    
    if command == 'generate':
        if len(sys.argv) < 3:
            print("❌ Prompt required")
            sys.exit(1)
        
        prompt = ' '.join(sys.argv[2:])
        result = client.generate_image(prompt)
        
        if result:
            print(f"\n💰 Invoice: {result['invoice'][:50]}...")
            print(f"💵 Amount: {result['amount_msats']} msats")
            
            # Display QR code
            client.display_qr_code(result['invoice'])
            
            # Poll status
            payment_hash = result['payment_hash']
            status = client.poll_status(payment_hash)
            
            if status == 'available':
                print("\n🖼️ Retrieving image...")
                image_base64 = client.retrieve_image(payment_hash)
                if image_base64:
                    print(f"✅ Image retrieved: {len(image_base64)} bytes")
    
    elif command == 'status':
        if len(sys.argv) < 3:
            print("❌ Payment hash required")
            sys.exit(1)
        
        payment_hash = sys.argv[2]
        status = client.get_status(payment_hash)
        
        if status:
            print(f"Status: {status}")
        else:
            print("❌ Could not get status")
    
    elif command == 'retrieve':
        if len(sys.argv) < 3:
            print("❌ Payment hash required")
            sys.exit(1)
        
        payment_hash = sys.argv[2]
        image_base64 = client.retrieve_image(payment_hash)
        
        if image_base64:
            print(f"✅ Image retrieved: {len(image_base64)} bytes")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
