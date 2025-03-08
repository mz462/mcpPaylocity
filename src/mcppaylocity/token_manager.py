import os
import time
import json
import base64
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger('mcppaylocity.token_manager')

class TokenManager:
    def __init__(self, base_url, client_id, client_secret, scope='WebLinkAPI'):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.access_token = None
        self.token_expiry = None
        self.max_retries = 3
        self.retry_delay = 1  # Initial retry delay in seconds
        
        # Keep token storage in access_token directory
        self.token_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'access_token')
        os.makedirs(self.token_dir, exist_ok=True)
        self.token_file = os.path.join(self.token_dir, 'token.json')
        self.token_info_file = os.path.join(self.token_dir, 'token_info.txt')
        
        logger.info("TokenManager initialized with base_url=%s", base_url)
        logger.info("Token cache directory: %s", self.token_dir)

    def get_access_token(self) -> str:
        """Get a valid access token, either from cache or by requesting a new one"""
        if self._load_cached_token():
            logger.debug("Using cached token")
            return self.access_token

        logger.info("Getting new access token...")
        return self._request_new_token()
    
    def _request_new_token(self) -> str:
        """Request a new access token from the Paylocity API with retry logic"""
        url = f"{self.base_url}/IdentityServer/connect/token"
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": self.scope
        }
        
        # Implement retry logic with exponential backoff
        current_retry = 0
        retry_delay = self.retry_delay
        
        while current_retry <= self.max_retries:
            try:
                response = requests.post(url, headers=headers, data=data, timeout=30)  # Add timeout
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expiry = time.time() + token_data['expires_in']
                
                # Save token with a buffer time to ensure we refresh before expiry
                self._save_token_to_cache(self.access_token, self.token_expiry)
                logger.info("Successfully obtained new token, expires in %d seconds", token_data['expires_in'])
                
                return self.access_token
            except requests.exceptions.Timeout:
                current_retry += 1
                if current_retry <= self.max_retries:
                    logger.warning("Token request timed out. Retry %d/%d in %ds", current_retry, self.max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed to get token after maximum retries")
                    raise
            except requests.exceptions.RequestException as e:
                current_retry += 1
                if current_retry <= self.max_retries:
                    logger.warning("Token request failed: %s. Retry %d/%d in %ds", str(e), current_retry, self.max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed to get token after maximum retries: %s", str(e))
                    raise
            except Exception as e:
                logger.error("Unexpected error getting access token: %s", str(e))
                raise

    def _load_cached_token(self) -> bool:
        """Load token from cache file if it exists and is still valid"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                    # Use a 10-minute buffer to ensure we refresh well before expiry
                    # This helps prevent issues with the 5-minute Smithery timeout
                    if token_data['expiry'] > time.time() + 600:  # 10 minutes buffer
                        self.access_token = token_data['token']
                        self.token_expiry = token_data['expiry']
                        return True
                    else:
                        logger.info("Cached token is expired or about to expire")
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in token cache file: %s", str(e))
            # Remove corrupted cache file
            try:
                os.remove(self.token_file)
            except OSError:
                pass
        except (IOError, OSError, ValueError) as e:
            logger.warning("Error loading cached token: %s", str(e))
        return False

    def _save_token_to_cache(self, token, expiry):
        """Save token and expiry to cache files"""
        try:
            token_data = {
                'token': token,
                'expiry': expiry,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'expires_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry))
            }
            
            # Create a temporary file first to avoid corruption if the process is interrupted
            temp_file = "{}.tmp".format(self.token_file)
            
            # Save token data as JSON
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2)
            
            # Atomic rename to ensure the file is either fully written or not at all
            os.replace(temp_file, self.token_file)
            
            # Save human-readable token info
            with open(self.token_info_file, 'w', encoding='utf-8') as f:
                f.write("Token Information:\n")
                f.write("Created At: {}\n".format(token_data['created_at']))
                f.write("Expires At: {}\n".format(token_data['expires_at']))
                f.write("Token: {}...\n".format(token[:50]))
            
            logger.info("Token saved to cache")
        except (IOError, OSError) as e:
            logger.error("Error saving token to cache: %s", str(e))
            
    def invalidate_token(self):
        """Invalidate the current token and force a new token to be fetched next time"""
        self.access_token = None
        self.token_expiry = None
        
        # Remove cached token files if they exist
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            if os.path.exists(self.token_info_file):
                os.remove(self.token_info_file)
            logger.info("Token cache invalidated")
        except (IOError, OSError) as e:
            logger.error("Error invalidating token cache: %s", str(e))