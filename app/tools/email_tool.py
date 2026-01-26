"""
Email notification tool for LangChain agent.

This tool allows the agent to send email notifications via SMTP.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

# You need to add this tool to your agent => app/tools/__init__.py
load_dotenv()

logger = logging.getLogger(__name__)

# SMTP configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


class EmailMessageInput(BaseModel):
    """Input schema for email message tool."""
    
    recipient: EmailStr = Field(
        description="Email address of the recipient"
    )
    subject: str = Field(
        description="Email subject line"
    )
    message: str = Field(
        description="Email message body content. Can include plain text or HTML."
    )


def send_email_message(recipient: str, subject: str, message: str) -> str:
    """
    Send an email message via SMTP.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        message: Email message body content
        
    Returns:
        Status string indicating success or failure
    """
    # Validate SMTP configuration
    if not SMTP_HOST:
        error_msg = "SMTP_HOST environment variable is not set"
        logger.error(error_msg)
        return f"Error: {error_msg}. Please configure SMTP settings in your .env file."
    
    if not SMTP_USER:
        error_msg = "SMTP_USER environment variable is not set"
        logger.error(error_msg)
        return f"Error: {error_msg}. Please configure SMTP settings in your .env file."
    
    if not SMTP_PASSWORD:
        error_msg = "SMTP_PASSWORD environment variable is not set"
        logger.error(error_msg)
        return f"Error: {error_msg}. Please configure SMTP settings in your .env file."
    
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add plain text version
        text_part = MIMEText(message, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Try to add HTML version if message contains HTML-like content
        # Otherwise, use plain text as HTML too
        if '<' in message and '>' in message:
            html_part = MIMEText(message, 'html', 'utf-8')
        else:
            # Convert plain text to HTML
            html_message = message.replace('\n', '<br>\n')
            html_part = MIMEText(html_message, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Connect to SMTP server
        if SMTP_PORT == 465:
            # SSL connection
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        else:
            # TLS connection (default for port 587)
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
        
        # Authenticate
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Successfully sent email to {recipient} with subject: {subject}")
        return f"Success: Email sent to {recipient} with subject '{subject}'"
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send email - {error_msg}"
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Recipient email address refused: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send email - {error_msg}"
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"SMTP server disconnected: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send email - {error_msg}"
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        logger.error(error_msg)
        return f"Error: Failed to send email - {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Error: Failed to send email - {error_msg}"


# Create LangChain StructuredTool
email_notification_tool = StructuredTool(
    name="send_email_message",
    description=(
        "Send an email notification via SMTP. "
        "Use this tool when you need to send detailed plant analysis reports, alerts, or important notifications via email. "
        "Requires SMTP configuration (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM) in environment variables."
    ),
    func=send_email_message,
    args_schema=EmailMessageInput
)
