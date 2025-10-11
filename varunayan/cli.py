import argparse
import datetime as dt
import logging
from typing import List, Union

from .core import era5ify_bbox, era5ify_geojson, era5ify_point
from .util.logging_utils import get_logger

logger = get_logger(level=logging.DEBUG)


def parse_flexible_date(date_string: str) -> dt.datetime:
    """Parse date string in either YYYY-M-D or YYYY-MM-DD format"""
    try:
        # Try YYYY-MM-DD format first
        return dt.datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        try:
            # Try YYYY-M-D format
            return dt.datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            # If both fail, raise a more informative error
            raise ValueError(
                f"Date '{date_string}' must be in YYYY-MM-DD or YYYY-M-D format"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="ERA5ify your climate data.")

    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Processing mode")
    subparsers.required = True

    def str2bool(v: Union[str, bool]) -> bool:
        if isinstance(v, bool):
            return v
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    # Common arguments function
    def add_common_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--request-id", required=True, help="Unique request identifier"
        )
        subparser.add_argument(
            "--variables", required=True, help="Comma-separated variable names"
        )
        subparser.add_argument(
            "--start", required=True, help="Start date (YYYY-MM-DD or YYYY-M-D)"
        )
        subparser.add_argument(
            "--end", required=True, help="End date (YYYY-MM-DD or YYYY-M-D)"
        )
        subparser.add_argument(
            "--dataset-type",
            default="single",
            choices=["single", "pressure"],
            help="Type of dataset: single (single level) or pressure (pressure level) - default: single",
        )
        subparser.add_argument(
            "--pressure-levels",
            default="",
            help="Comma-separated pressure levels (e.g., '1000,925,850') - only used with pressure dataset type",
        )
        subparser.add_argument(
            "--freq",
            default="hourly",
            choices=["hourly", "daily", "weekly", "monthly", "yearly"],
            help="Frequency (hourly, daily, weekly, monthly, yearly) - default: hourly",
        )
        subparser.add_argument(
            "--res",
            type=float,
            default=0.25,
            help="Grid resolution in degrees (e.g., 0.1, 0.25) - default: 0.25",
        )
        subparser.add_argument(
            "--verbosity",
            type=int,
            choices=[0, 1, 2],
            default=0,
            help="Verbosity level: 0 (quiet), 1 (normal), 2 (verbose)",
        )
        subparser.add_argument(
            "--save-raw",
            type=str2bool,
            default=True,
            help="Option to save raw data, True by default. Pass it as False if raw data is not needed.",
        )

    # GeoJSON/JSON file mode
    geojson_parser = subparsers.add_parser(
        "geojson", help="Process using GeoJSON/JSON file"
    )
    add_common_args(geojson_parser)
    geojson_parser.add_argument(
        "--geojson", required=True, help="Path to GeoJSON or JSON file"
    )
    geojson_parser.add_argument(
        "--dist-features",
        help="Distinguishing feature name/s in GeoJSON (e.g., 'state' or 'region')",
    )

    # Bounding box mode
    bbox_parser = subparsers.add_parser(
        "bbox", help="Process using bounding box coordinates"
    )
    add_common_args(bbox_parser)
    bbox_parser.add_argument(
        "--north", type=float, required=True, help="Northern latitude boundary"
    )
    bbox_parser.add_argument(
        "--south", type=float, required=True, help="Southern latitude boundary"
    )
    bbox_parser.add_argument(
        "--east", type=float, required=True, help="Eastern longitude boundary"
    )
    bbox_parser.add_argument(
        "--west", type=float, required=True, help="Western longitude boundary"
    )

    # Point mode
    point_parser = subparsers.add_parser(
        "point", help="Process using a single point (lat, lon)"
    )
    add_common_args(point_parser)
    point_parser.add_argument(
        "--lat", type=float, required=True, help="Latitude of the point"
    )
    point_parser.add_argument(
        "--lon", type=float, required=True, help="Longitude of the point"
    )

    args = parser.parse_args()

    # Parse common arguments
    try:
        start = parse_flexible_date(args.start)
        end = parse_flexible_date(args.end)
        logger.debug(f"Parsed start date: {start}, end date: {end}")
    except ValueError as e:
        logger.error(f"Error parsing dates: {e}")
        return

    variables = [v.strip() for v in args.variables.split(",")]

    dist_features: List[str] = []
    if args.mode == "geojson" and args.dist_features and args.dist_features.strip():
        dist_features = [feat.strip() for feat in args.dist_features.split(",")]

    # Parse pressure levels if provided
    pressure_levels: List[str] = []
    if args.pressure_levels and args.pressure_levels.strip():
        pressure_levels = [level.strip() for level in args.pressure_levels.split(",")]

    # Process based on mode
    if args.mode == "geojson":
        logger.info("Processing with GeoJSON/JSON file...")
        era5ify_geojson(
            request_id=args.request_id,
            variables=variables,
            start_date=args.start,  # Pass as string to match function signature
            end_date=args.end,  # Pass as string to match function signature
            json_file=args.geojson,
            dist_features=dist_features,
            dataset_type=args.dataset_type,
            pressure_levels=pressure_levels,
            frequency=args.freq,
            resolution=args.res,
            verbosity=args.verbosity,
            save_raw=args.save_raw,
        )

    elif args.mode == "bbox":
        logger.info("Processing with bounding box coordinates...")
        era5ify_bbox(
            request_id=args.request_id,
            variables=variables,
            start_date=args.start,  # Pass as string to match function signature
            end_date=args.end,  # Pass as string to match function signature
            north=args.north,
            south=args.south,
            east=args.east,
            west=args.west,
            dataset_type=args.dataset_type,
            pressure_levels=pressure_levels,
            frequency=args.freq,
            resolution=args.res,
            verbosity=args.verbosity,
            save_raw=args.save_raw,
        )

    elif args.mode == "point":
        logger.info("Processing for a single point location...")
        era5ify_point(
            request_id=args.request_id,
            variables=variables,
            start_date=args.start,
            end_date=args.end,
            latitude=args.lat,
            longitude=args.lon,
            dataset_type=args.dataset_type,
            pressure_levels=pressure_levels,
            frequency=args.freq,
            verbosity=args.verbosity,
            save_raw=args.save_raw,
        )
