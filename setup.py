from setuptools import setup, find_packages

setup(
    name="eranest",
    version="0.1",
    description="ERA5 climate data downloader and processor",
    author="JaggeryArray",
    packages=find_packages(),
    install_requires=[
        "cdsapi",
        "xarray",
        "netCDF4",
        "numpy",
        "pandas",
        "geopandas",
        "shapely",
        "python-dateutil",
        "matplotlib",
        "tqdm"
    ],
    entry_points={
        'console_scripts': [
            'eranest=eranest.cli:main'
        ]
    },
    python_requires=">=3.7"
)
