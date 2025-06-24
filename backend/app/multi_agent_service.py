import logging
from typing import Dict, List, Optional
import json
from app.claude_service import claude_service
from app.fabric_service import fabric_service
from app.auth_service import auth_service

logger = logging.getLogger(__name__)

class MultiAgentService:
    def __init__(self):
        self.schema_cache = None
        
    async def refresh_schema(self):
        """Refresh the schema cache"""
        result = fabric_service.discover_schema()
        if result.get("success"):
            self.schema_cache = result.get("tables", {})
            logger.info(f"Schema cached with {len(self.schema_cache)} tables")
        return result
    
    async def manager_agent(self, user_question: str) -> Dict:
        """Manager Claude: Understands the question and creates a plan"""
        if not self.schema_cache:
            await self.refresh_schema()
        
        # Build context about available tables
        schema_context = "Available tables and columns:\n"
        for table_name, table_info in self.schema_cache.items():
            columns = [col["name"] for col in table_info["columns"]]
            schema_context += f"\n{table_name}: {', '.join(columns)}"
        
        manager_prompt = f"""You are a data analyst manager. A user asked: "{user_question}"

{schema_context}

Your task:
1. Understand what data the user needs
2. Identify which tables and columns to query
3. Create a plan for the worker

Respond in JSON format:
{{
    "interpretation": "what the user wants",
    "tables_needed": ["table1", "table2"],
    "sql_query": "the SQL query to answer the question",
    "explanation": "how this query answers the question"
}}"""

        response = await claude_service.get_response(manager_prompt)
        
        try:
            # Parse Claude's response as JSON
            # Sometimes Claude includes markdown, so we need to extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: try to extract SQL from response
                sql_start = response.upper().find('SELECT')
                if sql_start >= 0:
                    sql_end = response.find(';', sql_start)
                    sql_query = response[sql_start:sql_end].strip()
                    return {
                        "interpretation": user_question,
                        "sql_query": sql_query,
                        "explanation": "Extracted SQL from response"
                    }
        except:
            logger.error(f"Failed to parse manager response: {response}")
        
        return {
            "interpretation": user_question,
            "sql_query": None,
            "error": "Failed to generate query plan"
        }
    
    async def worker_agent(self, task: Dict) -> Dict:
        """Worker Claude: Executes the SQL query and processes results"""
        sql_query = task.get("sql_query")
        
        if not sql_query:
            return {"error": "No SQL query provided"}
        
        # Execute the query
        logger.info(f"Executing query: {sql_query}")
        result = fabric_service.execute_query(sql_query)
        
        if not result.get("success"):
            return {"error": f"Query failed: {result.get('error')}"}
        
        return {
            "success": True,
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0)
        }
    
    async def answer_question(self, user_question: str) -> Dict:
        """Complete flow: question -> plan -> execute -> answer"""
        logger.info(f"Processing question: {user_question}")
        
        # Step 1: Manager creates plan
        plan = await self.manager_agent(user_question)
        
        if plan.get("error"):
            return {
                "answer": f"I couldn't understand how to answer your question: {plan.get('error')}",
                "success": False
            }
        
        # Step 2: Worker executes plan
        if plan.get("sql_query"):
            execution_result = await self.worker_agent(plan)
            
            if execution_result.get("success"):
                # Step 3: Format the answer
                data = execution_result.get("data", [])
                
                # Create a natural language answer
                answer_prompt = f"""The user asked: "{user_question}"

You ran this SQL query:
{plan.get('sql_query')}

The query returned {len(data)} rows. Here's the data:
{json.dumps(data[:10], indent=2)}

Please provide a clear, natural language answer to the user's question based on this data."""

                final_answer = await claude_service.get_response(answer_prompt)
                
                return {
                    "answer": final_answer,
                    "sql_query": plan.get("sql_query"),
                    "data": data,
                    "row_count": execution_result.get("row_count"),
                    "success": True
                }
            else:
                return {
                    "answer": f"I understood your question but couldn't execute the query: {execution_result.get('error')}",
                    "sql_query": plan.get("sql_query"),
                    "success": False
                }
        else:
            return {
                "answer": "I couldn't generate a SQL query for your question. Please try rephrasing it.",
                "success": False
            }

# Create singleton
multi_agent_service = MultiAgentService()