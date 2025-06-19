"""
Aurora format conversion utilities.

This module provides conversion from ERA5 data to Microsoft Aurora
compatible formats with proper variable mapping and tensor creation.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
import warnings

from ..constants import (
    ERA5_TO_AURORA_SURFACE,
    ERA5_TO_AURORA_ATMOSPHERIC,
    ERA5_TO_AURORA_STATIC,
    AURORA_PRESSURE_LEVELS,
    DEFAULT_SURFACE_VARIABLES,
    DEFAULT_ATMOSPHERIC_VARIABLES,
    DEFAULT_STATIC_VARIABLES,
)
from ..exceptions import AuroraError, ValidationError, DataProcessingError
from ..utils.validation import validate_dataframe_structure

logger = logging.getLogger(__name__)

# Try to import torch, but make it optional
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - Aurora batch creation will use mock tensors")


@dataclass
class AuroraBatchInfo:
    """Information about an Aurora batch."""
    
    batch_size: int
    time_steps: int
    height: int
    width: int
    pressure_levels: List[str]
    surface_variables: List[str]
    atmospheric_variables: List[str]
    static_variables: List[str]
    current_time: datetime
    
    def __post_init__(self):
        """Validate batch information."""
        if self.time_steps < 2:
            raise AuroraError("Aurora requires at least 2 time steps (current + previous)")
        
        if self.batch_size < 1:
            raise AuroraError("Batch size must be at least 1")


class AuroraConverter:
    """
    High-performance converter for ERA5 to Aurora format.
    
    This class handles the conversion of ERA5 data to Aurora-compatible
    tensors with proper variable mapping and validation.
    """
    
    def __init__(self,
                 strict_validation: bool = True,
                 optimize_tensors: bool = True,
                 device: str = "cpu"):
        """
        Initialize Aurora converter.
        
        Args:
            strict_validation: Enable strict validation of data
            optimize_tensors: Optimize tensor operations for memory/speed
            device: Device for tensor operations ("cpu" or "cuda")
        """
        self.strict_validation = strict_validation
        self.optimize_tensors = optimize_tensors
        self.device = device
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - using numpy arrays instead of tensors")
        
        # Variable mappings
        self.surface_mapping = ERA5_TO_AURORA_SURFACE
        self.atmospheric_mapping = ERA5_TO_AURORA_ATMOSPHERIC
        self.static_mapping = ERA5_TO_AURORA_STATIC
        
        # Cache for repeated conversions
        self._coordinate_cache = {}
        self._tensor_cache = {}
    
    def convert_era5_to_aurora(self,
                             surface_data: Optional[pd.DataFrame] = None,
                             atmospheric_data: Optional[pd.DataFrame] = None,
                             static_data: Optional[pd.DataFrame] = None,
                             lat_coord: str = "latitude",
                             lon_coord: str = "longitude",
                             time_coord: str = "time",
                             pressure_coord: str = "level") -> Dict[str, Any]:
        """
        Convert ERA5 data to Aurora format.
        
        Args:
            surface_data: Surface-level ERA5 data
            atmospheric_data: Atmospheric-level ERA5 data  
            static_data: Static ERA5 data
            lat_coord: Name of latitude coordinate
            lon_coord: Name of longitude coordinate
            time_coord: Name of time coordinate
            pressure_coord: Name of pressure coordinate
            
        Returns:
            Dictionary with Aurora-compatible tensors and metadata
        """
        logger.info("Converting ERA5 data to Aurora format...")
        
        # Validate inputs
        if not any([surface_data is not None, atmospheric_data is not None]):
            raise AuroraError("At least surface or atmospheric data must be provided")
        
        # Get coordinate information
        batch_info = self._analyze_data_structure(
            surface_data, atmospheric_data, static_data,
            lat_coord, lon_coord, time_coord, pressure_coord
        )
        
        logger.info(f"Aurora batch info: {batch_info}")
        
        # Convert each data type
        aurora_data = {}
        
        if surface_data is not None:
            aurora_data["surf_vars"] = self._convert_surface_variables(
                surface_data, batch_info, lat_coord, lon_coord, time_coord
            )
        
        if atmospheric_data is not None:
            aurora_data["atmos_vars"] = self._convert_atmospheric_variables(
                atmospheric_data, batch_info, lat_coord, lon_coord, time_coord, pressure_coord
            )
        
        if static_data is not None:
            aurora_data["static_vars"] = self._convert_static_variables(
                static_data, batch_info, lat_coord, lon_coord
            )
        
        # Create metadata
        aurora_data["metadata"] = self._create_metadata(batch_info)
        
        logger.info("Aurora conversion completed successfully")
        return aurora_data
    
    def _analyze_data_structure(self,
                               surface_data: Optional[pd.DataFrame],
                               atmospheric_data: Optional[pd.DataFrame],
                               static_data: Optional[pd.DataFrame],
                               lat_coord: str,
                               lon_coord: str,
                               time_coord: str,
                               pressure_coord: str) -> AuroraBatchInfo:
        """Analyze data structure to determine batch dimensions."""
        
        # Get coordinate information from available data
        coords_df = surface_data if surface_data is not None else atmospheric_data
        
        if coords_df is None:
            raise AuroraError("No coordinate reference data available")
        
        # Get unique coordinates
        unique_lats = sorted(coords_df[lat_coord].unique(), reverse=True)  # Aurora wants decreasing
        unique_lons = sorted(coords_df[lon_coord].unique())
        
        height = len(unique_lats)
        width = len(unique_lons)
        
        # Get time information
        if time_coord in coords_df.columns:
            unique_times = sorted(coords_df[time_coord].unique())
            time_steps = len(unique_times)
            current_time = pd.to_datetime(unique_times[-1])
        else:
            time_steps = 1
            current_time = datetime.now()
        
        # Get pressure levels
        if atmospheric_data is not None and pressure_coord in atmospheric_data.columns:
            pressure_levels = sorted(atmospheric_data[pressure_coord].unique(), reverse=True)
            pressure_levels = [str(int(p)) for p in pressure_levels]
        else:
            pressure_levels = AURORA_PRESSURE_LEVELS
        
        # Get variable lists
        surface_vars = []
        atmospheric_vars = []
        static_vars = []
        
        if surface_data is not None:
            surface_vars = [col for col in surface_data.columns 
                          if col not in [lat_coord, lon_coord, time_coord]]
        
        if atmospheric_data is not None:
            atmospheric_vars = [col for col in atmospheric_data.columns 
                              if col not in [lat_coord, lon_coord, time_coord, pressure_coord]]
        
        if static_data is not None:
            static_vars = [col for col in static_data.columns 
                         if col not in [lat_coord, lon_coord]]
        
        return AuroraBatchInfo(
            batch_size=1,  # Single batch
            time_steps=time_steps,
            height=height,
            width=width,
            pressure_levels=pressure_levels,
            surface_variables=surface_vars,
            atmospheric_variables=atmospheric_vars,
            static_variables=static_vars,
            current_time=current_time
        )
    
    def _convert_surface_variables(self,
                                 surface_data: pd.DataFrame,
                                 batch_info: AuroraBatchInfo,
                                 lat_coord: str,
                                 lon_coord: str,
                                 time_coord: str) -> Dict[str, Any]:
        """Convert surface variables to Aurora tensor format."""
        
        logger.debug("Converting surface variables...")
        
        surf_vars = {}
        
        # Get coordinate arrays
        lats = sorted(surface_data[lat_coord].unique(), reverse=True)
        lons = sorted(surface_data[lon_coord].unique())
        
        if time_coord in surface_data.columns:
            times = sorted(surface_data[time_coord].unique())
            time_steps = min(len(times), batch_info.time_steps)
            selected_times = times[-time_steps:]  # Use most recent time steps
        else:
            selected_times = [None]
            time_steps = 1
        
        # Process each variable
        for era5_var in batch_info.surface_variables:
            if era5_var in self.surface_mapping:
                aurora_var = self.surface_mapping[era5_var]
                
                # Create tensor: (batch_size, time_steps, height, width)
                tensor_shape = (batch_info.batch_size, time_steps, batch_info.height, batch_info.width)
                
                if TORCH_AVAILABLE:
                    tensor = torch.zeros(tensor_shape, dtype=torch.float32, device=self.device)
                else:
                    tensor = np.zeros(tensor_shape, dtype=np.float32)
                
                # Fill tensor with data
                for t_idx, time_val in enumerate(selected_times):
                    if time_val is not None:
                        time_data = surface_data[surface_data[time_coord] == time_val]
                    else:
                        time_data = surface_data
                    
                    for _, row in time_data.iterrows():
                        lat_idx = lats.index(row[lat_coord])
                        lon_idx = lons.index(row[lon_coord])
                        
                        value = row[era5_var]
                        if pd.notna(value):
                            if TORCH_AVAILABLE:
                                tensor[0, t_idx, lat_idx, lon_idx] = float(value)
                            else:
                                tensor[0, t_idx, lat_idx, lon_idx] = float(value)
                
                surf_vars[aurora_var] = tensor
                logger.debug(f"Converted {era5_var} → {aurora_var}: {tensor_shape}")
            else:
                logger.warning(f"No Aurora mapping for surface variable: {era5_var}")
        
        return surf_vars
    
    def _convert_atmospheric_variables(self,
                                     atmospheric_data: pd.DataFrame,
                                     batch_info: AuroraBatchInfo,
                                     lat_coord: str,
                                     lon_coord: str,
                                     time_coord: str,
                                     pressure_coord: str) -> Dict[str, Any]:
        """Convert atmospheric variables to Aurora tensor format."""
        
        logger.debug("Converting atmospheric variables...")
        
        atmos_vars = {}
        
        # Get coordinate arrays
        lats = sorted(atmospheric_data[lat_coord].unique(), reverse=True)
        lons = sorted(atmospheric_data[lon_coord].unique())
        pressure_levels = sorted(atmospheric_data[pressure_coord].unique(), reverse=True)
        
        if time_coord in atmospheric_data.columns:
            times = sorted(atmospheric_data[time_coord].unique())
            time_steps = min(len(times), batch_info.time_steps)
            selected_times = times[-time_steps:]
        else:
            selected_times = [None]
            time_steps = 1
        
        # Process each variable
        for era5_var in batch_info.atmospheric_variables:
            if era5_var in self.atmospheric_mapping:
                aurora_var = self.atmospheric_mapping[era5_var]
                
                # Create tensor: (batch_size, time_steps, pressure_levels, height, width)
                tensor_shape = (
                    batch_info.batch_size, time_steps, len(pressure_levels),
                    batch_info.height, batch_info.width
                )
                
                if TORCH_AVAILABLE:
                    tensor = torch.zeros(tensor_shape, dtype=torch.float32, device=self.device)
                else:
                    tensor = np.zeros(tensor_shape, dtype=np.float32)
                
                # Fill tensor with data
                for t_idx, time_val in enumerate(selected_times):
                    if time_val is not None:
                        time_data = atmospheric_data[atmospheric_data[time_coord] == time_val]
                    else:
                        time_data = atmospheric_data
                    
                    for _, row in time_data.iterrows():
                        lat_idx = lats.index(row[lat_coord])
                        lon_idx = lons.index(row[lon_coord])
                        pressure_idx = pressure_levels.index(row[pressure_coord])
                        
                        value = row[era5_var]
                        if pd.notna(value):
                            if TORCH_AVAILABLE:
                                tensor[0, t_idx, pressure_idx, lat_idx, lon_idx] = float(value)
                            else:
                                tensor[0, t_idx, pressure_idx, lat_idx, lon_idx] = float(value)
                
                atmos_vars[aurora_var] = tensor
                logger.debug(f"Converted {era5_var} → {aurora_var}: {tensor_shape}")
            else:
                logger.warning(f"No Aurora mapping for atmospheric variable: {era5_var}")
        
        return atmos_vars
    
    def _convert_static_variables(self,
                                static_data: pd.DataFrame,
                                batch_info: AuroraBatchInfo,
                                lat_coord: str,
                                lon_coord: str) -> Dict[str, Any]:
        """Convert static variables to Aurora tensor format."""
        
        logger.debug("Converting static variables...")
        
        static_vars = {}
        
        # Get coordinate arrays
        lats = sorted(static_data[lat_coord].unique(), reverse=True)
        lons = sorted(static_data[lon_coord].unique())
        
        # Process each variable
        for era5_var in batch_info.static_variables:
            if era5_var in self.static_mapping:
                aurora_var = self.static_mapping[era5_var]
                
                # Create tensor: (height, width)
                tensor_shape = (batch_info.height, batch_info.width)
                
                if TORCH_AVAILABLE:
                    tensor = torch.zeros(tensor_shape, dtype=torch.float32, device=self.device)
                else:
                    tensor = np.zeros(tensor_shape, dtype=np.float32)
                
                # Fill tensor with data
                for _, row in static_data.iterrows():
                    lat_idx = lats.index(row[lat_coord])
                    lon_idx = lons.index(row[lon_coord])
                    
                    value = row[era5_var]
                    if pd.notna(value):
                        if TORCH_AVAILABLE:
                            tensor[lat_idx, lon_idx] = float(value)
                        else:
                            tensor[lat_idx, lon_idx] = float(value)
                
                static_vars[aurora_var] = tensor
                logger.debug(f"Converted {era5_var} → {aurora_var}: {tensor_shape}")
            else:
                logger.warning(f"No Aurora mapping for static variable: {era5_var}")
        
        return static_vars
    
    def _create_metadata(self, batch_info: AuroraBatchInfo) -> Dict[str, Any]:
        """Create Aurora metadata."""
        
        # Create coordinate arrays
        if TORCH_AVAILABLE:
            # Note: These would need actual coordinate values from the data
            # This is a simplified version for demonstration
            lats = torch.linspace(90, -90, batch_info.height, dtype=torch.float32)
            lons = torch.linspace(0, 360, batch_info.width + 1, dtype=torch.float32)[:-1]
        else:
            lats = np.linspace(90, -90, batch_info.height, dtype=np.float32)
            lons = np.linspace(0, 360, batch_info.width + 1, dtype=np.float32)[:-1]
        
        # Convert pressure levels to tuple of floats
        pressure_levels_float = tuple(float(p) for p in batch_info.pressure_levels)
        
        metadata = {
            "lat": lats,
            "lon": lons,
            "time": (batch_info.current_time,),
            "atmos_levels": pressure_levels_float,
        }
        
        return metadata
    
    def create_aurora_batch(self, aurora_data: Dict[str, Any]) -> Any:
        """
        Create Aurora Batch object from converted data.
        
        Args:
            aurora_data: Aurora-compatible data dictionary
            
        Returns:
            Aurora Batch object (or mock object if Aurora not available)
        """
        try:
            # Try to import Aurora
            from aurora import Batch, Metadata
            
            # Create metadata object
            metadata = Metadata(
                lat=aurora_data["metadata"]["lat"],
                lon=aurora_data["metadata"]["lon"],
                time=aurora_data["metadata"]["time"],
                atmos_levels=aurora_data["metadata"]["atmos_levels"]
            )
            
            # Create batch
            batch = Batch(
                surf_vars=aurora_data.get("surf_vars", {}),
                static_vars=aurora_data.get("static_vars", {}),
                atmos_vars=aurora_data.get("atmos_vars", {}),
                metadata=metadata
            )
            
            logger.info("Created Aurora Batch object successfully")
            return batch
            
        except ImportError:
            logger.warning("Aurora not available, creating mock batch object")
            
            # Create mock batch for demonstration
            class MockBatch:
                def __init__(self, surf_vars, static_vars, atmos_vars, metadata):
                    self.surf_vars = surf_vars
                    self.static_vars = static_vars
                    self.atmos_vars = atmos_vars
                    self.metadata = metadata
                
                def __repr__(self):
                    return f"MockBatch(surf_vars={list(self.surf_vars.keys())}, static_vars={list(self.static_vars.keys())}, atmos_vars={list(self.atmos_vars.keys())})"
            
            class MockMetadata:
                def __init__(self, lat, lon, time, atmos_levels):
                    self.lat = lat
                    self.lon = lon
                    self.time = time
                    self.atmos_levels = atmos_levels
            
            metadata = MockMetadata(
                lat=aurora_data["metadata"]["lat"],
                lon=aurora_data["metadata"]["lon"],
                time=aurora_data["metadata"]["time"],
                atmos_levels=aurora_data["metadata"]["atmos_levels"]
            )
            
            return MockBatch(
                surf_vars=aurora_data.get("surf_vars", {}),
                static_vars=aurora_data.get("static_vars", {}),
                atmos_vars=aurora_data.get("atmos_vars", {}),
                metadata=metadata
            )


# Convenience functions

def era5_to_aurora_format(
    surface_data: Optional[pd.DataFrame] = None,
    atmospheric_data: Optional[pd.DataFrame] = None,
    static_data: Optional[pd.DataFrame] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convert ERA5 data to Aurora format.
    
    Args:
        surface_data: Surface-level ERA5 data
        atmospheric_data: Atmospheric-level ERA5 data
        static_data: Static ERA5 data
        **kwargs: Additional arguments for AuroraConverter
        
    Returns:
        Aurora-compatible data dictionary
    """
    converter = AuroraConverter(**kwargs)
    return converter.convert_era5_to_aurora(surface_data, atmospheric_data, static_data)


def create_aurora_batch(
    surface_data: Optional[pd.DataFrame] = None,
    atmospheric_data: Optional[pd.DataFrame] = None,
    static_data: Optional[pd.DataFrame] = None,
    **kwargs
) -> Any:
    """
    Create Aurora Batch object from ERA5 data.
    
    Args:
        surface_data: Surface-level ERA5 data
        atmospheric_data: Atmospheric-level ERA5 data
        static_data: Static ERA5 data
        **kwargs: Additional arguments for AuroraConverter
        
    Returns:
        Aurora Batch object
    """
    converter = AuroraConverter(**kwargs)
    aurora_data = converter.convert_era5_to_aurora(surface_data, atmospheric_data, static_data)
    return converter.create_aurora_batch(aurora_data)