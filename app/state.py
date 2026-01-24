"""
State model - Centralized state management for request processing.

This module defines the State Pydantic model that centralizes all data
from the request body and intermediate processing results.
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class State(BaseModel):
    """
    Centralized state for request processing.
    
    Contains:
    - sensor_data: Original sensor data from request body
    - plant_id: Unique ID of the plant instance (e.g., "basil-001")
    - plant_type: Type of plant for looking up ideal conditions (e.g., "basil")
    - comparisons: Results from comparison nodes (soil_moisture, temperature, light)
    - metadata: Additional metadata for processing
    """
    sensor_data: Dict[str, float]  # humidity, light, temperature
    plant_id: str  # Unique instance ID (stored in DB)
    plant_type: str  # Plant type for JSON lookup (used in nodes)
    comparisons: Dict[str, Dict[str, Any]] = {}  # Results from nodes
    metadata: Dict[str, Any] = {}
    
    class Config:
        """Pydantic config"""
        extra = "allow"  # Allow additional fields for flexibility
