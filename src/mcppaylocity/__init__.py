"""
Paylocity MCP Server

This module provides a Model Context Protocol (MCP) server for accessing Paylocity API data.
It exposes Paylocity resources and tools through the MCP interface.
"""

from typing import Any, Dict, List, Optional, Union
import os
import json
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from .paylocity_client import PaylocityClient

# Register custom URI scheme for paylocity resources
PAYLOCITY_SCHEME = "paylocity"

def main():
    """
    Main entry point for the Paylocity MCP server.
    Initializes the server, configures resources and tools, and starts the server.
    """
    try:
        print("Starting Paylocity MCP server...", file=sys.stderr)
        # Load environment variables from .env file
        load_dotenv()
        print("Loaded environment variables", file=sys.stderr)
        
        # Get configuration from environment variables
        client_id = os.getenv("PAYLOCITY_CLIENT_ID")
        client_secret = os.getenv("PAYLOCITY_CLIENT_SECRET")
        environment = os.getenv("PAYLOCITY_ENVIRONMENT", "production")
        
        # Get company IDs
        company_ids_str = os.getenv("PAYLOCITY_COMPANY_IDS", "")
        company_ids = [id.strip() for id in company_ids_str.split(",") if id.strip()]
        
        if not all([client_id, client_secret]) or not company_ids:
            error_msg = "Missing required Paylocity API credentials or company IDs"
            print(f"Error: {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)
        
        print(f"Environment: {environment}", file=sys.stderr)
        print(f"Company IDs: {company_ids}", file=sys.stderr)
        
        # Create FastMCP instance
        mcp = FastMCP("Paylocity")
        
        # Initialize Paylocity client
        client = PaylocityClient(client_id, client_secret, environment)
        
        # Register resources
        register_resources(mcp, client, company_ids)
        
        # Register tools
        register_tools(mcp, client, company_ids)
        
        print("Starting server...", file=sys.stderr)
        # Run the server
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        raise

def register_resources(mcp, client, company_ids):
    """
    Register all Paylocity resources with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        client: The PaylocityClient instance
        company_ids: List of company IDs to use
    """
    @mcp.resource(f"{PAYLOCITY_SCHEME}://employees/{{company_id}}")
    def get_employees(company_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get all employees for a company."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        print(f"Getting employees for company_id={company_id_str}", file=sys.stderr)
        return client.get_all_employees(company_id_str)
    
    @mcp.resource(f"{PAYLOCITY_SCHEME}://employees/{{company_id}}/{{employee_id}}")
    def get_employee_details(company_id: Optional[Union[str, int]] = None, employee_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get details for a specific employee."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        print(f"Getting employee details for company_id={company_id_str}, employee_id={employee_id_str}", file=sys.stderr)
        return client.get_employee_details(company_id_str, employee_id_str)
    
    @mcp.resource(f"{PAYLOCITY_SCHEME}://earnings/{{company_id}}/{{employee_id}}")
    def get_earnings(company_id: Optional[Union[str, int]] = None, employee_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Get earnings data for a specific employee."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        employee_id_str = str(employee_id)
        print(f"Getting earnings for company_id={company_id_str}, employee_id={employee_id_str}", file=sys.stderr)
        return client.get_employee_earnings(company_id_str, employee_id_str)
    
    @mcp.resource(f"{PAYLOCITY_SCHEME}://codes/{{company_id}}/{{code_resource}}")
    def get_codes(company_id: Optional[Union[str, int]] = None, code_resource: str = None) -> Dict[str, Any]:
        """Get company codes for a specific resource."""
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        print(f"Getting codes for company_id={company_id_str}, code_resource={code_resource}", file=sys.stderr)
        return client.get_company_codes(company_id_str, code_resource)

def register_tools(mcp, client, company_ids):
    """
    Register all Paylocity tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        client: The PaylocityClient instance
        company_ids: List of company IDs to use
    """
    @mcp.tool()
    def fetch_employees(company_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Fetch all employees for a company.
        
        Args:
            company_id: Optional company ID (string or integer). If not provided, uses the first company ID from configuration.
        """
        company_id_str = str(company_id) if company_id is not None else company_ids[0]
        return client.get_all_employees(company_id_str)
    
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

# Expose important items at package level
__all__ = ['main']