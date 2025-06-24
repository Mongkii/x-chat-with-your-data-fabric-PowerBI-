from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Chat with Data API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import services
from app.fabric_service import fabric_service
from app.data_analysis_service import data_analysis_service
from app.auth_service import auth_service
from app.semantic_model_service import semantic_model_service
from app.enhanced_multi_agent_service import enhanced_multi_agent_service

# Import Claude service
claude_available = False
claude_service = None
try:
    from app.claude_service import claude_service as cs
    if cs is not None:
        claude_service = cs
        claude_available = True
        logger.info("Claude service initialized successfully")
except Exception as e:
    logger.error(f"Claude service not available: {e}")

# Import multi-agent service if available
multi_agent_available = False
try:
    from app.multi_agent_service import multi_agent_service
    multi_agent_available = True
    logger.info("Multi-agent service available")
except Exception as e:
    logger.info(f"Multi-agent service not available: {e}")

# Import knowledge base service
try:
    from app.knowledge_base_service import knowledge_base_service
    logger.info("Knowledge base service available")
except Exception as e:
    logger.info(f"Knowledge base service not available: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
        }
    )

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Chat with Data API",
        "status": "running",
        "version": "1.0.0",
        "claude_available": claude_available,
        "services": {
            "claude": claude_available,
            "multi_agent": multi_agent_available,
            "fabric": True,
            "semantic_model": True,
            "auth": True
        }
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "claude_available": claude_available
    }

# Configuration check endpoint
@app.get("/api/config")
def check_config():
    api_key_exists = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "claude_configured": api_key_exists and claude_available,
        "api_key_exists": api_key_exists,
        "claude_service_loaded": claude_available,
        "app_name": os.getenv("APP_NAME", "Chat with Data")
    }

# ==========================================
# CLAUDE CHAT ENDPOINTS
# ==========================================

@app.post("/api/chat")
async def chat(body: Dict):
    """Basic chat endpoint with Claude"""
    message = body.get("message", "")
    use_claude = body.get("use_claude", True)
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        if use_claude and claude_available and claude_service:
            logger.info(f"Using Claude to respond to: {message}")
            response = await claude_service.get_response(message)
            logger.info("Claude response received successfully")
        else:
            logger.info("Using fallback response (Claude not available)")
            response = f"Echo: {message} (Claude not available - check your API key)"
        
        return {
            "response": response,
            "status": "success",
            "used_claude": use_claude and claude_available
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {
            "response": f"Error: {str(e)}",
            "status": "error",
            "used_claude": False
        }

# ==========================================
# OAUTH2 AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/auth/configure")
async def configure_oauth(body: Dict):
    """Configure OAuth2 authentication"""
    tenant_id = body.get("tenant_id", "")
    client_id = body.get("client_id", "")
    client_secret = body.get("client_secret", "")
    
    if not all([tenant_id, client_id, client_secret]):
        raise HTTPException(
            status_code=400, 
            detail="tenant_id, client_id, and client_secret are required"
        )
    
    auth_service.configure(tenant_id, client_id, client_secret)
    
    # Test the configuration
    result = auth_service.test_configuration()
    
    if result["success"]:
        return {
            "success": True,
            "message": "OAuth2 configured successfully",
            "authenticated": True
        }
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.get("/api/auth/status")
async def auth_status():
    """Check OAuth2 authentication status"""
    return {
        "configured": auth_service.is_configured(),
        "tenant_id": auth_service.tenant_id is not None,
        "client_id": auth_service.client_id is not None
    }

# ==========================================
# MICROSOFT FABRIC ENDPOINTS
# ==========================================

@app.post("/api/fabric/connect")
async def connect_to_fabric(body: Dict):
    """Connect to Microsoft Fabric using OAuth2"""
    server = body.get("server", "")
    database = body.get("database", "")
    
    if not server or not database:
        raise HTTPException(
            status_code=400, 
            detail="server and database are required"
        )
    
    # Check if OAuth2 is configured
    if not auth_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="OAuth2 authentication not configured. Please configure authentication first."
        )
    
    # Configure fabric service
    fabric_service.configure(server, database)
    
    # Test connection
    result = fabric_service.test_connection()
    
    if result["success"]:
        # Set connection type for multi-agent
        enhanced_multi_agent_service.set_connection_type("sql")
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.get("/api/fabric/schema")
async def get_schema():
    """Get database schema"""
    result = fabric_service.discover_schema()
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Schema discovery failed"))

@app.post("/api/fabric/query")
async def execute_query(body: Dict):
    """Execute a SQL query"""
    query = body.get("query", "")
    limit = body.get("limit", 100)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    result = fabric_service.execute_query(query, limit)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Query execution failed"))

@app.post("/api/fabric/sample")
async def get_sample_data(body: Dict):
    """Get sample data from a table"""
    table_name = body.get("table_name", "")
    limit = body.get("limit", 5)
    
    if not table_name:
        raise HTTPException(status_code=400, detail="Table name is required")
    
    return fabric_service.get_sample_data(table_name, limit)

# ==========================================
# POWER BI SEMANTIC MODEL ENDPOINTS
# ==========================================

@app.post("/api/powerbi/connect")
async def connect_to_powerbi(body: Dict):
    """Connect to Power BI dataset using XMLA endpoint"""
    xmla_endpoint = body.get("xmla_endpoint", "")
    dataset_name = body.get("dataset_name", "")
    workspace_name = body.get("workspace_name", "")
    
    if not xmla_endpoint or not dataset_name:
        raise HTTPException(
            status_code=400,
            detail="xmla_endpoint and dataset_name are required"
        )
    
    # Check if OAuth2 is configured
    if not auth_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="OAuth2 authentication not configured. Please configure authentication first."
        )
    
    # Configure semantic model service
    semantic_model_service.configure(
        xmla_endpoint=xmla_endpoint,
        dataset_name=dataset_name,
        workspace_name=workspace_name
    )
    
    # Test connection
    result = semantic_model_service.connect_to_powerbi()
    
    if result["success"]:
        # Set connection type for multi-agent
        enhanced_multi_agent_service.set_connection_type("semantic_model")
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.get("/api/powerbi/tables")
async def list_powerbi_tables():
    """list all available tables in the Power BI dataset"""
    result = semantic_model_service.list_tables()
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to list tables"))

@app.post("/api/powerbi/table-info")
async def get_powerbi_table_info(body: Dict):
    """Get detailed information about a specific table"""
    table_name = body.get("table_name", "")
    
    if not table_name:
        raise HTTPException(status_code=400, detail="table_name is required")
    
    result = semantic_model_service.get_table_info(table_name)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get table info"))

@app.get("/api/powerbi/suggest-questions")
async def suggest_powerbi_questions():
    """Get suggestions for interesting questions to ask about the data"""
    result = await semantic_model_service.suggest_questions()
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate suggestions"))

@app.post("/api/powerbi/clean-dax")
async def clean_dax_query_endpoint(body: Dict):
    """Test endpoint to clean DAX queries"""
    query = body.get("query", "")
    
    if not query:
        return {"error": "Query is required"}
    
    cleaned = semantic_model_service.clean_dax_query(query)
    
    return {
        "original": query,
        "cleaned": cleaned,
        "had_tags": "<oii>" in query or "</oii>" in query,
        "removed_characters": len(query) - len(cleaned)
    }

@app.get("/api/powerbi/test-simple")
async def test_simple_dax():
    """Test the simplest possible DAX query"""
    if not semantic_model_service.connected:
        return {"error": "Not connected to Power BI"}
    
    # Try the absolute simplest query
    test_queries = [
        {"name": "Empty evaluate", "query": "EVALUATE {}"},
        {"name": "Row function", "query": "EVALUATE ROW(\"Test\", 1)"},
    ]
    
    # Add table queries if we have tables
    if semantic_model_service.tables_cache:
        first_table = semantic_model_service.tables_cache[0]
        escaped = semantic_model_service._escape_table_name(first_table)
        test_queries.extend([
            {"name": f"Table {first_table} with quotes", "query": f"EVALUATE '{first_table}'"},
            {"name": f"Table {first_table} escaped", "query": f"EVALUATE {escaped}"},
            {"name": f"TOPN 1 row", "query": f"EVALUATE TOPN(1, {escaped})"},
        ])
    
    results = []
    for test in test_queries:
        try:
            result = semantic_model_service.execute_dax_query(test["query"])
            results.append({
                "test": test["name"],
                "query": test["query"],
                "success": result.get("success", False),
                "rows": result.get("row_count", 0) if result.get("success") else None,
                "error": result.get("error") if not result.get("success") else None
            })
        except Exception as e:
            results.append({
                "test": test["name"],
                "query": test["query"],
                "success": False,
                "error": str(e)
            })
    
    return {"tests": results}

@app.post("/api/powerbi/debug-query")
async def debug_powerbi_query(body: Dict):
    """Debug endpoint to test DAX query processing"""
    user_question = body.get("question", "")
    
    if not user_question:
        return {"error": "Question is required"}
    
    if not semantic_model_service.connected:
        return {"error": "Not connected to Power BI"}
    
    result = {
        "question": user_question,
        "tables": semantic_model_service.tables_cache[:10],
        "steps": []
    }
    
    try:
        # Step 1: Generate DAX
        result["steps"].append("Generating DAX query...")
        dax_query = semantic_model_service.generate_dax_query(user_question)
        result["generated_dax"] = dax_query
        result["steps"].append(f"Generated: {dax_query}")
        
        # Step 2: Clean DAX
        result["steps"].append("Cleaning DAX query...")
        cleaned = semantic_model_service.clean_dax_query(dax_query)
        result["cleaned_dax"] = cleaned
        result["steps"].append(f"Cleaned: {cleaned}")
        
        # Step 3: Execute
        result["steps"].append("Executing DAX query...")
        exec_result = semantic_model_service.execute_dax_query(cleaned)
        result["execution"] = exec_result
        
        if exec_result.get("success"):
            result["success"] = True
            result["steps"].append(f"Success! Rows: {exec_result.get('row_count')}")
        else:
            result["success"] = False
            result["steps"].append(f"Failed: {exec_result.get('error')}")
            
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["steps"].append(f"Exception: {str(e)}")
    
    return result

@app.post("/api/powerbi/test-dax")
async def test_powerbi_dax():
    """Test simple DAX query execution"""
    if not semantic_model_service.connected:
        return {
            "success": False,
            "error": "Not connected to Power BI"
        }
    
    # Try a simple query on the first available table
    if semantic_model_service.tables_cache:
        table_name = semantic_model_service.tables_cache[0]
        # Escape table name if needed
        if ' ' in table_name or '-' in table_name or table_name.startswith('_'):
            escaped_table = f"'{table_name}'"
        else:
            escaped_table = table_name
        test_query = f"EVALUATE TOPN(5, {escaped_table})"
        
        result = semantic_model_service.execute_dax_query(test_query)
        return {
            **result,
            "test_query": test_query,
            "table_used": table_name
        }
    else:
        return {
            "success": False,
            "error": "No tables available"
        }

@app.post("/api/powerbi/execute-dax")
async def execute_powerbi_dax(body: Dict):
    """Execute a custom DAX query on Power BI dataset"""
    dax_query = body.get("dax_query", "")
    
    if not dax_query:
        raise HTTPException(status_code=400, detail="dax_query is required")
    
    # Log the incoming query for debugging
    logger.info(f"Received DAX query: {dax_query}")
    
    result = semantic_model_service.execute_dax_query(dax_query)
    
    if result.get("success"):
        return result
    else:
        # Return error with details for debugging
        logger.error(f"DAX execution failed: {result}")
        raise HTTPException(
            status_code=400, 
            detail=result.get("error", "DAX execution failed"),
            headers={"X-DAX-Query": dax_query[:100]}  # Include part of query in header for debugging
        )

@app.post("/api/powerbi/query-natural")
async def query_powerbi_natural(body: Dict):
    """Ask a question about Power BI data in natural language"""
    question = body.get("question", "")
    
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    
    result = semantic_model_service.query_data_natural_language(question)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Query failed"))

@app.get("/api/powerbi/status")
async def get_powerbi_status():
    """Get Power BI connection status"""
    return {
        "connected": semantic_model_service.connected,
        "xmla_endpoint": semantic_model_service.xmla_endpoint,
        "dataset_name": semantic_model_service.dataset_name,
        "workspace_name": semantic_model_service.workspace_name,
        "tables_count": len(semantic_model_service.tables_cache),
        "has_model_info": semantic_model_service.model_info is not None
    }

# ==========================================
# SEMANTIC MODEL SCHEMA ENDPOINTS
# ==========================================

@app.get("/api/semantic-model/schema")
async def get_semantic_model_schema():
    """Get Power BI semantic model schema"""
    result = semantic_model_service.discover_model()
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Schema discovery failed"))

# ==========================================
# DATA ANALYSIS ENDPOINTS
# ==========================================

@app.post("/api/analyze/visualize")
async def create_visualization(body: Dict):
    """Create a visualization"""
    data = body.get("data", [])
    chart_type = body.get("chart_type", "bar")
    x_column = body.get("x_column", "")
    y_column = body.get("y_column", None)
    
    if not data or not x_column:
        raise HTTPException(status_code=400, detail="Data and x_column are required")
    
    result = data_analysis_service.create_visualization(data, chart_type, x_column, y_column)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/api/analyze/statistics")
async def analyze_data(body: Dict):
    """Analyze data statistics"""
    data = body.get("data", [])
    
    if not data:
        raise HTTPException(status_code=400, detail="Data is required")
    
    return data_analysis_service.analyze_data(data)

# ==========================================
# ENHANCED CHAT ENDPOINTS
# ==========================================

@app.post("/api/chat/with-data")
async def chat_with_data(body: Dict):
    """Chat with data context (Fabric SQL)"""
    message = body.get("message", "")
    include_schema = body.get("include_schema", False)
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    context = ""
    
    # Add schema context if requested
    if include_schema:
        schema_result = fabric_service.discover_schema()
        if schema_result.get("success"):
            tables = schema_result.get("tables", {})
            context = "Available tables and columns:\n"
            for table_name, table_info in tables.items():
                columns = [col["name"] for col in table_info["columns"]]
                context += f"\n{table_name}: {', '.join(columns)}"
    
    # Get response from Claude with context
    if claude_available and claude_service:
        response = await claude_service.get_response(message, context)
        
        # Check if Claude suggests a query
        if "SELECT" in response.upper():
            # Extract SQL query (simple extraction)
            lines = response.split('\n')
            sql_query = None
            for line in lines:
                if "SELECT" in line.upper():
                    sql_query = line.strip()
                    break
            
            if sql_query:
                # Try to execute the query
                query_result = fabric_service.execute_query(sql_query)
                if query_result.get("success"):
                    return {
                        "response": response,
                        "query": sql_query,
                        "query_result": query_result,
                        "status": "success"
                    }
        
        return {
            "response": response,
            "status": "success"
        }
    else:
        return {
            "response": "Claude is not available",
            "status": "error"
        }

@app.post("/api/chat/data-query")
async def chat_with_data_query(body: Dict):
    """Chat endpoint that automatically queries your data"""
    question = body.get("message", "")
    response_type = body.get("response_type", "text")
    
    if not question:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Use enhanced multi-agent system
    result = await enhanced_multi_agent_service.answer_with_options(question, response_type)
    
    return {
        "response": result.get("answer", ""),
        "sql_query": result.get("query"),
        "data": result.get("data", [])[:10],  # Return first 10 rows
        "total_rows": result.get("row_count", 0),
        "success": result.get("success", False),
        "visualization": result.get("visualization")
    }

@app.post("/api/chat/powerbi")
async def chat_with_powerbi(body: Dict):
    """Chat endpoint specifically for Power BI semantic models"""
    message = body.get("message", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Check if Power BI is connected
    if not semantic_model_service.connected:
        return {
            "response": "Please connect to Power BI first using the XMLA endpoint and dataset name.",
            "success": False
        }
    
    # Use the semantic model service for natural language queries
    result = semantic_model_service.query_data_natural_language(message)
    
    return {
        "response": result.get("answer", "Query completed"),
        "dax_query": result.get("dax_query"),
        "data": result.get("data", [])[:10],  # First 10 rows
        "total_rows": result.get("row_count", 0),
        "success": result.get("success", False)
    }

# ==========================================
# CONNECTION STATUS ENDPOINTS
# ==========================================

@app.get("/api/connection/status")
async def get_connection_status():
    """Get current connection status"""
    sql_connected = bool(fabric_service.server and fabric_service.database)
    semantic_model_connected = bool(
        hasattr(semantic_model_service, 'connected') and semantic_model_service.connected
    )
    
    return {
        "sql_connected": sql_connected,
        "semantic_model_connected": semantic_model_connected,
        "sql_details": {
            "server": fabric_service.server,
            "database": fabric_service.database
        } if sql_connected else None,
        "semantic_model_details": {
            "endpoint": getattr(semantic_model_service, 'xmla_endpoint', None),
            "dataset_name": getattr(semantic_model_service, 'dataset_name', None)
        } if semantic_model_connected else None
    }

@app.get("/api/schema/refresh")
async def refresh_schema():
    """Refresh the schema cache"""
    result = await enhanced_multi_agent_service.refresh_metadata()
    return result

# ==========================================
# KNOWLEDGE BASE ENDPOINTS
# ==========================================

@app.post("/api/knowledge/init")
async def initialize_knowledge_base():
    """Initialize knowledge base table"""
    result = knowledge_base_service.initialize_knowledge_base()
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.get("/api/knowledge/search")
async def search_knowledge(query: str, category: Optional[str] = None):
    """Search knowledge base"""
    results = knowledge_base_service.search_knowledge(query, category)
    return {"success": True, "results": results}

@app.get("/api/knowledge/all")
async def get_all_knowledge(category: Optional[str] = None):
    """Get all knowledge entries"""
    results = knowledge_base_service.get_all_knowledge(category)
    return {"success": True, "results": results, "count": len(results)}

# ==========================================
# STARTUP EVENT
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Chat with Data API starting up...")
    logger.info(f"Claude available: {claude_available}")
    logger.info(f"Multi-agent available: {multi_agent_available}")
    logger.info("API ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Chat with Data API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ==========================================
# PHASE 1: UNIFIED CHAT ENDPOINT
# ==========================================

@app.post("/api/chat/unified")
async def unified_chat(body: Dict):
    """
    Phase 1: Unified endpoint that handles the complete AI workflow in the backend.
    Replaces the complex frontend multi-step process with a single API call.
    """
    question = body.get("question", "")
    connection_type = body.get("connection_type")  # 'sql' or 'semantic_model'
    context_history = body.get("context_history", [])
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    if not connection_type:
        raise HTTPException(status_code=400, detail="Connection type is required ('sql' or 'semantic_model')")
    
    # Validate connection exists
    if connection_type == "sql":
        if not fabric_service.server or not fabric_service.database:
            raise HTTPException(status_code=400, detail="SQL connection not configured. Please connect to Microsoft Fabric first.")
    elif connection_type == "semantic_model":
        if not hasattr(semantic_model_service, 'connected') or not semantic_model_service.connected:
            raise HTTPException(status_code=400, detail="Semantic model connection not configured. Please connect to Power BI first.")
    else:
        raise HTTPException(status_code=400, detail="Invalid connection type. Must be 'sql' or 'semantic_model'")
    
    try:
        # Set the connection type for the enhanced service
        enhanced_multi_agent_service.set_connection_type(connection_type)
        
        # The enhanced service handles the entire AI workflow internally
        result = await enhanced_multi_agent_service.answer_with_self_correction(
            question=question,
            context_history=context_history
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Unified chat endpoint error: {str(e)}")
        return {
            "success": False,
            "answer": "An internal error occurred while processing your question.",
            "thinking": [f"💥 Critical Error: {str(e)}"],
            "query_attempts": [],
            "error_details": str(e)
        }

# ==========================================
# PHASE 2: MONITORING & ANALYTICS ENDPOINTS
# ==========================================

@app.get("/api/analytics/cache-performance")
async def get_cache_performance():
    """Get cache performance statistics"""
    try:
        cache_stats = enhanced_multi_agent_service.get_cache_stats()
        return {
            "success": True,
            "cache_performance": cache_stats,
            "recommendations": _generate_cache_recommendations(cache_stats)
        }
    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/analytics/knowledge-base")
async def get_knowledge_base_analytics():
    """Get knowledge base performance and insights"""
    try:
        analytics = knowledge_base_service.get_knowledge_analytics()
        return {
            "success": True,
            "knowledge_analytics": analytics,
            "insights": _generate_knowledge_insights(analytics)
        }
    except Exception as e:
        logger.error(f"Failed to get knowledge base analytics: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/analytics/query-patterns")
async def get_query_patterns():
    """Analyze query patterns and success rates"""
    try:
        # Get recent successful queries
        successful_queries = knowledge_base_service.get_popular_queries(limit=50)
        
        # Analyze patterns
        patterns = _analyze_query_patterns(successful_queries)
        
        return {
            "success": True,
            "query_patterns": patterns,
            "recommendations": _generate_query_recommendations(patterns)
        }
    except Exception as e:
        logger.error(f"Failed to analyze query patterns: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/analytics/system-health")
async def get_system_health():
    """Get overall system health and performance metrics"""
    try:
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "claude": {
                    "available": claude_available,
                    "status": "healthy" if claude_available else "unavailable"
                },
                "fabric": {
                    "connected": bool(fabric_service.server and fabric_service.database),
                    "server": fabric_service.server,
                    "database": fabric_service.database
                },
                "semantic_model": {
                    "connected": hasattr(semantic_model_service, 'connected') and semantic_model_service.connected,
                    "endpoint": getattr(semantic_model_service, 'xmla_endpoint', None)
                },
                "knowledge_base": {
                    "available": True,  # Assume available if we reach this point
                    "entries": len(knowledge_base_service.get_all_knowledge())
                }
            },
            "cache": enhanced_multi_agent_service.get_cache_stats(),
            "performance": _get_performance_metrics()
        }
        
        # Calculate overall health score
        health_score = _calculate_health_score(health_data)
        health_data["overall_health"] = health_score
        
        return {
            "success": True,
            "health": health_data
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/analytics/optimize-cache")
async def optimize_cache():
    """Trigger cache optimization and cleanup"""
    try:
        # Clear expired cache entries
        await enhanced_multi_agent_service._cleanup_expired_cache()
        
        # Get updated stats
        stats = enhanced_multi_agent_service.get_cache_stats()
        
        return {
            "success": True,
            "message": "Cache optimized successfully",
            "cache_stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to optimize cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/analytics/usage-trends")
async def get_usage_trends():
    """Get usage trends and insights"""
    try:
        # Get knowledge base entries from last 30 days
        recent_entries = knowledge_base_service.get_all_knowledge()
        
        # Analyze trends
        trends = _analyze_usage_trends(recent_entries)
        
        return {
            "success": True,
            "trends": trends,
            "insights": _generate_usage_insights(trends)
        }
    except Exception as e:
        logger.error(f"Failed to get usage trends: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ==========================================
# HELPER FUNCTIONS FOR ANALYTICS
# ==========================================

def _generate_cache_recommendations(cache_stats: Dict) -> list[str]:
    """Generate recommendations based on cache performance"""
    recommendations = []
    
    hit_rate = cache_stats.get("hit_rate_percentage", 0)
    
    if hit_rate < 60:
        recommendations.append("🔄 Low cache hit rate. Consider increasing cache TTL for stable schemas.")
    elif hit_rate > 90:
        recommendations.append("✅ Excellent cache performance! Schema caching is working optimally.")
    
    cached_schemas = cache_stats.get("cached_schemas", 0)
    cache_limit = cache_stats.get("cache_size_limit", 50)
    
    if cached_schemas >= cache_limit * 0.9:
        recommendations.append("📦 Cache nearly full. Consider increasing cache size limit or cleanup frequency.")
    
    if cache_stats.get("total_refreshes", 0) > cache_stats.get("total_misses", 0) * 2:
        recommendations.append("⚡ High refresh rate. Schema might be changing frequently.")
    
    return recommendations

def _generate_knowledge_insights(analytics: Dict) -> list[str]:
    """Generate insights from knowledge base analytics"""
    insights = []
    
    total_entries = analytics.get("total_entries", 0)
    avg_success = analytics.get("average_success_rate", 0)
    
    if total_entries < 10:
        insights.append("📚 Knowledge base is still learning. More queries will improve AI accuracy.")
    elif total_entries > 100:
        insights.append("🎓 Well-established knowledge base with extensive query history.")
    
    if avg_success > 3:
        insights.append("🎯 High-quality knowledge base with frequently reused successful queries.")
    elif avg_success < 1.5:
        insights.append("🔧 Knowledge base contains many experimental queries. Consider cleanup.")
    
    # Category insights
    categories = analytics.get("categories", [])
    if categories:
        most_used = max(categories, key=lambda x: x["count"])
        insights.append(f"📊 Most active category: {most_used['name']} with {most_used['count']} queries.")
    
    return insights

def _analyze_query_patterns(queries: list[Dict]) -> Dict:
    """Analyze patterns in successful queries"""
    if not queries:
        return {"error": "No queries to analyze"}
    
    patterns = {
        "total_queries": len(queries),
        "query_types": {},
        "common_entities": {},
        "success_distribution": {},
        "complexity_analysis": {
            "simple": 0,
            "moderate": 0,
            "complex": 0
        }
    }
    
    for query in queries:
        question = query.get("question", "").lower()
        success_count = query.get("success_count", 1)
        
        # Classify query type
        if any(word in question for word in ["show", "list", "display"]):
            query_type = "retrieval"
        elif any(word in question for word in ["count", "how many"]):
            query_type = "count"
        elif any(word in question for word in ["total", "sum"]):
            query_type = "aggregation"
        elif any(word in question for word in ["top", "best", "highest"]):
            query_type = "ranking"
        else:
            query_type = "other"
        
        patterns["query_types"][query_type] = patterns["query_types"].get(query_type, 0) + 1
        
        # Extract entities
        entities = ["sales", "customer", "product", "order", "revenue"]
        for entity in entities:
            if entity in question:
                patterns["common_entities"][entity] = patterns["common_entities"].get(entity, 0) + 1
        
        # Success distribution
        success_range = "high" if success_count > 5 else "medium" if success_count > 2 else "low"
        patterns["success_distribution"][success_range] = patterns["success_distribution"].get(success_range, 0) + 1
        
        # Complexity analysis (simple heuristic)
        word_count = len(question.split())
        if word_count > 15:
            patterns["complexity_analysis"]["complex"] += 1
        elif word_count > 8:
            patterns["complexity_analysis"]["moderate"] += 1
        else:
            patterns["complexity_analysis"]["simple"] += 1
    
    return patterns

def _generate_query_recommendations(patterns: Dict) -> list[str]:
    """Generate recommendations based on query patterns"""
    recommendations = []
    
    if patterns.get("error"):
        return ["📊 Not enough query data for recommendations."]
    
    # Query type recommendations
    query_types = patterns.get("query_types", {})
    most_common_type = max(query_types, key=query_types.get) if query_types else None
    
    if most_common_type == "retrieval":
        recommendations.append("🔍 Users frequently ask for data retrieval. Consider pre-built dashboard views.")
    elif most_common_type == "aggregation":
        recommendations.append("📈 Many aggregation queries. Consider adding calculated measures to your model.")
    
    # Entity recommendations
    entities = patterns.get("common_entities", {})
    if entities:
        top_entity = max(entities, key=entities.get)
        recommendations.append(f"🎯 '{top_entity}' is the most queried entity. Ensure this data is well-structured and accessible.")
    
    # Complexity recommendations
    complexity = patterns.get("complexity_analysis", {})
    if complexity.get("complex", 0) > complexity.get("simple", 0):
        recommendations.append("🧠 Users ask complex questions. AI is handling advanced queries well.")
    else:
        recommendations.append("✨ Mostly simple queries. System is accessible to all user levels.")
    
    return recommendations

def _get_performance_metrics() -> Dict:
    """Get basic performance metrics"""
    import psutil
    import time
    
    return {
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "memory_usage_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": time.time() - psutil.boot_time(),
        "python_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }

def _calculate_health_score(health_data: Dict) -> Dict:
    """Calculate overall system health score"""
    score = 100
    issues = []
    
    services = health_data.get("services", {})
    
    # Check service availability
    if not services.get("claude", {}).get("available"):
        score -= 30
        issues.append("Claude AI service unavailable")
    
    if not services.get("fabric", {}).get("connected") and not services.get("semantic_model", {}).get("connected"):
        score -= 40
        issues.append("No data connection established")
    
    # Check cache performance
    cache = health_data.get("cache", {})
    hit_rate = cache.get("hit_rate_percentage", 0)
    if hit_rate < 50:
        score -= 10
        issues.append("Low cache hit rate")
    
    # Check performance
    performance = health_data.get("performance", {})
    if performance.get("cpu_usage_percent", 0) > 80:
        score -= 10
        issues.append("High CPU usage")
    
    if performance.get("memory_usage_percent", 0) > 85:
        score -= 10
        issues.append("High memory usage")
    
    # Determine status
    if score >= 90:
        status = "excellent"
    elif score >= 75:
        status = "good"
    elif score >= 60:
        status = "fair"
    else:
        status = "poor"
    
    return {
        "score": max(score, 0),
        "status": status,
        "issues": issues
    }

def _analyze_usage_trends(entries: list[Dict]) -> Dict:
    """Analyze usage trends from knowledge base entries"""
    from collections import defaultdict
    from datetime import datetime, timedelta
    
    if not entries:
        return {"error": "No usage data available"}
    
    # Group by date
    daily_usage = defaultdict(int)
    category_trends = defaultdict(int)
    success_trends = defaultdict(list)
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    for entry in entries:
        created_at = entry.get("created_at")
        if created_at:
            try:
                entry_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if entry_date >= thirty_days_ago:
                    date_key = entry_date.strftime("%Y-%m-%d")
                    daily_usage[date_key] += 1
                    
                    category = entry.get("category", "unknown")
                    category_trends[category] += 1
                    
                    success_count = entry.get("success_count", 1)
                    success_trends[date_key].append(success_count)
            except:
                continue
    
    # Calculate average success rates by day
    daily_success_rates = {}
    for date, successes in success_trends.items():
        daily_success_rates[date] = sum(successes) / len(successes) if successes else 0
    
    return {
        "daily_usage": dict(daily_usage),
        "category_distribution": dict(category_trends),
        "daily_success_rates": daily_success_rates,
        "total_days_with_activity": len(daily_usage),
        "average_daily_queries": sum(daily_usage.values()) / len(daily_usage) if daily_usage else 0
    }

def _generate_usage_insights(trends: Dict) -> list[str]:
    """Generate insights from usage trends"""
    insights = []
    
    if trends.get("error"):
        return ["📊 Not enough usage data for insights."]
    
    avg_daily = trends.get("average_daily_queries", 0)
    if avg_daily > 10:
        insights.append("🚀 High system usage! Users are actively engaging with the AI.")
    elif avg_daily > 3:
        insights.append("📈 Moderate system usage with steady adoption.")
    else:
        insights.append("🌱 Growing system usage. Consider user training or promotion.")
    
    # Category insights
    categories = trends.get("category_distribution", {})
    if categories:
        most_used_category = max(categories, key=categories.get)
        insights.append(f"🎯 Most active connection type: {most_used_category}")
    
    # Success rate insights
    success_rates = trends.get("daily_success_rates", {})
    if success_rates:
        avg_success = sum(success_rates.values()) / len(success_rates)
        if avg_success > 3:
            insights.append("✅ Users are getting consistent value - high query reuse rate.")
        else:
            insights.append("🔄 Users are exploring diverse questions - good learning pattern.")
    
    return insights