# backend/app/semantic_model_service.py
import logging
import json
import sys
import os
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from difflib import get_close_matches
from app.auth_service import auth_service

logger = logging.getLogger(__name__)

# Custom JSON encoder for Power BI data types
class PowerBIJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Power BI data types"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return str(obj)
        return super().default(obj)

def safe_json_dumps(data, indent=2):
    """Safely serialize data containing datetime and other non-JSON types"""
    return json.dumps(data, indent=indent, cls=PowerBIJSONEncoder)

def setup_adomd_path():
    """Setup ADOMD.NET path and load required libraries"""
    adomd_paths = [
        r"C:\Program Files\Microsoft.NET\ADOMD.NET\160",
        r"C:\Program Files\Microsoft.NET\ADOMD.NET\150",
        r"C:\Program Files (x86)\Microsoft.NET\ADOMD.NET\160",
        r"C:\Program Files (x86)\Microsoft.NET\ADOMD.NET\150",
        r"C:\Program Files\Microsoft SQL Server\160\SDK\Assemblies",
        r"C:\Program Files\Microsoft SQL Server\150\SDK\Assemblies",
    ]
    
    adomd_loaded = False
    adomd_path = None
    
    for path in adomd_paths:
        if os.path.exists(path):
            try:
                sys.path.append(path)
                import clr
                clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
                adomd_loaded = True
                adomd_path = path
                logger.info(f"✅ Loaded ADOMD.NET from {path}")
                break
            except Exception as e:
                logger.debug(f"Failed to load ADOMD.NET from {path}: {e}")
                continue
    
    return adomd_loaded, adomd_path

class SemanticModelService:
    def __init__(self):
        self.xmla_endpoint = None
        self.dataset_name = None
        self.workspace_name = None
        self.connected = False
        self.tables_cache = []
        self.metadata_cache = {}
        self.model_info = None
        self.schema_cache = {}
        self.cache_timestamp = None
        self.cache_ttl = 3600  # 1 hour
        
        # Store credentials for XMLA connection
        self.tenant_id = None
        self.client_id = None
        self.client_secret = None
        
        # Try to setup ADOMD.NET and pyadomd
        self.adomd_available = False
        self.pyadomd_available = False
        self.error_message = None
        
        # DAX query templates
        self.dax_templates = {
            'yearly_aggregation': """EVALUATE
SUMMARIZECOLUMNS(
    {date_table}[{date_column}],
    "Year", YEAR({date_table}[{date_column}]),
    "{measure_name}", {aggregation}({value_table}[{value_column}])
)
ORDER BY [Year]""",
            
            'simple_aggregation': """EVALUATE
ROW(
    "{measure_name}", {aggregation}({table}[{column}])
)""",
            
            'grouped_aggregation': """EVALUATE
SUMMARIZECOLUMNS(
    {group_table}[{group_column}],
    "{measure_name}", {aggregation}({value_table}[{value_column}])
)""",
            
            'filtered_aggregation': """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        {group_table}[{group_column}],
        "{measure_name}", {aggregation}({value_table}[{value_column}])
    ),
    {filter_condition}
)""",
            
            'top_n': """EVALUATE
TOPN(
    {n},
    SUMMARIZECOLUMNS(
        {group_table}[{group_column}],
        "{measure_name}", {aggregation}({value_table}[{value_column}])
    ),
    [{measure_name}], DESC
)"""
        }
        
        self._initialize_dependencies()
        
    def _initialize_dependencies(self):
        """Initialize pyadomd and ADOMD.NET dependencies"""
        try:
            # Step 1: Setup ADOMD.NET path
            adomd_loaded, adomd_path = setup_adomd_path()
            
            if not adomd_loaded:
                self.error_message = "ADOMD.NET libraries not found. Please install SSMS or ADOMD.NET client."
                logger.error(self.error_message)
                return
            
            self.adomd_available = True
            
            # Step 2: Try to import pyadomd
            try:
                from pyadomd import Pyadomd
                self.pyadomd_available = True
                logger.info("✅ pyadomd and ADOMD.NET loaded successfully")
            except ImportError as e:
                self.error_message = f"pyadomd not available: {e}"
                logger.error(self.error_message)
                
        except Exception as e:
            self.error_message = f"Failed to initialize Power BI dependencies: {e}"
            logger.error(self.error_message)
    
    def configure(self, xmla_endpoint: str, dataset_name: str, workspace_name: str = None):
        """Configure semantic model connection"""
        self.xmla_endpoint = xmla_endpoint
        self.dataset_name = dataset_name
        self.workspace_name = workspace_name
        
        # Get credentials from auth_service
        self.tenant_id = auth_service.tenant_id
        self.client_id = auth_service.client_id
        self.client_secret = auth_service.client_secret
        
        logger.info(f"Configured semantic model: {xmla_endpoint} -> {dataset_name}")
    
    def connect_to_powerbi(self) -> Dict:
        """Connect to Power BI dataset using XMLA endpoint"""
        if not self.xmla_endpoint or not self.dataset_name:
            return {"success": False, "error": "XMLA endpoint and dataset name required"}
        
        if not self.pyadomd_available:
            return {
                "success": False, 
                "error": f"Power BI connection not available: {self.error_message or 'pyadomd not installed'}",
                "suggestion": "Please install SSMS or run: pip install pyadomd"
            }
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            return {
                "success": False,
                "error": "OAuth2 credentials not properly configured",
                "suggestion": "Please configure OAuth2 authentication first"
            }
            
        try:
            connection_string = (
                f"Provider=MSOLAP;"
                f"Data Source={self.xmla_endpoint};"
                f"Initial Catalog={self.dataset_name};"
                f"User ID=app:{self.client_id}@{self.tenant_id};"
                f"Password={self.client_secret};"
            )
            
            logger.info(f"Attempting XMLA connection to: {self.xmla_endpoint}")
            
            from pyadomd import Pyadomd
            
            with Pyadomd(connection_string) as conn:
                self.connected = True
                logger.info(f"✅ Successfully connected to Power BI dataset: {self.dataset_name}")
                
                # Discover model structure with enhanced discovery
                self._discover_enhanced_schema()
                
                return {
                    "success": True,
                    "message": f"Successfully connected to '{self.dataset_name}'",
                    "tables_count": len(self.tables_cache),
                    "endpoint": self.xmla_endpoint,
                    "tables": self.tables_cache[:5] if self.tables_cache else []
                }
                
        except Exception as e:
            self.connected = False
            error_msg = str(e)
            logger.error(f"Power BI XMLA connection failed: {error_msg}")
            
            return self._get_connection_error_response(error_msg)
    
    def _get_connection_error_response(self, error_msg: str) -> Dict:
        """Generate helpful error response based on error message"""
        if "Invalid client secret" in error_msg:
            return {
                "success": False, 
                "error": "Invalid client secret",
                "details": "The client secret provided is incorrect or expired",
                "troubleshooting": [
                    "Check that you're using the client secret VALUE, not the ID",
                    "Make sure the secret hasn't expired",
                    "Verify you copied the complete secret value",
                    "Create a new client secret if needed"
                ]
            }
        elif "Login failed" in error_msg or "Authentication failed" in error_msg:
            return {
                "success": False,
                "error": "Authentication failed",
                "details": "Service principal authentication failed",
                "troubleshooting": [
                    "Check tenant_id, client_id, and client_secret are correct",
                    "Verify service principal is not expired",
                    "Ensure service principal has Power BI workspace access"
                ]
            }
        else:
            return {
                "success": False, 
                "error": f"Connection failed: {error_msg}",
                "suggestion": "Check your XMLA endpoint and dataset name"
            }
    
    def _discover_enhanced_schema(self):
        """Enhanced schema discovery with column metadata"""
        try:
            # Check cache first
            if self._is_cache_valid():
                self.tables_cache = self.schema_cache.get('tables', [])
                self.model_info = self.schema_cache.get('model_info', {})
                logger.info("Using cached schema")
                return
            
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            
            schema_data = {
                'tables': [],
                'model_info': {
                    'tables': {},
                    'measures': [],
                    'relationships': []
                }
            }
            
            with Pyadomd(connection_string) as conn:
                # Discover tables
                tables = self._discover_tables_dmv(conn)
                schema_data['tables'] = tables
                
                # Discover columns for ALL tables (or at least more important ones)
                logger.info(f"Discovering columns for {len(tables)} tables...")
                
                # Prioritize certain table types
                priority_tables = []
                other_tables = []
                
                for table_name in tables:
                    table_lower = table_name.lower()
                    # Prioritize fact and key dimension tables
                    if any(keyword in table_lower for keyword in ['sales', 'order', 'revenue', 'fact', 'product', 'customer', 'date']):
                        priority_tables.append(table_name)
                    else:
                        other_tables.append(table_name)
                
                # Discover priority tables first
                discovered_count = 0
                for table_name in priority_tables + other_tables:
                    if discovered_count >= 50:  # Increase limit
                        logger.info(f"Reached discovery limit of 50 tables")
                        break
                        
                    table_info = self._discover_table_details(conn, table_name)
                    if table_info and table_info.get('columns'):
                        schema_data['model_info']['tables'][table_name] = table_info
                        discovered_count += 1
                        logger.debug(f"Discovered {len(table_info['columns'])} columns in {table_name}")
                
                # Discover measures
                measures = self._discover_measures_dmv(conn)
                schema_data['model_info']['measures'] = measures
            
            # Update cache
            self.tables_cache = schema_data['tables']
            self.model_info = schema_data['model_info']
            self.schema_cache = schema_data
            self.cache_timestamp = datetime.now()
            
            logger.info(f"✅ Enhanced schema discovered: {len(self.tables_cache)} tables, "
                    f"{len(self.model_info['tables'])} tables with columns, {len(measures)} measures")
            
        except Exception as e:
            logger.error(f"Enhanced schema discovery failed: {e}")
            # Fall back to basic discovery
            self.discover_tables()
    
    def _discover_tables_dmv(self, connection) -> List[str]:
        """Discover tables using DMV queries"""
        try:
            cursor = connection.cursor()
            
            # Try multiple DMV queries
            dmv_queries = [
                "SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [IsHidden] = false",
                "SELECT DISTINCT [TABLE_NAME] FROM $SYSTEM.DISCOVER_STORAGE_TABLES",
                "SELECT [TABLE_NAME] FROM $SYSTEM.DBSCHEMA_TABLES"
            ]
            
            tables = []
            for query in dmv_queries:
                try:
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        table_name = row[0]
                        if not table_name.startswith('$') and not table_name.startswith('DateTableTemplate'):
                            tables.append(table_name)
                    if tables:
                        break
                except:
                    continue
            
            cursor.close()
            return list(set(tables))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"DMV discovery failed: {e}")
            return []
    
    def _discover_table_details(self, connection, table_name: str) -> Dict:
        """Get detailed information about a table"""
        try:
            cursor = connection.cursor()
            
            # Get columns by querying the table
            escaped_table = self._escape_table_name(table_name)
            query = f"EVALUATE TOPN(1, {escaped_table})"
            
            cursor.execute(query)
            
            columns = []
            if cursor.description:
                for desc in cursor.description:
                    columns.append({
                        "name": desc[0],
                        "type": "string",  # Default type
                        "full_name": f"{table_name}[{desc[0]}]"
                    })
            
            cursor.close()
            
            return {
                "columns": columns,
                "type": "data_table",
                "row_count": self._estimate_row_count(connection, table_name)
            }
            
        except Exception as e:
            logger.debug(f"Could not get details for table {table_name}: {e}")
            return {"columns": [], "type": "unknown"}
    
    def _discover_measures_dmv(self, connection) -> List[Dict]:
        """Discover measures using DMV queries"""
        try:
            cursor = connection.cursor()
            measures = []
            
            # Try to get measures
            measure_queries = [
                "SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES",
                "SELECT [MEASURE_NAME], [EXPRESSION] FROM $SYSTEM.MDSCHEMA_MEASURES WHERE [MEASURE_IS_VISIBLE]"
            ]
            
            for query in measure_queries:
                try:
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        measures.append({
                            "name": row[0],
                            "expression": row[1] if len(row) > 1 else None
                        })
                    if measures:
                        break
                except:
                    continue
            
            cursor.close()
            return measures
            
        except Exception as e:
            logger.warning(f"Measure discovery failed: {e}")
            return []
    
    def _estimate_row_count(self, connection, table_name: str) -> int:
        """Estimate row count for a table"""
        try:
            cursor = connection.cursor()
            escaped_table = self._escape_table_name(table_name)
            query = f"EVALUATE ROW(\"Count\", COUNTROWS({escaped_table}))"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0
        except:
            return 0
    
    def _is_cache_valid(self) -> bool:
        """Check if schema cache is still valid"""
        if not self.cache_timestamp or not self.schema_cache:
            return False
        
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_ttl
    
    def _get_connection_string(self) -> str:
        """Get connection string for Power BI"""
        return (
            f"Provider=MSOLAP;"
            f"Data Source={self.xmla_endpoint};"
            f"Initial Catalog={self.dataset_name};"
            f"User ID=app:{self.client_id}@{self.tenant_id};"
            f"Password={self.client_secret};"
        )
    
    def discover_tables(self) -> Dict:
        """Discover all user-facing tables in the dataset"""
        if not self.connected and not self._test_connection():
            return {"success": False, "error": "Not connected to Power BI"}
        
        try:
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            
            tables_list = []
            with Pyadomd(connection_string) as pyadomd_conn:
                # Try ADOMD schema discovery first
                try:
                    from Microsoft.AnalysisServices.AdomdClient import AdomdSchemaGuid
                    
                    adomd_connection = pyadomd_conn.conn
                    tables_dataset = adomd_connection.GetSchemaDataSet(AdomdSchemaGuid.Tables, None)
                    
                    if tables_dataset and tables_dataset.Tables.Count > 0:
                        schema_table = tables_dataset.Tables[0]
                        for row in schema_table.Rows:
                            table_name = row["TABLE_NAME"]
                            if (not table_name.startswith("$") and 
                                not table_name.startswith("DateTableTemplate_") and 
                                not row["TABLE_SCHEMA"] == "$SYSTEM"):
                                tables_list.append(table_name)
                except Exception as schema_error:
                    logger.warning(f"Schema discovery via ADOMD failed: {schema_error}")
                    # Fallback to DAX discovery
                    tables_list = self._discover_tables_via_dax(pyadomd_conn)
            
            self.tables_cache = tables_list
            logger.info(f"✅ Discovered {len(tables_list)} tables")
            return {"success": True, "tables": tables_list}
            
        except Exception as e:
            logger.error(f"Failed to discover tables: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _discover_tables_via_dax(self, pyadomd_conn) -> List[str]:
        """Fallback method to discover tables using DAX queries"""
        tables = []
        try:
            # Common table name patterns in Power BI
            common_patterns = [
                # Fact tables
                "Sales", "Orders", "Transactions", "Revenue", "FactSales", "Fact_Sales",
                "FactOrders", "Fact_Orders", "FactRevenue", "FactTransactions",
                
                # Dimension tables  
                "Customer", "Product", "Date", "Calendar", "Time", "Geography",
                "Store", "Employee", "Supplier", "Category", "Subcategory",
                "DimCustomer", "DimProduct", "DimDate", "DimGeography",
                "Dim_Customer", "Dim_Product", "Dim_Date",
                
                # Common variations
                "Customers", "Products", "Dates", "Stores", "Employees",
                "Item", "Items", "Location", "Locations", "Region", "Regions",
                "Reseller", "Resellers", "Vendor", "Vendors"
            ]
            
            cursor = pyadomd_conn.cursor()
            
            # First try DMV query
            try:
                dmv_query = "SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [IsHidden] = false"
                cursor.execute(dmv_query)
                for row in cursor.fetchall():
                    table_name = row[0]
                    if not table_name.startswith('$'):
                        tables.append(table_name)
                        logger.info(f"✅ Found table via DMV: {table_name}")
            except:
                logger.debug("DMV query failed, trying pattern matching")
            
            # If no tables found, try common patterns
            if not tables:
                for table_name in common_patterns:
                    try:
                        escaped_table = self._escape_table_name(table_name)
                        test_query = f"EVALUATE TOPN(1, {escaped_table})"
                        cursor.execute(test_query)
                        cursor.fetchall()  # If this succeeds, table exists
                        tables.append(table_name)
                        logger.info(f"✅ Found table via DAX: {table_name}")
                    except:
                        pass
            
            cursor.close()
            
        except Exception as e:
            logger.warning(f"DAX table discovery failed: {e}")
        
        return tables
    
    def _test_connection(self) -> bool:
        """Test if connection is still valid"""
        try:
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            with Pyadomd(connection_string) as conn:
                return True
        except:
            return False
    
    def _escape_table_name(self, table_name: str) -> str:
        """Escape table name for DAX query"""
        # If table name contains spaces, special characters, or starts with underscore
        if ' ' in table_name or '-' in table_name or table_name.startswith('_') or '.' in table_name:
            return f"'{table_name}'"
        return table_name
    
    def list_tables(self) -> Dict:
        """List all available tables"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        return {
            "success": True,
            "tables": self.tables_cache,
            "count": len(self.tables_cache)
        }
    
    def execute_dax_query(self, dax_query: str) -> Dict:
        """Execute DAX query with enhanced error handling and retry logic"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        if not self.pyadomd_available:
            return {"success": False, "error": f"pyadomd not available: {self.error_message}"}
        
        # Clean the query
        dax_query = self.clean_dax_query(dax_query)
        
        # Validate query
        if not dax_query or len(dax_query.strip()) == 0:
            return {"success": False, "error": "Empty DAX query provided"}
        
        logger.info(f"Executing DAX query: {dax_query}")
        
        # Try to execute with retry logic
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = self._execute_dax_internal(dax_query)
                if result['success']:
                    return result
                
                # If query failed, try to fix it
                if attempt < max_retries - 1:
                    fixed_query = self._fix_dax_query(dax_query, result.get('error', ''))
                    if fixed_query != dax_query:
                        dax_query = fixed_query
                        logger.info(f"Retrying with fixed query (attempt {attempt + 2}/{max_retries})")
                        continue
                
                last_error = result.get('error')
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"DAX execution attempt {attempt + 1} failed: {last_error}")
        
        return {
            "success": False,
            "error": last_error or "DAX query execution failed after retries",
            "query": dax_query
        }
    
    def _execute_dax_internal(self, dax_query: str) -> Dict:
        """Internal DAX execution"""
        try:
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            
            with Pyadomd(connection_string) as conn:
                cursor = conn.cursor()
                
                try:
                    cursor.execute(dax_query)
                    
                    headers = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    results = []
                    for row in rows:
                        results.append(dict(zip(headers, row)))
                    
                    logger.info(f"✅ DAX query returned {len(results)} rows")
                    return {
                        "success": True,
                        "columns": headers,
                        "data": results,
                        "row_count": len(results)
                    }
                    
                except Exception as exec_error:
                    error_msg = str(exec_error)
                    logger.error(f"DAX execution error: {error_msg}")
                    
                    return self._analyze_dax_error(error_msg, dax_query)
                    
                finally:
                    cursor.close()
                    
        except Exception as e:
            logger.error(f"Connection error during DAX execution: {e}")
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    def _analyze_dax_error(self, error_msg: str, dax_query: str) -> Dict:
        """Analyze DAX error and provide helpful response"""
        error_lower = error_msg.lower()
        
        if "end of the input was reached" in error_lower:
            return {
                "success": False, 
                "error": "Invalid DAX syntax - query appears to be incomplete or malformed",
                "details": error_msg,
                "query": dax_query,
                "suggestion": "Check that the DAX query is complete and properly formatted"
            }
        elif "cannot be found" in error_lower or "not found" in error_lower:
            # Extract the problematic element
            import re
            column_match = re.search(r"Column '([^']+)'", error_msg)
            table_match = re.search(r"table '([^']+)'", error_msg)
            
            return {
                "success": False,
                "error": "Column or table not found in the model",
                "details": error_msg,
                "problematic_column": column_match.group(1) if column_match else None,
                "problematic_table": table_match.group(1) if table_match else None,
                "suggestion": f"Check column and table names. Available tables: {', '.join(self.tables_cache[:5])}"
            }
        elif "syntax" in error_lower:
            return {
                "success": False,
                "error": "DAX syntax error",
                "details": error_msg,
                "query": dax_query,
                "suggestion": "Check DAX syntax - common issues: missing EVALUATE, incorrect function usage"
            }
        else:
            return {
                "success": False,
                "error": f"DAX execution failed: {error_msg}",
                "query": dax_query
            }
    
    def _fix_dax_query(self, query: str, error: str) -> str:
        """Attempt to fix common DAX query issues"""
        original_query = query
        
        # Fix 1: Ensure EVALUATE is present
        if not query.strip().upper().startswith('EVALUATE'):
            query = 'EVALUATE\n' + query
        
        # Fix 2: Handle YEAR function usage in SUMMARIZE
        if 'YEAR' in query and 'syntax' in error.lower():
            # YEAR() cannot be used directly in SUMMARIZE, need to use ADDCOLUMNS
            if 'SUMMARIZE' in query:
                # Convert SUMMARIZE with YEAR to SUMMARIZECOLUMNS
                query = self._convert_summarize_to_summarizecolumns(query)
        
        # Fix 3: Fix table/column references
        if 'not found' in error.lower():
            query = self._fix_table_column_references(query, error)
        
        # Fix 4: Remove invalid ORDER BY in certain contexts
        if 'ORDER BY' in query and 'syntax' in error.lower():
            # ORDER BY can only be used at the top level
            query = re.sub(r'ORDER BY.*?(?=\)|$)', '', query, flags=re.IGNORECASE | re.DOTALL)
        
        return query if query != original_query else original_query
    
    def _convert_summarize_to_summarizecolumns(self, query: str) -> str:
        """Convert SUMMARIZE with calculated columns to SUMMARIZECOLUMNS"""
        # This is a simplified conversion - in practice would need more sophisticated parsing
        if 'SUMMARIZE' in query and 'YEAR' in query:
            # Replace SUMMARIZE with ADDCOLUMNS pattern
            query = re.sub(
                r'SUMMARIZE\s*\(\s*(\w+)\s*,\s*YEAR\s*\([^)]+\)\s*,',
                r'ADDCOLUMNS(SUMMARIZE(\1),',
                query,
                flags=re.IGNORECASE
            )
        
        return query
    
    def _fix_table_column_references(self, query: str, error: str) -> str:
        """Fix table and column references based on error"""
        # Extract problematic references
        import re
        
        # Look for unescaped table names with spaces
        for table in self.tables_cache:
            if ' ' in table and table in query and f"'{table}'" not in query:
                query = query.replace(table, f"'{table}'")
        
        # Try to fix column references
        column_pattern = r'\[([^\]]+)\]'
        columns = re.findall(column_pattern, query)
        
        for col in columns:
            # If column reference doesn't have table prefix, try to add it
            if '.' not in col and not any(f"{table}[{col}]" in query for table in self.tables_cache):
                # Find most likely table for this column
                likely_table = self._find_table_for_column(col)
                if likely_table:
                    query = query.replace(f"[{col}]", f"{self._escape_table_name(likely_table)}[{col}]")
        
        return query
    
    def _find_table_for_column(self, column_name: str) -> Optional[str]:
        """Try to find which table contains a column"""
        # Use cached model info if available
        if self.model_info and 'tables' in self.model_info:
            for table_name, table_info in self.model_info['tables'].items():
                if 'columns' in table_info:
                    for col in table_info['columns']:
                        if col['name'].lower() == column_name.lower():
                            return table_name
        
        # Heuristic matching
        column_lower = column_name.lower()
        
        # Common patterns
        if 'customer' in column_lower:
            return self._find_table_by_pattern(['Customer', 'DimCustomer', 'Customers'])
        elif 'product' in column_lower:
            return self._find_table_by_pattern(['Product', 'DimProduct', 'Products'])
        elif 'date' in column_lower or 'year' in column_lower or 'month' in column_lower:
            return self._find_table_by_pattern(['Date', 'Calendar', 'DimDate', 'Dates'])
        elif 'sales' in column_lower or 'amount' in column_lower or 'revenue' in column_lower:
            return self._find_table_by_pattern(['Sales', 'FactSales', 'Orders', 'Revenue'])
        
        return None
    
    def _find_table_by_pattern(self, patterns: List[str]) -> Optional[str]:
        """Find table matching patterns"""
        for pattern in patterns:
            for table in self.tables_cache:
                if pattern.lower() in table.lower():
                    return table
        return None
    
    def generate_dax_query(self, user_question: str) -> str:
        """Generate a DAX query based on user question with improved NL understanding"""
        if not self.tables_cache:
            raise Exception("No tables discovered. Connect to Power BI first.")
        
        # Analyze the question
        analysis = self._analyze_user_question(user_question)
        
        # Generate DAX based on analysis
        try:
            if analysis['intent'] == 'yearly_aggregation':
                return self._generate_yearly_aggregation_dax(analysis)
            elif analysis['intent'] == 'simple_aggregation':
                return self._generate_simple_aggregation_dax(analysis)
            elif analysis['intent'] == 'grouped_aggregation':
                return self._generate_grouped_aggregation_dax(analysis)
            elif analysis['intent'] == 'top_n':
                return self._generate_top_n_dax(analysis)
            else:
                # Fallback to simple query
                return self._generate_fallback_dax(analysis)
                
        except Exception as e:
            logger.error(f"Failed to generate DAX query: {e}")
            # Return a simple working query as fallback
            if self.tables_cache:
                return f"EVALUATE TOPN(10, '{self.tables_cache[0]}')"
            else:
                return "EVALUATE {}"
    
    def _analyze_user_question(self, question: str) -> Dict:
        """Analyze user question to extract intent and entities"""
        question_lower = question.lower()
        
        analysis = {
            'original_question': question,
            'intent': 'unknown',
            'time_dimension': None,
            'measure': None,
            'measure_column': None,
            'aggregation': 'SUM',
            'group_by': None,
            'filter': None,
            'top_n': None
        }
        
        # Detect intent patterns
        if any(word in question_lower for word in ['yearly', 'by year', 'per year', 'annual']):
            analysis['intent'] = 'yearly_aggregation'
            analysis['time_dimension'] = 'year'
        elif any(word in question_lower for word in ['monthly', 'by month', 'per month']):
            analysis['intent'] = 'yearly_aggregation'  # Will handle monthly too
            analysis['time_dimension'] = 'month'
        elif any(word in question_lower for word in ['top', 'highest', 'lowest', 'best', 'worst']):
            analysis['intent'] = 'top_n'
            # Extract number
            import re
            num_match = re.search(r'top\s+(\d+)', question_lower)
            analysis['top_n'] = int(num_match.group(1)) if num_match else 10
        elif any(word in question_lower for word in ['by', 'per', 'group by']):
            analysis['intent'] = 'grouped_aggregation'
        else:
            analysis['intent'] = 'simple_aggregation'
        
        # Detect measure
        if any(word in question_lower for word in ['sales', 'revenue', 'income']):
            analysis['measure'] = 'sales'
            analysis['measure_column'] = self._find_sales_column()
        elif any(word in question_lower for word in ['cost', 'expense']):
            analysis['measure'] = 'cost'
            analysis['measure_column'] = self._find_cost_column()
        elif any(word in question_lower for word in ['profit', 'margin']):
            analysis['measure'] = 'profit'
            analysis['measure_column'] = self._find_profit_column()
        elif any(word in question_lower for word in ['quantity', 'volume', 'units']):
            analysis['measure'] = 'quantity'
            analysis['measure_column'] = self._find_quantity_column()
        elif any(word in question_lower for word in ['count', 'number']):
            analysis['measure'] = 'count'
            analysis['aggregation'] = 'COUNT'
        
        # Detect aggregation
        if any(word in question_lower for word in ['average', 'avg', 'mean']):
            analysis['aggregation'] = 'AVERAGE'
        elif any(word in question_lower for word in ['maximum', 'max', 'highest']):
            analysis['aggregation'] = 'MAX'
        elif any(word in question_lower for word in ['minimum', 'min', 'lowest']):
            analysis['aggregation'] = 'MIN'
        elif any(word in question_lower for word in ['count', 'number of']):
            analysis['aggregation'] = 'COUNT'
        
        # Detect group by dimension
        if 'by product' in question_lower or 'per product' in question_lower:
            analysis['group_by'] = self._find_column_by_pattern(['product', 'item'])
        elif 'by customer' in question_lower or 'per customer' in question_lower:
            analysis['group_by'] = self._find_column_by_pattern(['customer', 'client'])
        elif 'by region' in question_lower or 'per region' in question_lower:
            analysis['group_by'] = self._find_column_by_pattern(['region', 'geography', 'location'])
        elif 'by category' in question_lower or 'per category' in question_lower:
            analysis['group_by'] = self._find_column_by_pattern(['category', 'subcategory'])
        
        return analysis
    
    def _find_sales_column(self) -> Optional[Dict]:
        """Find sales-related column"""
        patterns = ['sales', 'revenue', 'amount', 'salesamount', 'total', 'price']
        return self._find_column_by_pattern(patterns)
    
    def _find_cost_column(self) -> Optional[Dict]:
        """Find cost-related column"""
        patterns = ['cost', 'expense', 'cogs', 'unitcost']
        return self._find_column_by_pattern(patterns)
    
    def _find_profit_column(self) -> Optional[Dict]:
        """Find profit-related column"""
        patterns = ['profit', 'margin', 'income']
        return self._find_column_by_pattern(patterns)
    
    def _find_quantity_column(self) -> Optional[Dict]:
        """Find quantity-related column"""
        patterns = ['quantity', 'qty', 'units', 'volume']
        return self._find_column_by_pattern(patterns)
    
    def _find_column_by_pattern(self, patterns: List[str]) -> Optional[Dict]:
        """Find column matching patterns - USE ACTUAL DISCOVERED COLUMNS"""
        # First check cached model info
        if self.model_info and 'tables' in self.model_info:
            for table_name, table_info in self.model_info['tables'].items():
                if 'columns' in table_info and table_info['columns']:
                    for col in table_info['columns']:
                        col_lower = col['name'].lower()
                        for pattern in patterns:
                            if pattern in col_lower:
                                return {
                                    'table': table_name,
                                    'column': col['name'],
                                    'full_name': f"{self._escape_table_name(table_name)}[{col['name']}]"
                                }
        
        # If no columns discovered yet, try to discover them for relevant tables
        if not self.model_info or not self.model_info.get('tables'):
            logger.warning("No column information available - attempting discovery")
            self._discover_enhanced_schema()
            
            # Retry with discovered schema
            if self.model_info and 'tables' in self.model_info:
                for table_name, table_info in self.model_info['tables'].items():
                    if 'columns' in table_info and table_info['columns']:
                        for col in table_info['columns']:
                            col_lower = col['name'].lower()
                            for pattern in patterns:
                                if pattern in col_lower:
                                    return {
                                        'table': table_name,
                                        'column': col['name'],
                                        'full_name': f"{self._escape_table_name(table_name)}[{col['name']}]"
                                    }
        
        # Last resort: return None instead of guessing
        logger.warning(f"No column found matching patterns: {patterns}")
        return None
    
    def _generate_yearly_aggregation_dax(self, analysis: Dict) -> str:
        """Generate DAX for yearly aggregation queries"""
        # Find date column
        date_info = self._find_date_column()
        if not date_info:
            # Fallback to simple aggregation
            return self._generate_simple_aggregation_dax(analysis)
        
        # Get measure column
        measure_info = analysis.get('measure_column')
        if not measure_info:
            # Try to find any numeric column
            measure_info = self._find_any_numeric_column()
        
        if not measure_info:
            raise ValueError("Cannot find measure column for aggregation")
        
        # Build the query
        date_table = self._escape_table_name(date_info['table'])
        date_column = date_info['column']
        value_table = self._escape_table_name(measure_info['table'])
        value_column = measure_info['column']
        
        dax = self.dax_templates['yearly_aggregation'].format(
            date_table=date_table,
            date_column=date_column,
            measure_name=f"Total {analysis.get('measure', 'Value')}",
            aggregation=analysis['aggregation'],
            value_table=value_table,
            value_column=value_column
        )
        
        return self.clean_dax_query(dax)
    
    def _generate_simple_aggregation_dax(self, analysis: Dict) -> str:
        """Generate DAX for simple aggregation queries"""
        measure_info = analysis.get('measure_column')
        if not measure_info:
            measure_info = self._find_any_numeric_column()
        
        if not measure_info:
            # Fallback to row count
            if self.tables_cache:
                table = self._escape_table_name(self.tables_cache[0])
                return f"EVALUATE\nROW(\"Count\", COUNTROWS({table}))"
            else:
                return "EVALUATE {}"
        
        table = self._escape_table_name(measure_info['table'])
        column = measure_info['column']
        
        dax = self.dax_templates['simple_aggregation'].format(
            measure_name=f"Total {analysis.get('measure', 'Value')}",
            aggregation=analysis['aggregation'],
            table=table,
            column=column
        )
        
        return self.clean_dax_query(dax)
    
    def _generate_grouped_aggregation_dax(self, analysis: Dict) -> str:
        """Generate DAX for grouped aggregation queries"""
        # Get group by column
        group_info = analysis.get('group_by')
        if not group_info:
            # Try to find a dimension column
            group_info = self._find_any_dimension_column()
        
        if not group_info:
            # Fallback to simple aggregation
            return self._generate_simple_aggregation_dax(analysis)
        
        # Get measure column
        measure_info = analysis.get('measure_column')
        if not measure_info:
            measure_info = self._find_any_numeric_column()
        
        if not measure_info:
            raise ValueError("Cannot find measure column for aggregation")
        
        group_table = self._escape_table_name(group_info['table'])
        group_column = group_info['column']
        value_table = self._escape_table_name(measure_info['table'])
        value_column = measure_info['column']
        
        dax = self.dax_templates['grouped_aggregation'].format(
            group_table=group_table,
            group_column=group_column,
            measure_name=f"Total {analysis.get('measure', 'Value')}",
            aggregation=analysis['aggregation'],
            value_table=value_table,
            value_column=value_column
        )
        
        return self.clean_dax_query(dax)
    
    def _generate_top_n_dax(self, analysis: Dict) -> str:
        """Generate DAX for top N queries"""
        n = analysis.get('top_n', 10)
        
        # Get dimension to group by
        group_info = analysis.get('group_by')
        if not group_info:
            # For "top products by sales", we need a product identifier
            if 'product' in analysis['original_question'].lower():
                group_info = self._find_column_by_pattern(['productname', 'product', 'item', 'sku', 'productkey'])
            else:
                group_info = self._find_any_dimension_column()
        
        if not group_info:
            # If we can't find a dimension column, try to use the table itself
            product_tables = [t for t in self.tables_cache if 'product' in t.lower()]
            if product_tables:
                # Use a simple TOPN on the table
                table = self._escape_table_name(product_tables[0])
                return f"EVALUATE\nTOPN({n}, {table})"
            else:
                return self._generate_simple_aggregation_dax(analysis)
        
        # Get measure - check if it's a defined measure first
        measure_info = None
        measure_name = None
        
        # Check for existing measures
        if self.model_info and 'measures' in self.model_info:
            for measure in self.model_info['measures']:
                if any(word in measure['name'].lower() for word in ['sales', 'revenue', 'amount']):
                    measure_name = f"[{measure['name']}]"
                    break
        
        # If no measure found, look for a column
        if not measure_name:
            measure_info = analysis.get('measure_column')
            if not measure_info:
                measure_info = self._find_column_by_pattern(['sales', 'revenue', 'amount', 'total', 'price'])
        
        if not measure_info and not measure_name:
            # Can't do top N without a measure
            logger.warning("No measure found for top N query")
            # Return simple table query
            if group_info:
                table = self._escape_table_name(group_info['table'])
                return f"EVALUATE\nTOPN({n}, {table})"
            else:
                return self._generate_simple_aggregation_dax(analysis)
        
        # Build the query
        group_table = self._escape_table_name(group_info['table'])
        group_column = group_info['column']
        
        if measure_name:
            # Use existing measure
            dax = f"""EVALUATE
    TOPN(
        {n},
        SUMMARIZE(
            {group_table},
            {group_table}[{group_column}],
            "Total", {measure_name}
        ),
        [Total],
        DESC
    )"""
        else:
            # Use column aggregation
            value_table = self._escape_table_name(measure_info['table'])
            value_column = measure_info['column']
            
            dax = self.dax_templates['top_n'].format(
                n=n,
                group_table=group_table,
                group_column=group_column,
                measure_name=f"Total {analysis.get('measure', 'Value')}",
                aggregation=analysis['aggregation'],
                value_table=value_table,
                value_column=value_column
            )
        
        return self.clean_dax_query(dax)
    
    def _generate_fallback_dax(self, analysis: Dict) -> str:
        """Generate fallback DAX query"""
        # Try to generate something useful based on available tables
        if self.tables_cache:
            # Find likely fact table
            fact_table = None
            for table in self.tables_cache:
                if any(word in table.lower() for word in ['fact', 'sales', 'order', 'transaction']):
                    fact_table = table
                    break
            
            if not fact_table:
                fact_table = self.tables_cache[0]
            
            escaped_table = self._escape_table_name(fact_table)
            return f"EVALUATE\nTOPN(100, {escaped_table})"
        else:
            return "EVALUATE {}"
    
    def _find_date_column(self) -> Optional[Dict]:
        """Find date column in the model"""
        patterns = ['date', 'datetime', 'orderdate', 'saledate', 'transactiondate']
        
        # Check Date or Calendar table first
        date_tables = [t for t in self.tables_cache if any(d in t.lower() for d in ['date', 'calendar', 'time'])]
        
        for table in date_tables:
            # Common date column names
            for col in ['Date', 'DateKey', 'FullDate', 'CalendarDate']:
                return {
                    'table': table,
                    'column': col,
                    'full_name': f"{self._escape_table_name(table)}[{col}]"
                }
        
        # Look in fact tables
        return self._find_column_by_pattern(patterns)
    
    def _find_any_numeric_column(self) -> Optional[Dict]:
        """Find any numeric column as fallback"""
        # Common numeric column patterns
        patterns = ['amount', 'sales', 'revenue', 'cost', 'price', 'quantity', 'total']
        
        col_info = self._find_column_by_pattern(patterns)
        if col_info:
            return col_info
        
        # Last resort: return a guess based on table type
        fact_tables = [t for t in self.tables_cache if any(f in t.lower() for f in ['fact', 'sales', 'order'])]
        
        if fact_tables:
            return {
                'table': fact_tables[0],
                'column': 'Amount',  # Common column name
                'full_name': f"{self._escape_table_name(fact_tables[0])}[Amount]"
            }
        
        return None
    
    def _find_any_dimension_column(self) -> Optional[Dict]:
        """Find any dimension column as fallback"""
        # Look for dimension tables
        dim_tables = [t for t in self.tables_cache if any(d in t.lower() for d in ['dim', 'product', 'customer', 'geography'])]
        
        if dim_tables:
            table = dim_tables[0]
            # Guess common dimension column names
            if 'product' in table.lower():
                col = 'ProductName'
            elif 'customer' in table.lower():
                col = 'CustomerName'
            elif 'geography' in table.lower():
                col = 'Country'
            else:
                col = 'Name'
            
            return {
                'table': table,
                'column': col,
                'full_name': f"{self._escape_table_name(table)}[{col}]"
            }
        
        return None
    
    def clean_dax_query(self, dax_query: str) -> str:
        """Remove HTML/XML tags and clean DAX query"""
        if not dax_query:
            return ""
        
        # Remove HTML/XML tags including oii tags
        cleaned = re.sub(r'<[^>]+>', '', dax_query)
        
        # Remove any remaining angle brackets that aren't comparison operators
        # Preserve < and > when used as operators (preceded/followed by space or number)
        cleaned = re.sub(r'<(?![=\s\d])', '', cleaned)
        cleaned = re.sub(r'(?<![=\s\d])>', '', cleaned)
        
        # Remove markdown code blocks
        if '```' in cleaned:
            match = re.search(r'```(?:dax)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1)
            else:
                cleaned = cleaned.replace('```', '')
        
        # Remove any remaining backticks
        cleaned = cleaned.replace('`', '')
        
        # Remove "dax:" or "DAX:" prefix
        cleaned = re.sub(r'^(dax:|DAX:)\s*', '', cleaned.strip())
        
        # Clean up whitespace while preserving DAX structure
        lines = cleaned.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
        
        cleaned = '\n'.join(cleaned_lines)
        
        # Ensure EVALUATE is present
        if cleaned and not cleaned.upper().startswith('EVALUATE'):
            # Check if it's a complete query missing EVALUATE
            if any(keyword in cleaned.upper() for keyword in ['SUMMARIZE', 'FILTER', 'ADDCOLUMNS', 'ROW']):
                cleaned = 'EVALUATE\n' + cleaned
            # Or just a table name
            elif cleaned in self.tables_cache or any(table.lower() == cleaned.lower() for table in self.tables_cache):
                cleaned = f"EVALUATE {self._escape_table_name(cleaned)}"
        
        return cleaned.strip()
    
    def query_data_natural_language(self, user_question: str) -> Dict:
        """Process natural language query"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        try:
            # Generate DAX query
            dax_query = self.generate_dax_query(user_question)
            
            # Execute query
            results = self.execute_dax_query(dax_query)
            
            if not results.get("success"):
                return results
            
            # Create interpretation
            data = results.get("data", [])
            row_count = results.get("row_count", 0)
            
            interpretation = f"Found {row_count} results for your question."
            if row_count == 1 and data:
                # Single value result
                first_row = data[0]
                if len(first_row) == 1:
                    value = list(first_row.values())[0]
                    key = list(first_row.keys())[0]
                    interpretation = f"The {key} is {value}"
            elif row_count > 0:
                interpretation += " Here are the results:"
            
            return {
                "success": True,
                "question": user_question,
                "dax_query": dax_query,
                "data": data,
                "row_count": row_count,
                "answer": interpretation
            }
            
        except Exception as e:
            logger.error(f"Natural language query failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get detailed information about a specific table"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        try:
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            
            table_info = {
                "table_name": table_name,
                "columns": [],
                "sample_data": [],
                "row_count": 0
            }
            
            with Pyadomd(connection_string) as conn:
                cursor = conn.cursor()
                
                # Get columns and sample data
                try:
                    escaped_table = self._escape_table_name(table_name)
                    sample_query = f"EVALUATE TOPN(5, {escaped_table})"
                    cursor.execute(sample_query)
                    
                    # Get columns from description
                    if cursor.description:
                        table_info["columns"] = [
                            {"name": desc[0], "type": "string"} 
                            for desc in cursor.description
                        ]
                    
                    # Get sample data
                    rows = cursor.fetchall()
                    headers = [col["name"] for col in table_info["columns"]]
                    
                    for row in rows:
                        table_info["sample_data"].append(dict(zip(headers, row)))
                    
                    # Get row count
                    table_info["row_count"] = self._estimate_row_count(conn, table_name)
                    
                except Exception as e:
                    logger.error(f"Error getting table info for {table_name}: {e}")
                    return {"success": False, "error": str(e)}
                
                cursor.close()
            
            return {
                "success": True,
                **table_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {"success": False, "error": str(e)}
    
    def get_sample_data(self, table_name: str, num_rows: int = 10) -> Dict:
        """Get sample data from a table"""
        escaped_table = self._escape_table_name(table_name)
        dax_query = f"EVALUATE TOPN({num_rows}, {escaped_table})"
        return self.execute_dax_query(dax_query)
    
    async def suggest_questions(self) -> Dict:
        """Suggest interesting questions based on available data"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        suggestions = []
        
        try:
            # Base suggestions on discovered schema
            if self.model_info and self.model_info.get('measures'):
                # If we have measures, suggest measure-based questions
                for measure in self.model_info['measures'][:3]:
                    suggestions.append(f"What is the {measure['name']}?")
            
            # Table-based suggestions
            if self.tables_cache:
                # Sales/Revenue questions
                sales_tables = [t for t in self.tables_cache if any(s in t.lower() for s in ['sales', 'revenue', 'order'])]
                if sales_tables:
                    suggestions.extend([
                        "What are the total sales by year?",
                        "Show me the top 10 customers by revenue",
                        "What is the sales trend over time?"
                    ])
                
                # Product questions
                product_tables = [t for t in self.tables_cache if 'product' in t.lower()]
                if product_tables:
                    suggestions.extend([
                        "Which products have the highest sales?",
                        "Show me sales by product category",
                        "What are the top selling products?"
                    ])
                
                # Customer questions
                customer_tables = [t for t in self.tables_cache if 'customer' in t.lower()]
                if customer_tables:
                    suggestions.extend([
                        "How many customers do we have?",
                        "Show me customer distribution by region",
                        "Who are our top customers?"
                    ])
                
                # Date/Time questions
                date_tables = [t for t in self.tables_cache if any(d in t.lower() for d in ['date', 'calendar', 'time'])]
                if date_tables:
                    suggestions.extend([
                        "Show me the yearly sales trend",
                        "What are the monthly sales figures?",
                        "Compare this year's performance to last year"
                    ])
            
            # Ensure we have at least 5 suggestions
            if len(suggestions) < 5:
                suggestions.extend([
                    "What are the key metrics in this dataset?",
                    "Show me a summary of the data",
                    "What are the main trends?",
                    "Give me the top 10 records",
                    "What insights can you find in this data?"
                ])
            
            # Limit to 10 unique suggestions
            suggestions = list(dict.fromkeys(suggestions))[:10]
            
            return {"success": True, "questions": suggestions}
            
        except Exception as e:
            logger.error(f"Failed to generate question suggestions: {e}")
            # Return generic suggestions on error
            return {
                "success": True,
                "questions": [
                    "What are the total sales?",
                    "Show me the data by category",
                    "What are the trends over time?",
                    "Which items are most popular?",
                    "Give me a summary of key metrics"
                ]
            }
    
    def discover_model(self) -> Dict:
        """Discover complete model structure"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Power BI"}
        
        try:
            # Use enhanced discovery if available
            if self.model_info:
                return {
                    "success": True,
                    "model": self.model_info,
                    "table_count": len(self.model_info.get('tables', {})),
                    "measure_count": len(self.model_info.get('measures', []))
                }
            
            # Otherwise do basic discovery
            self._discover_enhanced_schema()
            
            return {
                "success": True,
                "model": self.model_info or {},
                "table_count": len(self.tables_cache),
                "measure_count": 0
            }
            
        except Exception as e:
            logger.error(f"Model discovery failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_available_columns(self, table_name: str) -> List[str]:
        """Get list of available columns for a table"""
        if self.model_info and 'tables' in self.model_info:
            table_info = self.model_info['tables'].get(table_name, {})
            if 'columns' in table_info:
                return [col['name'] for col in table_info['columns']]
        
        # Try to discover if not cached
        try:
            connection_string = self._get_connection_string()
            from pyadomd import Pyadomd
            
            with Pyadomd(connection_string) as conn:
                table_info = self._discover_table_details(conn, table_name)
                if table_info and 'columns' in table_info:
                    return [col['name'] for col in table_info['columns']]
        except:
            pass
        
        return []

    def debug_schema(self) -> Dict:
        """Debug method to show what's actually discovered"""
        debug_info = {
            "tables_discovered": len(self.tables_cache),
            "tables_with_columns": len(self.model_info.get('tables', {})) if self.model_info else 0,
            "measures_discovered": len(self.model_info.get('measures', [])) if self.model_info else 0,
            "sample_tables": {}
        }
        
        # Show first 5 tables with their columns
        if self.model_info and 'tables' in self.model_info:
            for i, (table_name, table_info) in enumerate(self.model_info['tables'].items()):
                if i >= 5:
                    break
                debug_info['sample_tables'][table_name] = {
                    'columns': [col['name'] for col in table_info.get('columns', [])],
                    'column_count': len(table_info.get('columns', []))
                }
        
        return debug_info

    def get_status(self) -> Dict:
        """Get detailed status information"""
        return {
            "connected": self.connected,
            "pyadomd_available": self.pyadomd_available,
            "adomd_available": self.adomd_available,
            "error_message": self.error_message,
            "xmla_endpoint": self.xmla_endpoint,
            "dataset_name": self.dataset_name,
            "tables_count": len(self.tables_cache),
            "tables": self.tables_cache[:10] if self.tables_cache else [],
            "credentials_configured": all([self.tenant_id, self.client_id, self.client_secret])
        }
    

# Singleton
semantic_model_service = SemanticModelService()