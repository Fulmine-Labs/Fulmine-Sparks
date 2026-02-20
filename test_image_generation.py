#!/usr/bin/env python3
"""
Real image generation test using Replicate API.
Tests actual image generation with your Replicate API key.
"""

import sys
import os
import asyncio

# Load .env FIRST before importing anything from fulmine_spark
from dotenv import load_dotenv
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from fulmine_spark.services.image_generation import image_generation_service
from fulmine_spark.config import settings


async def test_image_generation():
    """Test real image generation with Replicate API."""
    print("\n" + "=" * 60)
    print("Testing Real Image Generation with Replicate API")
    print("=" * 60)
    
    # Check if API key is configured
    if not settings.replicate_api_key:
        print("\n❌ REPLICATE_API_TOKEN or REPLICATE_API_KEY not configured!")
        print("Please set REPLICATE_API_TOKEN in .env file")
        print("Get your key from: https://replicate.com/account/api-tokens")
        return False
    
    print("\n✓ Replicate API Key: Configured")
    print(f"✓ API Key (first 10 chars): {settings.replicate_api_key[:10]}...")
    
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
    print("Running Image Generation Tests")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}] {test_case['description']}")
        print(f"  Prompt: {test_case['prompt']}")
        print(f"  Model: {test_case['model']}")
        
        try:
            print("  Status: Generating...")
            
            # Generate image
            image_urls = await image_generation_service.generate_image(
                prompt=test_case['prompt'],
                model=test_case['model'],
                num_outputs=1,
                guidance_scale=7.5,
                num_inference_steps=50,
            )
            
            print(f"  ✓ SUCCESS!")
            print(f"  Generated {len(image_urls)} image(s)")
            
            for j, url in enumerate(image_urls, 1):
                print(f"    Image {j}: {url[:80]}...")
            
            results.append({
                "test": test_case['description'],
                "status": "PASS",
                "urls": image_urls
            })
            
        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            results.append({
                "test": test_case['description'],
                "status": "FAIL",
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL IMAGE GENERATION TESTS PASSED!")
        print("\nYour Fulmine-Sparks service is ready to generate images! 🎉")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        print("\nTroubleshooting:")
        print("1. Check your Replicate API key is valid")
        print("2. Verify your account has sufficient credit")
        print("3. Check Replicate API status: https://status.replicate.com")
        return False


async def main():
    """Run all tests."""
    try:
        success = await test_image_generation()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
