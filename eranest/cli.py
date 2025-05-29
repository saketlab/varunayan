import argparse
import datetime as dt
from .core import era5ify_geojson
from .core import era5ify_bbox

def main():
    parser = argparse.ArgumentParser(description="ERA5ify your climate data.")
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest='mode', help='Processing mode')
    subparsers.required = True
    
    # Common arguments function
    def add_common_args(subparser):
        subparser.add_argument("--request-id", required=True, help="Unique request identifier")
        subparser.add_argument(
            "--variables", required=True, help="Comma-separated variable names"
        )
        subparser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
        subparser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
        subparser.add_argument(
            "--freq", default="hourly", help="Frequency (hourly, daily, weekly, monthly, yearly)"
        )
        subparser.add_argument(
            "--res", type=float, default=0.25, help="Grid resolution in degrees (default: 0.25)"
        )
    
    # GeoJSON/JSON file mode
    geojson_parser = subparsers.add_parser('geojson', help='Process using GeoJSON/JSON file')
    add_common_args(geojson_parser)
    geojson_parser.add_argument("--geojson", required=True, help="Path to GeoJSON or JSON file")
    
    # Bounding box mode
    bbox_parser = subparsers.add_parser('bbox', help='Process using bounding box coordinates')
    add_common_args(bbox_parser)
    bbox_parser.add_argument("--north", type=float, required=True, help="Northern latitude boundary")
    bbox_parser.add_argument("--south", type=float, required=True, help="Southern latitude boundary")
    bbox_parser.add_argument("--east", type=float, required=True, help="Eastern longitude boundary")
    bbox_parser.add_argument("--west", type=float, required=True, help="Western longitude boundary")
    
    args = parser.parse_args()
    
    # Parse common arguments
    try:
        start = dt.datetime.strptime(args.start, "%Y-%m-%d")
        end = dt.datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Please use YYYY-MM-DD format for dates")
        return
    
    variables = [v.strip() for v in args.variables.split(",")]
    
    # Process based on mode
    if args.mode == 'geojson':
        print("Processing with GeoJSON/JSON file...")
        df = era5ify_geojson(
            request_id=args.request_id,
            variables=variables,
            start_date=start,
            end_date=end,
            json_file=args.geojson,
            frequency=args.freq,
            resolution=args.res,
        )
    
    elif args.mode == 'bbox':
        print("Processing with bounding box coordinates...")
        df = era5ify_bbox(
            request_id=args.request_id,
            variables=variables,
            start_date=start,
            end_date=end,
            north=args.north,
            south=args.south,
            east=args.east,
            west=args.west,
            frequency=args.freq,
            resolution=args.res,
        )
    
    print("\nDone. Sample output:")
    print(df.head())


def main_legacy():
    """
    Legacy main function for backward compatibility.
    This maintains the old interface for existing scripts.
    """
    parser = argparse.ArgumentParser(description="ERA5ify your climate data.")

    parser.add_argument("--request-id", required=True)
    parser.add_argument(
        "--variables", required=True, help="Comma-separated variable names"
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--geojson", required=True, help="Path to GeoJSON or JSON file")
    parser.add_argument(
        "--freq", default="hourly", help="Frequency (hourly, daily, etc.)"
    )
    parser.add_argument(
        "--res", type=float, default=0.25, help="Grid resolution (default 0.25)"
    )

    args = parser.parse_args()

    start = dt.datetime.strptime(args.start, "%Y-%m-%d")
    end = dt.datetime.strptime(args.end, "%Y-%m-%d")
    variables = [v.strip() for v in args.variables.split(",")]

    df = era5ify_geojson(
        request_id=args.request_id,
        variables=variables,
        start_date=start,
        end_date=end,
        json_file=args.geojson,
        frequency=args.freq,
        resolution=args.res,
    )

    print("\nDone. Sample output:")
    print(df.head())


if __name__ == "__main__":
    main()