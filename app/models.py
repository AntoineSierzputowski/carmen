"""
Pydantic models for request/response validation.

TODO: Add validation rules later (e.g., min/max values, ranges)
"""

from pydantic import BaseModel
from typing import Literal


class SensorData(BaseModel):
    """
    Sensor data model without validation.
    
    TODO: Add validation rules:
    - humidity: 0-100
    - light: >= 0
    - temperature: reasonable range (e.g., -50 to 60)
    """
    humidity: float
    light: float
    temperature: float
    plant_id: str  # Unique ID of the plant instance (e.g., "basil-001", "tomato-123")
    plant_type: str  # Type of plant for looking up ideal conditions (e.g., "basil", "tomato")


class AnalysisResponse(BaseModel):
    """Response model for sensor data analysis"""
    status: Literal["OK", "ALERT"]
    message: str
    action: str  # Flexible action field - LLM decides based on context

