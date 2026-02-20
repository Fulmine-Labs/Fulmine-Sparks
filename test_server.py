#!/usr/bin/env python3
"""
Simple test server for Fulmine-Sparks API.
Perfect for testing the Pythonista client.
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from fulmine_spark.services.image_generation import image_generation_service
from fulmine_spark.services.moderation import moderation_service
from fulmine_spark.config import settings

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not installed. Installing...")
    os.system("pip install flask")
    from flask import Flask, request, jsonify

app = Flask(__name__)

# Enable CORS for testing
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    print("⚠️  Flask-CORS not installed. Installing...")
    os.system("pip install flask-cors")
    from flask_cors import CORS
    CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Fulmine-Sparks Test Server",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/moderation/check', methods=['POST'])
def check_moderation():
    """Check if content is safe."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        threshold = data.get('threshold', 0.15)
        
        if not prompt:
            return jsonify({
                "error": "No prompt provided",
                "is_safe": False
            }), 400
        
        print(f"\n🔍 Checking moderation for: {prompt}")
        
        # Check content
        is_safe, score, reason = asyncio.run(
            moderation_service.check_content(prompt, threshold)
        )
        
        result = {
            "prompt": prompt,
            "is_safe": is_safe,
            "score": score,
            "reason": reason,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Result: safe={is_safe}, score={score:.2f}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "is_safe": False
        }), 500

@app.route('/api/v1/services/image/generate', methods=['POST'])
def generate_image():
    """Generate an image."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        model = data.get('model', 'stable-diffusion')
        num_outputs = data.get('num_outputs', 1)
        guidance_scale = data.get('guidance_scale', 7.5)
        num_inference_steps = data.get('num_inference_steps', 50)
        
        if not prompt:
            return jsonify({
                "error": "No prompt provided",
                "status": "failed"
            }), 400
        
        print(f"\n🎨 Generating image for: {prompt}")
        
        # Check safety first
        is_safe, score, reason = asyncio.run(
            moderation_service.check_content(prompt)
        )
        
        if not is_safe:
            print(f"❌ Prompt rejected: {reason}")
            return jsonify({
                "status": "rejected",
                "reason": reason,
                "score": score,
                "prompt": prompt
            }), 400
        
        # Generate image
        import time
        start_time = time.time()
        
        image_urls, image_base64 = asyncio.run(
            image_generation_service.generate_image(
                prompt=prompt,
                model=model,
                num_outputs=num_outputs,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                return_base64=True
            )
        )
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "completed",
            "prompt": prompt,
            "model": model,
            "image_urls": image_urls,
            "image_base64": image_base64,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Image generated in {processing_time:.1f}s")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "failed"
        }), 500

@app.route('/api/v1/services/image/models', methods=['GET'])
def list_models():
    """List available models."""
    try:
        models = image_generation_service.get_available_models()
        return jsonify({
            "models": models,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        "service": "Fulmine-Sparks Test Server",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /api/v1/moderation/check": "Check if content is safe",
            "POST /api/v1/services/image/generate": "Generate an image",
            "GET /api/v1/services/image/models": "List available models"
        },
        "documentation": "https://github.com/Fulmine-Labs/Fulmine-Sparks"
    })

def main():
    """Run the test server."""
    import asyncio
    global asyncio
    
    print("=" * 60)
    print("🎨 Fulmine-Sparks Test Server")
    print("=" * 60)
    print("\n✅ Starting server...")
    print("✅ Endpoints:")
    print("   GET  /health")
    print("   POST /api/v1/moderation/check")
    print("   POST /api/v1/services/image/generate")
    print("   GET  /api/v1/services/image/models")
    print("\n")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,
        use_reloader=False
    )

if __name__ == "__main__":
    import asyncio
    main()
