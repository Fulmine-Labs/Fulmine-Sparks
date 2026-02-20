#!/usr/bin/env python3
"""
Start ngrok tunnel for Fulmine-Sparks test server.
Makes the local server accessible from your iPhone.
"""

import time
import sys

try:
    from pyngrok import ngrok
except ImportError:
    print("Installing pyngrok...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
    from pyngrok import ngrok

def main():
    print("=" * 60)
    print("🌐 Starting ngrok tunnel...")
    print("=" * 60)
    
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(8000, "http")
        
        print(f"\n✅ Tunnel created!")
        print(f"\n🔗 Public URL: {public_url}")
        print(f"\n📱 Use this URL in your Pythonista client:")
        print(f"\n   API_BASE_URL = \"{public_url}\"")
        print(f"\n💡 Or update line 20 in pythonista_client.py to:")
        print(f"   API_BASE_URL = \"{public_url}\"")
        print(f"\n⏱️  Tunnel will stay open. Press Ctrl+C to stop.\n")
        
        # Keep tunnel open
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the test server is running: python test_server.py")
        print("2. Make sure port 8000 is not blocked")
        print("3. Try: pip install --upgrade pyngrok")
        sys.exit(1)

if __name__ == "__main__":
    main()
