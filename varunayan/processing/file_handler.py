import logging
import os
import zipfile
from typing import List, Optional

from ..util.logging_utils import get_logger

logger = get_logger(level=logging.DEBUG)


def set_v_file_han(verbosity: int) -> None:

    if verbosity == 0:
        logger.setLevel(logging.WARNING)

    elif verbosity == 1:
        logger.setLevel(logging.INFO)

    elif verbosity == 2:
        logger.setLevel(logging.DEBUG)

    else:
        logger.setLevel(logging.WARNING)


def extract_download(
    zip_or_file_path: str, extract_dir: Optional[str] = None
) -> List[str]:
    """
    Extract downloaded file. Handles both single NC file and zip files.

    Args:
        zip_or_file_path: Path to the downloaded file
        extract_dir: Directory to extract to (optional)

    Returns:
        List of extracted file paths
    """
    # If no extract directory specified, create one based on filename
    if extract_dir is None:
        filename = os.path.basename(zip_or_file_path)
        filename_base = os.path.splitext(filename)[0]
        parent_dir = os.path.dirname(os.path.abspath(zip_or_file_path))
        if not parent_dir:
            parent_dir = "."
        extract_dir = os.path.join(parent_dir, filename_base)

    # Create extraction directory if it doesn't exist
    os.makedirs(extract_dir, exist_ok=True)

    # Determine file type
    if zip_or_file_path.lower().endswith(".zip"):
        # Zip file extraction
        logger.info(f"Extracting zip file: {zip_or_file_path}")
        with zipfile.ZipFile(zip_or_file_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
            extracted_files = [os.path.join(extract_dir, f) for f in extracted_files]
    elif zip_or_file_path.lower().endswith(".nc"):
        # Single NetCDF file - just copy to extraction directory
        logger.info(f"Copying NetCDF file: {zip_or_file_path}")
        import shutil

        dest_path = os.path.join(extract_dir, os.path.basename(zip_or_file_path))
        shutil.copy(zip_or_file_path, dest_path)
        extracted_files = [dest_path]
    else:
        raise ValueError(f"Unsupported file type: {zip_or_file_path}")

    # Find all NetCDF files in the extracted directory
    nc_files = find_netcdf_files(extract_dir)

    if not nc_files:
        logger.warning(f"Warning: No NetCDF files found in {zip_or_file_path}")
        logger.warning(f"Found files: {', '.join(extracted_files)}")
        return extracted_files

    logger.info("Extracted NetCDF files:")
    for file in nc_files:
        logger.info(f"  - {file}")

    return nc_files


def find_netcdf_files(extraction_dir: str) -> List[str]:
    """
    Find all NetCDF files in the extraction directory,
    including nested directories.

    Args:
        extraction_dir: Directory to search for NetCDF files

    Returns:
        List of full paths to NetCDF files
    """
    nc_files: List[str] = []
    for root, _, files in os.walk(extraction_dir):
        nc_files.extend(
            [os.path.join(root, file) for file in files if file.endswith(".nc")]
        )
    return nc_files
