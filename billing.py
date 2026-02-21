#!/usr/bin/env python3
"""
Bitcoin Lightning Billing Module
Integrates with Alby Hub for invoice generation with 25% markup
"""

import requests
import os
from typing import Dict, Any, Optional
from datetime import datetime


class AlbyBillingClient:
    """Bitcoin Lightning billing client using Alby Hub API"""
    
    def __init__(self, api_token: str = None, base_url: str = None):
        """
        Initialize Alby billing client
        
        Args:
            api_token: Alby API token (defaults to ALBY_API_TOKEN env var)
            base_url: Alby Hub base URL (defaults to ALBY_HUB_URL env var or https://api.getalby.com)
        """
        self.api_token = api_token or os.getenv('ALBY_API_TOKEN')
        self.base_url = base_url or os.getenv('ALBY_HUB_URL', 'https://api.getalby.com')
        
        if not self.api_token:
            raise ValueError("ALBY_API_TOKEN environment variable not set")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def create_invoice(
        self,
        amount_sats: int,
        description: str,
        metadata: Dict[str, Any] = None,
        expiry_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice
        
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
            - qr_code_png: QR code PNG URL
            - qr_code_svg: QR code SVG URL
        """
        payload = {
            "amount": int(amount_sats),
            "description": description,
            "currency": "btc"
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        try:
            response = requests.post(
                f"{self.base_url}/invoices",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Log successful invoice creation
            print(f"✅ Invoice created: {result.get('payment_hash', 'unknown')[:16]}...")
            
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to create invoice: {str(e)}"
            print(f"❌ {error_msg}")
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
        btc_price_usd: Current BTC/USD price (for satoshi conversion)
    
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
    
    # Convert to satoshis
    if btc_price_usd is None:
        btc_price_usd = 42000  # Default fallback price
    
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
