"""
Loggly Integration Module for ROGR API
Self-contained logging integration that can be easily removed.
"""

import logging
import json
import requests
from datetime import datetime
from typing import Optional


class LogglyHandler(logging.Handler):
    """Custom logging handler that sends logs to Loggly service."""
    
    def __init__(self, customer_token: str, service_name: str = "rogr-api"):
        super().__init__()
        self.url = f"https://logs-01.loggly.com/inputs/{customer_token}/tag/{service_name}/"
        self.service_name = service_name

    def emit(self, record):
        """Send log record to Loggly."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.name,
                'service': self.service_name
            }
            # Use timeout to prevent blocking the application
            requests.post(self.url, json=log_entry, timeout=2)
        except Exception:
            # Silently fail to avoid disrupting the main application
            pass


def setup_loggly_logging(customer_token: str = "c1cd1003-ccf8-40c0-bd86-53ef48b40bf1", 
                        service_name: str = "rogr-api",
                        log_level: int = logging.INFO) -> None:
    """
    Set up Loggly logging for the application.
    
    Args:
        customer_token: Loggly customer token for log ingestion
        service_name: Name of the service for log tagging
        log_level: Minimum logging level
    """
    # Configure basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(level=log_level)
    
    # Add Loggly handler
    loggly_handler = LogglyHandler(customer_token, service_name)
    logging.getLogger().addHandler(loggly_handler)


def log_endpoint_access(endpoint: str, method: str = "GET", user_id: Optional[str] = None) -> None:
    """Log API endpoint access."""
    message = f"{method} {endpoint}"
    if user_id:
        message += f" (user: {user_id})"
    logging.info(message)


def log_analysis_start(analysis_id: str, mode: str, source: str) -> None:
    """Log analysis operation start."""
    logging.info(f"Analysis started - ID: {analysis_id}, Mode: {mode}, Source: {source}")


def log_analysis_complete(analysis_id: str, success: bool, duration: Optional[float] = None) -> None:
    """Log analysis operation completion."""
    status = "completed" if success else "failed"
    message = f"Analysis {status} - ID: {analysis_id}"
    if duration:
        message += f", Duration: {duration:.2f}s"
    logging.info(message)


def log_error(message: str, error: Optional[Exception] = None) -> None:
    """Log error with optional exception details."""
    if error:
        logging.error(f"{message}: {str(error)}")
    else:
        logging.error(message)


def get_recent_logs(minutes: int = 10, size: int = 50, 
                   api_token: str = "2b379f67-1420-434d-95a8-ec842c5922bb",
                   subdomain: str = "rogr") -> dict:
    """
    Retrieve recent logs from Loggly.
    
    Args:
        minutes: Number of minutes back to search
        size: Maximum number of logs to return
        api_token: Loggly API token for retrieval
        subdomain: Loggly account subdomain
        
    Returns:
        Dictionary containing log events or error information
    """
    try:
        url = f"https://{subdomain}.loggly.com/apiv2/events/iterate"
        headers = {"Authorization": f"bearer {api_token}"}
        params = {
            "q": "service:rogr-api",
            "from": f"-{minutes}m",
            "until": "now",
            "size": size
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve logs: {str(e)}", "events": []}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "events": []}