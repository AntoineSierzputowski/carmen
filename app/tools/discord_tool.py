"""
Discord notification tool for LangChain agent.

This tool allows the agent to send messages to Discord channels via webhook.
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

# Discord webhook URL from environment
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


class DiscordMessageInput(BaseModel):
    """Input schema for Discord message tool."""
    
    channel: str = Field(
        description="Discord channel name or ID. Can be omitted if webhook is configured for a specific channel."
    )
    message: str = Field(
        description="The message content to send to Discord. Can include markdown formatting and Discord-specific formatting."
    )


def send_discord_message(channel: str, message: str) -> str:
    """
    Send a message to Discord via webhook.
    
    Args:
        channel: Discord channel name or ID (optional if webhook is channel-specific)
        message: Message content to send
        
    Returns:
        Status string indicating success or failure
    """
    if not DISCORD_WEBHOOK_URL:
        error_msg = "DISCORD_WEBHOOK_URL environment variable is not set"
        logger.error(error_msg)
        return f"Error: {error_msg}. Please configure DISCORD_WEBHOOK_URL in your .env file."
    
    try:
        # Discord webhook payload
        # Discord webhooks have a max message length of 2000 characters
        if len(message) > 2000:
            message = message[:1997] + "..."
            logger.warning("Discord message truncated to 2000 characters")
        
        payload = {
            "content": message
        }
        
        # Add username if channel is specified (optional)
        if channel:
            payload["username"] = f"Carmen Bot - {channel}"
        
        # Send POST request to Discord webhook
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        
        # Check response status
        if response.status_code == 204:
            logger.info(f"Successfully sent message to Discord channel: {channel}")
            return f"Success: Message sent to Discord channel '{channel}'"
        elif response.status_code in [200, 201]:
            logger.info(f"Successfully sent message to Discord channel: {channel}")
            return f"Success: Message sent to Discord channel '{channel}'"
        else:
            error_msg = f"Discord API returned status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            return f"Error: Failed to send message to Discord - {error_msg}"
            
    except requests.exceptions.Timeout:
        error_msg = "Request to Discord webhook timed out"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to Discord webhook: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send message to Discord - {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Error: Failed to send message to Discord - {error_msg}"


# Create LangChain StructuredTool
discord_notification_tool = StructuredTool(
    name="send_discord_message",
    description=(
        "Send a notification message to a Discord channel via webhook. "
        "Use this tool when you need to alert users about plant conditions, analysis results, or important events. "
        "The message can include Discord markdown formatting. "
        "Requires DISCORD_WEBHOOK_URL to be configured in environment variables."
    ),
    func=send_discord_message,
    args_schema=DiscordMessageInput
)
