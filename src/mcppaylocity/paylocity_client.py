import time
import logging
from typing import Dict, Any
import requests
from .token_manager import TokenManager

logger = logging.getLogger('mcppaylocity.client')

class PaylocityClient:
    def __init__(self, client_id, client_secret, environment='production', scope='WebLinkAPI'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.scope = scope
        self.max_retries = 3
        self.retry_delay = 1  # Initial retry delay in seconds
        self.request_timeout = 30  # Request timeout in seconds
        
        # Set base URL based on environment
        self.base_url = "https://apisandbox.paylocity.com" if self.environment == 'testing' else "https://api.paylocity.com"
        
        # Initialize token manager
        self.token_manager = TokenManager(self.base_url, client_id, client_secret, scope)
        
        logger.info("PaylocityClient initialized with environment=%s", environment)
        
    def _make_request(self, method, endpoint, params=None, data=None, headers=None):
        """Make an authenticated request to the Paylocity API with retry logic"""
        url = "{}{}".format(self.base_url, endpoint)
        logger.info("Making %s request to: %s", method, url)
        
        # Implement retry logic with exponential backoff
        current_retry = 0
        retry_delay = self.retry_delay
        last_exception = None
        
        while current_retry <= self.max_retries:
            try:
                # Get a fresh token for each attempt to ensure it's valid
                token = self.token_manager.get_access_token()
                
                default_headers = {
                    "Authorization": "Bearer {}".format(token),
                    "Content-Type": "application/json"
                }
                
                if headers:
                    default_headers.update(headers)
                
                response = requests.request(
                    method, 
                    url, 
                    headers=default_headers, 
                    params=params, 
                    json=data,
                    timeout=self.request_timeout
                )
                
                # Check for token expiration (401) and retry with a new token
                if response.status_code == 401:
                    if current_retry < self.max_retries:
                        logger.warning("Received 401 Unauthorized. Invalidating token and retrying...")
                        self.token_manager.invalidate_token()
                        current_retry += 1
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                
                # Raise exception for other error status codes
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                current_retry += 1
                if current_retry <= self.max_retries:
                    logger.warning("Request timed out. Retry %d/%d in %ds", current_retry, self.max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Request failed after maximum retries due to timeout: %s", str(e))
                    raise
                    
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                current_retry += 1
                if current_retry <= self.max_retries:
                    logger.warning("Connection error: %s. Retry %d/%d in %ds", str(e), current_retry, self.max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Request failed after maximum retries due to connection error: %s", str(e))
                    raise
                    
            except requests.exceptions.HTTPError as e:
                # For 5xx errors (server errors), retry
                if 500 <= e.response.status_code < 600 and current_retry < self.max_retries:
                    last_exception = e
                    current_retry += 1
                    logger.warning("Server error %d. Retry %d/%d in %ds", e.response.status_code, current_retry, self.max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # For other HTTP errors, don't retry
                    logger.error("HTTP error: %d - %s", e.response.status_code, e.response.text)
                    raise
                    
            except Exception as e:
                logger.error("Unexpected error making request: %s", str(e))
                raise
        
        # If we've exhausted retries, raise the last exception
        if last_exception:
            raise last_exception

    def get_all_employees(self, company_id) -> Dict[str, Any]:
        """Get all employees with automatic token management"""
        endpoint = "/api/v2/companies/{}/employees".format(company_id)
        
        params = {
            "pagesize": 100,
            "pagenumber": 0,
            "includetotalcount": True
        }
        
        try:
            return self._make_request("GET", endpoint, params=params).json()
        except Exception as e:
            logger.error("Failed to get employees for company %s: %s", company_id, str(e))
            raise

    def get_employee_details(self, company_id, employee_id):
        """Get detailed employee information with automatic token management"""
        endpoint = "/api/v2/companies/{}/{}".format(company_id, employee_id)
        return self._make_request("GET", endpoint).json()

    def get_employee_earnings(self, company_id, employee_id):
        """Get all earnings for a specific employee"""
        endpoint = "/api/v2/companies/{}/{}/earnings".format(company_id, employee_id)
        return self._make_request("GET", endpoint).json()

    def get_company_codes(self, company_id, code_resource):
        """Get company codes for a specific resource"""
        endpoint = "/api/v2/companies/{}/codes/{}".format(company_id, code_resource)
        return self._make_request("GET", endpoint).json()

    def get_employee_local_taxes(self, company_id, employee_id):
        """Get all local taxes for a specific employee"""
        endpoint = "/api/v2/companies/{}/{}/localTaxes".format(company_id, employee_id)
        return self._make_request("GET", endpoint).json()

    def get_employee_paystatement_details(self, company_id, employee_id, year, check_date):
        """Get employee pay statement details for a specific year and check date
        
        Args:
            company_id: Company ID
            employee_id: Employee ID
            year: The year to get pay statement details for
            check_date: The check date to get pay statement details for
        """
        endpoint = "/api/v2/companies/{}/{}/paystatement/details/{}/{}".format(company_id, employee_id, year, check_date)
        return self._make_request("GET", endpoint).json()

    def get_company_openapi_doc(self, company_id):
        """Get company-specific Open API documentation"""
        endpoint = "/api/v2/companies/{}/openapi".format(company_id)
        headers = {"Accept": "application/json"}
        return self._make_request("GET", endpoint, headers=headers).json()

    def get_employee_data(self, employee_id: str, company_id: str) -> Dict[str, Any]:
        """
        Retrieve data for a specific employee

        Args:
            employee_id (str): The ID of the employee
            company_id (str): The ID of the company

        Returns:
            dict: The employee data response
        """
        endpoint = '/api/v2/companies/{}/{}/sensitivedata'.format(company_id, employee_id)
        
        try:
            response = self._make_request('GET', endpoint)
            return response.json()
        except Exception as e:
            logger.error("Failed to retrieve employee data for employee %s in company %s: %s", employee_id, company_id, str(e))
            raise