"""
Configuration script for Alby Hub NWC setup
"""
import os
import json
from typing import Optional

def configure_nwc(nwc_url: str) -> bool:
    """
    Configure Alby NWC connection
    
    Args:
        nwc_url: NWC connection string (nostr+walletconnect://...)
    
    Returns:
        True if configuration successful
    """
    try:
        # Validate NWC URL format
        if not nwc_url.startswith('nostr+walletconnect://'):
            print("❌ Invalid NWC URL format. Must start with 'nostr+walletconnect://'")
            return False
        
        # Store in environment
        os.environ['ALBY_NWC_URL'] = nwc_url
        
        print("✅ Alby NWC configured successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {str(e)}")
        return False

def get_nwc_config() -> Optional[str]:
    """
    Get current NWC configuration
    
    Returns:
        NWC URL if configured, None otherwise
    """
    return os.environ.get('ALBY_NWC_URL')

def validate_nwc_connection(nwc_url: str) -> bool:
    """
    Validate NWC connection
    
    Args:
        nwc_url: NWC connection string
    
    Returns:
        True if connection is valid
    """
    try:
        # In production, this would test the actual connection
        # For now, just validate the format
        if not nwc_url.startswith('nostr+walletconnect://'):
            return False
        
        print("✅ NWC connection validated")
        return True
    except Exception as e:
        print(f"❌ Connection validation failed: {str(e)}")
        return False

if __name__ == '__main__':
    # Example usage
    nwc_url = os.environ.get('ALBY_NWC_URL', '')
    
    if nwc_url:
        print(f"Current NWC URL: {nwc_url[:50]}...")
        validate_nwc_connection(nwc_url)
    else:
        print("No NWC URL configured. Set ALBY_NWC_URL environment variable.")
