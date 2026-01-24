"""
Temperature comparison node.

Compares current temperature value with ideal conditions for a specific plant.
"""

import logging
from app.utils.utils import load_plant_data

logger = logging.getLogger(__name__)


def temperature(plant_type: str, value: float) -> dict:
    """
    Compare temperature value with ideal conditions for the plant.
    
    Args:
        plant_type: Type of the plant (e.g., "basil", "tomato") for looking up ideal conditions
        value: Current temperature in Celsius
        
    Returns:
        Dictionary with:
        - parameter: "temperature"
        - current: current value
        - ideal: dict with min, max, ideal values
        - difference: difference from ideal
        - status: "OK" or "ALERT"
        - message: descriptive message
        
    Raises:
        ValueError: If plant type is not found
    """
    try:
        plant = load_plant_data(plant_type)
        ideal_conditions = plant["ideal_conditions"]["temperature"]
        tolerance = plant["tolerances"]["temperature"]
        
        # Extract min, max, ideal from ideal_conditions
        min_temp = ideal_conditions["min"]
        max_temp = ideal_conditions["max"]
        ideal_temp = ideal_conditions["ideal"]
        
        # Calculate difference from ideal
        difference = value - ideal_temp
        
        # Determine status
        # OK if within [min, max] range, or within tolerance of ideal
        if min_temp <= value <= max_temp:
            status = "OK"
        elif abs(difference) <= tolerance:
            status = "OK"
        else:
            status = "ALERT"
        
        # Create message
        if status == "OK":
            if abs(difference) <= tolerance:
                message = f"Température optimale ({value}°C, idéal: {ideal_temp}°C)"
            else:
                message = f"Température acceptable ({value}°C, plage: {min_temp}-{max_temp}°C)"
        else:
            if value < min_temp:
                message = f"Température trop basse ({value}°C, minimum: {min_temp}°C, idéal: {ideal_temp}°C)"
            elif value > max_temp:
                message = f"Température trop élevée ({value}°C, maximum: {max_temp}°C, idéal: {ideal_temp}°C)"
            else:
                message = f"Température hors tolérance ({value}°C, idéal: {ideal_temp}°C, tolérance: ±{tolerance}°C)"
        
        result = {
            "parameter": "temperature",
            "current": value,
            "ideal": ideal_conditions,  # Full dict with min, max, ideal
            "difference": difference,
            "status": status,
            "message": message
        }
        
        logger.debug(f"Temperature comparison for {plant_type}: {status} (current: {value}°C, ideal: {ideal_temp}°C)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in temperature node for {plant_type}: {str(e)}")
        raise
