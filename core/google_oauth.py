import json
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleOAuthHandler:
    def __init__(self):
        self.config = self._load_config()

        self.client_id = self.config['client_id']
        self.client_secret = self.config['client_secret']
        self.redirect_uri = self.config['redirect_uri']
        self.auth_uri = self.config['auth_uri']
        self.token_uri = self.config['token_uri']
        
        # Store codes by state parameter for multi-user support
        self.auth_codes = {}
        self.tokens = {}  # Store tokens by state
        self.server = None

    def _load_config(self):
        env_client_id = os.getenv('GOOGLE_CLIENT_ID')
        env_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        env_redirect_uri = os.getenv('OAUTH_CALLBACK_URL')
        env_auth_uri = os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
        env_token_uri = os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token')

        if env_client_id and env_client_secret:
            return {
                'client_id': env_client_id,
                'client_secret': env_client_secret,
                'redirect_uri': env_redirect_uri or 'http://localhost:9000',
                'auth_uri': env_auth_uri,
                'token_uri': env_token_uri,
            }

        if os.path.exists('client_secret.json'):
            with open('client_secret.json', 'r', encoding='utf-8') as f:
                file_config = json.load(f)['web']

            return {
                'client_id': file_config['client_id'],
                'client_secret': file_config['client_secret'],
                'redirect_uri': env_redirect_uri or file_config['redirect_uris'][0],
                'auth_uri': file_config['auth_uri'],
                'token_uri': file_config['token_uri'],
            }

        raise RuntimeError(
            'Google OAuth config not found. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, '
            'or provide client_secret.json locally.'
        )
    
    def get_authorization_url(self, state=None):
        """Generate the Google OAuth authorization URL with unique state"""
        if state is None:
            state = str(uuid.uuid4())
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'state': state
        }
        return f"{self.auth_uri}?{urllib.parse.urlencode(params)}", state
    
    def start_callback_server(self):
        """Start a simple HTTP server to handle OAuth callback"""
        # Don't start if already running
        if self.server is not None:
            print("✅ OAuth callback server already running on port 9000")
            return
        
        try:
            handler = self._create_callback_handler()
            self.server = HTTPServer(('0.0.0.0', 9000), handler)
            # Use serve_forever with timeout instead of handle_request
            self.server.timeout = 0.5
            thread = threading.Thread(target=self._serve_forever, daemon=True)
            thread.start()
            print("✅ OAuth callback server started successfully on http://localhost:9000")
        except OSError as e:
            if "address already in use" in str(e).lower():
                print("⚠️ Port 9000 already in use - OAuth server may already be running")
                # Port already in use, which is fine - server is running
            else:
                print(f"❌ Failed to start OAuth callback server: {e}")
                raise
        except Exception as e:
            print(f"❌ Failed to start OAuth callback server: {e}")
            raise
    
    def _serve_forever(self):
        """Serve requests continuously - never stops"""
        while True:
            try:
                self.server.handle_request()
            except Exception as e:
                # Don't break - keep server running even on errors
                print(f"⚠️ Callback server handled error (continuing): {e}")
                # Continue serving instead of breaking
    
    def _create_callback_handler(self):
        """Create HTTP request handler for OAuth callback"""
        parent = self
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the callback URL
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                if 'code' in params and 'state' in params:
                    code = params['code'][0]
                    state = params['state'][0]
                    # Store code by state for multi-user support
                    parent.auth_codes[state] = code
                    print(f"✅ OAuth callback received for state: {state[:8]}...")
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """<html><head><title>Authorization Successful</title></head>
                    <body style='font-family: Arial; text-align: center; padding: 50px;'>
                    <h1 style='color: green;'>✅ Authorization Successful!</h1>
                    <p>You can close this window now and return to the app.</p>
                    <script>setTimeout(function() { window.close(); }, 2000);</script>
                    </body></html>"""
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """<html><body style='font-family: Arial; text-align: center; padding: 50px;'>
                    <h1 style='color: red;'>❌ Authorization Failed</h1>
                    <p>Please try again.</p>
                    </body></html>"""
                    self.wfile.write(html.encode('utf-8'))
            
            def log_message(self, format, *args):
                pass  # Suppress log messages
        
        return CallbackHandler
    
    def exchange_code_for_token(self, state):
        """Exchange authorization code for access token"""
        if state not in self.auth_codes:
            print(f"❌ No authorization code found for state: {state[:8]}...")
            return False
        
        auth_code = self.auth_codes[state]
        
        data = {
            'code': auth_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(self.token_uri, data=data, timeout=10)
            if response.status_code == 200:
                token = response.json()
                # Store token by state for multi-user support
                self.tokens[state] = token
                # Remove used code
                del self.auth_codes[state]
                print(f"✅ Successfully exchanged code for access token")
                return True
            else:
                print(f"❌ Token exchange failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Token exchange error: {e}")
            return False
    
    def get_user_info(self, state):
        """Get user information from Google using state-specific token"""
        if state not in self.tokens:
            print(f"❌ No token found for state: {state[:8]}...")
            return None
        
        token = self.tokens[state]
        if 'access_token' not in token:
            return None
        
        headers = {'Authorization': f"Bearer {token['access_token']}"}
        
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v1/userinfo',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                user_info = response.json()
                # Clean up token after successful use
                del self.tokens[state]
                return user_info
        except Exception as e:
            print(f"User info error: {e}")
        
        return None
    
    def authenticate(self):
        """Main authentication flow"""
        # Start callback server
        self.start_callback_server()
        
        # Open browser
        auth_url = self.get_authorization_url()
        webbrowser.open(auth_url)
        
        # Wait for callback (blocking)
        import time
        max_wait = 300  # 5 minutes timeout
        start_time = time.time()
        while not self.auth_code and (time.time() - start_time) < max_wait:
            time.sleep(0.5)
        
        if not self.auth_code:
            return None
        
        # Exchange code for token
        if not self.exchange_code_for_token():
            return None
        
        # Get user info
        user_info = self.get_user_info()
        
        return user_info
