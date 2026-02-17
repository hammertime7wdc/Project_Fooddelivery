import json
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
import uuid
import os

class GoogleOAuthHandler:
    def __init__(self):
        with open('client_secret.json', 'r') as f:
            self.config = json.load(f)['web']
        
        self.client_id = self.config['client_id']
        self.client_secret = self.config['client_secret']
        # Use environment variable if set, otherwise use config
        self.redirect_uri = os.getenv('OAUTH_CALLBACK_URL', self.config['redirect_uris'][0])
        self.auth_uri = self.config['auth_uri']
        self.token_uri = self.config['token_uri']
        
        # Store codes by state parameter for multi-user support
        self.auth_codes = {}
        self.tokens = {}  # Store tokens by state
        self.server = None
    
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
