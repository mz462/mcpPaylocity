import os
import time
import json
import requests
import base64
import sys

class TokenManager:
    def __init__(self, base_url, client_id, client_secret, scope='WebLinkAPI'):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.access_token = None
        self.token_expiry = None
        
        # Keep token storage in access_token directory
        self.token_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'access_token')
        os.makedirs(self.token_dir, exist_ok=True)
        self.token_file = os.path.join(self.token_dir, 'token.json')
        self.token_info_file = os.path.join(self.token_dir, 'token_info.txt')
        
        print(f"TokenManager initialized with base_url={base_url}", file=sys.stderr)
        print(f"Token cache directory: {self.token_dir}", file=sys.stderr)

    def get_access_token(self):
        if self._load_cached_token():
            print("Using cached token", file=sys.stderr)
            return self.access_token

        print("Getting new access token...", file=sys.stderr)
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
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expiry = time.time() + token_data['expires_in']
            
            self._save_token_to_cache(self.access_token, self.token_expiry)
            print(f"Successfully obtained new token, expires in {token_data['expires_in']} seconds", file=sys.stderr)
            
            return self.access_token
        except Exception as e:
            print(f"Error getting access token: {str(e)}", file=sys.stderr)
            raise

    def _load_cached_token(self):
        """Load token from cache file if it exists and is still valid"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    if token_data['expiry'] > time.time() + 300:  # 5 minutes buffer
                        self.access_token = token_data['token']
                        self.token_expiry = token_data['expiry']
                        return True
                    else:
                        print("Cached token is expired or about to expire", file=sys.stderr)
        except Exception as e:
            print(f"Error loading cached token: {e}", file=sys.stderr)
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
            
            # Save token data as JSON
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Save human-readable token info
            with open(self.token_info_file, 'w') as f:
                f.write(f"Token Information:\n")
                f.write(f"Created At: {token_data['created_at']}\n")
                f.write(f"Expires At: {token_data['expires_at']}\n")
                f.write(f"Token: {token[:50]}...\n")
            
            print("Token saved to cache", file=sys.stderr)
        except Exception as e:
            print(f"Error saving token to cache: {e}", file=sys.stderr) 