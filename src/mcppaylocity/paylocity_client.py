import os
import sys
import requests
from .token_manager import TokenManager

class PaylocityClient:
    def __init__(self, client_id, client_secret, environment='production', scope='WebLinkAPI'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.scope = scope
        
        # Set base URL based on environment
        self.base_url = "https://apisandbox.paylocity.com" if self.environment == 'testing' else "https://api.paylocity.com"
        
        # Initialize token manager
        self.token_manager = TokenManager(self.base_url, client_id, client_secret, scope)
        
        print(f"PaylocityClient initialized with environment={environment}", file=sys.stderr)
        
    def _make_request(self, method, endpoint, params=None, data=None, headers=None):
        """Make an authenticated request to the Paylocity API"""
        token = self.token_manager.get_access_token()
        
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        print(f"Making {method} request to: {url}", file=sys.stderr)
        try:
            response = requests.request(method, url, headers=default_headers, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making request: {str(e)}", file=sys.stderr)
            raise

    def get_all_employees(self, company_id):
        """Get all employees with automatic token management"""
        endpoint = f"/api/v2/companies/{company_id}/employees"
        
        params = {
            "pagesize": 100,
            "pagenumber": 0,
            "includetotalcount": True
        }
        
        return self._make_request("GET", endpoint, params=params)

    def get_employee_details(self, company_id, employee_id):
        """Get detailed employee information with automatic token management"""
        endpoint = f"/api/v2/companies/{company_id}/employees/{employee_id}"
        return self._make_request("GET", endpoint)

    def get_employee_earnings(self, company_id, employee_id):
        """Get all earnings for a specific employee"""
        endpoint = f"/api/v2/companies/{company_id}/employees/{employee_id}/earnings"
        return self._make_request("GET", endpoint)

    def get_company_codes(self, company_id, code_resource):
        """Get company codes for a specific resource"""
        endpoint = f"/api/v2/companies/{company_id}/codes/{code_resource}"
        return self._make_request("GET", endpoint)

    def get_company_openapi_doc(self, company_id):
        """Get company-specific Open API documentation"""
        endpoint = f"/api/v2/companies/{company_id}/openapi"
        headers = {"Accept": "application/json"}
        return self._make_request("GET", endpoint, headers=headers) 