"""
Nodes module - Pipeline nodes executed before agent tools.

Nodes are functions that take plant_id and value, and return comparison results.
They are executed to compare sensor data with ideal plant conditions.
"""

from .soil_moisture import soil_moisture
from .temperature import temperature
from .light_node import light

# List of nodes available for plant comparison
# Each node takes (plant_id: str, value: float) -> dict
NODES = [
    soil_moisture,
    temperature,
    light,
]
