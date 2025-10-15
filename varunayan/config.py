import logging
import os
import sys
from typing import Optional, Tuple

from .util import get_logger

logger = get_logger(level=logging.DEBUG)


def set_v_config(verbosity: int) -> None:

    if verbosity == 0:
        logger.setLevel(logging.WARNING)

    elif verbosity == 1:
        logger.setLevel(logging.INFO)

    elif verbosity == 2:
        logger.setLevel(logging.DEBUG)

    else:
        logger.setLevel(logging.WARNING)


def set_api_key(
    api_key: str,
    api_url: str = "https://cds.climate.copernicus.eu/api",
) -> None:
    """Programmatically set the CDS API key for the current session."""

    cleaned_key = api_key.strip() if api_key else ""
    cleaned_url = api_url.strip() if api_url else ""

    if not cleaned_key:
        raise ValueError("No API key provided")

    if not cleaned_url:
        raise ValueError("No API URL provided")

    _create_config_file(cleaned_key, cleaned_url)

    os.environ["CDS_API_KEY"] = cleaned_key
    os.environ["CDS_API_URL"] = cleaned_url


def check_cdsapi_config() -> bool:
    """
    Check if CDS API configuration exists and is valid.
    Returns True if configuration exists and is valid, False otherwise.
    """
    cds_file = os.path.expanduser("~/.cdsapirc")

    if not os.path.exists(cds_file):
        return False

    try:
        with open(cds_file, "r") as f:
            content = f.read().strip()

        if not content:
            return False

        # Check for required lines
        has_url = False
        has_key = False

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("url:") and "cds.climate.copernicus.eu" in line:
                has_url = True
            elif line.startswith("key:") and len(line.split(":", 1)[1].strip()) > 10:
                has_key = True

        return has_url and has_key

    except Exception:
        return False


def setup_cdsapi_config() -> None:
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
    except KeyboardInterrupt:
        raise
    except EOFError as exc:
        raise RuntimeError(
            "Input stream closed before a CDS API key was provided."
        ) from exc

    if not api_key:
        raise ValueError("No API key provided")

    _create_config_file(api_key)


def ensure_cdsapi_config() -> None:
    """
    Ensure CDS API configuration exists and is valid.
    If not, guide the user through setting it up.
    """
    # Check if we're in a testing, documentation build, or CI/CD environment
    if (
        "pytest" in sys.modules
        or os.environ.get("PYTEST_CURRENT_TEST")
        or "sphinx" in sys.modules
        or os.environ.get("READTHEDOCS")
        or os.environ.get("SPHINX_BUILD")
        or os.environ.get("GITHUB_ACTIONS")
        or os.environ.get("NETLIFY")
    ):
        logger.debug("CDS API configuration check skipped in test/docs/CI environment.")
        return

    env_credentials = _get_env_credentials()
    if env_credentials:
        api_url, api_key = env_credentials
        try:
            _create_config_file(api_key, api_url)
            logger.info("✓ CDS API configuration created from environment variable.")
            return
        except Exception as e:
            logger.error(f"Failed to create config from environment variable: {e}")
            # Fall through to normal flow

    if check_cdsapi_config():
        logger.info("✓ CDS API configuration is already set up and valid.")
        return

    logger.info("CDS API configuration not found or invalid.")

    if not sys.stdin:
        raise RuntimeError(
            "CDS API configuration is missing and interactive setup is unavailable. "
            "Set the CDS_API_KEY/CDSAPI_KEY environment variable or create ~/.cdsapirc manually."
        )

    try:
        if hasattr(sys.stdin, "isatty") and not sys.stdin.isatty():
            logger.warning(
                "Input stream is not a TTY; attempting to prompt for CDS API key anyway."
            )
    except Exception:
        pass

    try:
        setup_cdsapi_config()

        # Verify the configuration was created successfully
        if not check_cdsapi_config():
            raise RuntimeError(
                "Configuration file was created but appears to be invalid"
            )

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


def _get_env_credentials() -> Optional[Tuple[str, str]]:
    """Retrieve CDS API credentials from supported environment variables."""
    key_var_names = ("CDS_API_KEY", "CDSAPI_KEY")
    url_var_names = ("CDS_API_URL", "CDSAPI_URL")

    api_key: Optional[str] = None
    for var_name in key_var_names:
        value = os.environ.get(var_name)
        if value:
            api_key = value.strip()
            break

    if not api_key:
        return None

    api_url = "https://cds.climate.copernicus.eu/api"
    for var_name in url_var_names:
        value = os.environ.get(var_name)
        if value:
            api_url = value.strip()
            break

    return api_url, api_key


def _create_config_file(
    api_key: str, api_url: str = "https://cds.climate.copernicus.eu/api"
) -> None:
    """Create the CDS API configuration file."""
    config_path = os.path.expanduser("~/.cdsapirc")
    config_content = f"url: {api_url}\nkey: {api_key}"

    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        logger.info(f"✓ Configuration file created at: {config_path}")
        logger.info("You can now use the CDS API!")
    except Exception as e:
        raise RuntimeError(f"Failed to create configuration file: {e}")
