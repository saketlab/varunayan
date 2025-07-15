import os
import sys
import logging
from .util import get_logger

logger = get_logger(level=logging.INFO)

def check_cdsapi_config() -> bool:
    """
    Check if CDS API configuration exists and is valid.
    Returns True if configuration exists and is valid, False otherwise.
    """
    cds_file = os.path.expanduser("~/.cdsapirc")
    
    if not os.path.exists(cds_file):
        return False
    
    try:
        with open(cds_file, 'r') as f:
            content = f.read().strip()
        
        if not content:
            return False
        
        # Check for required lines
        has_url = False
        has_key = False
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('url:') and 'cds.climate.copernicus.eu' in line:
                has_url = True
            elif line.startswith('key:') and len(line.split(':', 1)[1].strip()) > 10:
                has_key = True
        
        return has_url and has_key
        
    except Exception:
        return False


def setup_cdsapi_config():
    """Interactive setup of CDS API configuration."""
    logger.info("\n=== CDS API Configuration Setup ===")
    logger.info("Get your API key from: https://cds.climate.copernicus.eu/profile")
    logger.info("\nSteps:")
    logger.info("1. Go to the URL above")
    logger.info("2. Log in to your account")
    logger.info("3. Click on your username (top right)")
    logger.info("4. Find 'API Token' section")
    logger.info("5. Copy your API key\n")
    
    try:
        api_key = input("\nEnter your CDS API key: ").strip()
        
        if not api_key:
            raise ValueError("No API key provided")
        
        _create_config_file(api_key)
        
    except KeyboardInterrupt:
        logger.error("\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def ensure_cdsapi_config():
    """
    Ensure CDS API configuration exists and is valid.
    If not, guide the user through setting it up.
    """
    if check_cdsapi_config():
        logger.info("✓ CDS API configuration is already set up and valid.")
        return
    
    logger.info("CDS API configuration not found or invalid.")
    
    try:
        setup_cdsapi_config()
        
        # Verify the configuration was created successfully
        if not check_cdsapi_config():
            raise RuntimeError("Configuration file was created but appears to be invalid")
            
    except KeyboardInterrupt:
        logger.error("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nError setting up CDS API configuration: {e}")
        logger.info("\nYou can manually create the configuration file:")
        logger.info("1. Create a file named '.cdsapirc' in your home directory")
        logger.info("2. Add these two lines:")
        logger.info("   url: https://cds.climate.copernicus.eu/api")
        logger.info("   key: YOUR_API_KEY_HERE")
        sys.exit(1)


def _create_config_file(api_key: str) -> None:
    """Create the CDS API configuration file."""
    config_path = os.path.expanduser("~/.cdsapirc")
    config_content = f"url: https://cds.climate.copernicus.eu/api\nkey: {api_key}"
    
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        logger.info(f"✓ Configuration file created at: {config_path}")
        logger.info("You can now use the CDS API!")
    except Exception as e:
        raise RuntimeError(f"Failed to create configuration file: {e}")
