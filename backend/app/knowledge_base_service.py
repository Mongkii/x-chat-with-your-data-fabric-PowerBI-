import logging
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import pyodbc
from difflib import SequenceMatcher
import hashlib
import re
import time
import math
from collections import Counter

from app.fabric_service import fabric_service

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        self.table_name = "dbo.ChatKnowledgeBase"
        self.cache = {}  # In-memory cache
        self.cache_ttl = 3600  # 1 hour
        
    def _get_connection(self):
        """Get connection to knowledge base (using same Fabric connection)"""
        return fabric_service._connect_with_token()
    
    def initialize_knowledge_base(self) -> Dict:
        """Create knowledge base table if it doesn't exist"""
        try:
            conn = self._get_connection()
            if not conn:
                return {"success": False, "error": "No database connection"}
                
            cursor = conn.cursor()
            
            # Drop existing table if schema needs update
            drop_sql = f"""
            IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ChatKnowledgeBase')
            BEGIN
                -- Check if columns match expected schema
                IF NOT EXISTS (
                    SELECT * FROM sys.columns 
                    WHERE object_id = OBJECT_ID('{self.table_name}') 
                    AND name = 'query_hash'
                )
                BEGIN
                    DROP TABLE {self.table_name}
                END
            END
            """
            cursor.execute(drop_sql)
            
            # Create table with enhanced schema
            create_table_sql = f"""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ChatKnowledgeBase')
            CREATE TABLE {self.table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                category NVARCHAR(100),
                question NVARCHAR(MAX),
                question_normalized NVARCHAR(MAX),
                query_hash NVARCHAR(64),
                context NVARCHAR(MAX),
                sql_query NVARCHAR(MAX),
                dax_query NVARCHAR(MAX),
                answer NVARCHAR(MAX),
                response_type NVARCHAR(50),
                metadata NVARCHAR(MAX),
                success_count INT DEFAULT 1,
                failure_count INT DEFAULT 0,
                last_used DATETIME DEFAULT GETDATE(),
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE(),
                INDEX idx_query_hash (query_hash),
                INDEX idx_category (category),
                INDEX idx_last_used (last_used)
            )
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            
            # Create similarity function if not exists
            self._create_similarity_function(cursor)
            
            conn.close()
            
            logger.info("Knowledge base table initialized successfully")
            return {"success": True, "message": "Knowledge base initialized"}
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_similarity_function(self, cursor):
        """Create a function for text similarity (if supported by database)"""
        try:
            # This is a simplified version - in production you might use 
            # full-text search or ML-based similarity
            pass
        except:
            pass
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better matching"""
        # Convert to lowercase
        normalized = question.lower().strip()
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'how', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'can', 'shall', 'me', 'my', 'give'
        }
        
        words = normalized.split()
        words = [w for w in words if w not in stop_words]
        
        # Sort words to handle different word orders
        words.sort()
        
        return ' '.join(words)
    
    def _calculate_hash(self, question: str, category: str) -> str:
        """Calculate hash for question + category"""
        normalized = self._normalize_question(question)
        combined = f"{category}:{normalized}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def add_knowledge(self, knowledge: Dict) -> Dict:
        """Add new knowledge entry with deduplication"""
        try:
            conn = self._get_connection()
            if not conn:
                return {"success": False, "error": "No database connection"}
                
            cursor = conn.cursor()
            
            # Normalize and hash
            question = knowledge.get("question", "")
            category = knowledge.get("category", "general")
            normalized = self._normalize_question(question)
            query_hash = self._calculate_hash(question, category)
            
            # Check if similar entry exists
            check_sql = f"""
            SELECT id, success_count, failure_count
            FROM {self.table_name}
            WHERE query_hash = ? AND category = ?
            """
            
            cursor.execute(check_sql, (query_hash, category))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                update_sql = f"""
                UPDATE {self.table_name}
                SET answer = ?,
                    sql_query = ?,
                    dax_query = ?,
                    metadata = ?,
                    success_count = success_count + 1,
                    last_used = GETDATE(),
                    updated_at = GETDATE()
                WHERE id = ?
                """
                
                cursor.execute(update_sql, (
                    knowledge.get("answer"),
                    knowledge.get("sql_query"),
                    knowledge.get("dax_query"),
                    json.dumps(knowledge.get("metadata", {})),
                    existing[0]
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Updated existing knowledge entry: {existing[0]}")
                return {"success": True, "id": existing[0], "action": "updated"}
            
            else:
                # Insert new entry
                insert_sql = f"""
                INSERT INTO {self.table_name} 
                (category, question, question_normalized, query_hash, context, 
                 sql_query, dax_query, answer, response_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    category,
                    question,
                    normalized,
                    query_hash,
                    knowledge.get("context"),
                    knowledge.get("sql_query"),
                    knowledge.get("dax_query"),
                    knowledge.get("answer"),
                    knowledge.get("response_type", "text"),
                    json.dumps(knowledge.get("metadata", {}))
                ))
                
                conn.commit()
                knowledge_id = cursor.lastrowid
                conn.close()
                
                # Clear cache
                self.cache.clear()
                
                logger.info(f"Added new knowledge entry: {knowledge_id}")
                return {"success": True, "id": knowledge_id, "action": "created"}
                
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return {"success": False, "error": str(e)}
    
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                         threshold: float = 0.7) -> List[Dict]:
        """Search knowledge base with similarity matching"""
        try:
            # Check cache first
            cache_key = f"{query}:{category}"
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if datetime.now().timestamp() - cached['timestamp'] < self.cache_ttl:
                    return cached['results']
            
            conn = self._get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            # Normalize query
            normalized_query = self._normalize_question(query)
            
            # First try exact hash match
            query_hash = self._calculate_hash(query, category or "general")
            
            exact_sql = f"""
            SELECT TOP 1
                id, category, question, context, sql_query, dax_query, 
                answer, response_type, metadata, success_count, created_at
            FROM {self.table_name}
            WHERE query_hash = ?
            """
            
            params = [query_hash]
            if category:
                exact_sql += " AND category = ?"
                params.append(category)
            
            cursor.execute(exact_sql, params)
            exact_match = cursor.fetchone()
            
            if exact_match:
                # Update last used
                update_sql = f"UPDATE {self.table_name} SET last_used = GETDATE() WHERE id = ?"
                cursor.execute(update_sql, (exact_match[0],))
                conn.commit()
                
                results = [self._row_to_dict(exact_match)]
            else:
                # Fuzzy search
                search_sql = f"""
                SELECT TOP 10
                    id, category, question, context, sql_query, dax_query, 
                    answer, response_type, metadata, success_count, created_at,
                    question_normalized
                FROM {self.table_name}
                WHERE 1=1
                """
                
                params = []
                
                if category:
                    search_sql += " AND category = ?"
                    params.append(category)
                
                # Add text search conditions
                search_terms = normalized_query.split()
                for term in search_terms[:5]:  # Limit to first 5 terms
                    search_sql += " AND (question_normalized LIKE ? OR context LIKE ?)"
                    params.extend([f"%{term}%", f"%{term}%"])
                
                search_sql += " ORDER BY success_count DESC, last_used DESC"
                
                cursor.execute(search_sql, params)
                
                # Calculate similarity scores
                results = []
                for row in cursor.fetchall():
                    # Calculate similarity
                    similarity = self._calculate_similarity(
                        normalized_query,
                        row[11]  # question_normalized
                    )
                    
                    if similarity >= threshold:
                        result = self._row_to_dict(row[:11])  # Exclude normalized column
                        result['similarity'] = similarity
                        results.append(result)
                
                # Sort by similarity
                results.sort(key=lambda x: x['similarity'], reverse=True)
                results = results[:5]  # Top 5 matches
            
            conn.close()
            
            # Cache results
            self.cache[cache_key] = {
                'results': results,
                'timestamp': datetime.now().timestamp()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
            
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        return SequenceMatcher(None, text1, text2).ratio()

    def _row_to_dict(self, row: tuple) -> Dict:
        """Convert database row to dictionary"""
        return {
            "id": row[0],
            "category": row[1],
            "question": row[2],
            "context": row[3],
            "sql_query": row[4],
            "dax_query": row[5],
            "answer": row[6],
            "response_type": row[7],
            "metadata": json.loads(row[8] or "{}"),
            "success_count": row[9],
            "created_at": row[10].isoformat() if row[10] else None
        }
    
    def update_knowledge_feedback(self, knowledge_id: int, success: bool) -> Dict:
        """Update success/failure count based on user feedback"""
        try:
            conn = self._get_connection()
            if not conn:
                return {"success": False, "error": "No database connection"}
            
            cursor = conn.cursor()
            
            if success:
                update_sql = f"""
                UPDATE {self.table_name}
                SET success_count = success_count + 1,
                    last_used = GETDATE()
                WHERE id = ?
                """
            else:
                update_sql = f"""
                UPDATE {self.table_name}
                SET failure_count = failure_count + 1,
                    last_used = GETDATE()
                WHERE id = ?
                """
            
            cursor.execute(update_sql, (knowledge_id,))
            conn.commit()
            conn.close()
            
            # Clear cache
            self.cache.clear()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to update feedback: {e}")
            return {"success": False, "error": str(e)}
    
    def get_popular_queries(self, category: Optional[str] = None, 
                            limit: int = 10) -> List[Dict]:
        """Get most popular/successful queries"""
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            sql = f"""
            SELECT TOP {limit}
                id, category, question, context, sql_query, dax_query, 
                answer, response_type, metadata, success_count, created_at
            FROM {self.table_name}
            WHERE success_count > 0
            """
            
            if category:
                sql += " AND category = ? ORDER BY success_count DESC, last_used DESC"
                cursor.execute(sql, (category,))
            else:
                sql += " ORDER BY success_count DESC, last_used DESC"
                cursor.execute(sql)
            
            results = []
            for row in cursor.fetchall():
                results.append(self._row_to_dict(row))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get popular queries: {e}")
            return []

    def search_knowledge_enhanced(self, question: str, category: Optional[str] = None, 
                                  threshold: float = 0.7) -> List[Dict]:
        """Enhanced knowledge search with semantic understanding and entity matching"""
        
        # Use cache for expensive operations
        cache_key = f"{question}:{category}:{threshold}"
        if cache_key in getattr(self, '_search_cache', {}):
            cached_result = self._search_cache[cache_key]
            if time.time() - cached_result['timestamp'] < 300:  # 5-minute cache
                return cached_result['results']
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            # Extract semantic features from the question
            question_features = self._extract_comprehensive_features(question)
            
            # First try exact hash match (fastest)
            exact_matches = self._find_exact_matches(question, category, conn)
            if exact_matches:
                return exact_matches[:3]
            
            # Semantic similarity search
            similar_queries = self._find_semantic_matches(question, question_features, category, conn, threshold)
            
            # Cache the results
            if not hasattr(self, '_search_cache'):
                self._search_cache = {}
            
            self._search_cache[cache_key] = {
                'results': similar_queries,
                'timestamp': time.time()
            }
            
            # Limit cache size
            if len(self._search_cache) > 100:
                oldest_key = min(self._search_cache.keys(), 
                                 key=lambda k: self._search_cache[k]['timestamp'])
                del self._search_cache[oldest_key]
            
            return similar_queries
            
        except Exception as e:
            logger.error(f"Enhanced knowledge search failed: {e}")
            return []
    
    def _extract_comprehensive_features(self, question: str) -> Dict:
        """Extract comprehensive semantic features from a question"""
        
        question_lower = question.lower().strip()
        
        features = {
            'entities': set(),
            'operations': set(),
            'intent': self._classify_intent(question_lower),
            'time_references': set(),
            'comparison_terms': set(),
            'aggregation_terms': set(),
            'filter_terms': set(),
            'table_hints': set(),
            'question_type': self._classify_question_type(question_lower),
            'key_phrases': self._extract_key_phrases(question_lower),
            'normalized_tokens': self._get_normalized_tokens(question_lower)
        }
        
        # Business entities
        business_entities = {
            'sales', 'revenue', 'profit', 'income', 'cost', 'expense', 'margin',
            'customer', 'client', 'user', 'account', 'contact',
            'product', 'item', 'sku', 'inventory', 'stock',
            'order', 'transaction', 'purchase', 'payment', 'invoice',
            'region', 'territory', 'country', 'state', 'city', 'location',
            'category', 'type', 'group', 'segment', 'division',
            'employee', 'staff', 'person', 'team', 'department'
        }
        
        # Operations and actions
        operations = {
            'show', 'display', 'list', 'get', 'find', 'search', 'lookup',
            'count', 'sum', 'total', 'average', 'mean', 'max', 'min',
            'compare', 'analyze', 'calculate', 'compute', 'measure',
            'filter', 'where', 'having', 'group', 'sort', 'order'
        }
        
        # Time references
        time_references = {
            'today', 'yesterday', 'tomorrow', 'week', 'month', 'year', 'quarter',
            'daily', 'weekly', 'monthly', 'yearly', 'annual', 'quarterly',
            'current', 'last', 'previous', 'next', 'recent', 'latest',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            '2023', '2024', '2025'
        }
        
        # Aggregation terms
        aggregation_terms = {
            'total', 'sum', 'count', 'average', 'mean', 'median', 'mode',
            'max', 'maximum', 'min', 'minimum', 'highest', 'lowest',
            'top', 'bottom', 'best', 'worst', 'most', 'least'
        }
        
        # Comparison terms
        comparison_terms = {
            'greater', 'less', 'more', 'fewer', 'above', 'below', 'over', 'under',
            'between', 'within', 'outside', 'equals', 'different', 'same',
            'versus', 'vs', 'compared', 'against', 'than'
        }
        
        words = question_lower.split()
        for word in words:
            # Clean word
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in business_entities:
                features['entities'].add(clean_word)
            if clean_word in operations:
                features['operations'].add(clean_word)
            if clean_word in time_references:
                features['time_references'].add(clean_word)
            if clean_word in aggregation_terms:
                features['aggregation_terms'].add(clean_word)
            if clean_word in comparison_terms:
                features['comparison_terms'].add(clean_word)
        
        # Extract table hints (words that might be table names)
        potential_tables = [word for word in words if len(word) > 3 and word.isalpha()]
        features['table_hints'] = set(potential_tables[:5])  # Limit to first 5
        
        return features
    
    def _classify_intent(self, question: str) -> str:
        """Classify the main intent of the question"""
        
        if any(term in question for term in ['show', 'list', 'display', 'get', 'find']):
            return 'RETRIEVE'
        elif any(term in question for term in ['count', 'how many', 'number of']):
            return 'COUNT'
        elif any(term in question for term in ['total', 'sum', 'add up']):
            return 'SUM'
        elif any(term in question for term in ['average', 'mean', 'avg']):
            return 'AVERAGE'
        elif any(term in question for term in ['compare', 'versus', 'vs', 'difference']):
            return 'COMPARE'
        elif any(term in question for term in ['trend', 'over time', 'by month', 'by year']):
            return 'TREND'
        elif any(term in question for term in ['top', 'highest', 'best', 'maximum']):
            return 'TOP'
        elif any(term in question for term in ['bottom', 'lowest', 'worst', 'minimum']):
            return 'BOTTOM'
        elif any(term in question for term in ['filter', 'where', 'with', 'having']):
            return 'FILTER'
        elif any(term in question for term in ['group', 'by', 'category', 'segment']):
            return 'GROUP'
        else:
            return 'GENERAL'
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question being asked"""
        
        if question.startswith(('what', 'which')):
            return 'WHAT'
        elif question.startswith(('how many', 'how much')):
            return 'HOW_MANY'
        elif question.startswith('how'):
            return 'HOW'
        elif question.startswith(('when', 'what time')):
            return 'WHEN'
        elif question.startswith(('where', 'in which')):
            return 'WHERE'
        elif question.startswith(('who', 'which person')):
            return 'WHO'
        elif question.startswith('why'):
            return 'WHY'
        elif question.startswith(('show', 'display', 'list')):
            return 'COMMAND'
        else:
            return 'STATEMENT'
    
    def _extract_key_phrases(self, question: str) -> Set[str]:
        """Extract key phrases that preserve meaning"""
        
        # Common business phrase patterns
        phrase_patterns = [
            r'sales by \w+',
            r'total \w+',
            r'top \d+ \w+',
            r'average \w+',
            r'count of \w+',
            r'\w+ by month',
            r'\w+ by year',
            r'\w+ by category',
            r'last \w+ \w+',
            r'current \w+',
            r'\w+ trends?',
            r'\w+ performance',
            r'\w+ analysis'
        ]
        
        key_phrases = set()
        for pattern in phrase_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            key_phrases.update(match.lower() for match in matches)
        
        return key_phrases
    
    def _get_normalized_tokens(self, question: str) -> List[str]:
        """Get normalized tokens for text similarity"""
        
        # Remove stop words but keep business-relevant ones
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
            'shall', 'me', 'my', 'give'
        }
        
        words = re.findall(r'\b\w+\b', question.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _find_exact_matches(self, question: str, category: Optional[str], connection) -> List[Dict]:
        """Find exact or near-exact matches using hash"""
        
        normalized = self._normalize_question(question)
        query_hash = self._calculate_hash(question, category or "general")
        
        cursor = connection.cursor()
        
        try:
            sql = f"""
            SELECT TOP 3
                id, category, question, context, sql_query, dax_query, 
                answer, response_type, metadata, success_count, created_at
            FROM {self.table_name}
            WHERE query_hash = ?
            """
            
            params = [query_hash]
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            sql += " ORDER BY success_count DESC, last_used DESC"
            
            cursor.execute(sql, params)
            results = []
            
            for row in cursor.fetchall():
                result = self._row_to_dict(row)
                result['similarity'] = 1.0  # Exact match
                result['match_type'] = 'EXACT'
                results.append(result)
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Exact match search failed: {e}")
            if cursor:
                cursor.close()
            return []
    
    def _find_semantic_matches(self, question: str, question_features: Dict, 
                               category: Optional[str], connection, threshold: float) -> List[Dict]:
        """Find semantically similar queries using advanced matching"""
        
        cursor = connection.cursor()
        
        try:
            # Build search query
            sql = f"""
            SELECT TOP 20
                id, category, question, context, sql_query, dax_query, 
                answer, response_type, metadata, success_count, created_at,
                question_normalized
            FROM {self.table_name}
            WHERE success_count > 0
            """
            
            params = []
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            # Add text search conditions for key entities
            key_entities = list(question_features['entities']) + list(question_features['operations'])
            for entity in key_entities[:3]:  # Limit to first 3 entities
                sql += " AND (question_normalized LIKE ? OR context LIKE ?)"
                params.extend([f"%{entity}%", f"%{entity}%"])
            
            sql += " ORDER BY success_count DESC, last_used DESC"
            
            cursor.execute(sql, params)
            
            candidates = []
            for row in cursor.fetchall():
                candidate = self._row_to_dict(row[:11])  # Exclude normalized column
                candidate_normalized = row[11]
                
                # Calculate comprehensive similarity
                similarity = self._calculate_comprehensive_similarity(
                    question_features, candidate['question'], candidate_normalized
                )
                
                if similarity >= threshold:
                    candidate['similarity'] = similarity
                    candidate['match_type'] = self._determine_match_type(similarity)
                    candidates.append(candidate)
            
            cursor.close()
            
            # Sort by similarity and return top matches
            candidates.sort(key=lambda x: x['similarity'], reverse=True)
            return candidates[:5]
            
        except Exception as e:
            logger.error(f"Semantic match search failed: {e}")
            if cursor:
                cursor.close()
            return []
    
    def _calculate_comprehensive_similarity(self, question_features: Dict, 
                                            candidate_question: str, candidate_normalized: str) -> float:
        """Calculate comprehensive similarity score using multiple factors"""
        
        # Extract features from candidate
        candidate_features = self._extract_comprehensive_features(candidate_question)
        
        # Calculate different similarity components
        similarity_scores = {
            'intent': self._calculate_intent_similarity(question_features, candidate_features),
            'entities': self._calculate_entity_similarity(question_features, candidate_features),
            'operations': self._calculate_operation_similarity(question_features, candidate_features),
            'text': self._calculate_similarity(
                ' '.join(question_features['normalized_tokens']), 
                candidate_normalized
            ),
            'structure': self._calculate_structural_similarity(question_features, candidate_features),
            'phrases': self._calculate_phrase_similarity(question_features, candidate_features)
        }
        
        # Weighted combination of similarity scores
        weights = {
            'intent': 0.25,      # Intent is very important
            'entities': 0.25,    # Business entities are crucial
            'operations': 0.20,  # Operations matter for understanding
            'text': 0.15,        # Text similarity is still relevant
            'structure': 0.10,   # Question structure helps
            'phrases': 0.05      # Key phrases provide context
        }
        
        final_score = sum(similarity_scores[component] * weights[component] 
                          for component in weights.keys())
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def _calculate_intent_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity of question intents"""
        intent1 = features1['intent']
        intent2 = features2['intent']
        
        if intent1 == intent2:
            return 1.0
        
        # Some intents are related
        related_intents = {
            ('RETRIEVE', 'FILTER'): 0.7,
            ('COUNT', 'SUM'): 0.6,
            ('TOP', 'BOTTOM'): 0.5,
            ('AVERAGE', 'SUM'): 0.6,
            ('COMPARE', 'TREND'): 0.5
        }
        
        for (i1, i2), score in related_intents.items():
            if (intent1, intent2) == (i1, i2) or (intent1, intent2) == (i2, i1):
                return score
        
        return 0.0
    
    def _calculate_entity_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity of business entities"""
        entities1 = features1['entities']
        entities2 = features2['entities']
        
        if not entities1 and not entities2:
            return 1.0
        
        if not entities1 or not entities2:
            return 0.0
        
        intersection = entities1.intersection(entities2)
        union = entities1.union(entities2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_operation_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity of operations"""
        ops1 = features1['operations']
        ops2 = features2['operations']
        
        if not ops1 and not ops2:
            return 1.0
        
        if not ops1 or not ops2:
            return 0.3  # Some operations might be implicit
        
        intersection = ops1.intersection(ops2)
        union = ops1.union(ops2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_structural_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity of question structure"""
        structure_score = 0.0
        
        # Question type similarity
        if features1['question_type'] == features2['question_type']:
            structure_score += 0.4
        
        # Time reference similarity
        time1 = features1['time_references']
        time2 = features2['time_references']
        if time1 and time2:
            time_overlap = len(time1.intersection(time2)) / len(time1.union(time2))
            structure_score += 0.3 * time_overlap
        elif not time1 and not time2:
            structure_score += 0.3
        
        # Aggregation similarity
        agg1 = features1['aggregation_terms']
        agg2 = features2['aggregation_terms']
        if agg1 and agg2:
            agg_overlap = len(agg1.intersection(agg2)) / len(agg1.union(agg2))
            structure_score += 0.3 * agg_overlap
        elif not agg1 and not agg2:
            structure_score += 0.3
        
        return min(structure_score, 1.0)
    
    def _calculate_phrase_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity of key phrases"""
        phrases1 = features1['key_phrases']
        phrases2 = features2['key_phrases']
        
        if not phrases1 and not phrases2:
            return 1.0
        
        if not phrases1 or not phrases2:
            return 0.0
        
        intersection = phrases1.intersection(phrases2)
        union = phrases1.union(phrases2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _determine_match_type(self, similarity: float) -> str:
        """Determine the type of match based on similarity score"""
        if similarity >= 0.95:
            return "EXACT"
        elif similarity >= 0.85:
            return "VERY_SIMILAR"
        elif similarity >= 0.75:
            return "SIMILAR"
        elif similarity >= 0.65:
            return "SOMEWHAT_SIMILAR"
        else:
            return "LOOSELY_RELATED"
    
    def get_knowledge_analytics(self) -> Dict:
        """Get analytics about the knowledge base performance"""
        try:
            conn = self._get_connection()
            if not conn:
                return {"error": "No database connection"}
            
            cursor = conn.cursor()
            
            # Basic statistics (Adjusted for T-SQL syntax)
            stats_sql = f"""
            SELECT 
                COUNT(*),
                COUNT(DISTINCT category),
                AVG(CAST(success_count AS FLOAT)),
                MAX(success_count),
                SUM(CASE WHEN success_count > 5 THEN 1 ELSE 0 END)
            FROM {self.table_name}
            """
            
            cursor.execute(stats_sql)
            stats = cursor.fetchone()
            
            # Category breakdown
            category_sql = f"""
            SELECT category, COUNT(*) as count, AVG(CAST(success_count AS FLOAT)) as avg_success
            FROM {self.table_name}
            GROUP BY category
            ORDER BY count DESC
            """
            
            cursor.execute(category_sql)
            categories = cursor.fetchall()
            
            # Recent performance (Adjusted for T-SQL syntax)
            recent_sql = f"""
            SELECT TOP 30
                CAST(created_at AS DATE) as entry_date,
                COUNT(*) as queries_added,
                AVG(CAST(success_count AS FLOAT)) as avg_success
            FROM {self.table_name}
            WHERE created_at >= DATEADD(day, -30, GETDATE())
            GROUP BY CAST(created_at AS DATE)
            ORDER BY entry_date DESC
            """
            
            cursor.execute(recent_sql)
            recent_performance = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "total_entries": stats[0] if stats else 0,
                "unique_categories": stats[1] if stats else 0,
                "average_success_rate": round(stats[2], 2) if stats and stats[2] else 0,
                "max_success_rate": stats[3] if stats else 0,
                "highly_successful_queries": stats[4] if stats else 0,
                "categories": [
                    {"name": cat[0], "count": cat[1], "avg_success": round(cat[2], 2) if cat[2] else 0}
                    for cat in categories
                ],
                "recent_performance": [
                    {"date": perf[0].isoformat(), "queries_added": perf[1], "avg_success": round(perf[2], 2) if perf[2] else 0}
                    for perf in recent_performance
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge analytics: {e}")
            return {"error": str(e)}

    def cleanup_old_entries(self, days: int = 90) -> Dict:
        """Clean up old, unused entries"""
        try:
            conn = self._get_connection()
            if not conn:
                return {"success": False, "error": "No database connection"}
            
            cursor = conn.cursor()
            
            # Delete entries not used in X days with low success rate
            delete_sql = f"""
            DELETE FROM {self.table_name}
            WHERE last_used < DATEADD(day, -{days}, GETDATE())
            AND success_count < 3
            AND failure_count > success_count
            """
            
            cursor.execute(delete_sql)
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # Clear cache
            self.cache.clear()
            
            return {"success": True, "deleted": deleted_count}
            
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
            return {"success": False, "error": str(e)}
    
    def get_all_knowledge(self, category: Optional[str] = None) -> List[Dict]:
        """Get all knowledge entries"""
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            if category:
                sql = f"""
                SELECT 
                    id, category, question, context, sql_query, dax_query, 
                    answer, response_type, metadata, success_count, created_at
                FROM {self.table_name} 
                WHERE category = ? 
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (category,))
            else:
                sql = f"""
                SELECT 
                    id, category, question, context, sql_query, dax_query, 
                    answer, response_type, metadata, success_count, created_at
                FROM {self.table_name} 
                ORDER BY created_at DESC
                """
                cursor.execute(sql)
            
            results = []
            for row in cursor.fetchall():
                results.append(self._row_to_dict(row))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get knowledge: {e}")
            return []
    
    def export_knowledge(self, category: Optional[str] = None) -> Dict:
        """Export knowledge base for backup or sharing"""
        try:
            entries = self.get_all_knowledge(category)
            
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "category": category,
                "entries": entries,
                "total": len(entries)
            }
            
            return {
                "success": True,
                "data": export_data
            }
            
        except Exception as e:
            logger.error(f"Failed to export knowledge: {e}")
            return {"success": False, "error": str(e)}
    
    def import_knowledge(self, import_data: Dict) -> Dict:
        """Import knowledge entries from export"""
        try:
            entries = import_data.get("entries", [])
            imported = 0
            errors = []
            
            for entry in entries:
                result = self.add_knowledge(entry)
                if result.get("success"):
                    imported += 1
                else:
                    errors.append(f"Failed to import: {entry.get('question', 'Unknown')}")
            
            return {
                "success": True,
                "imported": imported,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to import knowledge: {e}")
            return {"success": False, "error": str(e)}

# Singleton
knowledge_base_service = KnowledgeBaseService()