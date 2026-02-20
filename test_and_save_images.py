#!/usr/bin/env python3
"""
Generate images and save them locally as PNG files.
"""

import sys
import os
import asyncio
import json
import base64
from pathlib import Path

# Load .env FIRST before importing anything from fulmine_spark
from dotenv import load_dotenv
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from fulmine_spark.services.image_generation import image_generation_service
from fulmine_spark.config import settings


async def test_and_save_images():
    """Generate images and save them locally."""
    print("\n" + "=" * 60)
    print("Testing Image Generation and Saving Base64 Images")
    print("=" * 60)
    
    # Check if API key is configured
    if not settings.replicate_api_key:
        print("\n❌ REPLICATE_API_TOKEN or REPLICATE_API_KEY not configured!")
        return False
    
    print("\n✓ Replicate API Key: Configured")
    
    # Create output directory
    output_dir = Path("generated_images")
    output_dir.mkdir(exist_ok=True)
    
    # Test prompts
    test_cases = [
        {
            "prompt": "a beautiful sunset over mountains",
            "model": "stable-diffusion",
            "description": "Sunset landscape"
        },
        {
            "prompt": "a cute cat playing with a ball",
            "model": "stable-diffusion",
            "description": "Cat playing"
        },
        {
            "prompt": "a futuristic city skyline at night",
            "model": "stable-diffusion",
            "description": "Futuristic city"
        },
    ]
    
    print("\n" + "=" * 60)
    print("Generating and Saving Images")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['description']}")
        print(f"  Prompt: {test_case['prompt']}")
        
        try:
            print("  Status: Generating...")
            
            # Generate image
            image_urls, image_base64 = await image_generation_service.generate_image(
                prompt=test_case['prompt'],
                model=test_case['model'],
                num_outputs=1,
                guidance_scale=7.5,
                num_inference_steps=50,
                return_base64=True,
            )
            
            print(f"  ✓ Generated successfully!")
            
            # Save base64 images
            for j, b64 in enumerate(image_base64, 1):
                if b64:
                    # Remove data URI prefix if present
                    if b64.startswith("data:image/png;base64,"):
                        b64_data = b64.replace("data:image/png;base64,", "")
                    else:
                        b64_data = b64
                    
                    # Decode and save
                    try:
                        image_data = base64.b64decode(b64_data)
                        filename = output_dir / f"image_{i}_{j}.png"
                        
                        with open(filename, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"  ✓ Saved: {filename} ({len(image_data)} bytes)")
                        
                        results.append({
                            "test": test_case['description'],
                            "status": "PASS",
                            "file": str(filename),
                            "size": len(image_data)
                        })
                    except Exception as e:
                        print(f"  ✗ Failed to save: {str(e)}")
                        results.append({
                            "test": test_case['description'],
                            "status": "FAIL",
                            "error": str(e)
                        })
        
        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            results.append({
                "test": test_case['description'],
                "status": "FAIL",
                "error": str(e)
            })
        
        # Wait between requests
        if i < len(test_cases):
            print(f"\n  Waiting 10 seconds before next request...")
            for remaining in range(10, 0, -1):
                print(f"    {remaining}s remaining...", end='\r')
                await asyncio.sleep(1)
            print("                    ")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL IMAGES GENERATED AND SAVED!")
        print(f"\nImages saved to: {output_dir.absolute()}")
        print("\nGenerated files:")
        for result in results:
            if 'file' in result:
                print(f"  - {result['file']}")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


async def main():
    """Run all tests."""
    try:
        success = await test_and_save_images()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
