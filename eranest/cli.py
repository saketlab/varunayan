import argparse
import datetime as dt
from .core import era5ify


def main():
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

    df = era5ify(
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
