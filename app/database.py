"""
Database module for MySQL connection and models.

This module handles:
- MySQL database connection using SQLAlchemy
- Database models for storing analysis history
- Database initialization and session management
"""

import os
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "carmen")

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()


class PlantAnalysis(Base):
    """
    Model for storing plant analysis history.
    
    Stores all sensor data, comparisons, and analysis results for each plant.
    """
    __tablename__ = "plant_analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Sensor data
    humidity = Column(Float, nullable=False)
    light = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    
    # Comparison results (stored as JSON)
    comparisons = Column(JSON, nullable=True)
    
    # Analysis results
    status = Column(String(20), nullable=False)  # OK or ALERT
    message = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<PlantAnalysis(id={self.id}, plant_id='{self.plant_id}', status='{self.status}', timestamp='{self.timestamp}')>"


# Create engine and session
engine = None
SessionLocal = None


def init_database():
    """
    Initialize database connection and create tables if they don't exist.
    
    This function should be called at application startup.
    """
    global engine, SessionLocal
    
    try:
        # Create engine
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info(f"Database initialized successfully: {DB_NAME}@{DB_HOST}:{DB_PORT}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        logger.error(f"Connection string: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        logger.error("Make sure:")
        logger.error("  1. MySQL is running")
        logger.error("  2. Database '{}' exists (or will be created automatically)".format(DB_NAME))
        logger.error("  3. Credentials are correct in .env file")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    This should be used as a dependency in FastAPI routes.
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_analysis(
    plant_id: str,
    humidity: float,
    light: float,
    temperature: float,
    comparisons: dict,
    status: str,
    message: str,
    action: str,
    timestamp: Optional[datetime] = None
) -> PlantAnalysis:
    """
    Save a plant analysis to the database.
    
    Args:
        plant_id: Unique ID of the plant instance (e.g., "basil-001", "tomato-123")
        humidity: Humidity sensor value
        light: Light sensor value
        temperature: Temperature sensor value
        comparisons: Dictionary with comparison results from nodes
        status: Analysis status (OK or ALERT)
        message: Analysis message
        action: Recommended action
        timestamp: [TESTING ONLY] Optional datetime to use instead of current time
        
    Returns:
        Created PlantAnalysis object
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        # Use provided timestamp (for testing) or current time
        analysis_timestamp = timestamp if timestamp is not None else datetime.utcnow()
        
        analysis = PlantAnalysis(
            plant_id=plant_id,
            humidity=humidity,
            light=light,
            temperature=temperature,
            comparisons=comparisons,
            status=status,
            message=message,
            action=action,
            timestamp=analysis_timestamp
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        logger.debug(f"Analysis saved for plant {plant_id}: id={analysis.id}")
        return analysis
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving analysis: {str(e)}")
        raise
    finally:
        db.close()
