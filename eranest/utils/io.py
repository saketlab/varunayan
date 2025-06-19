"""
Input/Output utilities for file operations.

This module provides efficient and robust file I/O operations
with proper error handling and format detection.
"""

import os
import json
import zipfile
import tempfile
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import pandas as pd
import xarray as xr

from ..constants import SUPPORTED_FILE_FORMATS, SUPPORTED_JSON_FORMATS, ERROR_MESSAGES
from ..exceptions import FileFormatError, DataProcessingError

logger = logging.getLogger(__name__)


def load_json_file(file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Load JSON file with automatic encoding detection.
    
    Args:
        file_path: Path to JSON file
        encoding: Initial encoding to try
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileFormatError: If file cannot be parsed as JSON
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(ERROR_MESSAGES["file_not_found"].format(path=file_path))
    
    # Try multiple encodings
    encodings = [encoding, "utf-8", "utf-16", "latin-1", "cp1252"]
    
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded JSON file with {enc} encoding")
                return data
        except UnicodeDecodeError:
            logger.debug(f"Failed to decode with {enc} encoding")
            continue
        except json.JSONDecodeError as e:
            raise FileFormatError(
                ERROR_MESSAGES["invalid_json"].format(path=file_path),
                details={"error": str(e), "encoding": enc}
            )
        except Exception as e:
            logger.warning(f"Unexpected error loading JSON with {enc}: {e}")
            continue
    
    raise FileFormatError(f"Could not load JSON file {file_path} with any encoding")


def save_json_file(
    data: Dict[str, Any], 
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    Save data to JSON file with proper formatting.
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
        ensure_ascii: Whether to ensure ASCII encoding
    """
    file_path = Path(file_path)
    
    # Create directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        logger.debug(f"Successfully saved JSON file: {file_path}")
    except Exception as e:
        raise DataProcessingError(f"Failed to save JSON file {file_path}: {e}")


def extract_archive(
    archive_path: Union[str, Path],
    extract_dir: Optional[Union[str, Path]] = None,
    file_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Extract archive file and return paths to extracted files.
    
    Args:
        archive_path: Path to archive file
        extract_dir: Directory to extract to (auto-generated if None)
        file_patterns: List of file patterns to extract (extract all if None)
        
    Returns:
        List of paths to extracted files
    """
    archive_path = Path(archive_path)
    
    if not archive_path.exists():
        raise FileNotFoundError(ERROR_MESSAGES["file_not_found"].format(path=archive_path))
    
    # Determine extract directory
    if extract_dir is None:
        extract_dir = archive_path.parent / archive_path.stem
    else:
        extract_dir = Path(extract_dir)
    
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    
    try:
        if archive_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                # Get list of files to extract
                if file_patterns:
                    files_to_extract = []
                    for pattern in file_patterns:
                        files_to_extract.extend([
                            name for name in zip_ref.namelist() 
                            if any(name.endswith(ext) for ext in file_patterns)
                        ])
                else:
                    files_to_extract = zip_ref.namelist()
                
                # Extract files
                for file_name in files_to_extract:
                    zip_ref.extract(file_name, extract_dir)
                    extracted_files.append(extract_dir / file_name)
        
        else:
            raise FileFormatError(f"Unsupported archive format: {archive_path.suffix}")
    
    except Exception as e:
        raise DataProcessingError(f"Failed to extract archive {archive_path}: {e}")
    
    logger.info(f"Extracted {len(extracted_files)} files from {archive_path}")
    return extracted_files


def find_files_by_pattern(
    directory: Union[str, Path],
    patterns: List[str],
    recursive: bool = True
) -> List[Path]:
    """
    Find files matching patterns in directory.
    
    Args:
        directory: Directory to search
        patterns: List of file patterns (e.g., ["*.nc", "*.grib"])
        recursive: Whether to search recursively
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(ERROR_MESSAGES["file_not_found"].format(path=directory))
    
    found_files = []
    
    for pattern in patterns:
        if recursive:
            found_files.extend(directory.rglob(pattern))
        else:
            found_files.extend(directory.glob(pattern))
    
    # Remove duplicates and sort
    unique_files = sorted(set(found_files))
    
    logger.debug(f"Found {len(unique_files)} files matching patterns {patterns}")
    return unique_files


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(ERROR_MESSAGES["file_not_found"].format(path=file_path))
    
    stat = file_path.stat()
    
    info = {
        "path": str(file_path.absolute()),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / (1024 * 1024),
        "modified": stat.st_mtime,
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
    }
    
    # Add format-specific information
    if file_path.suffix.lower() in SUPPORTED_JSON_FORMATS:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                info["json_type"] = data.get("type", "unknown")
                if "features" in data:
                    info["feature_count"] = len(data["features"])
        except Exception:
            info["json_valid"] = False
    
    return info


def create_temp_file(
    content: Union[str, bytes, Dict[str, Any]],
    suffix: str = ".tmp",
    prefix: str = "eranest_",
    delete: bool = False
) -> Path:
    """
    Create temporary file with content.
    
    Args:
        content: Content to write to file
        suffix: File suffix
        prefix: File prefix
        delete: Whether to auto-delete file
        
    Returns:
        Path to created temporary file
    """
    with tempfile.NamedTemporaryFile(
        mode="w" if isinstance(content, (str, dict)) else "wb",
        suffix=suffix,
        prefix=prefix,
        delete=delete
    ) as tmp_file:
        
        if isinstance(content, dict):
            json.dump(content, tmp_file, indent=2)
        else:
            tmp_file.write(content)
        
        tmp_file.flush()
        temp_path = Path(tmp_file.name)
    
    logger.debug(f"Created temporary file: {temp_path}")
    return temp_path


def safe_file_operation(operation: callable, *args, **kwargs) -> Any:
    """
    Execute file operation with error handling.
    
    Args:
        operation: File operation function to execute
        *args: Positional arguments for operation
        **kwargs: Keyword arguments for operation
        
    Returns:
        Result of operation
    """
    try:
        return operation(*args, **kwargs)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {e}")
    except OSError as e:
        raise DataProcessingError(f"File system error: {e}")
    except Exception as e:
        raise DataProcessingError(f"Unexpected file operation error: {e}")


def validate_file_format(file_path: Union[str, Path], expected_formats: List[str]) -> bool:
    """
    Validate file format against expected formats.
    
    Args:
        file_path: Path to file
        expected_formats: List of expected file extensions
        
    Returns:
        True if format is valid
    """
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()
    
    return file_ext in [fmt.lower() for fmt in expected_formats]


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object for directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def cleanup_temp_files(temp_dir: Union[str, Path], max_age_hours: float = 24) -> int:
    """
    Clean up old temporary files.
    
    Args:
        temp_dir: Temporary directory to clean
        max_age_hours: Maximum age of files to keep
        
    Returns:
        Number of files cleaned up
    """
    temp_dir = Path(temp_dir)
    
    if not temp_dir.exists():
        return 0
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_count = 0
    
    for file_path in temp_dir.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Cleaned up old temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")
    
    logger.info(f"Cleaned up {cleaned_count} temporary files")
    return cleaned_count


def load_netcdf_dataset(file_path: Union[str, Path], **kwargs) -> xr.Dataset:
    """
    Load NetCDF dataset with error handling.
    
    Args:
        file_path: Path to NetCDF file
        **kwargs: Additional arguments for xarray.open_dataset
        
    Returns:
        Loaded xarray Dataset
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(ERROR_MESSAGES["file_not_found"].format(path=file_path))
    
    if not validate_file_format(file_path, [".nc", ".nc4", ".netcdf"]):
        raise FileFormatError(f"Invalid NetCDF file format: {file_path.suffix}")
    
    try:
        dataset = xr.open_dataset(file_path, **kwargs)
        logger.debug(f"Successfully loaded NetCDF dataset: {file_path}")
        return dataset
    except Exception as e:
        raise DataProcessingError(f"Failed to load NetCDF dataset {file_path}: {e}")


def save_dataframe(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    format: str = "csv",
    **kwargs
) -> None:
    """
    Save DataFrame in specified format.
    
    Args:
        df: DataFrame to save
        file_path: Output file path
        format: Output format (csv, parquet, json)
        **kwargs: Additional arguments for save function
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if format.lower() == "csv":
            df.to_csv(file_path, index=False, **kwargs)
        elif format.lower() == "parquet":
            df.to_parquet(file_path, **kwargs)
        elif format.lower() == "json":
            df.to_json(file_path, **kwargs)
        else:
            raise FileFormatError(f"Unsupported output format: {format}")
        
        logger.info(f"Successfully saved DataFrame to {file_path}")
    except Exception as e:
        raise DataProcessingError(f"Failed to save DataFrame to {file_path}: {e}")