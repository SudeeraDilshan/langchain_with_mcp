from mcp.server.fastmcp import FastMCP 
from db_helpers import get_customers, get_customer_by_id, add_customer, update_customer, delete_customer, get_customer_by_name
from textwrap import dedent
import logging
from api_helpers import make_nws_request, format_alert

mcp =FastMCP("mcp-server") 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting MCP server...")
logging.info("MCP server started successfully.")
logging.info("Listening for incoming requests...")

NWS_API_BASE = "https://api.weather.gov"


@mcp.tool()
def get_red_value(b:int) -> int:
    return b+5

@mcp.tool()
async def list_customers() -> str:
    """List all customers in the database.
    
    Args:
        None
    """
    logging.info("Processing request to list all customers")
    customers = await get_customers()
    
    if not customers:
        logging.info("No customers found in the database")
        return "No customers found in the database."
    
    result = "Customers:\n"
    for customer in customers:
        result += dedent(f"""
        ID: {customer.get('id')}
        Name: {customer.get('name', 'N/A')}
        Email: {customer.get('email', 'N/A')}
        Age: {customer.get('age', 'N/A')}
        Prefer Package: {customer.get('prefer_package', 'N/A')}
        ---
        """)
    
    logging.info(f"Returning list of {len(customers)} customers")
    return result

@mcp.tool()
async def get_customer(customer_id: int) -> str:
    """Get details of a specific customer by ID.
    
    Args:
        customer_id: Unique identifier of the customer to retrieve
    """
    logging.info(f"Processing request to get customer with ID: {customer_id}")
    customer = await get_customer_by_id(customer_id)
    
    if not customer:
        logging.info(f"No customer found with ID: {customer_id}")
        return f"No customer found with ID: {customer_id}"
    
    logging.info(f"Successfully retrieved customer with ID: {customer_id}")
    return dedent(f"""
    Customer Details:
    ID: {customer.get('id')}
    Name: {customer.get('name', 'N/A')}
    Email: {customer.get('email', 'N/A')}
    Age: {customer.get('age', 'N/A')}
    Prefer Package: {customer.get('prefer_package', 'N/A')}
    """)

@mcp.tool()
async def create_customer(name: str, email: str, age: int = None, prefer_package: int = None) -> str:
    """Create a new customer in the database.
    
    Args:
        name: Customer's full name
        email: Customer's email address
        age: Customer's age (optional)
        prefer_package: Customer's preferred package ID (optional)
    """
    logging.info(f"Processing request to create new customer: name='{name}', email='{email}', age={age}, prefer_package={prefer_package}")
    
    if not name or not email:
        logging.warning("Customer creation failed: Missing required name or email")
        return "Error: Customer name and email are required."
    
    customer = await add_customer(name, email, age, prefer_package)
    
    if not customer:
        logging.error("Failed to create customer in database")
        return "Failed to create customer. Please check database connection and try again."
    
    logging.info(f"Successfully created new customer with ID: {customer.get('id')}")
    return dedent(f"""
    Customer created successfully:
    ID: {customer.get('id')}
    Name: {customer.get('name')}
    Email: {customer.get('email')}
    Age: {customer.get('age', 'N/A')}
    Prefer Package: {customer.get('prefer_package', 'N/A')}
    """)

@mcp.tool()
async def modify_customer(customer_id: int, name: str = None, email: str = None, age: int = None, prefer_package: int = None) -> str:
    """Update an existing customer's information.
    
    Args:
        customer_id: Unique identifier of the customer to update
        name: New customer name (optional)
        email: New customer email (optional)
        age: New customer age (optional)
        prefer_package: New preferred package ID (optional)
    """
    if not any([name, email, age,prefer_package]):
        return "Error: At least one field (name, email, or phone) must be provided for update."
    
    customer = await update_customer(customer_id, name, email, age,prefer_package)
    
    if not customer:
        return f"Failed to update customer with ID: {customer_id}. Customer may not exist."
    
    return dedent(f"""
    Customer updated successfully:
    ID: {customer.get('id')}
    Name: {customer.get('name')}
    Email: {customer.get('email')}
    Age: {customer.get('age', 'N/A')}
    Prefer Package: {customer.get('prefer_package', 'N/A')}
    """)

@mcp.tool()
async def remove_customer(customer_id: int) -> str:
    """Remove a customer from the database.
    
    Args:
        customer_id: Unique identifier of the customer to delete
    """
    success = await delete_customer(customer_id)
    
    if not success:
        return f"Failed to delete customer with ID: {customer_id}. Customer may not exist."
    
    return f"Customer with ID: {customer_id} has been successfully deleted."

@mcp.tool()
async def find_customers_by_name(name: str) -> str:
    """Find customers by name (full or partial match).
    
    Args:
        name: Full or partial customer name to search for
    """
    if not name:
        return "Error: Customer name is required for searching."
    
    customers = await get_customer_by_name(name)
    
    if not customers:
        return f"No customers found with name containing: '{name}'"
    
    result = f"Found {len(customers)} customer(s) matching '{name}':\n"
    for customer in customers:
        result += dedent(f"""
        ID: {customer.get('id')}
        Name: {customer.get('name', 'N/A')}
        Email: {customer.get('email', 'N/A')}
        Age: {customer.get('age', 'N/A')}
        Prefer Package: {customer.get('prefer_package', 'N/A')}
        ---
        """)
    
    return result


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    logging.info(f"Processing request for weather alerts in state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    
    # Helper function call
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logging.warning(f"Failed to get alerts for state {state} or no 'features' in response")
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        logging.info(f"No active weather alerts found for state: {state}")
        return "No active alerts for this state."

    # Helper function call
    logging.info(f"Found {len(data['features'])} alerts for state: {state}")
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    logging.info(f"Processing request for weather forecast at coordinates: {latitude}, {longitude}")
    
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    logging.debug(f"Requesting points data from: {points_url}")
    # Helper function call
    points_data = await make_nws_request(points_url)

    if not points_data:
        logging.warning(f"Failed to get points data for coordinates: {latitude}, {longitude}")
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    logging.debug(f"Requesting forecast from: {forecast_url}")
    # Helper function call
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        logging.warning("Failed to get detailed forecast data")
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    logging.info(f"Received forecast with {len(periods)} time periods")
    
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        logging.debug(f"Formatting forecast for period: {period['name']}")
        forecast = dedent(
            f"""
            {period['name']}:
            Temperature: {period['temperature']}°{period['temperatureUnit']}
            Wind: {period['windSpeed']} {period['windDirection']}
            Forecast: {period['detailedForecast']}
            """
        )
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)



if __name__ =="__main__":
    mcp.run(transport="stdio")