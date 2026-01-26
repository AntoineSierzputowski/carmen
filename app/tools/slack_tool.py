"""
Slack notification tool for LangChain agent.

This tool allows the agent to send messages to Slack channels via webhook.
"""

import os
import logging
import requests
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Slack webhook URL from environment
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


class SlackMessageInput(BaseModel):
    """Input schema for Slack message tool."""
    
    channel: str = Field(
        description="Slack channel name (e.g., '#general', '#alerts') or channel ID. Can be omitted if webhook is configured for a specific channel."
    )
    message: str = Field(
        description="The message content to send to Slack. Can include markdown formatting."
    )


def send_slack_message(channel: str, message: str) -> str:
    """
    Send a message to Slack via webhook.
    
    Args:
        channel: Slack channel name or ID (optional if webhook is channel-specific)
        message: Message content to send
        
    Returns:
        Status string indicating success or failure
    """
    if not SLACK_WEBHOOK_URL:
        error_msg = "SLACK_WEBHOOK_URL environment variable is not set"
        logger.error(error_msg)
        return f"Error: {error_msg}. Please configure SLACK_WEBHOOK_URL in your .env file."
    
    try:
        # Slack webhook payload
        payload = {
            "text": message,
            "channel": channel if channel else None
        }
        
        # Remove None values from payload
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Send POST request to Slack webhook
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        
        # Check response status
        if response.status_code == 200:
            logger.info(f"Successfully sent message to Slack channel: {channel}")
            return f"Success: Message sent to Slack channel '{channel}'"
        else:
            error_msg = f"Slack API returned status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            return f"Error: Failed to send message to Slack - {error_msg}"
            
    except requests.exceptions.Timeout:
        error_msg = "Request to Slack webhook timed out"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to Slack webhook: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send message to Slack - {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Error: Failed to send message to Slack - {error_msg}"


# Create LangChain StructuredTool
slack_notification_tool = StructuredTool(
    name="send_slack_message",
    description=(
        "Send a notification message to a Slack channel via webhook. "
        "Use this tool when you need to alert users about plant conditions, analysis results, or important events. "
        "The message can include markdown formatting. "
        "Requires SLACK_WEBHOOK_URL to be configured in environment variables."
    ),
    func=send_slack_message,
    args_schema=SlackMessageInput
)
