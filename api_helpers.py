from textwrap import dedent
import httpx
from typing import Any
import logging
import traceback
import time
import json

USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    logging.info(f"Making API request to: {url}")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            logging.debug(f"Sending GET request with headers: {headers}")
            response = await client.get(url, headers=headers, timeout=30.0)
            elapsed_time = time.time() - start_time
            logging.info(f"API response received in {elapsed_time:.2f}s (status: {response.status_code})")
            
            response.raise_for_status()
            data = response.json()
            logging.debug(f"API response data summary: {truncate_json_summary(data)}")
            return data
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP Error: {e} (status code: {e.response.status_code})")
            logging.debug(f"Response content: {e.response.text}")
            return None
        except httpx.RequestError as e:
            logging.error(f"Request Error: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e}")
            logging.debug(f"Raw response text: {response.text[:500]}")
            return None 
        except Exception as e:
            logging.error(f"Unexpected error in API request: {e}")
            logging.debug(f"Exception details: {traceback.format_exc()}")
            return None

def truncate_json_summary(data: dict) -> str:
    """Create a truncated summary of JSON data for logging purposes."""
    if not data:
        return "empty data"
    
    try:
        summary = {}
        for key, value in data.items():
            if isinstance(value, dict):
                summary[key] = f"{{...}} ({len(value)} keys)"
            elif isinstance(value, list):
                summary[key] = f"[...] ({len(value)} items)"
            else:
                if isinstance(value, str) and len(value) > 50:
                    summary[key] = f"{value[:50]}..."
                else:
                    summary[key] = value
        return str(summary)
    except Exception:
        return "data summary unavailable"

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    logging.debug(f"Formatting alert: {props.get('event', 'Unknown')} - {props.get('areaDesc', 'Unknown')}")
    return dedent(
        f"""
        Event: {props.get('event', 'Unknown')}
        Area: {props.get('areaDesc', 'Unknown')}
        Severity: {props.get('severity', 'Unknown')}
        Description: {props.get('description', 'No description available')}
        Instructions: {props.get('instruction', 'No specific instructions provided')}
        """
    )