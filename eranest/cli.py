"""
Optimized command-line interface for eranest.

This module provides a comprehensive CLI with improved error handling,
progress monitoring, and support for all package features.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .aurora import create_aurora_batch
from .constants import (
    AURORA_PRESSURE_LEVELS,
    DEFAULT_ATMOSPHERIC_VARIABLES,
    DEFAULT_STATIC_VARIABLES,
    DEFAULT_SURFACE_VARIABLES,
    DataFrequency,
)

# Import optimized modules
from .download import (
    download_atmospheric_data,
    download_static_data,
    download_surface_data,
)
from .exceptions import DataDownloadError, EranestError, ValidationError
from .processing import aggregate_temporal_data, process_netcdf_dataset
from .spatial import filter_by_geometry
from .utils import load_json_file, validate_date_range, validate_geojson

# Set up logging
logger = logging.getLogger(__name__)


class CLIError(Exception):
    """CLI-specific error."""

    pass


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Set up logging configuration."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise CLIError(
            f"Invalid date format '{date_str}'. Use YYYY-MM-DD format."
        ) from e


def parse_variable_list(variables_str: str) -> List[str]:
    """Parse comma-separated variable list."""
    if not variables_str:
        return []
    return [var.strip() for var in variables_str.split(",") if var.strip()]


def parse_pressure_levels(levels_str: str) -> List[str]:
    """Parse comma-separated pressure levels."""
    if not levels_str:
        return AURORA_PRESSURE_LEVELS
    return [level.strip() for level in levels_str.split(",") if level.strip()]


def validate_output_directory(output_dir: str) -> Path:
    """Validate and create output directory."""
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        raise CLIError(f"Cannot create output directory '{output_dir}': {e}") from e


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser."""
    parser.add_argument("--request-id", required=True, help="Unique request identifier")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--freq",
        default="hourly",
        choices=["hourly", "daily", "weekly", "monthly", "yearly"],
        help="Data frequency (default: hourly)",
    )
    parser.add_argument(
        "--res",
        type=float,
        default=0.25,
        help="Grid resolution in degrees (default: 0.25)",
    )
    parser.add_argument(
        "--output-dir", help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel processing"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers (default: 4)",
    )


def cmd_surface(args: argparse.Namespace) -> None:
    """Handle surface data download command."""
    logger.info("🌡️  Starting surface data download...")

    try:
        # Parse arguments
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
        variables = (
            parse_variable_list(args.variables)
            if args.variables
            else DEFAULT_SURFACE_VARIABLES
        )

        # Validate dates
        validate_date_range(start_date, end_date)

        # Validate geometry if provided
        geometry = None
        if hasattr(args, "geojson") and args.geojson:
            geojson_data = load_json_file(args.geojson)
            if not validate_geojson(geojson_data, strict=False):
                logger.warning("GeoJSON validation failed, proceeding anyway")
            geometry = geojson_data

        # Set spatial bounds
        if hasattr(args, "north"):
            # Bounding box mode
            north, south, east, west = args.north, args.south, args.east, args.west
        else:
            # Default global bounds
            north, south, east, west = 90.0, -90.0, 180.0, -180.0

        # Download data
        output_file = download_surface_data(
            request_id=args.request_id,
            variables=variables,
            start_date=start_date,
            end_date=end_date,
            north=north,
            west=west,
            south=south,
            east=east,
            frequency=DataFrequency(args.freq.lower()),
            resolution=args.res,
            parallel_downloads=args.parallel,
            max_workers=args.max_workers,
        )

        logger.info(f"✅ Surface data downloaded: {output_file}")

        # Process data if geometry provided
        if geometry:
            logger.info("🔄 Processing data with spatial filtering...")
            result = process_netcdf_dataset(
                output_file,
                geometry=geometry,
                variables=variables,
            )
            logger.info(f"📊 Processed {len(result.processed_data)} records")

            # Save processed data
            if args.output_dir:
                output_dir = validate_output_directory(args.output_dir)
                csv_file = output_dir / f"{args.request_id}_surface_filtered.csv"
                result.processed_data.to_csv(csv_file, index=False)
                logger.info(f"💾 Filtered data saved: {csv_file}")

    except Exception as e:
        logger.error(f"❌ Surface data download failed: {e}")
        raise CLIError(f"Surface data download failed: {e}") from e


def cmd_atmospheric(args: argparse.Namespace) -> None:
    """Handle atmospheric data download command."""
    logger.info("🌪️  Starting atmospheric data download...")

    try:
        # Parse arguments
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
        variables = (
            parse_variable_list(args.variables)
            if args.variables
            else DEFAULT_ATMOSPHERIC_VARIABLES
        )
        pressure_levels = parse_pressure_levels(args.pressure_levels)

        # Validate dates
        validate_date_range(start_date, end_date)

        # Set spatial bounds
        if hasattr(args, "north"):
            north, south, east, west = args.north, args.south, args.east, args.west
        else:
            north, south, east, west = 90.0, -90.0, 180.0, -180.0

        # Download data
        output_file = download_atmospheric_data(
            request_id=args.request_id,
            variables=variables,
            start_date=start_date,
            end_date=end_date,
            north=north,
            west=west,
            south=south,
            east=east,
            pressure_levels=pressure_levels,
            frequency=DataFrequency(args.freq.lower()),
            resolution=args.res,
            parallel_downloads=args.parallel,
            max_workers=args.max_workers,
        )

        logger.info(f"✅ Atmospheric data downloaded: {output_file}")

    except Exception as e:
        logger.error(f"❌ Atmospheric data download failed: {e}")
        raise CLIError(f"Atmospheric data download failed: {e}") from e


def cmd_aurora(args: argparse.Namespace) -> None:
    """Handle Aurora-compatible data processing command."""
    logger.info("🤖 Starting Aurora data processing...")

    try:
        # Parse arguments
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)

        # Load geometry
        geojson_data = load_json_file(args.geojson)
        if not validate_geojson(geojson_data):
            raise ValidationError("Invalid GeoJSON file")

        # Parse variables
        surface_vars = (
            parse_variable_list(args.surface_vars)
            if args.surface_vars
            else DEFAULT_SURFACE_VARIABLES
        )
        atmospheric_vars = (
            parse_variable_list(args.atmospheric_vars)
            if args.atmospheric_vars
            else DEFAULT_ATMOSPHERIC_VARIABLES
        )
        static_vars = (
            parse_variable_list(args.static_vars)
            if args.static_vars
            else DEFAULT_STATIC_VARIABLES
        )
        pressure_levels = parse_pressure_levels(args.pressure_levels)

        # Download all required data
        downloads = []

        # Surface data
        logger.info("📥 Downloading surface data...")
        surface_file = download_surface_data(
            request_id=f"{args.request_id}_surface",
            variables=surface_vars,
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency(args.freq.lower()),
            resolution=args.res,
        )
        downloads.append(("surface", surface_file))

        # Atmospheric data
        logger.info("📥 Downloading atmospheric data...")
        atmospheric_file = download_atmospheric_data(
            request_id=f"{args.request_id}_atmospheric",
            variables=atmospheric_vars,
            start_date=start_date,
            end_date=end_date,
            pressure_levels=pressure_levels,
            frequency=DataFrequency(args.freq.lower()),
            resolution=args.res,
        )
        downloads.append(("atmospheric", atmospheric_file))

        # Static data (if requested)
        if args.include_static:
            logger.info("📥 Downloading static data...")
            static_file = download_static_data(
                request_id=f"{args.request_id}_static",
                variables=static_vars,
                resolution=args.res,
            )
            downloads.append(("static", static_file))

        # Process all data for Aurora
        logger.info("🔄 Processing data for Aurora compatibility...")

        # Load and filter each dataset
        processed_data = {}
        for data_type, file_path in downloads:
            logger.info(f"Processing {data_type} data...")
            result = process_netcdf_dataset(
                file_path,
                geometry=geojson_data,
                variables=(
                    surface_vars
                    if data_type == "surface"
                    else atmospheric_vars if data_type == "atmospheric" else static_vars
                ),
            )
            processed_data[data_type] = result.processed_data
            logger.info(f"✓ {data_type}: {len(result.processed_data)} records")

        # Create Aurora batch
        logger.info("🎯 Creating Aurora batch...")
        aurora_batch = create_aurora_batch(
            surface_data=processed_data.get("surface"),
            atmospheric_data=processed_data.get("atmospheric"),
            static_data=processed_data.get("static"),
        )

        logger.info("✅ Aurora batch created successfully!")
        logger.info(f"📊 Batch info: {type(aurora_batch)}")

        # Save results
        if args.output_dir:
            output_dir = validate_output_directory(args.output_dir)

            # Save individual datasets
            for data_type, df in processed_data.items():
                csv_file = output_dir / f"{args.request_id}_{data_type}_aurora.csv"
                df.to_csv(csv_file, index=False)
                logger.info(f"💾 {data_type} data saved: {csv_file}")

            # Save metadata
            metadata_file = output_dir / f"{args.request_id}_metadata.json"
            import json

            metadata = {
                "request_id": args.request_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "frequency": args.freq,
                "resolution": args.res,
                "surface_variables": surface_vars,
                "atmospheric_variables": atmospheric_vars,
                "static_variables": static_vars if args.include_static else [],
                "pressure_levels": pressure_levels,
                "records_count": {k: len(v) for k, v in processed_data.items()},
            }

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"📝 Metadata saved: {metadata_file}")

    except Exception as e:
        logger.error(f"❌ Aurora processing failed: {e}")
        raise CLIError(f"Aurora processing failed: {e}") from e


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description="eranest: Optimized ERA5 Climate Data Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download surface data for a region
  eranest surface --request-id my_request --start 2024-01-01 --end 2024-01-02 \\
                  --variables "2m_temperature,mean_sea_level_pressure" \\
                  --north 60 --south 40 --east 30 --west 10

  # Download atmospheric data
  eranest atmospheric --request-id my_request --start 2024-01-01 --end 2024-01-02 \\
                      --variables "temperature,u_component_of_wind" \\
                      --pressure-levels "850,925,1000"

  # Process data for Aurora model
  eranest aurora --request-id my_request --start 2024-01-01 --end 2024-01-02 \\
                 --geojson region.geojson --include-static

For more information, visit: https://github.com/JaggeryArray/eranest
        """,
    )

    # Global options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress all but error messages"
    )
    parser.add_argument("--version", action="version", version="eranest 1.0.0")

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # Surface data command
    surface_parser = subparsers.add_parser(
        "surface", help="Download surface-level data"
    )
    add_common_args(surface_parser)
    surface_parser.add_argument(
        "--variables",
        help=f"Comma-separated surface variables (default: {','.join(DEFAULT_SURFACE_VARIABLES)})",
    )

    # Add spatial options group
    spatial_group = surface_parser.add_mutually_exclusive_group(required=True)

    # Bounding box option
    bbox_group = spatial_group.add_argument_group("bounding_box")
    surface_parser.add_argument(
        "--north", type=float, help="Northern latitude boundary"
    )
    surface_parser.add_argument(
        "--south", type=float, help="Southern latitude boundary"
    )
    surface_parser.add_argument("--east", type=float, help="Eastern longitude boundary")
    surface_parser.add_argument("--west", type=float, help="Western longitude boundary")

    # GeoJSON option
    spatial_group.add_argument("--geojson", help="Path to GeoJSON file")

    surface_parser.set_defaults(func=cmd_surface)

    # Atmospheric data command
    atmos_parser = subparsers.add_parser(
        "atmospheric", help="Download atmospheric/pressure-level data"
    )
    add_common_args(atmos_parser)
    atmos_parser.add_argument(
        "--variables",
        help=f"Comma-separated atmospheric variables (default: {','.join(DEFAULT_ATMOSPHERIC_VARIABLES)})",
    )
    atmos_parser.add_argument(
        "--pressure-levels",
        help=f"Comma-separated pressure levels in hPa (default: {','.join(AURORA_PRESSURE_LEVELS)})",
    )
    atmos_parser.add_argument(
        "--north", type=float, default=90.0, help="Northern latitude boundary"
    )
    atmos_parser.add_argument(
        "--south", type=float, default=-90.0, help="Southern latitude boundary"
    )
    atmos_parser.add_argument(
        "--east", type=float, default=180.0, help="Eastern longitude boundary"
    )
    atmos_parser.add_argument(
        "--west", type=float, default=-180.0, help="Western longitude boundary"
    )
    atmos_parser.set_defaults(func=cmd_atmospheric)

    # Aurora processing command
    aurora_parser = subparsers.add_parser(
        "aurora", help="Process data for Aurora weather model"
    )
    add_common_args(aurora_parser)
    aurora_parser.add_argument("--geojson", required=True, help="Path to GeoJSON file")
    aurora_parser.add_argument(
        "--surface-vars",
        help=f"Comma-separated surface variables (default: {','.join(DEFAULT_SURFACE_VARIABLES)})",
    )
    aurora_parser.add_argument(
        "--atmospheric-vars",
        help=f"Comma-separated atmospheric variables (default: {','.join(DEFAULT_ATMOSPHERIC_VARIABLES)})",
    )
    aurora_parser.add_argument(
        "--static-vars",
        help=f"Comma-separated static variables (default: {','.join(DEFAULT_STATIC_VARIABLES)})",
    )
    aurora_parser.add_argument(
        "--pressure-levels",
        help=f"Comma-separated pressure levels in hPa (default: {','.join(AURORA_PRESSURE_LEVELS)})",
    )
    aurora_parser.add_argument(
        "--include-static",
        action="store_true",
        help="Include static variables (land-sea mask, soil type, etc.)",
    )
    aurora_parser.set_defaults(func=cmd_aurora)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose, args.quiet)

    try:
        # Validate required spatial arguments for surface command
        if args.command == "surface" and not args.geojson:
            if not all([args.north, args.south, args.east, args.west]):
                parser.error(
                    "surface command requires either --geojson or all of --north, --south, --east, --west"
                )

        # Execute the command
        logger.info(f"🚀 Starting eranest {args.command} command...")
        args.func(args)
        logger.info("🎉 Command completed successfully!")

    except CLIError as e:
        logger.error(f"CLI Error: {e}")
        sys.exit(1)
    except EranestError as e:
        logger.error(f"eranest Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
