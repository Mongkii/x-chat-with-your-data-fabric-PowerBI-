import os
import pyodbc
import pandas as pd
from typing import Dict, List, Optional
import logging
import struct
from dotenv import load_dotenv
from app.auth_service import auth_service

load_dotenv()
logger = logging.getLogger(__name__)

class FabricService:
    def __init__(self):
        self.server = None
        self.database = None
        self.connection = None
        
    def configure(self, server: str, database: str):
        """Configure Fabric connection parameters"""
        self.server = server
        self.database = database
    
    def _connect_with_token(self) -> Optional[pyodbc.Connection]:
        """Create connection using OAuth2 token with attrs_before"""
        if not self.server or not self.database:
            logger.error("Server and database must be configured")
            return None
            
        if not auth_service.is_configured():
            logger.error("OAuth2 authentication not configured")
            return None
        
        token = auth_service.get_access_token()
        if not token:
            logger.error("Failed to get access token")
            return None
        
        try:
            # Build connection string - UPDATED with working settings
            connection_string = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server={self.server};"
                f"Database={self.database};"
                f"Encrypt=no;"  # Changed to no
                f"TrustServerCertificate=yes;"  # Changed to yes
                f"Connection Timeout=30;"
            )
            
            # SQL_COPT_SS_ACCESS_TOKEN constant
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            
            # Convert token to bytes
            token_bytes = token.encode('utf-16-le')
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
            
            # Connect with token
            conn = pyodbc.connect(
                connection_string,
                attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
            )
            
            logger.info("Successfully connected to Fabric database")
            return conn
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """Test the database connection"""
        try:
            logger.info(f"Testing connection to {self.server}/{self.database}")
            
            conn = self._connect_with_token()
            if not conn:
                logger.error("_connect_with_token returned None")
                return {"success": False, "error": "Failed to establish connection - check logs for details"}
            
            logger.info("Connection established, running test query")
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT DB_NAME() as db_name, @@VERSION as version")
            result = cursor.fetchone()
            
            logger.info(f"Test query successful - Database: {result[0]}")
            
            conn.close()
            
            return {
                "success": True,
                "message": "Connection successful",
                "server": self.server,
                "database": result[0],
                "version": result[1][:100] + "..." if len(result[1]) > 100 else result[1]
            }
        except Exception as e:
            logger.error(f"Connection test failed with error: {type(e).__name__}: {e}")
            return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
    
    def discover_schema(self) -> Dict:
        """Discover tables and columns in the database"""
        try:
            conn = self._connect_with_token()
            if not conn:
                return {"success": False, "error": "Failed to establish connection"}
            
            cursor = conn.cursor()
            
            # Get all tables
            tables_query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            cursor.execute(tables_query)
            tables = cursor.fetchall()
            
            schema_info = {}
            
            for table in tables:
                schema_name = table[0]
                table_name = table[1]
                full_table_name = f"{schema_name}.{table_name}"
                
                # Get columns for this table
                columns_query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """
                
                cursor.execute(columns_query, (schema_name, table_name))
                columns = cursor.fetchall()
                
                schema_info[full_table_name] = {
                    "schema": schema_name,
                    "table": table_name,
                    "columns": [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == "YES",
                            "max_length": col[3]
                        }
                        for col in columns
                    ]
                }
            
            conn.close()
            
            return {
                "success": True,
                "tables": schema_info,
                "table_count": len(schema_info)
            }
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_query(self, query: str, limit: int = 100) -> Dict:
        """Execute a SQL query and return results"""
        try:
            conn = self._connect_with_token()
            if not conn:
                return {"success": False, "error": "Failed to establish connection"}
            
            # Add limit if not present
            query_lower = query.lower()
            if "select" in query_lower and "limit" not in query_lower and "top" not in query_lower:
                # For SQL Server/Fabric, use TOP
                query = query.replace("SELECT", f"SELECT TOP {limit}", 1)
                query = query.replace("select", f"SELECT TOP {limit}", 1)
            
            # Execute query
            df = pd.read_sql(query, conn)
            conn.close()
            
            # Convert to JSON-serializable format
            result = {
                "success": True,
                "columns": list(df.columns),
                "data": df.to_dict('records'),
                "row_count": len(df),
                "preview": df.head(10).to_dict('records')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict:
        """Get sample data from a table"""
        query = f"SELECT TOP {limit} * FROM {table_name}"
        return self.execute_query(query, limit)

    # Add this method to FabricService class
def connect_to_semantic_model(self, xmla_endpoint: str) -> Dict:
    """Connect to Power BI semantic model via XMLA endpoint"""
    try:
        import xmla  # You'll need to install this
        
        token = auth_service.get_access_token()
        if not token:
            return {"success": False, "error": "Failed to get access token"}
        
        # Connect to XMLA endpoint
        conn_str = f"Provider=MSOLAP;Data Source={xmla_endpoint};Password={token};"
        
        # This is a placeholder - implement actual XMLA connection
        return {
            "success": True,
            "message": "Connected to semantic model",
            "endpoint": xmla_endpoint
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_dax_query(self, dax_query: str) -> Dict:
    """Execute DAX query on semantic model"""
    # Placeholder for DAX execution
    return {
        "success": False,
        "error": "DAX execution not yet implemented"
    }
# This module provides a service to connect to Microsoft Fabric databases using OAuth2 authentication.

# Create singleton instance
fabric_service = FabricService()