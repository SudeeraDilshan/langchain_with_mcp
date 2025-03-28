import asyncpg
from typing import List, Dict, Any, Optional
import logging
import traceback
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", 5432)
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")  # Default password, change as needed
database = os.getenv("DB_NAME")  # Default database, change as needed

# Database connection parameters
DB_CONFIG = {
    "host": host,
    "port": port,
    "user": user,
    "password": password,  # Make sure this matches your PostgreSQL password
    "database": database   # Make sure this database exists
}

async def get_connection_pool():
    """Create and return a connection pool to the PostgreSQL database."""
    try:
        logging.info(f"Establishing connection pool to PostgreSQL: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
        pool = await asyncpg.create_pool(**DB_CONFIG)
        logging.info("Database connection pool created successfully")
        return pool
    except Exception as e:
        logging.error(f"Failed to create database connection pool: {e}")
        logging.debug(f"Connection error details: {traceback.format_exc()}")
        return None

async def get_customers() -> List[Dict[str, Any]]:
    """Retrieve all customers from the customers table."""
    logging.info("Attempting to retrieve all customers")
    pool = await get_connection_pool()
    if not pool:
        logging.error("Cannot retrieve customers - failed to establish connection pool")
        return []
    
    try:
        async with pool.acquire() as conn:
            logging.debug("Executing query: SELECT * FROM customers")
            rows = await conn.fetch("SELECT * FROM customers")
            # Convert to list of dictionaries
            customers = [dict(row) for row in rows]
            logging.info(f"Retrieved {len(customers)} customers from database")
            return customers
    except Exception as e:
        logging.error(f"Database query error while retrieving customers: {e}")
        logging.debug(f"Query error details: {traceback.format_exc()}")
        return []
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()

async def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]: 
    """Retrieve a customer by their ID."""
    logging.info(f"Attempting to retrieve customer with ID: {customer_id}")
    pool = await get_connection_pool()
    if not pool:
        logging.error(f"Cannot retrieve customer {customer_id} - failed to establish connection pool")
        return None
    
    try:
        async with pool.acquire() as conn:
            logging.debug(f"Executing query: SELECT * FROM customers WHERE id = {customer_id}")
            row = await conn.fetchrow("SELECT * FROM customers WHERE id = $1", customer_id)
            if row:
                logging.info(f"Successfully retrieved customer: {customer_id}")
                return dict(row)
            else:
                logging.info(f"No customer found with ID: {customer_id}")
                return None
    except Exception as e:
        logging.error(f"Database query error retrieving customer {customer_id}: {e}")
        logging.debug(f"Query error details: {traceback.format_exc()}")
        return None
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()

async def get_customer_by_name(name: str) -> List[Dict[str, Any]]:
    """Retrieve customers by their name."""
    logging.info(f"Searching for customers with name matching: '{name}'")
    pool = await get_connection_pool()
    if not pool:
        logging.error(f"Cannot search by name '{name}' - failed to establish connection pool")
        return []
    
    try:
        async with pool.acquire() as conn:
            search_pattern = f"%{name}%"
            logging.debug(f"Executing query: SELECT * FROM customers WHERE name ILIKE '{search_pattern}'")
            # Use ILIKE for case-insensitive search with pattern matching
            rows = await conn.fetch("SELECT * FROM customers WHERE name ILIKE $1", search_pattern)
            customers = [dict(row) for row in rows]
            logging.info(f"Found {len(customers)} customers matching name '{name}'")
            return customers
    except Exception as e:
        logging.error(f"Database query error during name search '{name}': {e}")
        logging.debug(f"Query error details: {traceback.format_exc()}")
        return []
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()

async def add_customer(name: str, email: str, age: int = None,prefer_package: int=None) -> Optional[Dict[str, Any]]:
    """Add a new customer to the database."""
    logging.info(f"Attempting to add new customer: name={name}, email={email}")
    pool = await get_connection_pool()
    if not pool:
        logging.error("Cannot add customer - failed to establish connection pool")
        return None
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO customers (name, email, age, prefer_package) VALUES ($1, $2, $3, $4) RETURNING *",
                name, email, age, prefer_package
            )
            if row:
                logging.info(f"Successfully added customer: {name}")
                return dict(row)
            else:
                logging.error(f"Failed to add customer: {name}")
                return None
    except Exception as e:
        logging.error(f"Database insert error while adding customer {name}: {e}")
        logging.debug(f"Insert error details: {traceback.format_exc()}")
        return None
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()

async def update_customer(customer_id: int, name: str = None, email: str = None, age: int = None, prefer_package: int=None) -> Optional[Dict[str, Any]]:
    """Update an existing customer."""
    logging.info(f"Attempting to update customer with ID: {customer_id}")
    pool = await get_connection_pool()
    if not pool:
        logging.error(f"Cannot update customer {customer_id} - failed to establish connection pool")
        return None
    
    try:
        async with pool.acquire() as conn:
            # Get current values
            logging.debug(f"Fetching current values for customer ID: {customer_id}")
            current = await conn.fetchrow("SELECT id,name, email, age, prefer_package FROM customers WHERE id = $1", customer_id)
            if not current:
                logging.info(f"No customer found with ID: {customer_id}")
                return None
            
            # Update with new values or keep existing ones
            new_name = name if name is not None else current['name']
            new_email = email if email is not None else current['email']
            new_age = age if age is not None else current['age']
            new_prefer_package = prefer_package if prefer_package is not None else current['prefer_package']
            
            logging.debug(f"Executing update for customer ID: {customer_id}")
            row = await conn.fetchrow(
                "UPDATE customers SET name = $1, email = $2, age = $3, prefer_package = $5 WHERE id = $4 RETURNING *",
                new_name, new_email, new_age, customer_id, new_prefer_package
            )
            if row:
                logging.info(f"Successfully updated customer ID: {customer_id}")
                return dict(row)
            else:
                logging.error(f"Failed to update customer ID: {customer_id}")
                return None
    except Exception as e:
        logging.error(f"Database update error for customer {customer_id}: {e}")
        logging.debug(f"Update error details: {traceback.format_exc()}")
        return None
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()

async def delete_customer(customer_id: int) -> bool:
    """Delete a customer by their ID."""
    logging.info(f"Attempting to delete customer with ID: {customer_id}")
    pool = await get_connection_pool()
    if not pool:
        logging.error(f"Cannot delete customer {customer_id} - failed to establish connection pool")
        return False
    
    try:
        async with pool.acquire() as conn:
            logging.debug(f"Executing delete for customer ID: {customer_id}")
            result = await conn.execute("DELETE FROM customers WHERE id = $1", customer_id)
            # Check if any rows were affected
            if 'DELETE' in result:
                logging.info(f"Successfully deleted customer ID: {customer_id}")
                return True
            else:
                logging.error(f"Failed to delete customer ID: {customer_id}")
                return False
    except Exception as e:
        logging.error(f"Database delete error for customer {customer_id}: {e}")
        logging.debug(f"Delete error details: {traceback.format_exc()}")
        return False
    finally:
        logging.debug("Closing database connection pool")
        await pool.close()
