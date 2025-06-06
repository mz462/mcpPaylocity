"""
Paylocity MCP Server

This module provides a Model Context Protocol (MCP) server for accessing Paylocity API data.
It exposes Paylocity resources and tools through the MCP interface.
"""

from typing import Any, Dict, List, Optional, Union
import os
import json
import sys
import logging
import time
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ModelHint, ModelPreferences
from .paylocity_client import PaylocityClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger('mcppaylocity')

# Register custom URI scheme for paylocity resources
PAYLOCITY_SCHEME = "paylocity"

# Default instructions presented in the MCP handshake
INSTRUCTIONS = (
    "This server exposes Paylocity resources and tools. "
    "Use the provided resources to fetch employee, payroll and code data."
)

# Package version used in the handshake
SERVER_VERSION = "0.1.0"

def main():
    """
    Main entry point for the Paylocity MCP server.
    Initializes the server, configures resources and tools, and starts the server.
    """
    try:
        logger.info("Starting Paylocity MCP server...")
        # Load environment variables from .env file
        load_dotenv()
        logger.info("Loaded environment variables")
        
        # Get configuration from environment variables
        client_id = os.getenv("PAYLOCITY_CLIENT_ID")
        client_secret = os.getenv("PAYLOCITY_CLIENT_SECRET")
        environment = os.getenv("PAYLOCITY_ENVIRONMENT", "production")

        # Optional model preference settings
        cost_pref = os.getenv("MODEL_COST_PRIORITY")
        speed_pref = os.getenv("MODEL_SPEED_PRIORITY")
        intel_pref = os.getenv("MODEL_INTELLIGENCE_PRIORITY")
        hints_pref = os.getenv("MODEL_HINTS")

        model_prefs: ModelPreferences | None = None
        if any([cost_pref, speed_pref, intel_pref, hints_pref]):
            hints: list[ModelHint] | None = None
            if hints_pref:
                hints = [ModelHint(name=h.strip()) for h in hints_pref.split(',') if h.strip()]

            model_prefs = ModelPreferences(
                hints=hints,
                costPriority=float(cost_pref) if cost_pref else None,
                speedPriority=float(speed_pref) if speed_pref else None,
                intelligencePriority=float(intel_pref) if intel_pref else None,
            )
        
        # Get company IDs
        company_ids_str = os.getenv("PAYLOCITY_COMPANY_IDS", "")
        company_ids = [id.strip() for id in company_ids_str.split(",") if id.strip()]
        
        # Validate required environment variables
        missing_vars = []
        if not client_id:
            missing_vars.append("PAYLOCITY_CLIENT_ID")
        if not client_secret:
            missing_vars.append("PAYLOCITY_CLIENT_SECRET")
        if not company_ids:
            missing_vars.append("PAYLOCITY_COMPANY_IDS")
            
        if missing_vars:
            error_msg = "Missing required environment variables: {}".format(', '.join(missing_vars))
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Environment: %s", environment)
        logger.info("Company IDs: %s", company_ids)
        
        # Create FastMCP instance with handshake metadata
        mcp = FastMCP("Paylocity", instructions=INSTRUCTIONS)
        mcp._mcp_server.version = SERVER_VERSION

        if model_prefs is not None:
            logger.info("Model preferences configured: %s", model_prefs.model_dump())
        else:
            logger.info("No model preferences configured")
        
        # Configure WebSocket settings
        # Note: FastMCP handles WebSocket transport automatically
        # We just need to set the appropriate parameters
        
        # Initialize Paylocity client
        client = PaylocityClient(client_id, client_secret, environment)
        
        # Register resources
        register_resources(mcp, client, company_ids)
        
        # Register tools
        register_tools(mcp, client, company_ids)
        
        logger.info("Starting server with WebSocket transport...")
        # Run the server
        mcp.run()
    except Exception as e:
        logger.error("Error starting server: %s", str(e), exc_info=True)
        raise

def register_resources(mcp, client, company_ids):
    """
    Register all Paylocity resources with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        client: The PaylocityClient instance
        company_ids: List of company IDs to use
    """
    @mcp.resource("{}://employees/{{company_id}}".format(PAYLOCITY_SCHEME))
    def get_employees(company_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get all employees for a company."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        logger.info("Getting employees for company_id=%s", company_id_str)
        
        # Implement retry logic for handling timeouts
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                return client.get_all_employees(company_id_str)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %d failed: %s. Retrying in %d seconds...", attempt+1, str(e), retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed after %d attempts: %s", max_retries, str(e))
                    raise
    
    @mcp.resource("{}://employees/{{company_id}}/{{employee_id}}".format(PAYLOCITY_SCHEME))
    def get_employee_details(company_id: Optional[Union[str, int]] = None, employee_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get details for a specific employee."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        print("Getting employee details for company_id={}, employee_id={}".format(company_id_str, employee_id_str), file=sys.stderr)
        return client.get_employee_details(company_id_str, employee_id_str)
    
    @mcp.resource("{}://earnings/{{company_id}}/{{employee_id}}".format(PAYLOCITY_SCHEME))
    def get_earnings(company_id: Optional[Union[str, int]] = None, employee_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get earnings data for a specific employee."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        print("Getting earnings for company_id={}, employee_id={}".format(company_id_str, employee_id_str), file=sys.stderr)
        return client.get_employee_earnings(company_id_str, employee_id_str)
    
    @mcp.resource("{}://codes/{{company_id}}/{{code_resource}}".format(PAYLOCITY_SCHEME))
    def get_codes(company_id: Optional[Union[str, int]] = None, code_resource: str = None) -> Dict[str, Any]:
        """Get company codes for a specific resource."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        print("Getting codes for company_id={}, code_resource={}".format(company_id_str, code_resource), file=sys.stderr)
        return client.get_company_codes(company_id_str, code_resource)

    @mcp.resource("{}://localtaxes/{{company_id}}/{{employee_id}}".format(PAYLOCITY_SCHEME))
    def get_local_taxes(company_id: Optional[Union[str, int]] = None, employee_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get local taxes for a specific employee."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        print("Getting local taxes for company_id={}, employee_id={}".format(company_id_str, employee_id_str), file=sys.stderr)
        return client.get_employee_local_taxes(company_id_str, employee_id_str)

    @mcp.resource("{}://paystatement/{{company_id}}/{{employee_id}}/{{year}}/{{check_date}}".format(PAYLOCITY_SCHEME))
    def get_paystatement_details(
        company_id: Optional[Union[str, int]] = None, 
        employee_id: Optional[Union[str, int]] = None,
        year: Union[str, int] = None,
        check_date: str = None
    ) -> Dict[str, Any]:
        """Get pay statement details for a specific employee, year and check date."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        year_str = str(year)
        print("Getting pay statement details for company_id={}, employee_id={}, year={}, check_date={}".format(company_id_str, employee_id_str, year_str, check_date), file=sys.stderr)
        return client.get_employee_paystatement_details(company_id_str, employee_id_str, year_str, check_date)

def register_tools(mcp, client, company_ids):
    """
    Register all Paylocity tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        client: The PaylocityClient instance
        company_ids: List of company IDs to use
    """
    # Helper function to create a new Paylocity client (for lazy initialization)
    def create_paylocity_client():
        client_id = os.getenv("PAYLOCITY_CLIENT_ID")
        client_secret = os.getenv("PAYLOCITY_CLIENT_SECRET")
        environment = os.getenv("PAYLOCITY_ENVIRONMENT", "production")
        return PaylocityClient(client_id, client_secret, environment)
    
    # Helper function for implementing retry logic
    def with_retry(func, *args, **kwargs):
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %d failed: %s. Retrying in %d seconds...", attempt+1, str(e), retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed after %d attempts: %s", max_retries, str(e))
                    raise
    
    @mcp.tool()
    def fetch_employees(company_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Fetch all employees for a company.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
        """
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        return with_retry(client.get_all_employees, company_id_str)
    
    @mcp.tool()
    def fetch_employee_details(company_id: Optional[Union[str, int]] = None, employee_id: Union[str, int] = None) -> Dict[str, Any]:
        """
        Fetch details for a specific employee.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
            employee_id: Employee ID (string or integer) to get details for.
        """
        if employee_id is None:
            raise ValueError("employee_id is required")
            
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        return client.get_employee_details(company_id_str, employee_id_str)
    
    @mcp.tool()
    def fetch_employee_earnings(company_id: Optional[Union[str, int]] = None, employee_id: Union[str, int] = None) -> Dict[str, Any]:
        """
        Fetch earnings data for a specific employee.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
            employee_id: Employee ID (string or integer) to get earnings for.
        """
        if employee_id is None:
            raise ValueError("employee_id is required")
            
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        return client.get_employee_earnings(company_id_str, employee_id_str)
    
    @mcp.tool()
    def fetch_company_codes(company_id: Optional[Union[str, int]] = None, code_resource: str = None) -> Dict[str, Any]:
        """
        Fetch company codes for a specific resource.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
            code_resource: Code resource to fetch (e.g., 'earnings', 'deductions', 'costcenter1', etc.)
        """
        if code_resource is None:
            raise ValueError("code_resource is required")
            
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        return client.get_company_codes(company_id_str, code_resource)

    @mcp.tool()
    def fetch_employee_local_taxes(company_id: Optional[Union[str, int]] = None, employee_id: Union[str, int] = None) -> Dict[str, Any]:
        """
        Fetch local taxes for a specific employee.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
            employee_id: Employee ID (string or integer) to get local taxes for.
        """
        if employee_id is None:
            raise ValueError("employee_id is required")
            
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        return client.get_employee_local_taxes(company_id_str, employee_id_str)

    @mcp.tool()
    def fetch_employee_paystatement_details(
        company_id: Optional[Union[str, int]] = None, 
        employee_id: Union[str, int] = None,
        year: Union[str, int] = None,
        check_date: str = None
    ) -> Dict[str, Any]:
        """
        Fetch pay statement details for a specific employee, year and check date.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
            employee_id: Employee ID (string or integer) to get pay statement details for.
            year: The year to get pay statement details for.
            check_date: The check date to get pay statement details for (format: MM/DD/YYYY).
        """
        if any(param is None for param in [employee_id, year, check_date]):
            raise ValueError("employee_id, year, and check_date are all required")
            
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        year_str = str(year)
        return client.get_employee_paystatement_details(company_id_str, employee_id_str, year_str, check_date)

# Expose important items at package level
__all__ = ['main']