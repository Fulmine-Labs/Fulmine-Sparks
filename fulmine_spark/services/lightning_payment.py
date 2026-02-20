"""
Lightning payment service using BTCPay Server.
Handles invoice creation and payment verification.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)


class LightningPaymentService:
    """Service for handling Lightning Network payments via BTCPay."""
    
    def __init__(self):
        """Initialize the payment service."""
        self.server_url = settings.BTCPAY_SERVER_URL
        self.api_key = settings.BTCPAY_API_KEY
        self.store_id = settings.BTCPAY_STORE_ID
        
        if not all([self.server_url, self.api_key, self.store_id]):
            logger.warning("BTCPay configuration incomplete. Payments will not work.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for BTCPay API requests."""
        return {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def create_invoice(
        self,
        amount: float,
        currency: str = "BTC",
        description: str = "",
        order_id: str = "",
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice via BTCPay.
        
        Args:
            amount: Amount in BTC
            currency: Currency code (default: BTC)
            description: Invoice description
            order_id: Order ID for tracking
            
        Returns:
            Invoice data including payment request (BOLT11)
            
        Raises:
            ValueError: If BTCPay is not configured
        """
        if not all([self.server_url, self.api_key, self.store_id]):
            raise ValueError("BTCPay Server not configured")
        
        try:
            url = f"{self.server_url}/api/v1/stores/{self.store_id}/invoices"
            
            payload = {
                "amount": str(amount),
                "currency": currency,
                "orderId": order_id,
                "itemDesc": description,
                "notificationURL": f"{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/api/v1/webhook/payment",
                "redirectURL": f"{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/api/v1/payment/success",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                
                invoice_data = response.json()
                logger.info(f"Created invoice: {invoice_data.get('id')}")
                
                return invoice_data
                
        except Exception as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            raise ValueError(f"Invoice creation failed: {str(e)}")
    
    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get invoice details from BTCPay.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice data
            
        Raises:
            ValueError: If BTCPay is not configured or invoice not found
        """
        if not all([self.server_url, self.api_key, self.store_id]):
            raise ValueError("BTCPay Server not configured")
        
        try:
            url = f"{self.server_url}/api/v1/stores/{self.store_id}/invoices/{invoice_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get invoice: {str(e)}")
            raise ValueError(f"Failed to retrieve invoice: {str(e)}")
    
    async def is_payment_confirmed(self, invoice_id: str) -> bool:
        """
        Check if a payment has been confirmed.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            True if payment is confirmed, False otherwise
        """
        try:
            invoice = await self.get_invoice(invoice_id)
            status = invoice.get("status", "").lower()
            
            # Payment is confirmed if status is "confirmed" or "complete"
            return status in ["confirmed", "complete", "paid"]
            
        except Exception as e:
            logger.error(f"Failed to check payment status: {str(e)}")
            return False
    
    @staticmethod
    def get_payment_request(invoice_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract BOLT11 payment request from invoice data.
        
        Args:
            invoice_data: Invoice data from BTCPay
            
        Returns:
            BOLT11 payment request string or None
        """
        # BTCPay returns payment request in different formats
        # Try common field names
        for field in ["paymentRequest", "payment_request", "bolt11"]:
            if field in invoice_data:
                return invoice_data[field]
        
        return None


# Global payment service instance
payment_service = LightningPaymentService()
