#!/usr/bin/env python3
"""
Decode base64 images from test output and save them locally.
"""

import base64
import re
import os
from pathlib import Path

def extract_base64_from_log(log_file):
    """Extract base64 images from test log."""
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find all base64 data URIs
    pattern = r'data:image/png;base64,([A-Za-z0-9+/=]+)'
    matches = re.findall(pattern, content)
    
    return matches

def save_images(base64_strings, output_dir='generated_images'):
    """Decode and save base64 images."""
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    saved_files = []
    
    for i, b64_string in enumerate(base64_strings, 1):
        try:
            # Decode base64
            image_data = base64.b64decode(b64_string)
            
            # Save to file
            filename = f"{output_dir}/generated_image_{i}.png"
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            saved_files.append(filename)
            print(f"✓ Saved: {filename} ({len(image_data)} bytes)")
            
        except Exception as e:
            print(f"✗ Failed to decode image {i}: {str(e)}")
    
    return saved_files

def main():
    """Main function."""
    log_file = 'test_output.log'
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return False
    
    print("=" * 60)
    print("Decoding Base64 Images from Test Output")
    print("=" * 60)
    
    # Extract base64 strings
    print("\nExtracting base64 images from log...")
    base64_strings = extract_base64_from_log(log_file)
    print(f"Found {len(base64_strings)} image(s)")
    
    if not base64_strings:
        print("❌ No base64 images found in log")
        return False
    
    # Save images
    print("\nDecoding and saving images...")
    saved_files = save_images(base64_strings)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\n✓ Successfully decoded {len(saved_files)} image(s)")
    print(f"\nSaved to:")
    for f in saved_files:
        print(f"  - {f}")
    
    print("\n✓ Images are ready to view!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
