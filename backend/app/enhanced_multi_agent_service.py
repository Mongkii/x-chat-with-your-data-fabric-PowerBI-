import logging
import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
import asyncio
from difflib import SequenceMatcher

from app.claude_service import claude_service
from app.fabric_service import fabric_service
from app.semantic_model_service import semantic_model_service
from app.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)

class EnhancedMultiAgentService:
    def __init__(self):
        self.sql_schema_cache = None
        self.model_info_cache = None
        self.connection_type = None  # 'sql' or 'semantic_model'
        
        # Phase 2: Advanced caching system
        self.schema_cache = {}
        self.schema_metadata = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "refreshes": 0,
            "last_cleanup": time.time()
        }
        
        # Cache configuration
        self.cache_config = {
            "default_ttl": 3600,  # 1 hour
            "max_cache_size": 50,  # Max cached schemas
            "cleanup_interval": 1800,  # 30 minutes
            "performance_boost_ttl": 7200,  # 2 hours for frequently used schemas
        }
        
        # Query similarity cache
        self.query_similarity_cache = {}
        self.entity_extraction_cache = {}

        # Phase 2: Advanced prompt templates with context awareness
        self.advanced_prompt_templates = {
            "sql_generation": {
                "base": """You are a Microsoft Fabric T-SQL expert with deep understanding of business data patterns.

CRITICAL REQUIREMENTS:
1. Use ONLY Microsoft Fabric T-SQL syntax
2. ALWAYS include TOP N (e.g., TOP 100) to limit results - this is mandatory for performance
3. Use [square brackets] for table/column names with spaces or special characters
4. NO CREATE, DROP, DELETE, INSERT, UPDATE statements unless explicitly requested
5. Handle NULL values with ISNULL() or COALESCE() where appropriate
6. Use proper JOINs based on table relationships and business logic
7. For calculations, use CAST() or CONVERT() for proper data types
8. Always specify table aliases for better readability and performance

SCHEMA CONTEXT:
{schema_context}

{similar_queries_context}

{conversation_context}

BUSINESS CONTEXT:
{business_context}

QUESTION: {question}

Based on the schema and context above, generate a single, optimized T-SQL query that:
- Directly answers the business question
- Uses appropriate table relationships
- Includes proper error handling for edge cases
- Follows T-SQL best practices

Generate ONLY the T-SQL query (no explanations, no markdown):""",

                "with_relationships": """You are a Microsoft Fabric T-SQL expert who understands data relationships and business logic.

TABLE RELATIONSHIPS DETECTED:
{relationship_hints}

SCHEMA WITH RELATIONSHIP CONTEXT:
{schema_context}

{similar_queries_context}

QUESTION: {question}

Generate a T-SQL query that leverages the table relationships above. Consider:
- Which tables need to be joined based on the question
- What keys/IDs should be used for joins
- Whether to use INNER, LEFT, or RIGHT joins based on business logic
- How to handle potential NULL values in relationships

Generate ONLY the T-SQL query:""",

                "aggregation_focused": """You are a T-SQL expert specializing in business aggregations and analytics.

AGGREGATION CONTEXT:
- Question type: {aggregation_type}
- Time dimension: {time_dimension}
- Grouping requirements: {grouping_requirements}

SCHEMA:
{schema_context}

{similar_queries_context}

QUESTION: {question}

Generate a T-SQL query optimized for aggregation that:
- Uses appropriate GROUP BY clauses
- Includes proper aggregation functions (SUM, COUNT, AVG, etc.)
- Handles time-based grouping correctly
- Includes ORDER BY for meaningful result ordering
- Uses TOP N to limit results appropriately

Generate ONLY the T-SQL query:"""
            },

            "dax_generation": {
                "base": """You are a Power BI DAX expert with deep understanding of semantic model design and business intelligence.

CRITICAL REQUIREMENTS:
1. MUST start with EVALUATE
2. Use 'Table Name'[Column Name] format for all column references
3. Wrap table names containing spaces in single quotes (e.g., 'Sales Data')
4. Use proper DAX functions: SUMMARIZECOLUMNS, CALCULATETABLE, FILTER, TOPN, ADDCOLUMNS
5. NEVER use SQL syntax (SELECT, FROM, WHERE, JOIN)
6. Ensure the query returns a table result that can be displayed
7. NO HTML/XML tags or markdown in the output
8. For aggregations, use SUM, COUNT, AVERAGE, MAX, MIN functions
9. Use RELATED() for accessing related table columns across relationships

POWER BI MODEL STRUCTURE:
{schema_context}

{similar_queries_context}

{conversation_context}

MODEL RELATIONSHIPS:
{relationship_context}

QUESTION: {question}

Based on the Power BI model structure above, generate a single DAX query that:
- Leverages the semantic model relationships
- Uses appropriate DAX functions for the business requirement
- Returns meaningful, formatted results
- Handles context transitions properly

Generate ONLY the DAX query (no explanations, no markdown):""",

                "measure_focused": """You are a DAX expert specializing in calculated measures and advanced analytics.

AVAILABLE MEASURES:
{measures_context}

MODEL CONTEXT:
{schema_context}

{similar_queries_context}

QUESTION: {question}

Generate a DAX query that leverages existing measures where possible. Consider:
- Using existing measures instead of recalculating
- Creating calculated columns if needed with ADDCOLUMNS
- Proper context filtering with CALCULATE
- Time intelligence functions if time-based analysis is needed

Generate ONLY the DAX query:""",

                "relationship_aware": """You are a DAX expert who understands Power BI model relationships and context propagation.

RELATIONSHIP CONTEXT:
{relationship_context}

TABLE STRUCTURE:
{schema_context}

{similar_queries_context}

QUESTION: {question}

Generate a DAX query that properly navigates relationships:
- Use RELATED() for one-to-many relationships
- Use RELATEDTABLE() for many-to-one relationships  
- Consider filter context propagation
- Handle bidirectional relationships appropriately

Generate ONLY the DAX query:"""
            },

            "error_fixing": {
                "schema_error": """You are a {query_language} debugging expert. Fix the schema-related errors in this query.

AVAILABLE SCHEMA:
{schema_context}

FAILED QUERY:
{failed_query}

DATABASE ERROR:
{error}

SCHEMA ERROR ANALYSIS:
{error_analysis}

The query references non-existent columns or tables. Fix by:
1. Replacing ALL incorrect table/column references with valid names from schema
2. Checking for typos in table/column names
3. Ensuring proper capitalization and spelling
4. Using correct table prefixes or aliases

Generate ONLY the corrected {query_language} query:""",

                "syntax_error": """You are a {query_language} syntax expert. Fix the syntax errors in this query.

FAILED QUERY:
{failed_query}

SYNTAX ERROR:
{error}

SYNTAX RULES FOR {query_language}:
{syntax_rules}

Fix the syntax error by:
1. Correcting function usage and parameters
2. Fixing missing or extra punctuation
3. Ensuring proper keyword order
4. Validating parentheses and brackets

Generate ONLY the corrected {query_language} query:""",

                "performance_error": """You are a {query_language} performance expert. Optimize this query to resolve timeout issues.

FAILED QUERY:
{failed_query}

PERFORMANCE ERROR:
{error}

OPTIMIZATION STRATEGIES:
{optimization_hints}

Optimize the query by:
1. Reducing data volume with appropriate filters
2. Limiting result set size
3. Simplifying complex calculations
4. Using more efficient functions

Generate ONLY the optimized {query_language} query:"""
            }
        }
        
    def set_connection_type(self, connection_type: str):
        """Set whether we're using SQL or Semantic Model"""
        self.connection_type = connection_type
        logger.info(f"Connection type set to: {connection_type}")
    
    async def refresh_metadata(self):
        """Refresh schema/model metadata based on connection type"""
        if self.connection_type == "sql":
            result = fabric_service.discover_schema()
            if result.get("success"):
                self.sql_schema_cache = result.get("tables", {})
        elif self.connection_type == "semantic_model":
            result = semantic_model_service.discover_model()
            if result.get("success"):
                self.model_info_cache = result.get("model", {})
        return result
    
    async def manager_agent_with_knowledge(self, user_question: str, response_type: str = "text") -> Dict:
        """Enhanced manager that uses knowledge base and handles both SQL and DAX"""
        # First, check knowledge base
        similar_questions = knowledge_base_service.search_knowledge(user_question)
        
        knowledge_context = ""
        if similar_questions:
            knowledge_context = "\n\nPrevious similar questions and answers:\n"
            for kb in similar_questions[:3]:
                knowledge_context += f"Q: {kb['question']}\n"
                if self.connection_type == "sql" and kb.get('sql_query'):
                    knowledge_context += f"SQL: {kb['sql_query']}\n"
                elif self.connection_type == "semantic_model" and kb.get('dax_query'):
                    knowledge_context += f"DAX: {kb['dax_query']}\n"
                knowledge_context += f"A: {kb['answer']}\n\n"
        
        # Build schema/model context
        if self.connection_type == "sql":
            if not self.sql_schema_cache:
                await self.refresh_metadata()
            
            schema_context = "Available SQL tables and columns:\n"
            for table_name, table_info in (self.sql_schema_cache or {}).items():
                columns = [col["name"] for col in table_info["columns"]]
                schema_context += f"\n{table_name}: {', '.join(columns)}"
                
            query_type = "SQL"
            
        else:  # semantic_model
            if not self.model_info_cache:
                await self.refresh_metadata()
            
            schema_context = "Available Power BI model structure:\n\nTables:\n"
            for table_name, table_info in (self.model_info_cache or {}).get("tables", {}).items():
                columns = [col["name"] for col in table_info["columns"]]
                schema_context += f"\n{table_name}: {', '.join(columns)}"
            
            schema_context += "\n\nMeasures:\n"
            for measure in (self.model_info_cache or {}).get("measures", []):
                schema_context += f"\n{measure['name']}"
                
            query_type = "DAX"
        
        # Create prompt for manager
        manager_prompt = f"""You are a data analyst manager. A user asked: "{user_question}"

Connection type: {self.connection_type}
Response type requested: {response_type}

{schema_context}

{knowledge_context}

Your task:
1. Understand what data the user needs
2. Create a {query_type} query to get the data
3. If response_type is "visualization", plan what chart type would be best

Respond in JSON format:
{{
    "interpretation": "what the user wants",
    "query": "the {query_type} query",
    "visualization": {{
        "needed": true/false,
        "chart_type": "bar/line/pie/scatter",
        "config": {{
            "x_column": "column_name",
            "y_column": "column_name",
            "title": "chart title"
        }}
    }},
    "explanation": "how this answers the question"
}}"""

        response = await claude_service.get_response(manager_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            logger.error(f"Failed to parse manager response: {response}")
        
        return {"error": "Failed to generate query plan"}
    
    async def worker_agent_execute(self, task: Dict) -> Dict:
        """Execute SQL or DAX query based on connection type"""
        query = task.get("query")
        if not query:
            return {"error": "No query provided"}
        
        logger.info(f"Executing {self.connection_type} query: {query}")
        
        if self.connection_type == "sql":
            result = fabric_service.execute_query(query)
        else:  # semantic_model
            result = semantic_model_service.execute_dax_query(query)
        
        if not result.get("success"):
            return {"error": f"Query failed: {result.get('error')}"}
        
        return {
            "success": True,
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0)
        }
    
    async def answer_with_options(self, user_question: str, response_type: str = "text") -> Dict:
        """Complete flow with text/visualization/both options"""
        logger.info(f"Processing question: {user_question} (type: {response_type})")
        
        # Step 1: Manager creates plan
        plan = await self.manager_agent_with_knowledge(user_question, response_type)
        
        if plan.get("error"):
            return {
                "answer": f"I couldn't understand your question: {plan.get('error')}",
                "success": False
            }
        
        # Step 2: Execute query
        if plan.get("query"):
            execution_result = await self.worker_agent_execute(plan)
            
            if execution_result.get("success"):
                data = execution_result.get("data", [])
                
                response = {
                    "query": plan.get("query"),
                    "data": data[:10],  # First 10 rows for preview
                    "row_count": execution_result.get("row_count"),
                    "success": True
                }
                
                # Step 3: Generate text answer if needed
                if response_type in ["text", "both"]:
                    answer_prompt = f"""The user asked: "{user_question}"

Query executed: {plan.get('query')}
Returned {len(data)} rows.

Data: {json.dumps(data[:10], indent=2)}

Provide a clear, natural language answer."""

                    text_answer = await claude_service.get_response(answer_prompt)
                    response["answer"] = text_answer
                
                # Step 4: Generate visualization if needed
                if response_type in ["visualization", "both"] and plan.get("visualization", {}).get("needed"):
                    if data:
                        df = pd.DataFrame(data)
                        viz_config = plan["visualization"]["config"]
                        chart_type = plan["visualization"]["chart_type"]
                        
                        image_base64 = semantic_model_service.create_visualization(
                            df, chart_type, viz_config
                        )
                        
                        if image_base64:
                            response["visualization"] = {
                                "image": image_base64,
                                "type": chart_type,
                                "config": viz_config
                            }
                
                # Step 5: Save to knowledge base
                knowledge_entry = {
                    "category": self.connection_type,
                    "question": user_question,
                    "context": plan.get("interpretation"),
                    "sql_query": plan.get("query") if self.connection_type == "sql" else None,
                    "dax_query": plan.get("query") if self.connection_type == "semantic_model" else None,
                    "answer": response.get("answer", ""),
                    "response_type": response_type,
                    "metadata": {
                        "row_count": execution_result.get("row_count"),
                        "visualization": plan.get("visualization")
                    }
                }
                
                knowledge_base_service.add_knowledge(knowledge_entry)
                
                return response
            else:
                return {
                    "answer": f"Query execution failed: {execution_result.get('error')}",
                    "query": plan.get("query"),
                    "success": False
                }
        else:
            return {
                "answer": "I couldn't generate a query for your question.",
                "success": False
            }
    
    async def answer_with_self_correction(self, question: str, context_history: List[str] = []) -> Dict:
        """
        Phase 1: Complete AI workflow with self-correction loop in backend.
        This replaces the complex frontend orchestration with a single backend method.
        """
        thinking_steps = []
        query_attempts = []
        max_attempts = 3
        start_time = time.time()
        
        try:
            # Step 1: Context Preparation
            thinking_steps.append("🔍 Analyzing question and preparing context...")
            schema_context, query_language = await self._get_schema_and_query_language()
            thinking_steps.append(f"✅ Schema loaded: {query_language} ({len(schema_context)} chars)")
            
            # Step 2: Check Knowledge Base for Similar Questions
            thinking_steps.append("💡 Checking knowledge base for similar questions...")
            similar_queries = knowledge_base_service.search_knowledge(question, self.connection_type)
            if similar_queries:
                thinking_steps.append(f"📚 Found {len(similar_queries)} similar previous queries")
            else:
                thinking_steps.append("📚 No similar queries found - generating fresh approach")
            
            # Step 3: Initial Query Generation
            thinking_steps.append(f"🧠 Generating optimized {query_language} query...")
            current_query = await self._generate_intelligent_query(
                question, schema_context, query_language, context_history, similar_queries
            )
            thinking_steps.append(f"📝 Generated {len(current_query)} character query")
            
            # Step 4: Execution with Smart Retry Loop
            final_result = None
            for attempt in range(max_attempts):
                thinking_steps.append(f"⚡ Executing query (attempt {attempt + 1}/{max_attempts})...")
                
                execution_result = await self._execute_with_validation(current_query)
                
                query_attempts.append({
                    "query": current_query,
                    "success": execution_result["success"],
                    "error": execution_result.get("error"),
                    "attempt": attempt + 1,
                    "duration": execution_result.get("duration", 0),
                    "row_count": execution_result.get("row_count", 0)
                })
                
                if execution_result["success"]:
                    thinking_steps.append(f"✅ Success! Found {execution_result.get('row_count', 0)} rows in {execution_result.get('duration', 0):.2f}s")
                    final_result = execution_result
                    break
                else:
                    error_type = self._categorize_error(execution_result["error"])
                    thinking_steps.append(f"❌ {error_type}: {str(execution_result['error'])[:100]}...")
                    
                    if attempt < max_attempts - 1:
                        thinking_steps.append(f"🔧 Applying {error_type} fix strategy...")
                        current_query = await self._apply_targeted_fix(
                            current_query, execution_result["error"], error_type, schema_context, query_language
                        )
                        thinking_steps.append("🔄 Generated corrected query")
                    else:
                        thinking_steps.append("❌ Reached maximum attempts - unable to fix query")
            
            # Step 5: Generate Final Response
            total_time = time.time() - start_time
            
            if final_result:
                thinking_steps.append("📝 Crafting natural language response...")
                natural_answer = await self._generate_contextual_answer(question, current_query, final_result["data"])
                
                # Save successful interaction to knowledge base
                await self._update_knowledge_base(question, current_query, natural_answer, final_result)
                
                thinking_steps.append(f"✨ Analysis complete in {total_time:.2f}s!")
                
                return {
                    "success": True,
                    "answer": natural_answer,
                    "query": current_query,
                    "data": final_result["data"][:100],  # Limit for performance
                    "total_rows": final_result.get("row_count", 0),
                    "thinking": thinking_steps,
                    "query_attempts": query_attempts,
                    "execution_time": total_time,
                    "query_language": query_language
                }
            else:
                return {
                    "success": False,
                    "answer": f"After {max_attempts} attempts, I couldn't generate a working {query_language} query. This might be due to data structure limitations or the complexity of your question. Please try rephrasing or asking about different data.",
                    "thinking": thinking_steps,
                    "query_attempts": query_attempts,
                    "execution_time": total_time,
                    "query_language": query_language
                }
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Critical error in answer_with_self_correction: {e}")
            return {
                "success": False,
                "answer": "An internal error occurred during analysis. Please try again with a simpler question.",
                "thinking": thinking_steps + [f"💥 Critical Error: {str(e)}"],
                "query_attempts": query_attempts,
                "execution_time": total_time,
                "error_details": str(e)
            }

    async def _get_schema_and_query_language(self) -> Tuple[str, str]:
        """Enhanced schema retrieval with intelligent caching and performance optimization"""
        cache_key = f"{self.connection_type}_schema_v2"
        
        # Check if we need cleanup first
        await self._cleanup_expired_cache()
        
        # Try to get from cache
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            self.cache_stats["hits"] += 1
            logger.info(f"✅ Schema cache hit for {self.connection_type}")
            return cached_result
        
        # Cache miss - need to fetch fresh data
        self.cache_stats["misses"] += 1
        logger.info(f"🔄 Schema cache miss for {self.connection_type} - fetching fresh data")
        
        try:
            if self.connection_type == 'sql':
                schema_context, query_language = await self._fetch_and_optimize_sql_schema()
            else:  # semantic_model
                schema_context, query_language = await self._fetch_and_optimize_dax_schema()
            
            # Cache the result with metadata
            await self._store_in_cache(cache_key, (schema_context, query_language))
            
            return schema_context, query_language
            
        except Exception as e:
            logger.error(f"Failed to fetch schema: {e}")
            # Return minimal fallback
            if self.connection_type == 'sql':
                return "Schema unavailable - using fallback mode", "T-SQL"
            else:
                return "Model unavailable - using fallback mode", "DAX"

    async def _fetch_and_optimize_sql_schema(self) -> Tuple[str, str]:
        """Fetch and optimize SQL schema with intelligent prioritization"""
        
        # Refresh metadata if needed
        if not self.sql_schema_cache:
            result = await self.refresh_metadata()
            if not result.get("success"):
                raise Exception("Failed to refresh SQL metadata")
        
        schema = self.sql_schema_cache or {}
        
        # Intelligent schema optimization
        optimized_schema = self._optimize_sql_schema_for_ai(schema)
        
        schema_context = "Available Microsoft Fabric tables and columns:\n\n"
        
        # Prioritize tables by importance and usage patterns
        table_priority = self._calculate_table_priority(schema, "sql")
        
        for table_name in table_priority:
            table_info = optimized_schema.get(table_name, {})
            columns = table_info.get('columns', [])
            
            # Create enhanced table description
            schema_context += f"📊 {table_name}:\n"
            
            # Group columns by type for better AI understanding
            column_groups = self._group_columns_by_type(columns)
            
            for group_name, group_columns in column_groups.items():
                if group_columns:
                    schema_context += f"  {group_name}: {', '.join(group_columns)}\n"
            
            # Add table metadata if available
            row_estimate = table_info.get('estimated_rows', 'Unknown')
            schema_context += f"  Estimated rows: {row_estimate}\n\n"
        
        return schema_context, "T-SQL"
    
    async def _fetch_and_optimize_dax_schema(self) -> Tuple[str, str]:
        """Fetch and optimize Power BI schema with relationship awareness"""
        
        # Refresh metadata if needed
        if not self.model_info_cache:
            result = await self.refresh_metadata()
            if not result.get("success"):
                raise Exception("Failed to refresh Power BI metadata")
        
        schema = self.model_info_cache or {}
        
        # Enhanced Power BI schema formatting
        schema_context = "Available Power BI semantic model:\n\n"
        
        # Tables with intelligent prioritization
        tables = schema.get("tables", {})
        table_priority = self._calculate_table_priority(tables, "dax")
        
        schema_context += "📊 TABLES:\n"
        for table_name in table_priority:
            table_info = tables.get(table_name, {})
            columns = table_info.get('columns', [])
            
            schema_context += f"\n'{table_name}':\n"
            
            # Categorize columns for better AI understanding
            key_columns = [col['name'] for col in columns if 'key' in col['name'].lower() or 'id' in col['name'].lower()]
            date_columns = [col['name'] for col in columns if any(date_term in col['name'].lower() for date_term in ['date', 'time', 'year', 'month'])]
            measure_columns = [col['name'] for col in columns if any(measure_term in col['name'].lower() for measure_term in ['amount', 'total', 'sum', 'count', 'value'])]
            other_columns = [col['name'] for col in columns if col['name'] not in key_columns + date_columns + measure_columns]
            
            if key_columns:
                schema_context += f"  🔑 Keys: {', '.join(key_columns[:5])}\n"
            if date_columns:
                schema_context += f"  📅 Dates: {', '.join(date_columns[:5])}\n"
            if measure_columns:
                schema_context += f"  📈 Measures: {', '.join(measure_columns[:8])}\n"
            if other_columns:
                schema_context += f"  📝 Other: {', '.join(other_columns[:8])}\n"
    
        # Add measures
        measures = schema.get("measures", [])
        if measures:
            schema_context += "\n📈 CALCULATED MEASURES:\n"
            for measure in measures[:15]:  # Top 15 measures
                schema_context += f"  • {measure['name']}\n"
                
            if len(measures) > 15:
                schema_context += f"  ... and {len(measures) - 15} more measures\n"
        
        return schema_context, "DAX"
    
    def _optimize_sql_schema_for_ai(self, schema: Dict) -> Dict:
        """Optimize SQL schema information for AI consumption"""
        optimized = {}
        
        for table_name, table_info in schema.items():
            columns = table_info.get('columns', [])
            
            # Add estimated row count (you might get this from table stats)
            estimated_rows = self._estimate_table_size(table_name, len(columns))
            
            # Filter out system columns
            filtered_columns = [
                col for col in columns 
                if not col['name'].lower().startswith('__') 
                and col['name'].lower() not in ['rowguid', 'timestamp']
            ]
            
            optimized[table_name] = {
                **table_info,
                'columns': filtered_columns,
                'estimated_rows': estimated_rows,
                'column_count': len(filtered_columns)
            }
        
        return optimized
    
    def _calculate_table_priority(self, schema: Dict, connection_type: str) -> List[str]:
        """Calculate table priority based on naming patterns and usage"""
        tables = list(schema.keys())
        
        # Priority scoring
        priority_scores = {}
        
        for table_name in tables:
            score = 0
            table_lower = table_name.lower()
            
            # Business entity tables get higher priority
            if any(entity in table_lower for entity in ['sales', 'customer', 'order', 'product', 'revenue']):
                score += 100
            
            # Fact tables (for both SQL and Power BI)
            if any(fact_term in table_lower for fact_term in ['fact', 'transaction', 'activity']):
                score += 80
            
            # Dimension tables
            if table_lower.startswith('dim') or any(dim_term in table_lower for dim_term in ['dimension', 'lookup']):
                score += 60
            
            # Avoid system/temp tables
            if any(sys_term in table_lower for sys_term in ['temp', 'tmp', 'sys', 'log', 'audit']):
                score -= 50
            
            # Table size consideration (more columns = potentially more important)
            if connection_type == 'sql':
                column_count = len(schema[table_name].get('columns', []))
            else:
                column_count = len(schema[table_name].get('columns', []))
            
            if column_count > 10:
                score += 20
            elif column_count > 5:
                score += 10
            
            priority_scores[table_name] = score
        
        # Sort by priority score (highest first)
        return sorted(tables, key=lambda t: priority_scores[t], reverse=True)
    
    def _group_columns_by_type(self, columns: List[Dict]) -> Dict[str, List[str]]:
        """Group columns by logical types for better AI understanding"""
        groups = {
            "🔑 Keys/IDs": [],
            "📅 Dates": [],
            "📈 Measures": [],
            "📝 Text": [],
            "🔢 Numbers": [],
            "🏷️ Categories": []
        }
        
        for col in columns:
            col_name = col['name']
            col_type = col.get('type', '').lower()
            col_name_lower = col_name.lower()
            
            # Categorize by name patterns
            if any(key_term in col_name_lower for key_term in ['id', 'key', 'guid']):
                groups["🔑 Keys/IDs"].append(col_name)
            elif any(date_term in col_name_lower for date_term in ['date', 'time', 'created', 'modified']):
                groups["📅 Dates"].append(col_name)
            elif any(measure_term in col_name_lower for measure_term in ['amount', 'total', 'price', 'cost', 'revenue', 'sum']):
                groups["📈 Measures"].append(col_name)
            elif any(text_type in col_type for text_type in ['varchar', 'nvarchar', 'text', 'string']):
                if any(cat_term in col_name_lower for cat_term in ['name', 'description', 'category', 'type', 'status']):
                    groups["🏷️ Categories"].append(col_name)
                else:
                    groups["📝 Text"].append(col_name)
            elif any(num_type in col_type for num_type in ['int', 'decimal', 'float', 'numeric', 'money']):
                groups["🔢 Numbers"].append(col_name)
            else:
                groups["📝 Text"].append(col_name)  # Default fallback
        
        # Remove empty groups and limit items per group
        return {k: v[:8] for k, v in groups.items() if v}
    
    def _estimate_table_size(self, table_name: str, column_count: int) -> str:
        """Estimate table size based on naming patterns and column count"""
        table_lower = table_name.lower()
        
        # Heuristic-based estimation
        if any(large_term in table_lower for large_term in ['fact', 'transaction', 'log', 'history']):
            return "Large (1M+ rows)"
        elif any(medium_term in table_lower for medium_term in ['sales', 'order', 'customer']):
            return "Medium (10K-1M rows)"
        elif column_count > 15:
            return "Medium (10K-1M rows)"
        else:
            return "Small (<10K rows)"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Tuple[str, str]]:
        """Get data from cache with TTL checking"""
        if cache_key not in self.schema_cache:
            return None
        
        cached_data = self.schema_cache[cache_key]
        metadata = self.schema_metadata.get(cache_key, {})
        
        current_time = time.time()
        cache_time = metadata.get('cached_at', 0)
        ttl = metadata.get('ttl', self.cache_config['default_ttl'])
        
        # Check if cache is still valid
        if current_time - cache_time < ttl:
            # Update access time for LRU
            metadata['last_accessed'] = current_time
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            
            # Extend TTL for frequently accessed schemas
            if metadata['access_count'] > 5:
                metadata['ttl'] = self.cache_config['performance_boost_ttl']
            
            return cached_data
        else:
            # Cache expired
            del self.schema_cache[cache_key]
            del self.schema_metadata[cache_key]
            return None
    
    async def _store_in_cache(self, cache_key: str, data: Tuple[str, str]) -> None:
        """Store data in cache with metadata"""
        current_time = time.time()
        
        # Check cache size limit
        if len(self.schema_cache) >= self.cache_config['max_cache_size']:
            await self._evict_least_used()
        
        self.schema_cache[cache_key] = data
        self.schema_metadata[cache_key] = {
            'cached_at': current_time,
            'last_accessed': current_time,
            'access_count': 1,
            'ttl': self.cache_config['default_ttl'],
            'size_bytes': len(str(data))
        }
        
        self.cache_stats["refreshes"] += 1
        logger.info(f"📦 Cached schema for {cache_key}")
    
    async def _evict_least_used(self) -> None:
        """Evict least recently used cache entries"""
        if not self.schema_metadata:
            return
        
        # Find least recently accessed
        lru_key = min(
            self.schema_metadata.keys(),
            key=lambda k: self.schema_metadata[k]['last_accessed']
        )
        
        del self.schema_cache[lru_key]
        del self.schema_metadata[lru_key]
        
        logger.info(f"🗑️ Evicted cache entry: {lru_key}")
    
    async def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries"""
        current_time = time.time()
        
        # Only run cleanup every 30 minutes
        if current_time - self.cache_stats["last_cleanup"] < self.cache_config["cleanup_interval"]:
            return
        
        expired_keys = []
        for cache_key, metadata in self.schema_metadata.items():
            cache_time = metadata.get('cached_at', 0)
            ttl = metadata.get('ttl', self.cache_config['default_ttl'])
            
            if current_time - cache_time >= ttl:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            del self.schema_cache[key]
            del self.schema_metadata[key]
        
        self.cache_stats["last_cleanup"] = current_time
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate_percentage": round(hit_rate, 2),
            "total_hits": self.cache_stats["hits"],
            "total_misses": self.cache_stats["misses"],
            "total_refreshes": self.cache_stats["refreshes"],
            "cached_schemas": len(self.schema_cache),
            "cache_size_limit": self.cache_config["max_cache_size"],
            "last_cleanup": datetime.fromtimestamp(self.cache_stats["last_cleanup"]).isoformat()
        }

    def _categorize_error(self, error_message: str) -> str:
        """Categorize errors for targeted fixing strategies"""
        if not error_message:
            return "UNKNOWN_ERROR"
            
        error_lower = error_message.lower()
        
        # Schema-related errors
        if any(term in error_lower for term in ["invalid column name", "invalid object name", "cannot be found", "not found"]):
            return "SCHEMA_ERROR"
        
        # Syntax errors
        elif any(term in error_lower for term in ["syntax error", "incorrect syntax", "expected", "unexpected"]):
            return "SYNTAX_ERROR"
        
        # Permission errors
        elif any(term in error_lower for term in ["permission", "access", "denied", "unauthorized"]):
            return "PERMISSION_ERROR"
        
        # Timeout errors
        elif any(term in error_lower for term in ["timeout", "cancelled", "aborted"]):
            return "TIMEOUT_ERROR"
        
        # Calculation errors
        elif any(term in error_lower for term in ["division by zero", "arithmetic overflow", "conversion failed"]):
            return "CALCULATION_ERROR"
        
        # DAX-specific errors
        elif any(term in error_lower for term in ["evaluate", "dax", "measure", "table expression"]):
            return "DAX_ERROR"
        
        else:
            return "GENERAL_ERROR"

    async def _execute_with_validation(self, query: str) -> Dict:
        """Execute query with validation and performance monitoring"""
        try:
            # Pre-execution validation
            validation_result = self._validate_query_safety(query)
            if not validation_result["safe"]:
                return {
                    "success": False,
                    "error": f"Query validation failed: {validation_result['reason']}"
                }
            
            # Execute with timing
            start_time = time.time()
            
            if self.connection_type == "sql":
                result = fabric_service.execute_query(query, limit=1000)
            else:
                result = semantic_model_service.execute_dax_query(query)
            
            duration = time.time() - start_time
            
            if result.get("success"):
                result["duration"] = duration
                logger.info(f"Query executed successfully in {duration:.2f}s, returned {result.get('row_count', 0)} rows")
            else:
                logger.warning(f"Query failed after {duration:.2f}s: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration": 0
            }

    def _validate_query_safety(self, query: str) -> Dict:
        """Validate query for safety and performance concerns"""
        if not query or not query.strip():
            return {"safe": False, "reason": "Empty query"}
        
        query_upper = query.upper()
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "EXEC", "EXECUTE", "INSERT", "UPDATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper and "CREATE" not in query_upper:  # Allow CREATE statements
                return {"safe": False, "reason": f"Dangerous operation detected: {keyword}"}
        
        # Performance concerns for SQL
        if self.connection_type == "sql":
            if "SELECT *" in query_upper and "TOP" not in query_upper and "LIMIT" not in query_upper:
                return {"safe": False, "reason": "SELECT * without TOP/LIMIT clause can cause performance issues"}
        
        # Basic DAX validation
        if self.connection_type == "semantic_model":
            if not query_upper.startswith("EVALUATE"):
                return {"safe": False, "reason": "DAX queries must start with EVALUATE"}
        
        return {"safe": True}

    async def _update_knowledge_base(self, question: str, query: str, answer: str, result: Dict) -> None:
        """Save successful interaction to knowledge base for future improvement"""
        try:
            knowledge_entry = {
                "category": self.connection_type,
                "question": question,
                "context": f"Successfully answered with {result.get('row_count', 0)} results",
                "sql_query": query if self.connection_type == "sql" else None,
                "dax_query": query if self.connection_type == "semantic_model" else None,
                "answer": answer,
                "response_type": "text",
                "metadata": {
                    "row_count": result.get("row_count", 0),
                    "execution_time": result.get("duration", 0),
                    "success": True
                }
            }
            
            knowledge_base_service.add_knowledge(knowledge_entry)
            logger.info(f"Added successful query to knowledge base: {question[:50]}...")
            
        except Exception as e:
            logger.warning(f"Failed to update knowledge base: {e}")
            # Don't fail the main operation if knowledge base update fails
    
    async def _generate_intelligent_query(self, question: str, schema_context: str, query_language: str, 
                                          context_history: List[str], similar_queries: List[Dict]) -> str:
        """Enhanced query generation with advanced context awareness"""
        
        try:
            # Analyze the question to determine the best prompt template
            question_analysis = self._analyze_question_complexity(question)
            
            # Build context sections
            context_sections = self._build_comprehensive_context(
                question, context_history, similar_queries, question_analysis
            )
            
            # Select appropriate prompt template
            template_key = self._select_prompt_template(question_analysis, query_language)
            template_lang_key = "dax_generation" if query_language == "DAX" else "sql_generation"
            template = self.advanced_prompt_templates[template_lang_key][template_key]
            
            # Build the complete prompt
            prompt = self._build_contextual_prompt(
                template, question, schema_context, context_sections, question_analysis, query_language
            )
            
            response = await claude_service.get_response(prompt)
            cleaned_query = self._clean_query_response(response, query_language)
            
            # Apply advanced query optimization
            optimized_query = self._apply_advanced_optimization(cleaned_query, query_language, question_analysis)
            
            logger.info(f"Generated {query_language} query ({len(optimized_query)} chars) using template '{template_key}'")
            return optimized_query

        except Exception as e:
            logger.error(f"Advanced query generation failed: {e}")
            # Fallback to simple generation
            return await self._generate_fallback_query(question, schema_context, query_language)

    async def _apply_targeted_fix(self, failed_query: str, error: str, error_type: str, 
                                  schema_context: str, query_language: str) -> str:
        """Enhanced targeted fixing with advanced error analysis"""
        
        # Analyze the error for more specific fixing
        error_analysis = self._analyze_error_details(error, error_type, failed_query)
        
        # Select appropriate fixing template
        fix_template = self.advanced_prompt_templates["error_fixing"].get(
            error_type.lower() + "_error", 
            self.advanced_prompt_templates["error_fixing"]["syntax_error"]
        )
        
        # Build fixing context
        fixing_context = self._build_error_fixing_context(error_type, query_language, error_analysis)
        
        prompt = fix_template.format(
            query_language=query_language,
            failed_query=failed_query,
            error=error,
            schema_context=schema_context,
            error_analysis=error_analysis,
            **fixing_context
        )
        
        try:
            response = await claude_service.get_response(prompt)
            fixed_query = self._clean_query_response(response, query_language)
            
            # Apply post-fix optimizations
            optimized_fix = self._apply_post_fix_optimizations(fixed_query, error_type, query_language)
            
            logger.info(f"Applied enhanced {error_type} fix: {len(optimized_fix)} chars")
            return optimized_fix
            
        except Exception as e:
            logger.error(f"Enhanced targeted fix failed: {e}")
            # Fallback to simple fix
            return await self._apply_simple_fix(failed_query, error, query_language)

    def _clean_query_response(self, response: str, query_language: str) -> str:
        """Clean and validate query response from Claude"""
        if not response:
            return ""
        
        cleaned = response.strip()
        
        # Remove markdown code blocks
        if '```' in cleaned:
            # Extract content from code blocks
            patterns = [
                r'```(?:sql|dax|tsql)?\s*(.*?)\s*```',
                r'```\s*(.*?)\s*```'
            ]
            for pattern in patterns:
                match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
                if match:
                    cleaned = match.group(1).strip()
                    break
            else:
                # Remove triple backticks if no pattern matched
                cleaned = cleaned.replace('```', '')
        
        # Remove any remaining backticks
        cleaned = cleaned.replace('`', '')
        
        # Remove language prefixes
        cleaned = re.sub(r'^(sql|dax|t-sql|tsql):\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Apply language-specific cleaning
        if query_language == "T-SQL":
            cleaned = self._clean_sql_query(cleaned)
        else:
            cleaned = self._clean_dax_query(cleaned)
        
        return cleaned

    def _clean_sql_query(self, query: str) -> str:
        """Apply SQL-specific cleaning"""
        # Ensure TOP clause is present for SELECT statements
        if query.upper().startswith('SELECT') and 'TOP' not in query.upper() and 'LIMIT' not in query.upper():
            query = re.sub(r'^SELECT\s+', 'SELECT TOP 100 ', query, flags=re.IGNORECASE)
        
        # Replace LIMIT with TOP
        query = re.sub(r'\s+LIMIT\s+(\d+)', r' TOP \1', query, flags=re.IGNORECASE)
        
        # Fix common SQL patterns
        query = re.sub(r'\bILIKE\b', 'LIKE', query, flags=re.IGNORECASE)
        
        return query.strip()

    def _clean_dax_query(self, query: str) -> str:
        """Apply DAX-specific cleaning"""
        # Ensure EVALUATE is present
        if not query.upper().startswith('EVALUATE'):
            # Check if it looks like a table expression
            if any(func in query.upper() for func in ['SUMMARIZE', 'FILTER', 'CALCULATE', 'TOPN']):
                query = 'EVALUATE\n' + query
            elif query and not query.startswith('{'):
                # Likely a table name
                query = f'EVALUATE {query}'
        
        # Remove any SQL artifacts
        query = re.sub(r'\bSELECT\s+', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\bFROM\s+', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\bWHERE\s+', 'FILTER(', query, flags=re.IGNORECASE)
        
        return query.strip()

    def _optimize_query(self, query: str, query_language: str) -> str:
        """Apply final optimizations to the query"""
        if query_language == "T-SQL":
            # Ensure reasonable TOP limit
            if 'TOP' in query.upper():
                query = re.sub(r'TOP\s+(\d{4,})', 'TOP 1000', query, flags=re.IGNORECASE)
        
        elif query_language == "DAX":
            # Add TOPN wrapper if query might return too many rows
            if 'TOPN(' not in query.upper() and 'EVALUATE' in query.upper():
                # Only wrap simple table evaluations
                table_pattern = r'EVALUATE\s+([\'"]?\w+[\'"]?)\s*$'
                if re.match(table_pattern, query.strip(), re.IGNORECASE):
                    table_match = re.match(table_pattern, query.strip(), re.IGNORECASE)
                    if table_match:
                        table_name = table_match.group(1)
                        query = f'EVALUATE\nTOPN(100, {table_name})'
        
        return query

    # --- New Advanced Prompt Engineering Methods ---
    def _analyze_question_complexity(self, question: str) -> Dict:
        """Analyze question complexity and requirements"""
        
        question_lower = question.lower()
        
        analysis = {
            'complexity': 'simple',
            'requires_joins': False,
            'requires_aggregation': False,
            'requires_time_analysis': False,
            'requires_filtering': False,
            'aggregation_type': None,
            'time_dimension': None,
            'grouping_requirements': [],
            'business_entities': [],
            'operations': [],
            'question_intent': self._classify_detailed_intent(question_lower)
        }
        
        # Detect complexity indicators
        complexity_indicators = {
            'joins': ['customer', 'product', 'order', 'between', 'and', 'with', 'from'],
            'aggregation': ['total', 'sum', 'count', 'average', 'max', 'min', 'by'],
            'time': ['year', 'month', 'quarter', 'daily', 'weekly', 'trend', 'over time'],
            'filtering': ['where', 'filter', 'only', 'specific', 'particular', 'certain']
        }
        
        # Check for complexity indicators
        for category, indicators in complexity_indicators.items():
            if any(indicator in question_lower for indicator in indicators):
                if category == 'joins':
                    analysis['requires_joins'] = True
                elif category == 'aggregation':
                    analysis['requires_aggregation'] = True
                elif category == 'time':
                    analysis['requires_time_analysis'] = True
                elif category == 'filtering':
                    analysis['requires_filtering'] = True
        
        # Determine aggregation type
        if 'total' in question_lower or 'sum' in question_lower:
            analysis['aggregation_type'] = 'SUM'
        elif 'count' in question_lower or 'how many' in question_lower:
            analysis['aggregation_type'] = 'COUNT'
        elif 'average' in question_lower or 'mean' in question_lower:
            analysis['aggregation_type'] = 'AVERAGE'
        elif 'max' in question_lower or 'highest' in question_lower:
            analysis['aggregation_type'] = 'MAX'
        elif 'min' in question_lower or 'lowest' in question_lower:
            analysis['aggregation_type'] = 'MIN'
        
        # Determine time dimension
        if any(time_word in question_lower for time_word in ['year', 'yearly', 'annual']):
            analysis['time_dimension'] = 'YEAR'
        elif any(time_word in question_lower for time_word in ['month', 'monthly']):
            analysis['time_dimension'] = 'MONTH'
        elif any(time_word in question_lower for time_word in ['quarter', 'quarterly']):
            analysis['time_dimension'] = 'QUARTER'
        
        # Determine grouping requirements
        group_patterns = [
            r'by (\w+)',
            r'per (\w+)',
            r'for each (\w+)',
            r'(\w+) breakdown'
        ]
        
        for pattern in group_patterns:
            matches = re.findall(pattern, question_lower)
            analysis['grouping_requirements'].extend(matches)
        
        # Calculate overall complexity
        complexity_score = 0
        if analysis['requires_joins']: complexity_score += 2
        if analysis['requires_aggregation']: complexity_score += 1
        if analysis['requires_time_analysis']: complexity_score += 1
        if analysis['requires_filtering']: complexity_score += 1
        if len(analysis['grouping_requirements']) > 1: complexity_score += 1
        
        if complexity_score >= 4:
            analysis['complexity'] = 'complex'
        elif complexity_score >= 2:
            analysis['complexity'] = 'moderate'
        else:
            analysis['complexity'] = 'simple'
        
        return analysis

    def _classify_detailed_intent(self, question: str) -> str:
        """Classify detailed intent beyond basic categories"""
        
        intent_patterns = {
            'TREND_ANALYSIS': ['trend', 'over time', 'progression', 'growth', 'decline'],
            'COMPARISON': ['compare', 'versus', 'vs', 'difference', 'better', 'worse'],
            'RANKING': ['top', 'bottom', 'best', 'worst', 'highest', 'lowest', 'rank'],
            'DISTRIBUTION': ['breakdown', 'distribution', 'split', 'allocation'],
            'PERFORMANCE': ['performance', 'kpi', 'metric', 'achievement', 'target'],
            'RELATIONSHIP': ['relationship', 'correlation', 'related', 'connected'],
            'ANOMALY': ['unusual', 'strange', 'outlier', 'anomaly', 'exception'],
            'FORECAST': ['predict', 'forecast', 'future', 'projection', 'estimate']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in question for pattern in patterns):
                return intent
        
        return 'GENERAL_INQUIRY'

    def _select_prompt_template(self, question_analysis: Dict, query_language: str) -> str:
        """Select the most appropriate prompt template"""
        
        language_key = "dax" if query_language == "DAX" else "sql"
        
        # For DAX, check for measure-focused queries
        if language_key == "dax":
            if question_analysis['requires_aggregation'] and question_analysis['aggregation_type']:
                return "measure_focused"
            elif question_analysis['requires_joins'] or question_analysis['complexity'] == 'complex':
                return "relationship_aware"
            else:
                return "base"
        
        # For SQL, check for relationship requirements
        else:
            if question_analysis['requires_joins'] or len(question_analysis['grouping_requirements']) > 1:
                return "with_relationships"
            elif question_analysis['requires_aggregation']:
                return "aggregation_focused"
            else:
                return "base"

    def _build_comprehensive_context(self, question: str, context_history: List[str], 
                                     similar_queries: List[Dict], question_analysis: Dict) -> Dict:
        """Build comprehensive context for prompt generation"""
        
        context = {}
        
        # Conversation context
        if context_history:
            context['conversation_context'] = f"""
CONVERSATION HISTORY:
{chr(10).join(context_history[-3:])}

This appears to be a follow-up question. Consider the previous context when generating the query.
"""
        else:
            context['conversation_context'] = ""
        
        # Similar queries context
        if similar_queries:
            context['similar_queries_context'] = """
SIMILAR SUCCESSFUL QUERIES FOR REFERENCE:
"""
            for sq in similar_queries[:2]:
                context['similar_queries_context'] += f"""
Previous Q: {sq['question']}
Query: {sq.get('sql_query') or sq.get('dax_query', 'N/A')}
Success Rate: {sq.get('success_count', 1)} times
"""
        else:
            context['similar_queries_context'] = ""
        
        # Business context based on question analysis
        business_context_parts = []
        
        if question_analysis['question_intent'] == 'TREND_ANALYSIS':
            business_context_parts.append("This is a trend analysis query. Focus on time-based patterns and changes.")
        elif question_analysis['question_intent'] == 'COMPARISON':
            business_context_parts.append("This is a comparison query. Ensure results can be easily compared.")
        elif question_analysis['question_intent'] == 'RANKING':
            business_context_parts.append("This is a ranking query. Use ORDER BY and TOP/TOPN appropriately.")
        
        if question_analysis['requires_aggregation']:
            business_context_parts.append(f"Aggregation required: {question_analysis['aggregation_type'] or 'Multiple types'}")
        
        if question_analysis['time_dimension']:
            business_context_parts.append(f"Time dimension: {question_analysis['time_dimension']}")
        
        context['business_context'] = "\n".join(business_context_parts) if business_context_parts else "General data retrieval query."
        
        return context

    def _build_contextual_prompt(self, template: str, question: str, schema_context: str, 
                                 context_sections: Dict, question_analysis: Dict, query_language: str) -> str:
        """Build the complete contextual prompt"""
        
        # Prepare template variables
        template_vars = {
            'question': question,
            'schema_context': schema_context,
            'query_language': query_language,
            'relationship_hints': '',
            'measures_context': '',
            'relationship_context': '',
            **context_sections
        }
        
        # Add analysis-specific variables
        template_vars.update({
            'aggregation_type': question_analysis.get('aggregation_type', 'None'),
            'time_dimension': question_analysis.get('time_dimension', 'None'),
            'grouping_requirements': ', '.join(question_analysis.get('grouping_requirements', [])) or 'None'
        })
        
        # Add relationship hints for SQL
        if query_language == "T-SQL" and question_analysis['requires_joins']:
            template_vars['relationship_hints'] = self._generate_relationship_hints(schema_context, question_analysis)
        
        # Add measures context for DAX
        if query_language == "DAX":
            template_vars['measures_context'] = self._extract_measures_context(schema_context)
            template_vars['relationship_context'] = "Leverage model relationships for cross-table analysis"
        
        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template variable missing: {e}. Using base template.")
            # Fallback to base template with available variables
            base_template_key = "dax_generation" if query_language == "DAX" else "sql_generation"
            base_template = self.advanced_prompt_templates[base_template_key]["base"]
            
            # Filter only keys that exist in the base template to avoid another KeyError
            valid_vars = {k: v for k, v in template_vars.items() if f"{{{k}}}" in base_template}
            return base_template.format(**valid_vars)

    def _generate_relationship_hints(self, schema_context: str, question_analysis: Dict) -> str:
        """Generate hints about potential table relationships"""
        
        # Extract table names from schema
        table_names = re.findall(r'📊 (\w+):', schema_context)
        
        hints = []
        
        # Common relationship patterns
        if any('customer' in table.lower() for table in table_names) and any('order' in table.lower() for table in table_names):
            hints.append("• Customer-Order relationship likely via CustomerID")
        
        if any('product' in table.lower() for table in table_names) and any('order' in table.lower() for table in table_names):
            hints.append("• Product-Order relationship likely via ProductID")
        
        if any('sales' in table.lower() for table in table_names):
            hints.append("• Sales table likely central fact table with foreign keys")
        
        # Add grouping-based hints
        for group_req in question_analysis.get('grouping_requirements', []):
            hints.append(f"• Consider grouping by {group_req} - look for related dimension table")
        
        return "\n".join(hints) if hints else "• Analyze schema for ID/Key columns to determine relationships"

    def _extract_measures_context(self, schema_context: str) -> str:
        """Extract measures context for DAX queries"""
        
        if "CALCULATED MEASURES:" in schema_context:
            measures_section = schema_context.split("CALCULATED MEASURES:")[1]
            return f"Use existing measures where possible:\n{measures_section[:500]}..."
        else:
            return "No pre-calculated measures found. Create aggregations using DAX functions."

    def _apply_advanced_optimization(self, query: str, query_language: str, question_analysis: Dict) -> str:
        """Apply advanced optimizations based on question analysis"""
        
        if query_language == "T-SQL":
            return self._optimize_sql_advanced(query, question_analysis)
        else:
            return self._optimize_dax_advanced(query, question_analysis)

    def _optimize_sql_advanced(self, query: str, question_analysis: Dict) -> str:
        """Advanced SQL optimization"""
        
        optimized = query
        
        # Ensure appropriate TOP limit based on complexity
        if 'TOP ' not in optimized.upper():
             optimized = re.sub(r'SELECT\s', 'SELECT TOP 100 ', optimized, flags=re.IGNORECASE, count=1)

        if question_analysis['complexity'] == 'complex':
            optimized = re.sub(r'TOP\s+\d+', 'TOP 50', optimized, flags=re.IGNORECASE)
        elif question_analysis['complexity'] == 'moderate':
            optimized = re.sub(r'TOP\s+\d+', 'TOP 100', optimized, flags=re.IGNORECASE)
        
        # Add ORDER BY if ranking is required
        if question_analysis['question_intent'] == 'RANKING' and 'ORDER BY' not in optimized.upper():
            if question_analysis['aggregation_type'] in ['SUM', 'COUNT', 'MAX']:
                # Add a generic ORDER BY for aggregated results
                optimized += "\nORDER BY 2 DESC"  # Order by second column (usually the aggregated value)
        
        return optimized

    def _optimize_dax_advanced(self, query: str, question_analysis: Dict) -> str:
        """Advanced DAX optimization"""
        
        optimized = query
        
        # Add TOPN for complex queries to prevent large result sets
        if question_analysis['complexity'] == 'complex' and 'TOPN(' not in optimized.upper():
            # Wrap simple table evaluations with TOPN
            if optimized.strip().startswith('EVALUATE') and '\n' not in optimized.strip()[8:].strip():
                table_ref = optimized.strip()[8:].strip()
                optimized = f"EVALUATE\nTOPN(50, {table_ref})"
        
        # Optimize for ranking queries
        if question_analysis['question_intent'] == 'RANKING':
            if 'TOPN(' not in optimized.upper() and 'SUMMARIZE' in optimized.upper():
                # Wrap with TOPN if it's a summarization for ranking
                lines = optimized.split('\n')
                evaluate_content = '\n'.join(lines[1:]) if lines[0].strip().upper() == 'EVALUATE' else optimized
                optimized = f"EVALUATE\nTOPN(10, {evaluate_content})"
        
        return optimized

    def _analyze_error_details(self, error: str, error_type: str, failed_query: str) -> str:
        """Analyze error details for more specific fixing"""
        
        analysis = []
        error_lower = error.lower()
        
        if error_type == "SCHEMA_ERROR":
            # Extract specific column/table names mentioned in error
            column_matches = re.findall(r"column name '([^']+)'", error, re.IGNORECASE)
            table_matches = re.findall(r"object name '([^']+)'", error, re.IGNORECASE)
            
            if column_matches:
                analysis.append(f"Problematic columns: {', '.join(column_matches)}")
            if table_matches:
                analysis.append(f"Problematic tables: {', '.join(table_matches)}")
            
            # Check for common typos
            query_words = re.findall(r'\b\w+\b', failed_query.lower())
            common_business_terms = ['sales', 'customer', 'product', 'order', 'revenue', 'date', 'amount']
            
            for term in common_business_terms:
                similar_words = [word for word in query_words if self._is_similar_word(word, term)]
                if similar_words:
                    analysis.append(f"Possible typo: '{similar_words[0]}' might be '{term}'")
        
        elif error_type == "SYNTAX_ERROR":
            if "expected" in error_lower:
                expected_matches = re.findall(r"expected '([^']+)'", error, re.IGNORECASE)
                if expected_matches:
                    analysis.append(f"Missing or incorrect: {', '.join(expected_matches)}")
            
            if "unexpected" in error_lower:
                unexpected_matches = re.findall(r"unexpected '([^']+)'", error, re.IGNORECASE)
                if unexpected_matches:
                    analysis.append(f"Unexpected tokens: {', '.join(unexpected_matches)}")
        
        elif error_type == "CALCULATION_ERROR":
            if "division by zero" in error_lower:
                analysis.append("Division by zero detected - need NULLIF() protection")
            if "overflow" in error_lower:
                analysis.append("Arithmetic overflow - need data type casting")
        
        return "; ".join(analysis) if analysis else "General error - apply standard fixes"

    def _build_error_fixing_context(self, error_type: str, query_language: str, error_analysis: str) -> Dict:
        """Build context for error fixing"""
        
        context = {}
        
        if query_language == "T-SQL":
            context["syntax_rules"] = """
- Use TOP instead of LIMIT for row limiting
- Use [square brackets] for names with spaces/special characters
- Proper JOIN syntax: INNER/LEFT/RIGHT JOIN table ON condition
- Use ISNULL() or COALESCE() for NULL handling
- CAST() or CONVERT() for data type conversions
- Proper quote usage: single quotes for strings, brackets for identifiers
"""
            
            if error_type == "PERFORMANCE_ERROR":
                context["optimization_hints"] = """
- Add WHERE clauses to filter data early
- Use TOP to limit result sets
- Avoid SELECT * in favor of specific columns
- Use appropriate indexes (consider column usage)
- Simplify complex subqueries
"""
        
        else:  # DAX
            context["syntax_rules"] = """
- Must start with EVALUATE
- Table references: 'Table Name' or TableName
- Column references: 'Table Name'[Column Name]
- Use DAX functions: FILTER, SUMMARIZE, CALCULATE, TOPN
- NO SQL syntax: no SELECT, FROM, WHERE, JOIN
- Use RELATED() for cross-table column access
"""
            
            if error_type == "PERFORMANCE_ERROR":
                context["optimization_hints"] = """
- Use TOPN() to limit results
- Apply FILTER() early to reduce data volume
- Use SUMMARIZECOLUMNS instead of SUMMARIZE when possible
- Avoid complex calculated columns in large tables
- Use measures instead of calculated columns where appropriate
"""
        
        return context

    def _apply_post_fix_optimizations(self, fixed_query: str, error_type: str, query_language: str) -> str:
        """Apply optimizations after fixing errors"""
        
        optimized = fixed_query
        
        # Apply error-type specific optimizations
        if error_type == "TIMEOUT_ERROR":
            # More aggressive optimization for timeout issues
            if query_language == "T-SQL":
                # Reduce TOP limit more aggressively
                optimized = re.sub(r'TOP\s+(\d+)', lambda m: f'TOP {min(int(m.group(1)), 25)}', optimized, flags=re.IGNORECASE)
            else:  # DAX
                # Wrap with smaller TOPN
                if 'TOPN(' not in optimized.upper():
                    if optimized.strip().startswith('EVALUATE'):
                        content = optimized[8:].strip()
                        optimized = f'EVALUATE\nTOPN(25, {content})'
        
        elif error_type == "SCHEMA_ERROR":
            # Add defensive programming
            if query_language == "T-SQL":
                # Ensure all potential NULL columns are handled
                optimized = re.sub(r'(\w+\.\w+|\[\w+\]\.\[\w+\])', r'ISNULL(\1, \'\')', optimized, count=3)
        
        return optimized

    def _is_similar_word(self, word1: str, word2: str, threshold: float = 0.8) -> bool:
        """Check if two words are similar (for typo detection)"""
        if len(word1) < 3 or len(word2) < 3:
            return False
        
        similarity = SequenceMatcher(None, word1, word2).ratio()
        return similarity >= threshold

    async def _apply_simple_fix(self, failed_query: str, error: str, query_language: str) -> str:
        """Fallback simple fix when advanced fixing fails"""
        
        simple_fixes = {
            "T-SQL": [
                (r'\bLIMIT\s+(\d+)', r'TOP \1'),  # Replace LIMIT with TOP
                (r'SELECT\s+(\*|\w+)', r'SELECT TOP 50 \1'),  # Add TOP if missing
                (r'\bILIKE\b', 'LIKE'),  # Replace ILIKE with LIKE
            ],
            "DAX": [
                (r'^(?!EVALUATE)', r'EVALUATE '),  # Add EVALUATE if missing
                (r'\bSELECT\b.*?\bFROM\b', ''),  # Remove SQL syntax
                (r'\bWHERE\b', 'FILTER('),  # Replace WHERE with FILTER
            ]
        }
        
        fixed = failed_query
        for pattern, replacement in simple_fixes.get(query_language, []):
            fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
        
        return fixed

    async def _generate_fallback_query(self, question: str, schema_context: str, query_language: str) -> str:
        """Generate a simple fallback query when advanced generation fails"""
        
        if query_language == "T-SQL":
            # Extract first table name from schema
            table_match = re.search(r'📊 (\w+):', schema_context)
            if table_match:
                table_name = table_match.group(1)
                return f"SELECT TOP 10 * FROM [{table_name}]"
            else:
                return "SELECT TOP 10 * FROM INFORMATION_SCHEMA.TABLES"
        
        else:  # DAX
            # Extract first table name from schema
            table_match = re.search(r"'([^']+)':", schema_context)
            if table_match:
                table_name = table_match.group(1)
                return f"EVALUATE\nTOPN(10, '{table_name}')"
            else:
                return "EVALUATE {}"

    async def _generate_contextual_answer(self, question: str, query: str, data: List[Dict]) -> str:
        """Generate natural language answer with business context"""
        
        # Prepare data summary
        data_summary = {
            "row_count": len(data),
            "columns": list(data[0].keys()) if data else [],
            "sample_data": data[:3] if data else []
        }
        
        # Create context-aware prompt
        prompt = f"""Convert this database query result into a clear, business-focused answer.

USER QUESTION: {question}

QUERY EXECUTED: {query}

RESULTS SUMMARY:
- Found {data_summary['row_count']} rows
- Columns: {', '.join(data_summary['columns'])}

SAMPLE DATA:
{json.dumps(data_summary['sample_data'], indent=2, default=str)}

Please provide a clear, concise answer that:
1. Directly addresses the user's question
2. Highlights key insights from the data
3. Uses business language rather than technical jargon
4. Mentions specific numbers and findings
5. If the result is empty, explain what this means

Keep the answer conversational and informative."""

        try:
            response = await claude_service.get_response(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to generate contextual answer: {e}")
            # Fallback to basic summary
            if data_summary['row_count'] == 0:
                return f"I couldn't find any data matching your question '{question}'. This might mean the data doesn't exist in the current dataset or the criteria were too specific."
            elif data_summary['row_count'] == 1:
                return f"I found one result for your question. Here's what the data shows: {json.dumps(data_summary['sample_data'][0], default=str)}"
            else:
                return f"I found {data_summary['row_count']} results for your question. The data includes columns: {', '.join(data_summary['columns'])}. Here are the first few results: {json.dumps(data_summary['sample_data'], default=str)}"

# Singleton
enhanced_multi_agent_service = EnhancedMultiAgentService()