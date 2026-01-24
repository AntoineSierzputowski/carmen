"""
Light comparison node.

Compares current light value with ideal conditions for a specific plant.
"""

import logging
from app.utils.utils import load_plant_data

logger = logging.getLogger(__name__)


def light(plant_type: str, value: float) -> dict:
    """
    Compare light value with ideal conditions for the plant.
    
    Args:
        plant_type: Type of the plant (e.g., "basil", "tomato") for looking up ideal conditions
        value: Current light intensity in lux
        
    Returns:
        Dictionary with:
        - parameter: "light"
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
        ideal_conditions = plant["ideal_conditions"]["light"]
        tolerance = plant["tolerances"]["light"]
        
        # Extract min, max, ideal from ideal_conditions
        min_light = ideal_conditions["min"]
        max_light = ideal_conditions["max"]
        ideal_light = ideal_conditions["ideal"]
        
        # Calculate difference from ideal
        difference = value - ideal_light
        
        # Determine status
        # OK if within [min, max] range, or within tolerance of ideal
        if min_light <= value <= max_light:
            status = "OK"
        elif abs(difference) <= tolerance:
            status = "OK"
        else:
            status = "ALERT"
        
        # Create message
        if status == "OK":
            if abs(difference) <= tolerance:
                message = f"Luminosité optimale ({value} lux, idéal: {ideal_light} lux)"
            else:
                message = f"Luminosité acceptable ({value} lux, plage: {min_light}-{max_light} lux)"
        else:
            if value < min_light:
                message = f"Luminosité trop faible ({value} lux, minimum: {min_light} lux, idéal: {ideal_light} lux)"
            elif value > max_light:
                message = f"Luminosité trop élevée ({value} lux, maximum: {max_light} lux, idéal: {ideal_light} lux)"
            else:
                message = f"Luminosité hors tolérance ({value} lux, idéal: {ideal_light} lux, tolérance: ±{tolerance} lux)"
        
        result = {
            "parameter": "light",
            "current": value,
            "ideal": ideal_conditions,  # Full dict with min, max, ideal
            "difference": difference,
            "status": status,
            "message": message
        }
        
        logger.debug(f"Light comparison for {plant_type}: {status} (current: {value} lux, ideal: {ideal_light} lux)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in light node for {plant_type}: {str(e)}")
        raise
