#!/usr/bin/env python3
"""
Bitcoin Lightning Billing Module
Integrates with Alby Hub for invoice generation with 25% markup
"""

import requests
import os
from typing import Dict, Any, Optional
from datetime import datetime
import time


class BitcoinPriceFetcher:
    """Fetch real-time Bitcoin prices from multiple sources"""
    
    # Cache for price data (to avoid excessive API calls)
    _price_cache = {
        "price": None,
        "timestamp": 0,
        "cache_duration": 60  # Cache for 60 seconds
    }
    
    @staticmethod
    def get_btc_price_usd() -> float:
        """
        Get current Bitcoin price in USD
        
        Tries multiple sources in order:
        1. CoinGecko API (free, no auth required)
        2. Kraken API (free, no auth required)
        3. Coinbase API (free, no auth required)
        4. Fallback to cached price or default
        
        Returns:
            BTC price in USD
        """
        # Check cache first
        current_time = time.time()
        if (BitcoinPriceFetcher._price_cache["price"] is not None and 
            current_time - BitcoinPriceFetcher._price_cache["timestamp"] < 
            BitcoinPriceFetcher._price_cache["cache_duration"]):
            return BitcoinPriceFetcher._price_cache["price"]
        
        # Try CoinGecko API
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd"},
                timeout=5
            )
            response.raise_for_status()
            price = response.json()["bitcoin"]["usd"]
            BitcoinPriceFetcher._price_cache["price"] = price
            BitcoinPriceFetcher._price_cache["timestamp"] = current_time
            print(f"✅ BTC price from CoinGecko: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"⚠️  CoinGecko failed: {str(e)}")
        
        # Try Kraken API
        try:
            response = requests.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": "XBTUSDT"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            ticker_key = list(data["result"].keys())[0]
            price = float(data["result"][ticker_key]["c"][0])
            BitcoinPriceFetcher._price_cache["price"] = price
            BitcoinPriceFetcher._price_cache["timestamp"] = current_time
            print(f"✅ BTC price from Kraken: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"⚠️  Kraken failed: {str(e)}")
        
        # Try Coinbase API
        try:
            response = requests.get(
                "https://api.coinbase.com/v2/prices/BTC-USD/spot",
                timeout=5
            )
            response.raise_for_status()
            price = float(response.json()["data"]["amount"])
            BitcoinPriceFetcher._price_cache["price"] = price
            BitcoinPriceFetcher._price_cache["timestamp"] = current_time
            print(f"✅ BTC price from Coinbase: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"⚠️  Coinbase failed: {str(e)}")
        
        # Return cached price if available
        if BitcoinPriceFetcher._price_cache["price"] is not None:
            print(f"⚠️  Using cached BTC price: ${BitcoinPriceFetcher._price_cache['price']:,.2f}")
            return BitcoinPriceFetcher._price_cache["price"]
        
        # Fallback to default price
        default_price = 67000
        print(f"⚠️  Using fallback BTC price: ${default_price:,.2f}")
        return default_price
    
    @staticmethod
    def clear_cache():
        """Clear the price cache"""
        BitcoinPriceFetcher._price_cache["price"] = None
        BitcoinPriceFetcher._price_cache["timestamp"] = 0


class AlbyBillingClient:
    """Bitcoin Lightning billing client using Alby Hub NWC Connection String"""
    
    def __init__(self, nwc_url: str = None):
        """
        Initialize Alby billing client
        
        Args:
            nwc_url: Alby Hub NWC Connection String (defaults to ALBY_NWC_URL env var)
                     Format: nostr+walletconnect://pubkey?relay=wss://...&secret=...
        """
        self.nwc_url = nwc_url or os.getenv('ALBY_NWC_URL')
        
        if not self.nwc_url:
            raise ValueError(
                "ALBY_NWC_URL environment variable not set.\n"
                "Get it from Alby Hub:\n"
                "1. Go to App Store\n"
                "2. Click 'Connect' or 'Add New App'\n"
                "3. Name it 'Fulmine-Sparks'\n"
                "4. Select: Create invoices + Look up Status of Invoices\n"
                "5. Copy the NWC Connection String"
            )
        
        # Parse NWC URL to extract components
        self._parse_nwc_url()
        print(f"✅ Alby Hub NWC client initialized")
    
    def _parse_nwc_url(self):
        """Parse NWC URL to extract relay and secret"""
        try:
            # Format: nostr+walletconnect://pubkey?relay=wss://...&secret=...
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(self.nwc_url)
            query_params = parse_qs(parsed.query)
            
            self.relay = query_params.get('relay', ['wss://relay.getalby.com/v1'])[0]
            self.secret = query_params.get('secret', [''])[0]
            self.pubkey = parsed.netloc
            
            if not self.secret:
                raise ValueError("No secret found in NWC URL")
                
        except Exception as e:
            print(f"Warning: Could not parse NWC URL: {str(e)}")
            self.relay = 'wss://relay.getalby.com/v1'
            self.secret = ''
            self.pubkey = ''
    
    def create_invoice(
        self,
        amount_sats: int,
        description: str,
        metadata: Dict[str, Any] = None,
        expiry_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice via Alby Hub NWC
        
        Args:
            amount_sats: Amount in satoshis (whole number)
            description: Invoice description (included in BOLT11)
            metadata: Custom metadata to attach (not included in BOLT11)
            expiry_seconds: Invoice expiry time in seconds (default 1 hour)
        
        Returns:
            Invoice details including:
            - payment_request: BOLT11 invoice string
            - payment_hash: Payment hash
            - expires_at: Expiration timestamp
        """
        try:
            # Use Alby API to create REAL invoices
            from datetime import datetime, timedelta
            
            # Get API token from environment variable
            alby_token = os.getenv('ALBY_API_TOKEN')
            if not alby_token:
                return {"error": "ALBY_API_TOKEN environment variable not set"}
            
            print(f"🔄 Creating real invoice via Alby API...")
            
            headers = {
                "Authorization": f"Bearer {alby_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": int(amount_sats),
                "description": description,
                "expiry": expiry_seconds
            }
            
            response = requests.post(
                "https://api.getalby.com/invoices",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                invoice_data = response.json()
                print(f"✅ Real invoice created via Alby API")
                
                result = {
                    "payment_request": invoice_data.get('payment_request'),
                    "payment_hash": invoice_data.get('payment_hash'),
                    "expires_at": invoice_data.get('expires_at'),
                    "amount_sats": amount_sats,
                    "description": description,
                    "qr_code_png": invoice_data.get('qr_code_png'),
                    "qr_code_svg": invoice_data.get('qr_code_svg')
                }
                
                print(f"✅ Invoice created: {result.get('payment_hash', 'unknown')[:16]}...")
                return result
            else:
                error_msg = f"Alby API error: {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Failed to create invoice: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
    
    def get_invoice(self, payment_hash: str) -> Dict[str, Any]:
        """
        Get invoice details and status
        
        Args:
            payment_hash: Payment hash of the invoice
        
        Returns:
            Invoice details including settled status
        """
        try:
            response = requests.get(
                f"{self.base_url}/invoices/{payment_hash}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def check_payment(self, payment_hash: str) -> bool:
        """
        Check if invoice has been paid
        
        Args:
            payment_hash: Payment hash of the invoice
        
        Returns:
            True if invoice is settled, False otherwise
        """
        invoice = self.get_invoice(payment_hash)
        if "error" in invoice:
            return False
        return invoice.get("settled", False)
    
    def list_invoices(self, limit: int = 10) -> Dict[str, Any]:
        """
        List recent incoming invoices
        
        Args:
            limit: Number of invoices to return
        
        Returns:
            List of invoices
        """
        try:
            response = requests.get(
                f"{self.base_url}/invoices/incoming",
                headers=self.headers,
                params={"items": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


def calculate_image_price(num_images: int = 1, btc_price_usd: float = None) -> Dict[str, Any]:
    """
    Calculate price for image generation with 25% markup on Replicate cost
    
    Replicate: $0.04 per image
    Markup: 25%
    Your Price: $0.05 per image
    
    Args:
        num_images: Number of images
        btc_price_usd: Current BTC/USD price (optional, fetches real-time if not provided)
    
    Returns:
        Pricing breakdown including satoshi amount
    """
    # Fixed costs
    replicate_cost_usd = 0.04  # Replicate charges $0.04 per image
    markup_multiplier = 1.25   # 25% markup
    your_price_usd = replicate_cost_usd * markup_multiplier
    
    # Calculate totals
    replicate_total_usd = replicate_cost_usd * num_images
    your_total_usd = your_price_usd * num_images
    
    # Get real-time BTC price if not provided
    if btc_price_usd is None:
        btc_price_usd = BitcoinPriceFetcher.get_btc_price_usd()
    
    # 1 BTC = 100,000,000 sats
    total_sats = int((your_total_usd / btc_price_usd) * 100_000_000)
    
    # Ensure minimum 1 sat
    if total_sats < 1:
        total_sats = 1
    
    return {
        "num_images": num_images,
        "replicate_cost_usd": round(replicate_total_usd, 4),
        "your_price_usd": round(your_total_usd, 4),
        "total_sats": total_sats,
        "markup_percent": 25,
        "btc_price_usd": btc_price_usd,
        "timestamp": datetime.now().isoformat()
    }


def format_invoice_display(invoice: Dict[str, Any], pricing: Dict[str, Any]) -> str:
    """
    Format invoice for display
    
    Args:
        invoice: Invoice from Alby API
        pricing: Pricing information
    
    Returns:
        Formatted string for display
    """
    if "error" in invoice:
        return f"❌ Error creating invoice: {invoice['error']}"
    
    payment_request = invoice.get("payment_request", "")
    payment_hash = invoice.get("payment_hash", "")
    expires_at = invoice.get("expires_at", "")
    
    display = f"""
💰 Payment Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount:        {pricing['total_sats']:,} sats (${pricing['your_price_usd']:.4f})
Images:        {pricing['num_images']}
Markup:        {pricing['markup_percent']}% on Replicate cost
Expires:       {expires_at}

⚡ Lightning Invoice (BOLT11)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{payment_request}

📱 Scan QR code or paste invoice into your Lightning wallet
Payment Hash: {payment_hash[:16]}...
"""
    return display


def verify_payment(payment_hash: str, api_token: str = None) -> bool:
    """
    Verify if a payment has been received
    
    Args:
        payment_hash: Payment hash to verify
        api_token: Alby API token (defaults to env var)
    
    Returns:
        True if payment received, False otherwise
    """
    try:
        client = AlbyBillingClient(api_token=api_token)
        return client.check_payment(payment_hash)
    except Exception as e:
        print(f"❌ Error verifying payment: {str(e)}")
        return False
