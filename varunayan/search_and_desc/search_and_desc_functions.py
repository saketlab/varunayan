from typing import Any, Callable, Dict, List, Optional


def get_available_datasets() -> List[str]:
    """
    Get list of available dataset types

    Returns:
        list: Available dataset types
    """
    return ["single", "pressure", "all"]  # Update this when adding new datasets


def get_single_levels_dataset() -> Dict[str, List[Dict[str, Any]]]:
    """
    Helper function to combine all single level variable categories

    Returns:
        dict: Dictionary with all single level variable categories
    """
    from .single_levels_variables import (
        cloud_variables,
        evaporation_and_runoff_variables,
        heat_and_radiation_variables,
        lake_variables,
        mean_rates_variables,
        ocean_wave_variables,
        other_variables,
        precipitation_variables,
        snow_variables,
        soil_variables,
        temperature_and_pressure,
        vegetation_variables,
        vertical_integral_variables,
        wind_variables,
    )

    return {
        "temperature_and_pressure": temperature_and_pressure,
        "wind_variables": wind_variables,
        "mean_rates_variables": mean_rates_variables,
        "heat_and_radiation_variables": heat_and_radiation_variables,
        "cloud_variables": cloud_variables,
        "lake_variables": lake_variables,
        "evaporation_and_runoff_variables": evaporation_and_runoff_variables,
        "precipitation_variables": precipitation_variables,
        "snow_variables": snow_variables,
        "soil_variables": soil_variables,
        "vertical_integral_variables": vertical_integral_variables,
        "vegetation_variables": vegetation_variables,
        "ocean_wave_variables": ocean_wave_variables,
        "other_variables": other_variables,
    }


def get_pressure_levels_dataset() -> List[Dict[str, Any]]:
    """
    Helper function to get pressure level variables

    Returns:
        list: List of pressure level variable dictionaries
    """
    from .pressure_levels_variables import pressure_level_variables

    return pressure_level_variables


# pyright: reportUnknownMemberType=false
def describe_variables(variable_names: List[str], dataset_type: str) -> Dict[str, str]:
    """
    Get descriptions for specific variables

    Args:
        variable_names (list): List of variable names to describe
        dataset_type (str): Dataset type to search ("single", "pressure", "all", or any other registered dataset)
    """
    # Define available datasets and their processors
    dataset_processors: Dict[str, Callable[..., List[Dict[str, Any]]]] = {
        "single": _process_single_dataset,
        "pressure": _process_pressure_dataset,
        # Easy to add more datasets here:
        # 'surface': _process_surface_dataset,
        # 'satellite': _process_satellite_dataset,
    }

    dataset_type = dataset_type.strip().lower()

    # Get the appropriate dataset(s)
    if dataset_type == "all":
        # Process all available datasets
        dataset: List[Dict[str, Any]] = []
        for ds_type, processor in dataset_processors.items():
            dataset.extend(processor(ds_type))
    elif dataset_type in dataset_processors:
        # Process specific dataset
        dataset = dataset_processors[dataset_type](dataset_type)
    else:
        available_types = list(dataset_processors.keys()) + ["all"]
        raise ValueError(f"dataset_type must be one of: {available_types}")

    descriptions: Dict[str, str] = {}

    # Print header
    print(f"\n=== Variable Descriptions ({dataset_type.upper()} LEVELS) ===")

    for var_name in variable_names:
        for var in dataset:
            if var["name"] == var_name:
                descriptions[var_name] = var["description"]
                print(f"\n{var_name}:")
                print(f"  Category: {var.get('category', 'Unknown')}")
                # Show dataset info when describing all datasets
                if dataset_type == "all":
                    print(f"  Dataset: {var.get('dataset', 'Unknown')}")
                print(f"  Description: {var['description']}")
                break
        else:
            descriptions[var_name] = "Variable not found"
            print(f"\n{var_name}:")
            print("  Variable not found")

    return descriptions


def search_variable(pattern: Optional[str], dataset_type: str = "all") -> None:
    """
    Search for variables in the dataset by pattern

    Args:
        pattern (str or None): The string pattern to search for in variable names.
                              If None, prints all variables.
        dataset_type (str): Dataset type to search ("single", "pressure", "all", or any other registered dataset)
    """
    # remove whitespace from pattern and dataset_type and lowercase them
    pattern = pattern.strip().lower() if pattern else None
    dataset_type = dataset_type.strip().lower()

    # Define available datasets and their processors
    dataset_processors: Dict[str, Callable[[str], List[Dict[str, Any]]]] = {
        "single": _process_single_dataset,
        "pressure": _process_pressure_dataset,
        # Easy to add more datasets here:
        # 'surface': _process_surface_dataset,
        # 'satellite': _process_satellite_dataset,
    }

    # Get the appropriate dataset(s)
    if dataset_type == "all":
        # Process all available datasets
        dataset: List[Dict[str, Any]] = []
        for ds_type, processor in dataset_processors.items():
            dataset.extend(processor(ds_type))
    elif dataset_type in dataset_processors:
        # Process specific dataset
        dataset = dataset_processors[dataset_type](dataset_type)
    else:
        available_types = list(dataset_processors.keys()) + ["all"]
        raise ValueError(f"dataset_type must be one of: {available_types}")

    # If no search pattern provided, return all variables
    matches: List[Dict[str, Any]]
    if pattern is None:
        matches = dataset
        print(f"\n=== ALL VARIABLES ({dataset_type.upper()} LEVELS) ===")
        print(f"Total variables found: {len(matches)}")
    else:
        pattern = pattern.lower()
        matches = []

        for var in dataset:
            if pattern in var["name"].lower():
                matches.append(var)

        print(f"\n=== SEARCH RESULTS ({dataset_type.upper()} LEVELS) ===")
        print(f"Pattern: '{pattern}'")
        print(f"Variables found: {len(matches)}")

    # Print results grouped by category
    if len(matches) > 0:
        # Group matches by category
        category_groups: Dict[str, List[Dict[str, Any]]] = {}
        for var in matches:
            category: str = var.get("category", "Unknown")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(var)

        # Print each category group
        for category, vars_in_category in category_groups.items():
            print(f"\n--- {category.replace('_', ' ').title()} ---")
            for i, var in enumerate(vars_in_category, 1):
                # Show dataset info when searching all datasets
                dataset_info = (
                    f" (from {var['dataset']} levels)" if dataset_type == "all" else ""
                )
                print(f"{i}. {var['name']}{dataset_info}")
                print(f"   Description: {var['description']}\n")
    else:
        print("No variables found matching the pattern.")


def _process_single_dataset(dataset_type: str) -> List[Dict[str, Any]]:
    """Process single levels dataset"""
    dataset = get_single_levels_dataset()
    all_vars: List[Dict[str, Any]] = []
    for category_name, category_vars in dataset.items():
        for var in category_vars:
            var_with_category = var.copy()
            var_with_category["category"] = category_name
            var_with_category["dataset"] = dataset_type
            all_vars.append(var_with_category)
    return all_vars


def _process_pressure_dataset(dataset_type: str) -> List[Dict[str, Any]]:
    """Process pressure levels dataset"""
    dataset = get_pressure_levels_dataset()
    processed_vars: List[Dict[str, Any]] = []
    for var in dataset:
        var_with_info = var.copy()
        var_with_info["category"] = "pressure_levels"
        var_with_info["dataset"] = dataset_type
        processed_vars.append(var_with_info)
    return processed_vars


# Example of how to add a new dataset:
# def _process_surface_dataset(dataset_type):
#     """Process surface dataset"""
#     dataset = get_surface_dataset()  # Your new dataset function
#     processed_vars = []
#     for var in dataset:
#         var_with_info = var.copy()
#         var_with_info['category'] = 'surface_variables'
#         var_with_info['dataset'] = dataset_type
#         processed_vars.append(var_with_info)
#     return processed_vars
