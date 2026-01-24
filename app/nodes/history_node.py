"""
History node - Retrieves and analyzes plant analysis history.

This node:
- Retrieves recent analyses from the database
- Calculates trends (increasing/decreasing/stable)
- Generates statistical summary
- Provides context for the LLM analysis
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.database import get_db, PlantAnalysis

logger = logging.getLogger(__name__)


def calculate_trend(values: list, current_value: float) -> Dict[str, Any]:
    """
    Calculate trend direction and change.
    
    Args:
        values: List of historical values
        current_value: Current value to compare
        
    Returns:
        Dictionary with trend information
    """
    if not values or len(values) < 2:
        return {
            "direction": "insufficient_data",
            "change": 0,
            "period": "N/A"
        }
    
    # Calculate average of historical values
    avg_historical = sum(values) / len(values)
    change = current_value - avg_historical
    change_percent = (change / avg_historical * 100) if avg_historical > 0 else 0
    
    # Determine direction
    if abs(change_percent) < 2:  # Less than 2% change
        direction = "stable"
    elif change > 0:
        direction = "increasing"
    else:
        direction = "decreasing"
    
    return {
        "direction": direction,
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "average_historical": round(avg_historical, 2),
        "period": f"{len(values)} analyses"
    }


def history(plant_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve and analyze plant analysis history.
    
    Args:
        plant_id: Unique ID of the plant instance
        limit: Number of recent analyses to retrieve (default: 10)
        
    Returns:
        Dictionary with:
        - recent_analyses: List of recent analysis records
        - trends: Trend analysis for each metric
        - summary: Statistical summary
        - has_history: Boolean indicating if history exists
    """
    try:
        # Get database session
        db = next(get_db())
        
        try:
            # Retrieve recent analyses, ordered by most recent first
            analyses = db.query(PlantAnalysis)\
                .filter(PlantAnalysis.plant_id == plant_id)\
                .order_by(PlantAnalysis.timestamp.desc())\
                .limit(limit)\
                .all()
            
            if not analyses or len(analyses) == 0:
                logger.debug(f"No history found for plant {plant_id}")
                return {
                    "has_history": False,
                    "recent_analyses": [],
                    "trends": {},
                    "summary": {
                        "total_analyses": 0,
                        "message": "No historical data available"
                    }
                }
            
            # Convert to list format (excluding current analysis if it exists)
            recent_analyses = []
            humidity_values = []
            light_values = []
            temperature_values = []
            alert_count = 0
            last_alert_date = None
            
            for analysis in analyses:
                recent_analyses.append({
                    "timestamp": analysis.timestamp.isoformat(),
                    "humidity": analysis.humidity,
                    "light": analysis.light,
                    "temperature": analysis.temperature,
                    "status": analysis.status
                })
                
                # Collect values for trend calculation
                humidity_values.append(analysis.humidity)
                light_values.append(analysis.light)
                temperature_values.append(analysis.temperature)
                
                # Count alerts
                if analysis.status == "ALERT":
                    alert_count += 1
                    if last_alert_date is None:
                        last_alert_date = analysis.timestamp
            
            # Reverse to get chronological order (oldest first) for trend calculation
            humidity_values.reverse()
            light_values.reverse()
            temperature_values.reverse()
            
            # Get current values (most recent analysis)
            current_humidity = humidity_values[-1] if humidity_values else None
            current_light = light_values[-1] if light_values else None
            current_temperature = temperature_values[-1] if temperature_values else None
            
            # Calculate trends (excluding current value from historical average)
            trends = {}
            if current_humidity is not None and len(humidity_values) > 1:
                trends["humidity"] = calculate_trend(
                    humidity_values[:-1],  # Exclude current from historical
                    current_humidity
                )
            
            if current_light is not None and len(light_values) > 1:
                trends["light"] = calculate_trend(
                    light_values[:-1],
                    current_light
                )
            
            if current_temperature is not None and len(temperature_values) > 1:
                trends["temperature"] = calculate_trend(
                    temperature_values[:-1],
                    current_temperature
                )
            
            # Calculate summary statistics
            total_analyses = len(analyses)
            avg_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else 0
            avg_light = sum(light_values) / len(light_values) if light_values else 0
            avg_temperature = sum(temperature_values) / len(temperature_values) if temperature_values else 0
            
            # Calculate time span
            if len(analyses) > 1:
                time_span = analyses[0].timestamp - analyses[-1].timestamp
                days_span = time_span.days if time_span.days > 0 else 1
            else:
                days_span = 1
            
            summary = {
                "total_analyses": total_analyses,
                "alert_count": alert_count,
                "alert_percentage": round((alert_count / total_analyses * 100), 1) if total_analyses > 0 else 0,
                "last_alert_date": last_alert_date.isoformat() if last_alert_date else None,
                "time_span_days": days_span,
                "average_values": {
                    "humidity": round(avg_humidity, 2),
                    "light": round(avg_light, 2),
                    "temperature": round(avg_temperature, 2)
                },
                "most_recent_date": analyses[0].timestamp.isoformat() if analyses else None
            }
            
            result = {
                "has_history": True,
                "recent_analyses": recent_analyses,
                "trends": trends,
                "summary": summary
            }
            
            logger.debug(f"History retrieved for plant {plant_id}: {total_analyses} analyses, {alert_count} alerts")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error retrieving history for plant {plant_id}: {str(e)}", exc_info=True)
        # Return empty history on error (don't fail the pipeline)
        return {
            "has_history": False,
            "recent_analyses": [],
            "trends": {},
            "summary": {
                "total_analyses": 0,
                "message": f"Error retrieving history: {str(e)}"
            }
        }
