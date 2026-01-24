"""
Core business routes for sensor data analysis.

This module contains the /analyze endpoint that uses the pipeline processor
from agent.py to analyze sensor data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models import SensorData, AnalysisResponse
from app.agent import process_with_pipeline
from app.database import get_db, PlantAnalysis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_sensor_data(
    data: SensorData,
    test_date: Optional[str] = Query(
        None,
        description="[TESTING ONLY] ISO format date string (YYYY-MM-DDTHH:MM:SS) to simulate a specific timestamp. Example: 2024-01-15T10:30:00"
    )
):
    """
    Analyze sensor data using the pipeline processor.
    
    The pipeline executes nodes (validation, enrichment) then the agent with tools.
    
    Accepts sensor data (humidity, light, temperature) and returns
    analysis results with recommendations.
    
    Example request:
        {
            "humidity": 60,
            "light": 1200,
            "temperature": 22,
            "plant_id": "basil-001",
            "plant_type": "basil"
        }
    
    Query Parameters (Testing):
        - test_date: [TESTING ONLY] ISO format date string to simulate a specific timestamp.
          Use this to simulate multiple days by sending requests with different dates.
          Example: ?test_date=2024-01-15T10:30:00
    
    Note:
        - plant_id: Unique ID of the plant instance (e.g., "basil-001", "tomato-123")
        - plant_type: Type of plant for looking up ideal conditions (e.g., "basil", "tomato")
    
    Example response:
        {
            "status": "OK",
            "message": "Conditions are optimal",
            "action": "aucune"
        }
    """
    try:
        # Parse test_date if provided (for testing only)
        test_timestamp = None
        if test_date:
            try:
                # Try ISO format first
                test_timestamp = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
                logger.debug(f"[TESTING] Using test_date: {test_timestamp}")
            except ValueError:
                try:
                    # Try common formats: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
                    if 'T' in test_date or ' ' in test_date:
                        # Has time component
                        test_timestamp = datetime.strptime(test_date, '%Y-%m-%dT%H:%M:%S')
                    else:
                        # Date only, set to midnight
                        test_timestamp = datetime.strptime(test_date, '%Y-%m-%d')
                    logger.debug(f"[TESTING] Using test_date (parsed): {test_timestamp}")
                except ValueError as e:
                    logger.warning(f"Invalid test_date format: {test_date}. Expected ISO format (YYYY-MM-DDTHH:MM:SS). Ignoring. Error: {str(e)}")
        
        # Process through pipeline: nodes -> agent -> formatted response
        return process_with_pipeline(data, test_timestamp=test_timestamp)
        
    except RuntimeError as e:
        # Agent not initialized
        logger.error(f"Agent initialization error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="LangChain agent is not initialized. Check server logs."
        )
    except Exception as e:
        logger.error(f"Error analyzing sensor data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during analysis: {str(e)}"
        )


@router.get("/history/{plant_id}")
async def get_plant_history(
    plant_id: str,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db)
):
    """
    Get analysis history for a specific plant.
    
    Args:
        plant_id: ID of the plant
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        
    Returns:
        List of analysis records with sensor data, comparisons, and results
    """
    try:
        logger.debug(f"Querying history for plant_id: {plant_id}, limit: {limit}, offset: {offset}")
        
        # Query analyses for the plant, ordered by most recent first
        analyses = db.query(PlantAnalysis)\
            .filter(PlantAnalysis.plant_id == plant_id)\
            .order_by(PlantAnalysis.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        logger.debug(f"Found {len(analyses)} analyses for plant {plant_id}")
        
        # Convert to dict format
        results = []
        for analysis in analyses:
            try:
                results.append({
                    "id": analysis.id,
                    "plant_id": analysis.plant_id,
                    "timestamp": analysis.timestamp.isoformat(),
                    "sensor_data": {
                        "humidity": analysis.humidity,
                        "light": analysis.light,
                        "temperature": analysis.temperature
                    },
                    "comparisons": analysis.comparisons or {},
                    "status": analysis.status,
                    "message": analysis.message,
                    "action": analysis.action
                })
            except Exception as e:
                logger.error(f"Error serializing analysis {analysis.id}: {str(e)}", exc_info=True)
                # Skip this analysis but continue with others
                continue
        
        return {
            "plant_id": plant_id,
            "count": len(results),
            "analyses": results
        }
        
    except RuntimeError as e:
        # Database not initialized
        logger.error(f"Database not initialized: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database is not available. Please check server logs."
        )
    except Exception as e:
        logger.error(f"Error retrieving history for plant {plant_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}"
        )


@router.get("/history")
async def get_all_history(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db)
):
    """
    Get analysis history for all plants.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        
    Returns:
        List of all analysis records
    """
    try:
        # Query all analyses, ordered by most recent first
        analyses = db.query(PlantAnalysis)\
            .order_by(PlantAnalysis.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        # Convert to dict format
        results = []
        for analysis in analyses:
            results.append({
                "id": analysis.id,
                "plant_id": analysis.plant_id,
                "timestamp": analysis.timestamp.isoformat(),
                "sensor_data": {
                    "humidity": analysis.humidity,
                    "light": analysis.light,
                    "temperature": analysis.temperature
                },
                "comparisons": analysis.comparisons or {},
                "status": analysis.status,
                "message": analysis.message,
                "action": analysis.action
            })
        
        return {
            "count": len(results),
            "analyses": results
        }
        
    except RuntimeError as e:
        # Database not initialized
        logger.error(f"Database not initialized: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database is not available. Please check server logs."
        )
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}"
        )
