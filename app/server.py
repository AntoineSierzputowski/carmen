from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
DEBUG_MODE = os.getenv("DEBUG_MODE", "")

# Configure logging
if DEBUG_MODE == "dev":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Carmen AI agent",
    description="API for Carmen AI agent",
    version="1.0.0"
)

# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with format: [YYYY-MM-DD HH:MM:SS] METHOD PATH STATUS"""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = datetime.now() - start_time
    
    log_message = f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path} {response.status_code}"
    logger.info(log_message)
    
    return response


# Health check route
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Initialize database
try:
    from app.database import init_database
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
    logger.error("=" * 70)
    logger.error("CRITICAL: Database initialization failed!")
    logger.error("The application will continue, but history endpoints will not work.")
    logger.error("Please check:")
    logger.error("  1. MySQL is running (docker-compose ps)")
    logger.error("  2. Database credentials in .env file are correct")
    logger.error("  3. Database 'carmen' exists")
    logger.error("=" * 70)

# Preload agent after app initialization
# This ensures the agent is initialized at server startup
try:
    from app.agent import agent as _agent
    if _agent is None:
        logger.warning("Agent failed to initialize. Check agent.py logs.")
    else:
        logger.info("Agent preloaded successfully")
except Exception as e:
    logger.error(f"Failed to preload agent: {str(e)}")


# Import routes after app initialization
from app.core_routes import router
app.include_router(router, prefix="/api", tags=["analysis"])


# Entry point for running with: python server.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
