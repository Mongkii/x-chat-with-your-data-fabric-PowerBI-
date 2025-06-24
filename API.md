# 🔌 API Documentation

Complete API reference for the Chat with Data application backend.

## 📋 Overview

The Chat with Data API is built with FastAPI and provides endpoints for:
- Natural language data querying
- Database and semantic model connections
- Authentication management
- Schema exploration
- Health monitoring

**Base URL**: `http://localhost:8000`

## 🔐 Authentication

All data-related endpoints require Azure AD OAuth2 authentication. Configure authentication first before using data endpoints.

### Authentication Headers
```http
Authorization: Bearer {azure_access_token}
Content-Type: application/json
```

## 🗣️ Chat Endpoints

### POST `/api/chat/unified`

**Main endpoint for natural language queries with AI-powered self-correction.**

#### Request Body
```json
{
  "question": "string",                    // Required: Natural language question
  "connection_type": "sql|semantic_model", // Required: Data source type
  "context_history": ["string"]           // Optional: Previous conversation context
}
```

#### Response
```json
{
  "success": true,
  "answer": "string",              // Human-readable answer
  "query": "string",               // Generated SQL/DAX query
  "data": [{}],                    // Query results (array of objects)
  "thinking": ["string"],          // AI thinking process steps
  "query_attempts": [              // All query attempts made
    {
      "query": "string",
      "success": boolean,
      "error": "string"
    }
  ],
  "execution_time": 1.23,          // Query execution time in seconds
  "query_language": "T-SQL|DAX",   // Query language used
  "total_rows": 150,               // Total number of rows returned
  "row_count": 100                 // Displayed row count (limited)
}
```

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/chat/unified" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me the top 10 customers by revenue",
    "connection_type": "sql",
    "context_history": []
  }'
```

#### Example Response
```json
{
  "success": true,
  "answer": "Here are the top 10 customers by total revenue. The leading customer is Acme Corp with $2.3M in revenue, followed by Global Industries with $1.8M.",
  "query": "SELECT TOP 10 c.CustomerName, SUM(o.TotalAmount) as TotalRevenue FROM Customers c JOIN Orders o ON c.CustomerID = o.CustomerID GROUP BY c.CustomerName ORDER BY TotalRevenue DESC",
  "data": [
    {"CustomerName": "Acme Corp", "TotalRevenue": 2300000},
    {"CustomerName": "Global Industries", "TotalRevenue": 1800000}
  ],
  "thinking": [
    "🤔 Understanding your question about top customers by revenue",
    "✅ Using cached T-SQL schema",
    "💡 Generating initial T-SQL query with customer and order joins",
    "⚡ Executing T-SQL query (Attempt 1/3)",
    "✅ Query successful! Found 10 rows",
    "📝 Generating human-readable answer",
    "✨ Analysis complete!"
  ],
  "query_attempts": [
    {
      "query": "SELECT TOP 10 c.CustomerName, SUM(o.TotalAmount) as TotalRevenue FROM Customers c JOIN Orders o ON c.CustomerID = o.CustomerID GROUP BY c.CustomerName ORDER BY TotalRevenue DESC",
      "success": true,
      "error": null
    }
  ],
  "execution_time": 0.847,
  "query_language": "T-SQL",
  "total_rows": 10,
  "row_count": 10
}
```

### POST `/api/chat/data-query`

**Legacy endpoint for simple data queries without self-correction.**

#### Request Body
```json
{
  "message": "string",                    // Required: Natural language question
  "response_type": "text|visualization"   // Optional: Response format (default: "text")
}
```

#### Response
```json
{
  "response": "string",        // AI-generated response
  "sql_query": "string",       // Generated SQL query
  "data": [{}],                // Query results (first 10 rows)
  "total_rows": 150,           // Total number of rows
  "success": boolean,          // Execution success status
  "visualization": {}          // Visualization config (if requested)
}
```

## 🔌 Connection Management

### GET `/api/connection/status`

**Check the status of all data source connections.**

#### Response
```json
{
  "sql_connected": boolean,             // Microsoft Fabric connection status
  "semantic_model_connected": boolean,  // Power BI connection status
  "auth_configured": boolean,           // OAuth2 configuration status
  "fabric_info": {                      // Fabric connection details (if connected)
    "server": "string",
    "database": "string",
    "connected_at": "2024-01-15T10:30:00Z"
  },
  "powerbi_info": {                     // Power BI connection details (if connected)
    "xmla_endpoint": "string",
    "dataset_name": "string",
    "connected_at": "2024-01-15T10:30:00Z"
  }
}
```

## 🗄️ Microsoft Fabric Endpoints

### POST `/api/fabric/connect`

**Connect to Microsoft Fabric database using SQL endpoint.**

#### Request Body
```json
{
  "server": "string",     // Required: Fabric SQL endpoint server
  "database": "string"    // Required: Database name
}
```

#### Response
```json
{
  "success": boolean,
  "message": "string",
  "server": "string",
  "database": "string",
  "connected_at": "2024-01-15T10:30:00Z"
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/fabric/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "server": "your-workspace.datawarehouse.fabric.microsoft.com",
    "database": "your-database"
  }'
```

### GET `/api/fabric/schema`

**Discover and retrieve the database schema.**

#### Response
```json
{
  "success": boolean,
  "tables": {
    "TableName": {
      "columns": [
        {
          "name": "string",
          "type": "string",
          "nullable": boolean,
          "is_primary_key": boolean,
          "is_foreign_key": boolean
        }
      ],
      "row_count": 1000,
      "relationships": [
        {
          "foreign_table": "string",
          "foreign_column": "string",
          "relationship_type": "one_to_many|many_to_one"
        }
      ]
    }
  },
  "total_tables": 15,
  "cached_at": "2024-01-15T10:30:00Z"
}
```

### POST `/api/fabric/query`

**Execute a custom SQL query against the Fabric database.**

#### Request Body
```json
{
  "query": "string",    // Required: T-SQL query to execute
  "limit": 100          // Optional: Row limit (default: 100, max: 1000)
}
```

#### Response
```json
{
  "success": boolean,
  "data": [{}],                    // Query results
  "columns": ["string"],           // Column names
  "row_count": 150,                // Number of rows returned
  "execution_time": 1.23,          // Execution time in seconds
  "query": "string",               // Original query
  "message": "string"              // Success/error message
}
```

### POST `/api/fabric/sample`

**Get sample data from a specific table.**

#### Request Body
```json
{
  "table_name": "string",   // Required: Table name
  "limit": 5                // Optional: Number of rows (default: 5)
}
```

#### Response
```json
{
  "success": boolean,
  "table_name": "string",
  "data": [{}],
  "columns": ["string"],
  "row_count": 5,
  "total_table_rows": 10000
}
```

## 📊 Power BI Semantic Model Endpoints

### POST `/api/powerbi/connect`

**Connect to Power BI semantic model using XMLA endpoint.**

#### Request Body
```json
{
  "xmla_endpoint": "string",     // Required: Power BI XMLA endpoint
  "dataset_name": "string",      // Required: Dataset/semantic model name
  "workspace_name": "string"     // Optional: Workspace name for display
}
```

#### Response
```json
{
  "success": boolean,
  "message": "string",
  "xmla_endpoint": "string",
  "dataset_name": "string",
  "workspace_name": "string",
  "connected_at": "2024-01-15T10:30:00Z",
  "model_info": {
    "tables_count": 10,
    "measures_count": 25,
    "calculated_columns_count": 15
  }
}
```

### GET `/api/powerbi/status`

**Check Power BI connection status and model information.**

#### Response
```json
{
  "connected": boolean,
  "xmla_endpoint": "string",
  "dataset_name": "string",
  "model_info": {
    "tables": [
      {
        "name": "string",
        "columns": ["string"],
        "measures": ["string"]
      }
    ],
    "relationships": [
      {
        "from_table": "string",
        "from_column": "string",
        "to_table": "string",
        "to_column": "string",
        "cardinality": "one_to_many|many_to_one|one_to_one"
      }
    ]
  }
}
```

### POST `/api/powerbi/query`

**Execute a DAX query against the semantic model.**

#### Request Body
```json
{
  "dax_query": "string",    // Required: DAX query to execute
  "limit": 100              // Optional: Row limit
}
```

#### Response
```json
{
  "success": boolean,
  "data": [{}],
  "columns": ["string"],
  "row_count": 150,
  "execution_time": 1.23,
  "query": "string",
  "message": "string"
}
```

### GET `/api/powerbi/suggest-questions`

**Get AI-suggested questions based on the semantic model structure.**

#### Response
```json
{
  "questions": [
    {
      "question": "string",
      "category": "string",
      "complexity": "simple|moderate|complex",
      "estimated_result_type": "table|scalar|visualization"
    }
  ],
  "total_suggestions": 12
}
```

## 🔐 Authentication Endpoints

### POST `/api/auth/configure`

**Configure OAuth2 authentication settings.**

#### Request Body
```json
{
  "tenant_id": "string",      // Required: Azure AD tenant ID
  "client_id": "string",      // Required: Application client ID
  "client_secret": "string"   // Required: Application client secret
}
```

#### Response
```json
{
  "success": boolean,
  "message": "string",
  "configured_at": "2024-01-15T10:30:00Z"
}
```

### GET `/api/auth/status`

**Check authentication configuration status.**

#### Response
```json
{
  "configured": boolean,
  "tenant_id": "string",      // Masked for security
  "client_id": "string",      // Masked for security
  "has_valid_token": boolean,
  "token_expires_at": "2024-01-15T11:30:00Z"
}
```

### POST `/api/auth/test-token`

**Test the current authentication token.**

#### Response
```json
{
  "valid": boolean,
  "expires_at": "2024-01-15T11:30:00Z",
  "scopes": ["string"],
  "user_info": {
    "name": "string",
    "email": "string",
    "tenant": "string"
  }
}
```

## 📊 Analytics and Monitoring

### GET `/api/analytics/usage`

**Get usage analytics and statistics.**

#### Query Parameters
- `days`: Number of days to include (default: 7, max: 30)
- `include_details`: Include detailed breakdowns (default: false)

#### Response
```json
{
  "period": {
    "start_date": "2024-01-08T00:00:00Z",
    "end_date": "2024-01-15T00:00:00Z",
    "days": 7
  },
  "metrics": {
    "total_queries": 150,
    "successful_queries": 142,
    "failed_queries": 8,
    "success_rate": 0.947,
    "avg_execution_time": 1.23,
    "total_data_rows_returned": 15420
  },
  "query_types": {
    "sql": 89,
    "dax": 61
  },
  "top_question_categories": [
    {"category": "Revenue Analysis", "count": 45},
    {"category": "Customer Analysis", "count": 32}
  ]
}
```

### GET `/api/analytics/performance`

**Get performance metrics and optimization insights.**

#### Response
```json
{
  "cache_performance": {
    "schema_cache_hit_rate": 0.85,
    "query_cache_hit_rate": 0.23,
    "avg_cache_response_time": 0.05
  },
  "query_performance": {
    "avg_sql_execution_time": 1.45,
    "avg_dax_execution_time": 2.12,
    "slowest_queries": [
      {
        "query": "string",
        "execution_time": 5.67,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "ai_performance": {
    "avg_generation_time": 2.34,
    "self_correction_rate": 0.15,
    "avg_attempts_per_query": 1.2
  }
}
```

## 🏥 Health and Status

### GET `/health`

**Application health check endpoint.**

#### Response
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "claude_available": boolean,
    "database_connections": {
      "fabric": boolean,
      "powerbi": boolean
    },
    "auth_service": boolean,
    "cache_service": boolean
  },
  "performance": {
    "response_time_ms": 123,
    "memory_usage_mb": 256,
    "cpu_usage_percent": 15
  }
}
```

### GET `/api/system/info`

**Get system information and configuration.**

#### Response
```json
{
  "application": {
    "name": "Chat with Data API",
    "version": "1.0.0",
    "environment": "development|production",
    "started_at": "2024-01-15T09:00:00Z"
  },
  "ai_services": {
    "claude_model": "claude-3-sonnet-20240229",
    "claude_available": boolean,
    "max_tokens": 4096
  },
  "database_support": {
    "fabric": boolean,
    "powerbi": boolean,
    "max_query_timeout": 30,
    "max_result_rows": 1000
  },
  "features": {
    "self_correction": boolean,
    "conversation_context": boolean,
    "auto_visualization": boolean,
    "caching": boolean
  }
}
```

## ❌ Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "string",           // Error description
  "error_code": "INVALID_INPUT|MISSING_PARAMETER",
  "field": "string"             // Field that caused the error (if applicable)
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required",
  "error_code": "AUTH_REQUIRED"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "string"        // For debugging purposes
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable",
  "error_code": "SERVICE_UNAVAILABLE",
  "retry_after": 60             // Seconds to wait before retrying
}
```

## 📝 Rate Limits

- **General API calls**: 100 requests per minute per IP
- **AI-powered endpoints**: 20 requests per minute per user
- **Authentication endpoints**: 10 requests per minute per IP
- **Health checks**: No rate limit

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642248000
```

## 🔍 Request/Response Examples

### Complete Chat Session Example

**1. Configure Authentication**
```bash
curl -X POST "http://localhost:8000/api/auth/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'
```

**2. Connect to Data Source**
```bash
curl -X POST "http://localhost:8000/api/fabric/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "server": "your-workspace.datawarehouse.fabric.microsoft.com",
    "database": "your-database"
  }'
```

**3. Ask a Question**
```bash
curl -X POST "http://localhost:8000/api/chat/unified" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are my top selling products this month?",
    "connection_type": "sql"
  }'
```

**4. Follow-up Question**
```bash
curl -X POST "http://localhost:8000/api/chat/unified" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me the same data for last month",
    "connection_type": "sql",
    "context_history": [
      "Q: What are my top selling products this month?\nT-SQL: SELECT TOP 10 ProductName, SUM(Quantity) as TotalSold FROM Sales WHERE MONTH(SaleDate) = MONTH(GETDATE()) GROUP BY ProductName ORDER BY TotalSold DESC"
    ]
  }'
```

---

## 📚 Additional Resources

- **OpenAPI/Swagger UI**: Available at `http://localhost:8000/docs`
- **ReDoc Documentation**: Available at `http://localhost:8000/redoc`
- **Health Dashboard**: Available at `http://localhost:8000/health`

For more detailed examples and integration guides, see the main README.md file.
