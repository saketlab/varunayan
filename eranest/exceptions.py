"""
Custom exceptions for the eranest package.

This module defines all custom exceptions used throughout the package
to provide clear error messages and proper error handling.
"""

from typing import Optional, Any


class EranestError(Exception):
    """Base exception for all eranest-related errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class DataDownloadError(EranestError):
    """Raised when data download fails."""
    pass


class DataProcessingError(EranestError):
    """Raised when data processing fails."""
    pass


class ValidationError(EranestError):
    """Raised when input validation fails."""
    pass


class FileFormatError(EranestError):
    """Raised when file format is invalid or unsupported."""
    pass


class GeospatialError(EranestError):
    """Raised when geospatial operations fail."""
    pass


class ConfigurationError(EranestError):
    """Raised when configuration is invalid."""
    pass


class CredentialsError(EranestError):
    """Raised when CDS API credentials are missing or invalid."""
    pass


class NetworkError(EranestError):
    """Raised when network operations fail."""
    pass


class AuroraError(EranestError):
    """Raised when Aurora-specific operations fail."""
    pass


class MemoryError(EranestError):
    """Raised when memory-related operations fail."""
    pass


class TimeoutError(EranestError):
    """Raised when operations timeout."""
    pass