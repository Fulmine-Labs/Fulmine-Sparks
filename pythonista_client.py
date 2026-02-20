#!/usr/bin/env python3
"""
Fulmine-Sparks Pythonista Client
iOS app for testing image generation and content filtering.
Run this in Pythonista on your iPhone.
"""

import requests
import json
import base64
import io
from datetime import datetime
import sys

# Try to import Pythonista-specific modules
try:
    import ui
    import photos
    import clipboard
    PYTHONISTA = True
except ImportError:
    PYTHONISTA = False
    print("⚠️  Not running in Pythonista. Some features will be limited.")

# Configuration
API_BASE_URL = "http://10.2.38.143:8000"  # Change this to your server IP
MODERATION_ENDPOINT = f"{API_BASE_URL}/api/v1/moderation/check"
GENERATE_ENDPOINT = f"{API_BASE_URL}/api/v1/services/image/generate"

class FulmineClient:
    """Client for Fulmine-Sparks API."""
    
    def __init__(self):
        self.api_base = API_BASE_URL
        self.last_response = None
        self.last_image = None
    
    def check_content(self, prompt, threshold=0.15):
        """Check if content is safe."""
        try:
            response = requests.post(
                MODERATION_ENDPOINT,
                json={
                    "prompt": prompt,
                    "threshold": threshold
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            return {
                "error": str(e),
                "is_safe": False,
                "score": 0,
                "reason": f"Error checking content: {str(e)}"
            }
    
    def generate_image(self, prompt, model="stable-diffusion", 
                      negative_prompt="", num_outputs=1):
        """Generate an image."""
        try:
            payload = {
                "prompt": prompt,
                "model": model,
                "num_outputs": num_outputs,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
            
            response = requests.post(
                GENERATE_ENDPOINT,
                json=payload,
                timeout=120  # Image generation can take time
            )
            response.raise_for_status()
            data = response.json()
            self.last_response = data
            
            # Extract base64 image if available
            if data.get('image_base64'):
                self.last_image = data['image_base64'][0]
            
            return data
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def decode_base64_image(self, base64_str):
        """Decode base64 image to PIL Image."""
        try:
            # Remove data URI prefix if present
            if base64_str.startswith("data:image/png;base64,"):
                base64_str = base64_str.replace("data:image/png;base64,", "")
            
            # Decode
            image_data = base64.b64decode(base64_str)
            return image_data
        except Exception as e:
            print(f"Error decoding image: {e}")
            return None


class FulmineUI(ui.View):
    """Pythonista UI for Fulmine-Sparks client."""
    
    def __init__(self):
        self.client = FulmineClient()
        self.selected_image = None
        
    def layout(self):
        """Layout the UI."""
        # Title
        title = ui.Label()
        title.text = "🎨 Fulmine-Sparks"
        title.font = ('<system-bold>', 24)
        title.text_color = '#667eea'
        title.frame = (10, 20, self.width - 20, 40)
        self.add_subview(title)
        
        # Subtitle
        subtitle = ui.Label()
        subtitle.text = "Image Generation & Content Filtering"
        subtitle.font = ('<system>', 12)
        subtitle.text_color = '#999'
        subtitle.frame = (10, 60, self.width - 20, 20)
        self.add_subview(subtitle)
        
        # Positive Prompt Label
        pos_label = ui.Label()
        pos_label.text = "Positive Prompt:"
        pos_label.font = ('<system-bold>', 14)
        pos_label.frame = (10, 90, 150, 20)
        self.add_subview(pos_label)
        
        # Positive Prompt Input
        self.positive_prompt = ui.TextField()
        self.positive_prompt.placeholder = "e.g., beautiful sunset over mountains"
        self.positive_prompt.frame = (10, 115, self.width - 20, 40)
        self.add_subview(self.positive_prompt)
        
        # Negative Prompt Label
        neg_label = ui.Label()
        neg_label.text = "Negative Prompt:"
        neg_label.font = ('<system-bold>', 14)
        neg_label.frame = (10, 160, 150, 20)
        self.add_subview(neg_label)
        
        # Negative Prompt Input
        self.negative_prompt = ui.TextField()
        self.negative_prompt.placeholder = "e.g., blurry, low quality"
        self.negative_prompt.frame = (10, 185, self.width - 20, 40)
        self.add_subview(self.negative_prompt)
        
        # Check Safety Button
        check_btn = ui.Button(title="🛡️ Check Safety")
        check_btn.frame = (10, 235, (self.width - 30) / 2, 40)
        check_btn.action = self.check_safety
        self.add_subview(check_btn)
        
        # Generate Button
        gen_btn = ui.Button(title="🎨 Generate Image")
        gen_btn.frame = ((self.width - 30) / 2 + 20, 235, (self.width - 30) / 2, 40)
        gen_btn.action = self.generate_image
        self.add_subview(gen_btn)
        
        # Status Label
        self.status = ui.Label()
        self.status.text = "Ready"
        self.status.font = ('<system>', 12)
        self.status.text_color = '#666'
        self.status.frame = (10, 285, self.width - 20, 20)
        self.add_subview(self.status)
        
        # Results Text View
        self.results = ui.TextView()
        self.results.frame = (10, 315, self.width - 20, 200)
        self.results.editable = False
        self.results.font = ('<monospace>', 10)
        self.add_subview(self.results)
        
        # Image Preview
        self.image_view = ui.ImageView()
        self.image_view.frame = (10, 525, self.width - 20, 200)
        self.image_view.content_mode = ui.CONTENT_MODE_ASPECT_FIT
        self.add_subview(self.image_view)
        
        # Save Image Button
        save_btn = ui.Button(title="💾 Save Image")
        save_btn.frame = (10, 735, self.width - 20, 40)
        save_btn.action = self.save_image
        self.add_subview(save_btn)
    
    def check_safety(self, sender):
        """Check if prompt is safe."""
        prompt = self.positive_prompt.text
        
        if not prompt:
            self.status.text = "❌ Please enter a prompt"
            return
        
        self.status.text = "🔍 Checking safety..."
        
        result = self.client.check_content(prompt)
        
        # Format result
        if "error" in result:
            output = f"❌ Error: {result['error']}"
        else:
            is_safe = result.get('is_safe', False)
            score = result.get('score', 0)
            reason = result.get('reason', '')
            
            status_icon = "✅" if is_safe else "❌"
            output = f"""{status_icon} Safety Check Result

Prompt: {prompt}

Safe: {is_safe}
Score: {score:.2f}
Reason: {reason}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.results.text = output
        self.status.text = "✅ Safety check complete"
    
    def generate_image(self, sender):
        """Generate an image."""
        prompt = self.positive_prompt.text
        
        if not prompt:
            self.status.text = "❌ Please enter a prompt"
            return
        
        # First check safety
        self.status.text = "🔍 Checking safety..."
        safety_result = self.client.check_content(prompt)
        
        if not safety_result.get('is_safe', False):
            reason = safety_result.get('reason', 'Content rejected')
            output = f"""❌ Prompt Rejected

Reason: {reason}

Please try a different prompt.
"""
            self.results.text = output
            self.status.text = "❌ Prompt rejected"
            return
        
        # Generate image
        self.status.text = "🎨 Generating image... (this may take 30-60 seconds)"
        result = self.client.generate_image(
            prompt=prompt,
            negative_prompt=self.negative_prompt.text
        )
        
        # Format result
        if "error" in result:
            output = f"❌ Error: {result['error']}"
            self.status.text = "❌ Generation failed"
        elif result.get('status') == 'completed':
            processing_time = result.get('processing_time', 0)
            output = f"""✅ Image Generated Successfully

Prompt: {prompt}
Negative Prompt: {self.negative_prompt.text or 'None'}

Processing Time: {processing_time:.1f}s
Status: {result['status']}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Display image if available
            if self.client.last_image:
                try:
                    image_data = self.client.decode_base64_image(self.client.last_image)
                    if image_data:
                        from PIL import Image
                        img = Image.open(io.BytesIO(image_data))
                        self.image_view.image = img
                except Exception as e:
                    output += f"\n⚠️ Could not display image: {e}"
            
            self.status.text = "✅ Image generated successfully"
        else:
            output = f"❌ Generation failed: {result.get('status', 'Unknown error')}"
            self.status.text = "❌ Generation failed"
        
        self.results.text = output
    
    def save_image(self, sender):
        """Save the generated image to Photos."""
        if not self.client.last_image:
            self.status.text = "❌ No image to save"
            return
        
        try:
            image_data = self.client.decode_base64_image(self.client.last_image)
            if not image_data:
                self.status.text = "❌ Could not decode image"
                return
            
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            
            # Save to Photos
            if PYTHONISTA:
                photos.save_image(img)
                self.status.text = "✅ Image saved to Photos"
            else:
                self.status.text = "⚠️ Not in Pythonista - cannot save to Photos"
        except Exception as e:
            self.status.text = f"❌ Error saving image: {e}"


def main():
    """Run the Pythonista client."""
    if PYTHONISTA:
        # Create and show UI
        v = FulmineUI()
        v.background_color = '#f5f5f5'
        v.name = "Fulmine-Sparks"
        
        # Create navigation controller
        nav = ui.NavigationView(v)
        nav.present('sheet')
    else:
        # Command-line mode for testing
        print("=" * 60)
        print("🎨 Fulmine-Sparks Client (CLI Mode)")
        print("=" * 60)
        
        client = FulmineClient()
        
        while True:
            print("\n1. Check Safety")
            print("2. Generate Image")
            print("3. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                prompt = input("Enter prompt: ").strip()
                if prompt:
                    print("\n🔍 Checking safety...")
                    result = client.check_content(prompt)
                    print(json.dumps(result, indent=2))
            
            elif choice == "2":
                prompt = input("Enter positive prompt: ").strip()
                if prompt:
                    print("\n🔍 Checking safety...")
                    safety = client.check_content(prompt)
                    
                    if not safety.get('is_safe', False):
                        print(f"❌ Rejected: {safety.get('reason')}")
                        continue
                    
                    print("🎨 Generating image...")
                    result = client.generate_image(prompt)
                    print(json.dumps(result, indent=2))
            
            elif choice == "3":
                print("Goodbye!")
                break


if __name__ == "__main__":
    main()
