# Carmen

**Intelligent Plant Care Analysis System**

Carmen is an AI-powered API that analyzes sensor data from plants and provides intelligent recommendations for optimal plant care. Built with FastAPI and LangChain, it uses local LLM (Ollama Mistral 7B) to provide contextual analysis and actionable insights.

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

-  **AI-Powered Analysis**: Uses local LLM (Ollama/Mistral) for intelligent plant condition analysis
-  **Multi-Sensor Support**: Analyzes humidity, light, and temperature data
-  **Plant-Specific Recommendations**: Compares sensor data against ideal conditions for different plant types
-  **Modular Pipeline Architecture**: Extensible node-based processing system
-  **Fast & Efficient**: Built with FastAPI for high performance
-  **Privacy-First**: Runs entirely locally with Ollama - no data sent to external services
- **Historical Data Storage**: All analyses and actions are automatically saved to MySQL for tracking and analysis

## Architecture

Carmen follows a clean, modular architecture:

```
app/
├── server.py          # FastAPI application, middlewares, error handlers
├── core_routes.py     # Business routes (API endpoints)
├── agent.py           # LLM agent initialization and pipeline orchestration
├── models.py          # Pydantic models for request/response validation
├── state.py           # Centralized state management for pipeline
├── nodes/             # Processing nodes (comparison logic)
│   ├── soil_moisture.py
│   ├── temperature.py
│   └── light_node.py
├── tools/             # LangChain tools (extensible)
├── utils/             # Utility functions
└── data/              # Plant ideal conditions database
    └── plants_ideal.json
```

### Pipeline Flow

1. **Request Reception**: FastAPI receives sensor data
2. **State Creation**: Data is structured into a centralized State object
3. **Node Processing**: Sequential execution of comparison nodes:
   - Soil moisture comparison
   - Temperature comparison
   - Light intensity comparison
4. **AI Analysis**: LLM analyzes enriched state and generates recommendations
5. **Response Formatting**: Structured response with status, message, and action

## Quick Start

### Prerequisites

- Python 3.14+
- [Ollama](https://ollama.ai/) installed and running
- Mistral model downloaded in Ollama
- MySQL server (can be installed locally or via Docker - see setup instructions)
- Docker and Docker Compose (optional, for MySQL container)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AntoineSierzputowski/carmen.git
   cd carmen
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Ollama**
   ```bash
   # Install Ollama (if not already installed)
   # Visit https://ollama.ai/ for installation instructions
   
   # Pull the Mistral model
   ollama pull mistral
   ```

4. **Set up MySQL database**

   **Option A: Using Docker (Recommended)**
   ```bash
   # Make sure Docker is installed and running
   # Start MySQL container
   docker-compose up -d mysql
   
   # Check if MySQL is running
   docker-compose ps
   ```
   
   **Option B: Local MySQL installation**
   ```bash
   # Install MySQL (if not already installed)
   # On macOS: brew install mysql
   # On Ubuntu: sudo apt-get install mysql-server
   # On Windows: Download from https://dev.mysql.com/downloads/mysql/
   
   # Start MySQL service
   # On macOS: brew services start mysql
   # On Ubuntu: sudo systemctl start mysql
   
   # Create the database (optional - will be created automatically)
   mysql -u root -p < init_database.sql
   
   # Or create manually:
   mysql -u root -p
   CREATE DATABASE carmen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

5. **Configure environment variables**
   ```bash
   # Create a .env file
   OLLAMA_API_URL=http://localhost:11434
   DEBUG_MODE=dev  # Optional: for debug logging
   
   # MySQL Configuration
   # For Docker: use the default values below
   # For local MySQL: adjust according to your setup
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=carmen123  # Default for Docker, change for local MySQL
   DB_NAME=carmen
   ```

6. **Run the server**
   ```bash
   # Using uvicorn directly
   uvicorn app.server:app --reload
   
   # Or using Python
   python -m app.server
   ```

The API will be available at `http://localhost:8000`

### 🐳 Using Docker for MySQL (Quick Start)

The easiest way to set up MySQL is using Docker:

```bash
# 1. Create a .env file with MySQL configuration
cat > .env << EOF
OLLAMA_API_URL=http://localhost:11434
DEBUG_MODE=dev
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=carmen123
DB_NAME=carmen
EOF

# 2. Start MySQL container
docker-compose up -d mysql

# 3. Wait a few seconds for MySQL to initialize, then start the server
uvicorn app.server:app --reload
```

### Docker Commands for MySQL

If you're using Docker for MySQL, here are some useful commands:

```bash
# Start MySQL container
docker-compose up -d mysql

# Stop MySQL container
docker-compose stop mysql

# Stop and remove MySQL container (data is preserved in volume)
docker-compose down mysql

# Stop and remove MySQL container and data
docker-compose down -v mysql

# View MySQL logs
docker-compose logs -f mysql

# Check MySQL status
docker-compose ps

# Access MySQL CLI inside container
docker-compose exec mysql mysql -u root -p
```

The MySQL data is persisted in a Docker volume (`mysql_data`), so your data will be preserved even if you stop the container.

## 📖 API Documentation

### Endpoints

#### `POST /api/analyze`

Analyzes sensor data and returns plant care recommendations.

**Request Body:**
```json
{
  "humidity": 60.0,
  "light": 1200.0,
  "temperature": 22.0,
  "plant_id": "basil-001",
  "plant_type": "basil"
}
```

**Request Fields:**
- `plant_id`: Unique ID of the plant instance (e.g., "basil-001", "tomato-123")
- `plant_type`: Type of plant for looking up ideal conditions (e.g., "basil", "tomato")

**Query Parameters (Testing Only):**
- `test_date`: ISO format date string (YYYY-MM-DDTHH:MM:SS) to simulate a specific timestamp.
  Use this to simulate multiple days by sending requests with different dates.
  Example: `?test_date=2024-01-15T10:30:00`

**Response:**
```json
{
  "status": "OK",
  "message": "Conditions are optimal for the plant",
  "action": "No action needed, conditions are optimal"
}
```

**Response Fields:**
- `status`: `"OK"` or `"ALERT"` - Overall condition status
- `message`: Detailed analysis explanation
- `action`: Descriptive sentence in English explaining recommended actions

#### `GET /api/history/{plant_id}`

Get analysis history for a specific plant.

**Path Parameters:**
- `plant_id`: ID of the plant (e.g., "basil", "tomato")

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "plant_id": "basil-001",
  "count": 2,
  "analyses": [
    {
      "id": 1,
      "plant_id": "basil-001",
      "timestamp": "2024-01-15T10:30:00",
      "sensor_data": {
        "humidity": 60.0,
        "light": 1200.0,
        "temperature": 22.0
      },
      "comparisons": {
        "soil_moisture": {...},
        "temperature": {...},
        "light": {...}
      },
      "status": "OK",
      "message": "Conditions are optimal",
      "action": "No action needed, conditions are optimal"
    }
  ]
}
```

#### `GET /api/history`

Get analysis history for all plants.

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "count": 5,
  "analyses": [
    {
      "id": 1,
      "plant_id": "basil-001",
      "timestamp": "2024-01-15T10:30:00",
      "sensor_data": {...},
      "comparisons": {...},
      "status": "OK",
      "message": "...",
      "action": "..."
    }
  ]
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📝 Example Requests

### Optimal Conditions
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 70,
    "light": 1200,
    "temperature": 22,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'
```

### Low Humidity (Needs Watering)
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 30,
    "light": 1200,
    "temperature": 22,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'
```

### Insufficient Light
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 70,
    "light": 200,
    "temperature": 22,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'
```

### Multiple Issues
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 25,
    "light": 300,
    "temperature": 8,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'
```

### Get Plant History
```bash
# Get history for a specific plant (by unique plant_id)
curl http://localhost:8000/api/history/basil-001?limit=10

# Get all history
curl http://localhost:8000/api/history?limit=50&offset=0
```

### Testing: Simulate Multiple Days
```bash
# Simulate data from different days by using test_date parameter
# Day 1
curl -X POST "http://localhost:8000/api/analyze?test_date=2024-01-15T10:30:00" \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 60,
    "light": 1200,
    "temperature": 22,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'

# Day 2
curl -X POST "http://localhost:8000/api/analyze?test_date=2024-01-16T10:30:00" \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 55,
    "light": 1100,
    "temperature": 21,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'

# Day 3
curl -X POST "http://localhost:8000/api/analyze?test_date=2024-01-17T10:30:00" \
  -H "Content-Type: application/json" \
  -d '{
    "humidity": 50,
    "light": 1000,
    "temperature": 20,
    "plant_id": "basil-001",
    "plant_type": "basil"
  }'
```

## 🌿 Supported Plants

Currently supported plants (defined in `app/data/plants_ideal.json`):

- **Basil** (`plant_id: "basil"`)
  - Ideal soil moisture: 70%
  - Temperature range: 18-25°C (ideal: 22°C)
  - Light range: 500-2000 lux (ideal: 1200 lux)

- **Tomato** (`plant_id: "tomato"`)
  - Ideal soil moisture: 65%
  - Temperature range: 20-30°C (ideal: 25°C)
  - Light range: 1000-3000 lux (ideal: 2000 lux)

To add more plants, edit `app/data/plants_ideal.json`.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_API_URL` | `http://localhost:11434` | Ollama API endpoint |
| `DEBUG_MODE` | (empty) | Set to `"dev"` for debug logging |
| `DB_HOST` | `localhost` | MySQL server host |
| `DB_PORT` | `3306` | MySQL server port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | (empty) | MySQL password |
| `DB_NAME` | `carmen` | MySQL database name |

### Adding Custom Tools

Tools can be added in `app/tools/` and registered in `app/tools/__init__.py`:

```python
# app/tools/__init__.py
from .my_custom_tool import my_custom_tool

TOOLS = [
    my_custom_tool,
]
```

### Adding Processing Nodes

Create new nodes in `app/nodes/` following the pattern:

```python
def my_node(plant_id: str, value: float) -> dict:
    """
    Process and compare value against ideal conditions.
    
    Returns:
        dict with 'status', 'message', 'value', 'ideal', etc.
    """
    # Your logic here
    return {
        "status": "OK",
        "message": "...",
        "value": value,
        # ...
    }
```

## Development

### Project Structure

```
carmen/
├── app/
│   ├── __init__.py
│   ├── server.py          # FastAPI app & middlewares
│   ├── core_routes.py     # API routes
│   ├── agent.py           # LLM agent & pipeline
│   ├── models.py           # Pydantic models
│   ├── state.py            # State management
│   ├── nodes/              # Processing nodes
│   ├── tools/              # LangChain tools
│   ├── utils/              # Utilities
│   └── data/               # Plant data
├── requirements.txt
├── .gitignore
└── README.md
```

### Running in Development Mode

```bash
# Enable debug logging
export DEBUG_MODE=dev

# Run with auto-reload
uvicorn app.server:app --reload
```

### Code Style

This project follows PEP 8 style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking