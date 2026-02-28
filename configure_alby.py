#!/usr/bin/env python3
"""
Configure Alby Hub NWC Connection for Fulmine-Sparks
This script helps set up the NWC connection string in AWS Lambda
"""

import os
import json
import subprocess
import sys

def get_lambda_function_name():
    """Get Lambda function name"""
    return "fulmine-sparks"

def set_lambda_env_variable(nwc_url):
    """Set environment variable in AWS Lambda"""
    function_name = get_lambda_function_name()
    
    print(f"\n🔧 Configuring AWS Lambda: {function_name}")
    print("=" * 80)
    
    try:
        # Get current configuration
        result = subprocess.run(
            ["aws", "lambda", "get-function-configuration", "--function-name", function_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ Error getting Lambda configuration:")
            print(result.stderr)
            return False
        
        current_config = json.loads(result.stdout)
        current_env = current_config.get("Environment", {}).get("Variables", {})
        
        # Add NWC URL to environment
        current_env["ALBY_NWC_URL"] = nwc_url
        
        # Update Lambda configuration
        result = subprocess.run(
            ["aws", "lambda", "update-function-configuration",
             "--function-name", function_name,
             "--environment", f"Variables={json.dumps(current_env)}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ Error updating Lambda configuration:")
            print(result.stderr)
            return False
        
        print(f"✅ Successfully set ALBY_NWC_URL in Lambda!")
        print(f"   Function: {function_name}")
        print(f"   NWC URL: {nwc_url[:50]}...")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ AWS CLI command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def create_local_env_file(nwc_url):
    """Create .env file for local testing"""
    env_content = f"""# Alby Hub NWC Connection String
ALBY_NWC_URL="{nwc_url}"

# Optional: Custom Bitcoin price (defaults to live fetch)
# BTC_PRICE_USD="67000"
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file for local testing")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {str(e)}")
        return False

def test_connection(nwc_url):
    """Test the NWC connection"""
    print(f"\n🧪 Testing NWC Connection")
    print("=" * 80)
    
    try:
        # Set environment variable
        os.environ["ALBY_NWC_URL"] = nwc_url
        
        # Import and test
        from billing import AlbyBillingClient, calculate_image_price
        
        # Test client initialization
        client = AlbyBillingClient(nwc_url=nwc_url)
        print("✅ Alby Hub NWC client initialized successfully!")
        
        # Test pricing calculation
        pricing = calculate_image_price(1)
        print(f"✅ Pricing calculation works!")
        print(f"   1 image: {pricing['total_sats']} sats (${pricing['your_price_usd']:.4f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing connection: {str(e)}")
        return False

def main():
    """Main configuration function"""
    print("\n" + "=" * 80)
    print("🔐 Fulmine-Sparks Alby Hub Configuration")
    print("=" * 80)
    
    nwc_url = "nostr+walletconnect://f5feb0e362845c4fbba44dc93175e2e3d96f32817bf4d5bd4bb71ec743d32074?relay=wss://relay.getalby.com/v1&secret=5bfe237e5b4370b1c88da7174ef5580b4f1bed91fe8f04d6146c83191dad2051&lud16=eporediese@getalby.com"
    
    print(f"\n📝 NWC Connection String:")
    print(f"   {nwc_url[:60]}...")
    
    # Test local connection
    if not test_connection(nwc_url):
        print("\n❌ Local connection test failed!")
        sys.exit(1)
    
    # Create local .env file
    print(f"\n💾 Creating local configuration")
    print("=" * 80)
    if not create_local_env_file(nwc_url):
        print("⚠️  Warning: Could not create .env file")
    
    # Set Lambda environment variable
    print(f"\n☁️  Configuring AWS Lambda")
    print("=" * 80)
    
    # Check if AWS CLI is available
    try:
        subprocess.run(["aws", "--version"], capture_output=True, timeout=5)
        if not set_lambda_env_variable(nwc_url):
            print("\n⚠️  Could not set Lambda environment variable")
            print("   You can set it manually in AWS Console:")
            print(f"   Key: ALBY_NWC_URL")
            print(f"   Value: {nwc_url}")
    except FileNotFoundError:
        print("⚠️  AWS CLI not found. You can set it manually in AWS Console:")
        print(f"   Key: ALBY_NWC_URL")
        print(f"   Value: {nwc_url}")
    
    print("\n" + "=" * 80)
    print("✅ Configuration Complete!")
    print("=" * 80)
    print("\n📋 Next Steps:")
    print("   1. Deploy updated zip file to Lambda")
    print("   2. Test with: python3 client.py generate 'test' 1")
    print("   3. Verify invoice appears in response")
    print("\n🔗 Resources:")
    print("   - Setup Guide: ALBY_SETUP.md")
    print("   - Billing Module: billing.py")
    print("   - GitHub: https://github.com/Fulmine-Labs/Fulmine-Sparks")
    print()

if __name__ == "__main__":
    main()
