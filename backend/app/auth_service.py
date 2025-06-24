import os
from typing import Dict, Optional
import msal
from azure.identity import ClientSecretCredential
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AzureAuthService:
    def __init__(self):
        self.tenant_id = None
        self.client_id = None
        self.client_secret = None
        self.authority = None
        # Use the database scope that worked
        self.scope = ["https://database.windows.net//.default"]
        self.token_cache = {}
        
    def configure(self, tenant_id: str, client_id: str, client_secret: str):
        """Configure OAuth2 credentials"""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        
    def is_configured(self) -> bool:
        """Check if OAuth2 is configured"""
        return all([self.tenant_id, self.client_id, self.client_secret])
    
    def get_access_token(self) -> Optional[str]:
        """Get access token using client credentials flow"""
        if not self.is_configured():
            logger.error("OAuth2 not configured")
            return None
            
        try:
            # Create MSAL confidential client
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )
            
            # Try to get token from cache first
            result = app.acquire_token_silent(self.scope, account=None)
            
            if not result:
                # Get new token
                logger.info(f"Acquiring new token for scope: {self.scope}")
                result = app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                logger.info("Successfully acquired access token")
                return result["access_token"]
            else:
                error = result.get('error', 'Unknown error')
                error_desc = result.get('error_description', 'No description')
                logger.error(f"Failed to acquire token: {error} - {error_desc}")
                return None
                
        except Exception as e:
            logger.error(f"Error acquiring token: {str(e)}")
            return None
    
    def get_fabric_connection_string(self, server: str, database: str) -> Optional[str]:
        """Build connection string with OAuth2 token"""
        token = self.get_access_token()
        if not token:
            return None
        
        # Use the token in the password field with UID
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={server};"
            f"Database={database};"
            f"UID=token;"
            f"PWD={token};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
        )
        
        return connection_string
    
    def test_configuration(self) -> Dict:
        """Test OAuth2 configuration"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "OAuth2 not configured"
            }
            
        token = self.get_access_token()
        if token:
            return {
                "success": True,
                "message": "OAuth2 authentication successful",
                "token_preview": token[:20] + "..." if len(token) > 20 else token
            }
        else:
            return {
                "success": False,
                "error": "Failed to acquire access token"
            }


# Create singleton instance
auth_service = AzureAuthService()
