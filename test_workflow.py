#!/usr/bin/env python3
"""
Test script to validate the Fulmine-Sparks workflow
Tests the complete flow: generate → status → retrieve
"""
import requests
import json
import time
import sys
from typing import Optional, Dict

class WorkflowTester:
    """Test the complete Fulmine-Sparks workflow"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
    
    def test(self, name: str, condition: bool, details: str = ""):
        """Record test result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results['tests'].append({
            'name': name,
            'status': status,
            'details': details
        })
        
        if condition:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        
        print(f"{status}: {name}")
        if details:
            print(f"       {details}")
    
    def test_generate(self, prompt: str = "A beautiful sunset") -> Optional[Dict]:
        """Test image generation endpoint"""
        print("\n📊 Testing: POST /api/v1/services/image/generate")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/services/image/generate",
                json={"prompt": prompt},
                timeout=30
            )
            
            self.test(
                "Generate endpoint returns 200",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.test(
                    "Response contains payment_hash",
                    'payment_hash' in data,
                    f"Keys: {list(data.keys())}"
                )
                
                self.test(
                    "Response contains invoice",
                    'invoice' in data,
                    f"Invoice: {data.get('invoice', 'N/A')[:30]}..."
                )
                
                self.test(
                    "Response contains amount_msats",
                    'amount_msats' in data,
                    f"Amount: {data.get('amount_msats')} msats"
                )
                
                self.test(
                    "Response contains prediction_id",
                    'prediction_id' in data,
                    f"Prediction ID: {data.get('prediction_id', 'N/A')[:30]}..."
                )
                
                # Check rate limit headers
                self.test(
                    "Response contains rate limit headers",
                    'X-RateLimit-Remaining' in response.headers,
                    f"Remaining: {response.headers.get('X-RateLimit-Remaining')}"
                )
                
                return data
            else:
                print(f"Response: {response.text}")
                return None
        
        except Exception as e:
            self.test("Generate endpoint accessible", False, str(e))
            return None
    
    def test_status(self, payment_hash: str) -> Optional[str]:
        """Test status endpoint"""
        print(f"\n📊 Testing: GET /api/v1/services/image/status/{payment_hash[:16]}...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/status/{payment_hash}",
                timeout=10
            )
            
            self.test(
                "Status endpoint returns 200 or 404",
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.test(
                    "Response contains payment_hash",
                    'payment_hash' in data,
                    f"Hash: {data.get('payment_hash', 'N/A')[:16]}..."
                )
                
                self.test(
                    "Response contains status",
                    'status' in data,
                    f"Status: {data.get('status')}"
                )
                
                status = data.get('status')
                self.test(
                    "Status is valid (pending/available/expired)",
                    status in ['pending', 'available', 'expired'],
                    f"Status: {status}"
                )
                
                return status
            elif response.status_code == 404:
                self.test("Status endpoint returns 404 for unknown hash", True)
                return None
            else:
                print(f"Response: {response.text}")
                return None
        
        except Exception as e:
            self.test("Status endpoint accessible", False, str(e))
            return None
    
    def test_retrieve(self, payment_hash: str) -> Optional[str]:
        """Test retrieve endpoint"""
        print(f"\n📊 Testing: GET /api/v1/services/image/retrieve/{payment_hash[:16]}...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/services/image/retrieve/{payment_hash}",
                timeout=10
            )
            
            self.test(
                "Retrieve endpoint returns 200, 402, or 404",
                response.status_code in [200, 402, 404],
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.test(
                    "Response contains image_base64",
                    'image_base64' in data,
                    f"Image size: {len(data.get('image_base64', ''))} bytes"
                )
                
                self.test(
                    "Response contains status",
                    'status' in data,
                    f"Status: {data.get('status')}"
                )
                
                return data.get('image_base64')
            
            elif response.status_code == 402:
                self.test("Retrieve returns 402 for unpaid invoice", True)
                return None
            
            elif response.status_code == 404:
                self.test("Retrieve returns 404 for unknown hash", True)
                return None
            
            else:
                print(f"Response: {response.text}")
                return None
        
        except Exception as e:
            self.test("Retrieve endpoint accessible", False, str(e))
            return None
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting"""
        print("\n📊 Testing: Rate Limiting")
        
        try:
            # Make requests up to the limit
            limit = 10
            for i in range(limit):
                response = self.session.post(
                    f"{self.base_url}/api/v1/services/image/generate",
                    json={"prompt": "Test"},
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.test(
                        f"Rate limit test: Request {i+1} succeeded",
                        False,
                        f"Status: {response.status_code}"
                    )
                    return False
            
            self.test(
                f"Rate limit test: Made {limit} requests successfully",
                True
            )
            
            # Try one more (should be rate limited)
            response = self.session.post(
                f"{self.base_url}/api/v1/services/image/generate",
                json={"prompt": "Test"},
                timeout=10
            )
            
            self.test(
                "Rate limit test: Request after limit returns 429",
                response.status_code == 429,
                f"Status: {response.status_code}"
            )
            
            return True
        
        except Exception as e:
            self.test("Rate limiting test", False, str(e))
            return False
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        print("\n📊 Testing: GET /health")
        
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            
            self.test(
                "Health endpoint returns 200",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test(
                    "Health endpoint returns status",
                    'status' in data,
                    f"Status: {data.get('status')}"
                )
                return True
            
            return False
        
        except Exception as e:
            self.test("Health endpoint accessible", False, str(e))
            return False
    
    def run_full_workflow(self) -> bool:
        """Run complete workflow test"""
        print("\n" + "="*60)
        print("🚀 FULMINE-SPARKS WORKFLOW TEST")
        print("="*60)
        
        # Test health
        if not self.test_health():
            print("\n❌ API is not accessible!")
            return False
        
        # Test generate
        generate_result = self.test_generate()
        if not generate_result:
            print("\n❌ Generate endpoint failed!")
            return False
        
        payment_hash = generate_result['payment_hash']
        
        # Test status
        status = self.test_status(payment_hash)
        
        # Test retrieve
        image = self.test_retrieve(payment_hash)
        
        # Print summary
        self.print_summary()
        
        return self.results['failed'] == 0
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for test in self.results['tests']:
            print(f"{test['status']}: {test['name']}")
            if test['details']:
                print(f"       {test['details']}")
        
        print("\n" + "="*60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Total:  {self.results['passed'] + self.results['failed']}")
        print("="*60)
        
        if self.results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.results['failed']} TEST(S) FAILED")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 test_workflow.py <api_endpoint>")
        print("\nExample:")
        print("  python3 test_workflow.py https://abc123.execute-api.us-east-2.amazonaws.com/prod")
        sys.exit(1)
    
    api_endpoint = sys.argv[1]
    
    # Remove trailing slash
    if api_endpoint.endswith('/'):
        api_endpoint = api_endpoint[:-1]
    
    print(f"Testing API: {api_endpoint}\n")
    
    tester = WorkflowTester(api_endpoint)
    success = tester.run_full_workflow()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
