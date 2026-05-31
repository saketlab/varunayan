"""
Caching system for varunayan downloads.

This module provides functions for managing cached climate data downloads
to avoid redundant API calls.
"""

import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def get_cache_dir() -> Path:
    """
    Get the cache directory for varunayan.

    Uses platformdirs-style logic to find appropriate cache location:
    - Linux: ~/.cache/varunayan
    - macOS: ~/Library/Caches/varunayan
    - Windows: %LOCALAPPDATA%/varunayan/cache

    Returns:
        Path to the cache directory
    """
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        cache_dir = base / "varunayan" / "cache"
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():
            cache_dir = Path.home() / "Library" / "Caches" / "varunayan"
        else:
            xdg_cache = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
            cache_dir = Path(xdg_cache) / "varunayan"
    else:
        cache_dir = Path.home() / ".varunayan_cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _generate_cache_key(params: Dict[str, Any]) -> str:
    """Generate MD5 hash from request parameters."""
    params_str = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(params_str.encode()).hexdigest()


def _get_cache_metadata_path() -> Path:
    """Get path to cache metadata file."""
    return get_cache_dir() / "cache_metadata.json"


def _load_cache_metadata() -> Dict[str, Any]:
    """Load cache metadata from file."""
    metadata_path = _get_cache_metadata_path()
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            return json.load(f)
    return {}


def _save_cache_metadata(metadata: Dict[str, Any]) -> None:
    """Save cache metadata to file."""
    metadata_path = _get_cache_metadata_path()
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)


def _build_cache_params(
    variables: List[str],
    start_date: str,
    end_date: str,
    frequency: str,
    source: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build the canonical parameter dict used to derive a cache key."""
    return {
        "variables": sorted(variables),
        "start_date": start_date,
        "end_date": end_date,
        "frequency": frequency,
        "source": source,
        **kwargs,
    }


def _resolve_cache_entry(
    variables: List[str],
    start_date: str,
    end_date: str,
    frequency: str,
    source: str,
    **kwargs: Any,
) -> "tuple[Dict[str, Any], str, Any]":
    """Return (params, cache_key, cache_file) for the given request parameters."""
    params = _build_cache_params(
        variables, start_date, end_date, frequency, source, **kwargs
    )
    cache_key = _generate_cache_key(params)
    cache_file = get_cache_dir() / f"{cache_key}.parquet"
    return params, cache_key, cache_file


def cache_exists(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    frequency: str,
    source: str = "era5",
    **kwargs: Any,
) -> bool:
    """
    Check if cached data exists for the given parameters.

    Args:
        request_id: Original request identifier
        variables: List of variables requested
        start_date: Start date
        end_date: End date
        frequency: Temporal frequency
        source: Data source ('era5' or 'imd')
        **kwargs: Additional parameters (bounds, resolution, etc.)

    Returns:
        True if cache exists, False otherwise
    """
    _, _, cache_file = _resolve_cache_entry(
        variables, start_date, end_date, frequency, source, **kwargs
    )
    return cache_file.exists()


def get_cached_data(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    frequency: str,
    source: str = "era5",
    **kwargs: Any,
) -> Optional[pd.DataFrame]:
    """
    Retrieve cached data if it exists.

    Args:
        request_id: Original request identifier
        variables: List of variables requested
        start_date: Start date
        end_date: End date
        frequency: Temporal frequency
        source: Data source ('era5' or 'imd')
        **kwargs: Additional parameters

    Returns:
        DataFrame if cache exists, None otherwise
    """
    _, _, cache_file = _resolve_cache_entry(
        variables, start_date, end_date, frequency, source, **kwargs
    )

    if cache_file.exists():
        return pd.read_parquet(cache_file)
    return None


def save_to_cache(
    df: pd.DataFrame,
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    frequency: str,
    source: str = "era5",
    **kwargs: Any,
) -> str:
    """
    Save data to cache.

    Args:
        df: DataFrame to cache
        request_id: Original request identifier
        variables: List of variables requested
        start_date: Start date
        end_date: End date
        frequency: Temporal frequency
        source: Data source ('era5' or 'imd')
        **kwargs: Additional parameters

    Returns:
        Cache key (MD5 hash)
    """
    params, cache_key, cache_file = _resolve_cache_entry(
        variables, start_date, end_date, frequency, source, **kwargs
    )

    df.to_parquet(cache_file, index=False)

    metadata = _load_cache_metadata()
    metadata[cache_key] = {
        "request_id": request_id,
        "params": params,
        "created_at": datetime.now().isoformat(),
        "file_size_bytes": cache_file.stat().st_size,
        "n_rows": len(df),
        "n_cols": len(df.columns),
    }
    _save_cache_metadata(metadata)

    return cache_key


def show_cache_info() -> None:
    """
    Display information about the cache directory and its contents.
    """
    cache_dir = get_cache_dir()
    stats = cache_stats()

    print(f"\nCache Directory: {cache_dir}")
    print(f"{'='*60}")
    print(f"Total files:     {stats['n_files']}")
    print(f"Total size:      {stats['total_size_mb']:.2f} MB")
    print(f"ERA5 files:      {stats.get('era5_files', 0)}")
    print(f"IMD files:       {stats.get('imd_files', 0)}")

    if stats["oldest_cache"]:
        print(f"Oldest cache:    {stats['oldest_cache']}")
    if stats["newest_cache"]:
        print(f"Newest cache:    {stats['newest_cache']}")


def list_cache(source: str = "all") -> pd.DataFrame:
    """
    List all cached files with metadata.

    Args:
        source: Filter by source ('era5', 'imd', or 'all')

    Returns:
        DataFrame with cache entries
    """
    metadata = _load_cache_metadata()

    if not metadata:
        return pd.DataFrame(
            columns=[
                "cache_key",
                "request_id",
                "source",
                "start_date",
                "end_date",
                "created_at",
                "size_mb",
            ]
        )

    rows = []
    for cache_key, info in metadata.items():
        if source != "all" and info["params"].get("source", "era5") != source:
            continue

        rows.append(
            {
                "cache_key": cache_key[:12] + "...",
                "request_id": info["request_id"],
                "source": info["params"].get("source", "era5"),
                "start_date": info["params"]["start_date"],
                "end_date": info["params"]["end_date"],
                "frequency": info["params"]["frequency"],
                "created_at": info["created_at"][:10],
                "size_mb": info["file_size_bytes"] / (1024 * 1024),
                "n_rows": info.get("n_rows", 0),
            }
        )

    return pd.DataFrame(rows)


def cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the cache.

    Returns:
        Dictionary with cache statistics
    """
    cache_dir = get_cache_dir()
    metadata = _load_cache_metadata()

    parquet_files = list(cache_dir.glob("*.parquet"))
    total_size = sum(f.stat().st_size for f in parquet_files)

    era5_count = sum(
        1
        for info in metadata.values()
        if info["params"].get("source", "era5") == "era5"
    )
    imd_count = sum(
        1 for info in metadata.values() if info["params"].get("source") == "imd"
    )

    dates = [info["created_at"] for info in metadata.values()]
    oldest = min(dates) if dates else None
    newest = max(dates) if dates else None

    return {
        "n_files": len(parquet_files),
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "era5_files": era5_count,
        "imd_files": imd_count,
        "oldest_cache": oldest[:10] if oldest else None,
        "newest_cache": newest[:10] if newest else None,
    }


def clear_cache(
    source: str = "all",
    older_than_days: Optional[int] = None,
    confirm: bool = True,
) -> int:
    """
    Clear cached files.

    Args:
        source: Filter by source ('era5', 'imd', or 'all')
        older_than_days: Only delete files older than this many days
        confirm: If True, prompt for confirmation before deleting

    Returns:
        Number of files deleted
    """
    cache_dir = get_cache_dir()
    metadata = _load_cache_metadata()

    keys_to_delete = []
    now = datetime.now()

    for cache_key, info in metadata.items():
        if source != "all" and info["params"].get("source", "era5") != source:
            continue

        if older_than_days is not None:
            created = datetime.fromisoformat(info["created_at"])
            age_days = (now - created).days
            if age_days < older_than_days:
                continue

        keys_to_delete.append(cache_key)

    if not keys_to_delete:
        print("No cache files match the criteria.")
        return 0

    if confirm:
        print(f"\nAbout to delete {len(keys_to_delete)} cache file(s).")
        response = input("Continue? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return 0

    deleted_count = 0
    for cache_key in keys_to_delete:
        cache_file = cache_dir / f"{cache_key}.parquet"
        if cache_file.exists():
            cache_file.unlink()
            deleted_count += 1
        del metadata[cache_key]

    _save_cache_metadata(metadata)
    print(f"Deleted {deleted_count} cache file(s).")
    return deleted_count


def invalidate_cache(cache_key: str) -> bool:
    """
    Invalidate a specific cache entry.

    Args:
        cache_key: The cache key (or partial key) to invalidate

    Returns:
        True if cache was found and deleted, False otherwise
    """
    cache_dir = get_cache_dir()
    metadata = _load_cache_metadata()

    full_key = None
    for key in metadata.keys():
        if key.startswith(cache_key.replace("...", "")):
            full_key = key
            break

    if full_key is None:
        return False

    cache_file = cache_dir / f"{full_key}.parquet"
    if cache_file.exists():
        cache_file.unlink()

    del metadata[full_key]
    _save_cache_metadata(metadata)

    return True
