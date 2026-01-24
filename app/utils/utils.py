"""
Utility functions for plant nodes.

Shared functions used by all plant comparison nodes.
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Path to plants data file (relative to app directory)
PLANTS_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "plants_ideal.json"
)


def load_plant_data(plant_id: str) -> Dict[str, Any]:
    """
    Load plant data from JSON file.
    
    Args:
        plant_id: ID of the plant to load (e.g., "basil", "tomato")
        
    Returns:
        Dictionary with plant data containing:
        - id: plant ID
        - name: plant name
        - ideal_conditions: dict with ideal conditions
        - tolerances: dict with tolerance values
        
    Raises:
        ValueError: If plant is not found
        FileNotFoundError: If plants_ideal.json is not found
        json.JSONDecodeError: If JSON file is invalid
    """
    try:
        with open(PLANTS_DATA_PATH, "r", encoding="utf-8") as f:
            plants = json.load(f)
        
        for plant in plants:
            if plant["id"] == plant_id:
                return plant
        
        raise ValueError(f"Plante {plant_id} non trouvée")
    except FileNotFoundError:
        logger.error(f"Plants data file not found: {PLANTS_DATA_PATH}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing plants data file: {str(e)}")
        raise
