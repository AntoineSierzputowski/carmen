"""
Agent LangChain initialization and pipeline processing.

This module handles:
- Agent initialization with LLM and tools
- Pipeline execution (nodes -> agent -> response formatting)
"""

import os
import json
import logging
import ast
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_community.llms import Ollama
from app.models import AnalysisResponse, SensorData
from app.state import State

# Import nodes and tools explicitly
from app.nodes.soil_moisture import soil_moisture
from app.nodes.temperature import temperature
from app.nodes.light_node import light
from app.nodes.history_node import history
from app.tools import TOOLS

# Load environment variables
load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
DEBUG_MODE = os.getenv("DEBUG_MODE", "")

logger = logging.getLogger(__name__)


def create_agent():
    """
    Initialize and return a LangChain agent with LLM and tools.
    If no tools are provided, returns the LLM directly.
    
    Returns:
        LangChain agent instance or LLM instance
        
    Raises:
        Exception: If agent initialization fails
    """
    try:
        llm = Ollama(
            base_url=OLLAMA_API_URL,
            model="mistral"
        )
        
        # If no tools, use LLM directly (no need for an agent)
        if not TOOLS or len(TOOLS) == 0:
            logger.info(f"No tools provided, using LLM directly with Ollama at {OLLAMA_API_URL}")
            return llm
        
        # Log tools count for debugging
        logger.info(f"Initializing agent with {len(TOOLS)} tool(s)")
        
        agent = initialize_agent(
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            llm=llm,
            tools=TOOLS,
            verbose=DEBUG_MODE == "dev",
            handle_parsing_errors=True
        )
        
        logger.info(f"LangChain agent initialized successfully with Ollama at {OLLAMA_API_URL}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize LangChain agent: {str(e)}", exc_info=True)
        raise


# Initialize global agent at module load time
try:
    agent = create_agent()
except Exception as e:
    logger.error(f"Failed to preload agent: {str(e)}", exc_info=True)
    agent = None


def create_state(sensor_data: SensorData) -> State:
    """
    Create State instance from SensorData.
    
    Args:
        sensor_data: SensorData instance with humidity, light, temperature, plant_id, plant_type
        
    Returns:
        State instance initialized with sensor data
    """
    return State(
        sensor_data={
            "humidity": sensor_data.humidity,
            "light": sensor_data.light,
            "temperature": sensor_data.temperature
        },
        plant_id=sensor_data.plant_id,  # Unique instance ID
        plant_type=sensor_data.plant_type,  # Plant type for JSON lookup
        comparisons={},
        metadata={}
    )


def process_with_pipeline(sensor_data: SensorData, test_timestamp: Optional[datetime] = None) -> AnalysisResponse:
    """
    Process sensor data through the pipeline: nodes -> agent -> response formatting.
    
    Pipeline flow:
    1. Execute nodes sequentially (each modifies the context)
    2. Pass enriched context to agent with tools
    3. Format agent response as AnalysisResponse
    
    Args:
        sensor_data: SensorData instance with humidity, light, temperature
        test_timestamp: [TESTING ONLY] Optional datetime to use instead of current time for DB storage
        
    Returns:
        AnalysisResponse with status, message, and action
        
    Raises:
        Exception: If agent is not initialized or processing fails
    """
    if agent is None:
        raise RuntimeError("LangChain agent is not initialized. Check server logs.")
    
    # Create state from sensor data
    state = create_state(sensor_data)
    
    # Execute comparison nodes
    logger.debug(f"Starting pipeline with plant_id: {state.plant_id} (type: {state.plant_type})")
    
    # Execute soil_moisture node (uses plant_type for JSON lookup)
    try:
        soil_moisture_result = soil_moisture(state.plant_type, state.sensor_data["humidity"])
        state.comparisons["soil_moisture"] = soil_moisture_result
        logger.debug(f"Soil moisture comparison completed: {soil_moisture_result['status']}")
    except Exception as e:
        logger.error(f"Error in soil_moisture node: {str(e)}")
        raise
    
    # Execute temperature node (uses plant_type for JSON lookup)
    try:
        temperature_result = temperature(state.plant_type, state.sensor_data["temperature"])
        state.comparisons["temperature"] = temperature_result
        logger.debug(f"Temperature comparison completed: {temperature_result['status']}")
    except Exception as e:
        logger.error(f"Error in temperature node: {str(e)}")
        raise
    
    # Execute light node (uses plant_type for JSON lookup)
    try:
        light_result = light(state.plant_type, state.sensor_data["light"])
        state.comparisons["light"] = light_result
        logger.debug(f"Light comparison completed: {light_result['status']}")
    except Exception as e:
        logger.error(f"Error in light node: {str(e)}")
        raise
    
    # Execute history node (retrieves and analyzes historical data)
    try:
        history_result = history(state.plant_id, limit=10)
        state.metadata["history"] = history_result
        if history_result.get("has_history"):
            logger.debug(f"History retrieved: {history_result['summary']['total_analyses']} analyses found")
        else:
            logger.debug("No history found for this plant")
    except Exception as e:
        logger.error(f"Error in history node: {str(e)}")
        # Don't fail the pipeline if history retrieval fails
        state.metadata["history"] = {"has_history": False, "error": str(e)}
    
    # Build prompt from state and comparisons
    prompt = f"""
    Analyze the following sensor data for plant {state.plant_id} (type: {state.plant_type}) and provide a JSON response:
    - Humidity: {state.sensor_data['humidity']}%
    - Light: {state.sensor_data['light']} lux
    - Temperature: {state.sensor_data['temperature']}°C
    
    Comparison results:
    - Soil moisture: {state.comparisons['soil_moisture']['status']} - {state.comparisons['soil_moisture']['message']}
    - Temperature: {state.comparisons['temperature']['status']} - {state.comparisons['temperature']['message']}
    - Light: {state.comparisons['light']['status']} - {state.comparisons['light']['message']}
    """
    
    # Add detailed comparison data if available
    if state.comparisons:
        prompt += f"\nDetailed comparisons: {json.dumps(state.comparisons, indent=2, default=str)}"
    
    # Add historical context if available
    if state.metadata.get("history") and state.metadata["history"].get("has_history"):
        history_data = state.metadata["history"]
        prompt += "\n\nHistorical context:"
        prompt += f"\n- Total previous analyses: {history_data['summary']['total_analyses']}"
        prompt += f"\n- Time span: {history_data['summary']['time_span_days']} day(s)"
        prompt += f"\n- Alert history: {history_data['summary']['alert_count']} alert(s) ({history_data['summary']['alert_percentage']}%)"
        
        if history_data.get("trends"):
            prompt += "\n- Trends (compared to historical average):"
            if "humidity" in history_data["trends"]:
                trend = history_data["trends"]["humidity"]
                prompt += f"\n  * Humidity: {trend['direction']} ({trend['change']:+.1f}%, avg: {trend['average_historical']:.1f}%)"
            if "light" in history_data["trends"]:
                trend = history_data["trends"]["light"]
                prompt += f"\n  * Light: {trend['direction']} ({trend['change']:+.1f} lux, avg: {trend['average_historical']:.1f} lux)"
            if "temperature" in history_data["trends"]:
                trend = history_data["trends"]["temperature"]
                prompt += f"\n  * Temperature: {trend['direction']} ({trend['change']:+.1f}°C, avg: {trend['average_historical']:.1f}°C)"
        
        if history_data['summary'].get("last_alert_date"):
            prompt += f"\n- Last alert: {history_data['summary']['last_alert_date']}"
        
        # Add recent values for context (last 3-5 analyses)
        if history_data.get("recent_analyses") and len(history_data["recent_analyses"]) > 1:
            prompt += "\n- Recent values (last analyses):"
            for i, analysis in enumerate(history_data["recent_analyses"][:5], 1):
                prompt += f"\n  {i}. {analysis['timestamp'][:10]} - H:{analysis['humidity']:.0f}% L:{analysis['light']:.0f} T:{analysis['temperature']:.1f}°C [{analysis['status']}]"
    
    prompt += """
    
    Return a JSON object with:
    - status: "OK" or "ALERT"
    - message: A clear explanation of the analysis
    - action: A descriptive sentence in English explaining what action should be taken.
      This should be a natural English sentence describing the problem and recommended action.
      Examples: 
      - "No action needed, conditions are optimal"
      - "Water the plant as soil moisture is too low"
      - "Increase lighting as light intensity is insufficient"
      - "Water the plant and increase lighting due to low moisture and insufficient light"
      - "Move the plant to a warmer location as temperature is too low"
    
    The action field must be a single descriptive sentence in English, not a list or array.
    If multiple issues exist, describe them in a natural sentence.
    
    Analyze the conditions and decide the best action(s) considering:
    - Current sensor readings (humidity, light, temperature)
    - Comparison with ideal conditions for this plant type
    - Historical trends (if available) - pay attention to whether values are improving, worsening, or stable
    - Previous alerts and patterns in the historical data
    - The specific needs of this plant type
    
    If historical data is available, use it to:
    - Detect trends (e.g., "humidity has been decreasing over the past week")
    - Avoid repetitive recommendations (e.g., if you just recommended watering, don't recommend it again immediately)
    - Provide context-aware advice (e.g., "humidity is low and has been decreasing, urgent action needed")
    
    Return ONLY valid JSON, no additional text.
    """
    
    # Invoke the agent or LLM
    try:
        # If agent is actually an LLM (when no tools), call it directly
        if hasattr(agent, 'run'):
            # It's an agent
            response = agent.run(prompt)
        else:
            # It's an LLM, call it directly
            response = agent(prompt)
    except Exception as e:
        logger.error(f"Error invoking agent/LLM: {str(e)}")
        raise
    
    # Parse and format response
    try:
        # Try to find JSON in the response
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            result = json.loads(json_str)
        else:
            # Fallback: create a simple response
            logger.warning(f"Agent response does not contain JSON: {response}")
            result = {
                "status": "OK",
                "message": response,
                "action": "aucune"
            }
    except json.JSONDecodeError as e:
        # If JSON parsing fails, create a structured response from the text
        logger.warning(f"Could not parse JSON from agent response: {response}, error: {str(e)}")
        result = {
            "status": "OK",
            "message": response,
            "action": "aucune"
        }
    
    # Extract action - convert to descriptive English sentence if needed
    action_value = result.get("action", "No action needed")
    
    # Handle different formats the LLM might return
    if isinstance(action_value, list):
        # Convert list to descriptive sentence
        if len(action_value) == 0:
            action_value = "No action needed"
        elif len(action_value) == 1:
            action_value = f"Take action: {action_value[0]}"
        else:
            # Multiple actions - create a descriptive sentence
            actions_str = ", ".join(action_value[:-1]) + f" and {action_value[-1]}"
            action_value = f"Take multiple actions: {actions_str}"
    elif not isinstance(action_value, str):
        # Convert other types to string
        action_value = str(action_value)
    
    # Clean up the action string
    action_value = action_value.strip()
    
    # Remove quotes if the action is wrapped in quotes (e.g., "['arroser', 'éclairer']")
    if action_value.startswith('"') and action_value.endswith('"'):
        action_value = action_value[1:-1]
    if action_value.startswith("'") and action_value.endswith("'"):
        action_value = action_value[1:-1]
    
    # If it looks like a Python list string, try to parse and convert to sentence
    if action_value.startswith('[') and action_value.endswith(']'):
        try:
            parsed_list = ast.literal_eval(action_value)
            if isinstance(parsed_list, list):
                if len(parsed_list) == 0:
                    action_value = "No action needed"
                elif len(parsed_list) == 1:
                    action_value = f"Take action: {parsed_list[0]}"
                else:
                    actions_str = ", ".join(parsed_list[:-1]) + f" and {parsed_list[-1]}"
                    action_value = f"Take multiple actions: {actions_str}"
        except:
            # If parsing fails, just use the string as is
            pass
    
    # Default if empty
    if not action_value:
        action_value = "No action needed"
    
    # Create AnalysisResponse
    analysis_response = AnalysisResponse(
        status=result.get("status", "OK"),
        message=result.get("message", "Analysis completed"),
        action=action_value
    )
    
    # Save analysis to database
    try:
        from app.database import save_analysis
        save_analysis(
            plant_id=state.plant_id,
            humidity=state.sensor_data["humidity"],
            light=state.sensor_data["light"],
            temperature=state.sensor_data["temperature"],
            comparisons=state.comparisons,
            status=analysis_response.status,
            message=analysis_response.message,
            action=analysis_response.action,
            timestamp=test_timestamp  # Use test_timestamp if provided (for testing)
        )
        if test_timestamp:
            logger.debug(f"[TESTING] Analysis saved to database for plant {state.plant_id} with test_timestamp: {test_timestamp}")
        else:
            logger.debug(f"Analysis saved to database for plant {state.plant_id}")
    except Exception as e:
        # Log error but don't fail the request if database save fails
        logger.error(f"Failed to save analysis to database: {str(e)}")
    
    return analysis_response