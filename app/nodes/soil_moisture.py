"""
Soil moisture comparison node.

Compares current soil moisture value with ideal conditions for a specific plant.
"""

import logging
from app.utils.utils import load_plant_data

logger = logging.getLogger(__name__)


def soil_moisture(plant_type: str, value: float) -> dict:
    """
    Compare soil moisture value with ideal conditions for the plant.
    
    Args:
        plant_type: Type of the plant (e.g., "basil", "tomato") for looking up ideal conditions
        value: Current soil moisture percentage (0-100)
        
    Returns:
        Dictionary with:
        - parameter: "soil_moisture"
        - current: current value
        - ideal: ideal value
        - difference: difference from ideal
        - status: "OK" or "ALERT"
        - message: descriptive message
        
    Raises:
        ValueError: If plant type is not found
    """
    try:
        plant = load_plant_data(plant_type)
        ideal = plant["ideal_conditions"]["soil_moisture"]
        tolerance = plant["tolerances"]["soil_moisture"]
        
        # Calculate difference
        difference = value - ideal
        
        # Determine status based on tolerance
        status = "OK" if abs(difference) <= tolerance else "ALERT"
        
        # Create message
        if abs(difference) <= tolerance:
            message = f"Humidité du sol optimale ({value}%, idéal: {ideal}%)"
        elif difference > 0:
            message = f"Humidité du sol trop élevée de {difference:+.1f}% par rapport à l'idéal ({ideal}%)"
        else:
            message = f"Humidité du sol trop faible de {abs(difference):+.1f}% par rapport à l'idéal ({ideal}%)"
        
        result = {
            "parameter": "soil_moisture",
            "current": value,
            "ideal": ideal,
            "difference": difference,
            "status": status,
            "message": message
        }
        
        logger.debug(f"Soil moisture comparison for {plant_type}: {status} (diff: {difference:+.1f}%)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in soil_moisture node for {plant_type}: {str(e)}")
        raise
