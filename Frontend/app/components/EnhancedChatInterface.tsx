// Complete EnhancedChatInterface.tsx - Phase 3 Final Version
// Replace your existing EnhancedChatInterface.tsx with this complete version

'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

// Note: You'll need to create these components from the previous artifacts
// For now, I'll include simplified versions to make this complete
interface VirtualizedDataTableProps {
  data: any[];
  columns: string[];
  maxHeight?: number;
  showExportButton?: boolean;
}

const VirtualizedDataTable: React.FC<VirtualizedDataTableProps> = ({ 
  data, 
  columns, 
  maxHeight = 400,
  showExportButton = true 
}) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [filterText, setFilterText] = useState('');

  const processedData = data.filter(row =>
    filterText ? Object.values(row).some(value =>
      String(value).toLowerCase().includes(filterText.toLowerCase())
    ) : true
  ).sort((a, b) => {
    if (!sortConfig) return 0;
    const aVal = a[sortConfig.key];
    const bVal = b[sortConfig.key];
    if (aVal === bVal) return 0;
    const comparison = aVal < bVal ? -1 : 1;
    return sortConfig.direction === 'desc' ? comparison * -1 : comparison;
  });

  const exportToCSV = () => {
    const csvContent = [
      columns.join(','),
      ...processedData.map(row =>
        columns.map(col => `"${String(row[col] || '').replace(/"/g, '""')}"`).join(',')
      )
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `data_export_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ border: '1px solid #dee2e6', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'white' }}>
      <div style={{ padding: '12px', backgroundColor: '#f8f9fa', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>📊 {processedData.length} rows</span>
          <input
            type="text"
            placeholder="Filter data..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{ padding: '4px 8px', fontSize: '0.875rem', border: '1px solid #ced4da', borderRadius: '4px' }}
          />
        </div>
        {showExportButton && (
          <button onClick={exportToCSV} style={{ padding: '4px 12px', fontSize: '0.875rem', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            📥 Export CSV
          </button>
        )}
      </div>
      
      <div style={{ maxHeight, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead style={{ backgroundColor: '#e9ecef', position: 'sticky', top: 0 }}>
            <tr>
              {columns.map(col => (
                <th
                  key={col}
                  onClick={() => setSortConfig(current => ({
                    key: col,
                    direction: current?.key === col && current.direction === 'asc' ? 'desc' : 'asc'
                  }))}
                  style={{ padding: '12px', borderBottom: '2px solid #dee2e6', cursor: 'pointer', textAlign: 'left', fontWeight: 'bold' }}
                >
                  {col} {sortConfig?.key === col ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '↕'}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {processedData.slice(0, 200).map((row, idx) => (
              <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f8f9fa' }}>
                {columns.map(col => (
                  <td key={col} style={{ padding: '8px 12px', borderBottom: '1px solid #e9ecef', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={String(row[col] || '')}>
                    {String(row[col] || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div style={{ padding: '8px 12px', backgroundColor: '#f8f9fa', borderTop: '1px solid #dee2e6', fontSize: '0.75rem', color: '#6c757d' }}>
        Showing {Math.min(processedData.length, 200)} of {data.length} rows
      </div>
    </div>
  );
};

const IntelligentVisualization: React.FC<{ data: any[]; question?: string; title?: string }> = ({ 
  data, 
  question = '', 
  title 
}) => {
  // Simplified visualization component - you can enhance this with recharts
  const [chartType, setChartType] = useState('bar');
  
  const recommendChartType = () => {
    const questionLower = question.toLowerCase();
    if (questionLower.includes('trend') || questionLower.includes('over time')) return 'line';
    if (questionLower.includes('distribution') || questionLower.includes('breakdown')) return 'pie';
    if (questionLower.includes('correlation') || questionLower.includes('versus')) return 'scatter';
    return 'bar';
  };

  useEffect(() => {
    setChartType(recommendChartType());
  }, [question]);

  return (
    <div style={{ border: '1px solid #dee2e6', borderRadius: '8px', backgroundColor: 'white', padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0 }}>{title || 'Data Visualization'}</h4>
        <div style={{ display: 'flex', gap: '4px' }}>
          {['bar', 'line', 'pie'].map(type => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              style={{
                padding: '4px 8px',
                fontSize: '0.75rem',
                backgroundColor: chartType === type ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {type}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
        <div style={{ textAlign: 'center', color: '#6c757d' }}>
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📊</div>
          <div>{chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart</div>
          <div style={{ fontSize: '0.875rem', marginTop: '4px' }}>{data.length} data points</div>
          <div style={{ fontSize: '0.75rem', marginTop: '8px', fontStyle: 'italic' }}>
            Chart would render here with recharts library
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#6c757d', textAlign: 'center' }}>
        🤖 AI Recommended: {recommendChartType()} chart for this question
      </div>
    </div>
  );
};

// ** NEW COMPONENT ADDED **
const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
  return (
    <ReactMarkdown
      components={{
        // Custom styling for markdown elements
        h1: ({ children }) => (
          <h1 style={{ 
            fontSize: '1.25rem', 
            fontWeight: 'bold', 
            margin: '1rem 0 0.5rem 0',
            color: '#1a202c'
          }}>
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 style={{ 
            fontSize: '1.1rem', 
            fontWeight: 'bold', 
            margin: '0.75rem 0 0.5rem 0',
            color: '#2d3748'
          }}>
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 style={{ 
            fontSize: '1rem', 
            fontWeight: 'bold', 
            margin: '0.5rem 0 0.25rem 0',
            color: '#4a5568'
          }}>
            {children}
          </h3>
        ),
        strong: ({ children }) => (
          <strong style={{ 
            fontWeight: 'bold',
            color: '#2b6cb0'
          }}>
            {children}
          </strong>
        ),
        em: ({ children }) => (
          <em style={{ 
            fontStyle: 'italic',
            color: '#2d3748'
          }}>
            {children}
          </em>
        ),
        p: ({ children }) => (
          <p style={{ 
            margin: '0.5rem 0',
            lineHeight: '1.6'
          }}>
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul style={{ 
            margin: '0.5rem 0',
            paddingLeft: '1.5rem',
            lineHeight: '1.6'
          }}>
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol style={{ 
            margin: '0.5rem 0',
            paddingLeft: '1.5rem',
            lineHeight: '1.6'
          }}>
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li style={{ 
            margin: '0.25rem 0'
          }}>
            {children}
          </li>
        ),
        code: ({ children, className }) => {
          const isInline = !className;
          
          if (isInline) {
            return (
              <code style={{
                backgroundColor: '#f7fafc',
                padding: '0.125rem 0.25rem',
                borderRadius: '0.25rem',
                fontSize: '0.875rem',
                fontFamily: 'Monaco, Consolas, monospace',
                border: '1px solid #e2e8f0'
              }}>
                {children}
              </code>
            );
          }
          
          return (
            <pre style={{
              backgroundColor: '#f7fafc',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              fontFamily: 'Monaco, Consolas, monospace',
              border: '1px solid #e2e8f0',
              overflow: 'auto',
              margin: '0.5rem 0'
            }}>
              <code>{children}</code>
            </pre>
          );
        },
        blockquote: ({ children }) => (
          <blockquote style={{
            borderLeft: '4px solid #3182ce',
            paddingLeft: '1rem',
            margin: '0.5rem 0',
            fontStyle: 'italic',
            color: '#4a5568',
            backgroundColor: '#f7fafc',
            padding: '0.5rem 1rem',
            borderRadius: '0 0.25rem 0.25rem 0'
          }}>
            {children}
          </blockquote>
        ),
        // Handle tables
        table: ({ children }) => (
          <div style={{ overflow: 'auto', margin: '0.5rem 0' }}>
            <table style={{
              borderCollapse: 'collapse',
              width: '100%',
              fontSize: '0.875rem',
              border: '1px solid #e2e8f0'
            }}>
              {children}
            </table>
          </div>
        ),
        th: ({ children }) => (
          <th style={{
            border: '1px solid #e2e8f0',
            padding: '0.5rem',
            backgroundColor: '#f7fafc',
            fontWeight: 'bold',
            textAlign: 'left'
          }}>
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td style={{
            border: '1px solid #e2e8f0',
            padding: '0.5rem'
          }}>
            {children}
          </td>
        ),
        // Handle links
        a: ({ children, href }) => (
          <a 
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#3182ce',
              textDecoration: 'underline'
            }}
          >
            {children}
          </a>
        )
      }}
    >
      {content}
    </ReactMarkdown>
  );
};


interface Message {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  query?: string;
  data?: any[];
  thinking?: string[];
  queryAttempts?: {
    query: string;
    success: boolean;
    error?: string;
    attempt: number;
    duration?: number;
    row_count?: number;
  }[];
  executionTime?: number;
  queryLanguage?: string;
  success?: boolean;
  visualization?: {
    enabled: boolean;
    type?: string;
    config?: any;
  };
}

interface EnhancedChatInterfaceProps {
  connectionType: 'sql' | 'semantic_model' | null;
}

interface SuggestedQuestion {
  text: string;
  category: string;
  complexity: 'simple' | 'moderate' | 'complex';
}

export default function EnhancedChatInterface({ connectionType }: EnhancedChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: `🚀 Welcome to your AI Data Analysis Assistant! I'm ready to help you explore your ${connectionType === 'sql' ? 'Microsoft Fabric database' : 'Power BI semantic model'} with intelligent insights and visualizations.`,
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationContext, setConversationContext] = useState<string[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [autoVisualize, setAutoVisualize] = useState(true);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load suggested questions
  useEffect(() => {
    loadSuggestedQuestions();
    checkSystemHealth();
  }, [connectionType]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSuggestedQuestions = async () => {
    try {
      const questions: SuggestedQuestion[] = connectionType === 'sql' ? [
        { text: "Show me the top 10 customers by total revenue", category: "Revenue Analysis", complexity: "simple" },
        { text: "What are the sales trends by month for this year?", category: "Time Analysis", complexity: "moderate" },
        { text: "Compare product performance across different regions", category: "Comparison", complexity: "moderate" },
        { text: "Identify the most profitable product categories", category: "Profitability", complexity: "simple" },
        { text: "Analyze customer churn patterns over time", category: "Customer Analysis", complexity: "complex" },
        { text: "Show sales distribution by geographic region", category: "Geographic", complexity: "simple" }
      ] : [
        { text: "What are the key measures available in this model?", category: "Model Exploration", complexity: "simple" },
        { text: "Show me sales performance by product category", category: "Sales Analysis", complexity: "simple" },
        { text: "Compare this year's revenue to last year", category: "Comparison", complexity: "moderate" },
        { text: "What's the relationship between sales and customer satisfaction?", category: "Correlation", complexity: "complex" },
        { text: "Display the top performing regions by revenue", category: "Performance", complexity: "simple" },
        { text: "Analyze trends in customer acquisition over time", category: "Trends", complexity: "moderate" }
      ];
      
      setSuggestedQuestions(questions);
    } catch (error) {
      console.error('Failed to load suggested questions:', error);
    }
  };

  const checkSystemHealth = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/system-health`);
      if (response.data.success) {
        setSystemHealth(response.data.health);
      }
    } catch (error) {
      console.error('Failed to check system health:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const question = messageText || input;
    if (!question.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: question,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageText) setInput('');
    setLoading(true);
    setShowSuggestions(false);

    // Add thinking placeholder
    const thinkingId = Date.now() + 1;
    const thinkingMessage: Message = {
      id: thinkingId,
      text: '🤔 Analyzing your question...',
      sender: 'assistant',
      timestamp: new Date(),
      thinking: ['🚀 Starting AI analysis...'],
      queryAttempts: []
    };

    setMessages(prev => [...prev, thinkingMessage]);

    try {
      // Enhanced request with visualization preference
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/chat/unified`, {
        question: question,
        connection_type: connectionType,
        context_history: conversationContext,
        enable_visualization: autoVisualize,
        response_format: 'enhanced'
      });

      const result = response.data;

      // Determine if we should auto-generate visualization
      const shouldVisualize = autoVisualize && 
                              result.success && 
                              result.data && 
                              result.data.length > 0 &&
                              result.data.length <= 1000 && // Don't visualize very large datasets
                              isVisualizableQuestion(question);

      // Update the thinking message with complete result
      setMessages(prev => prev.map(msg => 
        msg.id === thinkingId ? {
          ...msg,
          text: result.answer || 'Analysis completed',
          query: result.query,
          data: result.data,
          thinking: result.thinking || ['✅ Analysis completed'],
          queryAttempts: result.query_attempts || [],
          executionTime: result.execution_time,
          queryLanguage: result.query_language,
          success: result.success,
          visualization: {
            enabled: shouldVisualize,
            type: shouldVisualize ? 'auto' : undefined
          }
        } : msg
      ));

      // Update conversation context
      if (result.success && result.query) {
        const contextEntry = `Q: ${question}\n${result.query_language || 'Query'}: ${result.query}`;
        setConversationContext(prev => [...prev.slice(-2), contextEntry]);
      }

      // Log performance metrics
      if (result.success) {
        console.log(`✅ Query successful: ${result.total_rows} rows in ${result.execution_time?.toFixed(2)}s`);
      } else {
        console.log(`❌ Query failed: ${result.answer}`);
      }

    } catch (error: any) {
      console.error('Enhanced chat error:', error);
      
      setMessages(prev => prev.map(msg => 
        msg.id === thinkingId ? {
          ...msg,
          text: 'Sorry, I encountered an error while analyzing your question. Please try again.',
          thinking: [
            '❌ Error occurred during analysis',
            `Error details: ${error.response?.data?.detail || error.message}`,
            'Please check your connection and try again.'
          ],
          success: false
        } : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  const isVisualizableQuestion = (question: string): boolean => {
    const visualKeywords = [
      'show', 'display', 'chart', 'graph', 'plot', 'trend', 'distribution',
      'top', 'compare', 'by region', 'by category', 'over time', 'breakdown'
    ];
    
    return visualKeywords.some(keyword => 
      question.toLowerCase().includes(keyword)
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const useSuggestedQuestion = (question: string) => {
    setInput(question);
    setShowSuggestions(false);
  };

  const renderMessage = (message: Message) => (
    <div
      key={message.id}
      style={{
        marginBottom: '1.5rem',
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
      }}
    >
      <div style={{
        maxWidth: '85%',
        padding: '1rem',
        borderRadius: '12px',
        backgroundColor: message.sender === 'user' ? '#007bff' : 'white',
        color: message.sender === 'user' ? 'white' : 'black',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        border: message.success === false ? '2px solid #ff6b6b' : 
                message.success === true ? '2px solid #51cf66' : '1px solid #e9ecef'
      }}>
        {/* ** UPDATED: Render markdown for assistant messages, plain text for user messages ** */}
        <div style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>
          {message.sender === 'assistant' ? (
            <MarkdownRenderer content={message.text} />
          ) : (
            message.text
          )}
        </div>
        
        {/* Enhanced execution summary */}
        {message.success && message.executionTime && (
          <div style={{ 
            fontSize: '0.8rem', 
            opacity: 0.9, 
            marginTop: '0.75rem',
            padding: '0.5rem',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            borderRadius: '6px',
            border: '1px solid rgba(40, 167, 69, 0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span>✅</span>
            <span>
              Query executed in {message.executionTime.toFixed(2)}s
              {message.data && ` • ${message.data.length.toLocaleString()} rows returned`}
              {message.queryLanguage && ` • ${message.queryLanguage}`}
            </span>
          </div>
        )}
        
        {/* Show Thinking Process */}
        {message.thinking && message.thinking.length > 0 && (
          <details style={{ marginTop: '0.75rem' }}>
            <summary style={{ 
              cursor: 'pointer', 
              fontSize: '0.85rem', 
              opacity: 0.8,
              fontWeight: 'bold',
              padding: '0.25rem',
              borderRadius: '4px',
              backgroundColor: 'rgba(0,0,0,0.05)'
            }}>
              🧠 AI Thinking Process ({message.thinking.length} steps)
            </summary>
            <div style={{ 
              fontSize: '0.8rem', 
              backgroundColor: '#f0f8ff', 
              padding: '0.75rem',
              borderRadius: '6px',
              marginTop: '0.5rem',
              border: '1px solid #e6f3ff',
              maxHeight: '250px',
              overflowY: 'auto'
            }}>
              {message.thinking.map((step, idx) => (
                <div key={idx} style={{ 
                  marginBottom: '0.5rem',
                  paddingLeft: '0.75rem',
                  borderLeft: '3px solid #007bff',
                  lineHeight: '1.4'
                }}>
                  {step}
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Enhanced Query Attempts */}
        {message.queryAttempts && message.queryAttempts.length > 0 && (
          <details style={{ marginTop: '0.75rem' }}>
            <summary style={{ 
              cursor: 'pointer', 
              fontSize: '0.85rem', 
              opacity: 0.8,
              fontWeight: 'bold',
              padding: '0.25rem',
              borderRadius: '4px',
              backgroundColor: 'rgba(0,0,0,0.05)'
            }}>
              🔧 Query Development ({message.queryAttempts.length} attempts)
            </summary>
            <div style={{ marginTop: '0.5rem' }}>
              {message.queryAttempts.map((attempt, idx) => (
                <div key={idx} style={{
                  marginBottom: '0.75rem',
                  padding: '0.75rem',
                  backgroundColor: attempt.success ? '#f0fff4' : '#fff5f5',
                  border: `1px solid ${attempt.success ? '#c6f6d5' : '#fed7d7'}`,
                  borderRadius: '6px'
                }}>
                  <div style={{ 
                    fontSize: '0.8rem', 
                    fontWeight: 'bold', 
                    marginBottom: '0.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <span>
                      {attempt.success ? '✅' : '❌'} Attempt {attempt.attempt}
                    </span>
                    <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                      {attempt.duration && `${attempt.duration.toFixed(2)}s`}
                      {attempt.row_count !== undefined && ` • ${attempt.row_count} rows`}
                    </span>
                  </div>
                  <pre style={{ 
                    fontSize: '0.75rem', 
                    margin: '0 0 0.5rem 0',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'Monaco, Consolas, monospace',
                    backgroundColor: 'rgba(0,0,0,0.05)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    overflow: 'auto'
                  }}>
                    {attempt.query}
                  </pre>
                  {attempt.error && (
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: '#e53e3e', 
                      fontStyle: 'italic',
                      backgroundColor: 'rgba(229, 62, 62, 0.1)',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px'
                    }}>
                      <strong>Error:</strong> {attempt.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Final Successful Query */}
        {message.query && (
          <details style={{ marginTop: '0.75rem' }}>
            <summary style={{ 
              cursor: 'pointer', 
              fontSize: '0.85rem', 
              opacity: 0.8,
              fontWeight: 'bold',
              padding: '0.25rem',
              borderRadius: '4px',
              backgroundColor: 'rgba(0,0,0,0.05)'
            }}>
              📝 Final {message.queryLanguage || 'Query'}
            </summary>
            <pre style={{ 
              fontSize: '0.8rem', 
              backgroundColor: '#f8f9fa', 
              padding: '0.75rem',
              borderRadius: '6px',
              marginTop: '0.5rem',
              overflowX: 'auto',
              color: '#333',
              fontFamily: 'Monaco, Consolas, monospace',
              border: '1px solid #dee2e6'
            }}>
              {message.query}
            </pre>
          </details>
        )}

        {/* Data Visualization */}
        {message.visualization?.enabled && message.data && message.data.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <IntelligentVisualization
              data={message.data}
              question={message.text}
              title="Auto-Generated Visualization"
            />
          </div>
        )}

        {/* Enhanced Data Table */}
        {message.data && message.data.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <VirtualizedDataTable
              data={message.data}
              columns={Object.keys(message.data[0])}
              maxHeight={350}
              showExportButton={true}
            />
          </div>
        )}
        
        {/* Timestamp */}
        <div style={{
          fontSize: '0.75rem',
          marginTop: '0.75rem',
          opacity: 0.7,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{message.timestamp.toLocaleTimeString()}</span>
          {message.executionTime && (
            <span>⚡ {message.executionTime.toFixed(2)}s</span>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '800px',
      border: '1px solid #dee2e6',
      borderRadius: '12px',
      overflow: 'hidden',
      backgroundColor: 'white'
    }}>
      {/* Enhanced Header */}
      <div style={{
        padding: '1rem',
        backgroundColor: '#f8f9fa',
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
            🤖 AI Data Assistant
          </span>
          <span style={{ fontSize: '0.9rem', color: '#666' }}>
            {connectionType === 'sql' ? 'Microsoft Fabric T-SQL' : 'Power BI DAX'} • Enhanced Mode
          </span>
          {systemHealth && (
            <div style={{
              padding: '0.25rem 0.5rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              backgroundColor: systemHealth.overall_health.score > 80 ? '#d4edda' : '#fff3cd',
              color: systemHealth.overall_health.score > 80 ? '#155724' : '#856404'
            }}>
              Health: {systemHealth.overall_health.score}/100
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
            <input
              type="checkbox"
              checked={autoVisualize}
              onChange={(e) => setAutoVisualize(e.target.checked)}
            />
            Auto-visualize
          </label>
          
          <button
            onClick={() => setShowSuggestions(!showSuggestions)}
            style={{
              padding: '0.25rem 0.5rem',
              fontSize: '0.75rem',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {showSuggestions ? 'Hide' : 'Show'} Suggestions
          </button>
          
          {conversationContext.length > 0 && (
            <button
              onClick={() => setConversationContext([])}
              style={{
                padding: '0.25rem 0.5rem',
                fontSize: '0.75rem',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              title="Clear conversation context"
            >
              🗑️ Clear Context
            </button>
          )}
        </div>
      </div>

      {/* Suggested Questions */}
      {showSuggestions && suggestedQuestions.length > 0 && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#e3f2fd',
          borderBottom: '1px solid #dee2e6'
        }}>
          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', fontWeight: 'bold' }}>
            💡 Suggested Questions
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '0.5rem'
          }}>
            {suggestedQuestions.slice(0, 6).map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => useSuggestedQuestion(suggestion.text)}
                style={{
                  padding: '0.75rem',
                  textAlign: 'left',
                  backgroundColor: 'white',
                  border: '1px solid #bbdefb',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0f8ff';
                  e.currentTarget.style.borderColor = '#2196f3';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                  e.currentTarget.style.borderColor = '#bbdefb';
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                  {suggestion.text}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#666', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{suggestion.category}</span>
                  <span style={{
                    padding: '0.125rem 0.375rem',
                    borderRadius: '8px',
                    backgroundColor: suggestion.complexity === 'simple' ? '#d4edda' : 
                                     suggestion.complexity === 'moderate' ? '#fff3cd' : '#f8d7da',
                    color: suggestion.complexity === 'simple' ? '#155724' : 
                           suggestion.complexity === 'moderate' ? '#856404' : '#721c24'
                  }}>
                    {suggestion.complexity}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        backgroundColor: '#fafbfc'
      }}>
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
        
        {loading && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '1rem'
          }}>
            <div style={{
              maxWidth: '80%',
              padding: '1rem',
              borderRadius: '12px',
              backgroundColor: '#fff3cd',
              border: '1px solid #ffeaa7',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                border: '2px solid #f39c12',
                borderTop: '2px solid transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <span style={{ fontSize: '0.9rem' }}>
                AI is analyzing your question...
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Input Area */}
      <div style={{
        padding: '1rem',
        backgroundColor: 'white',
        borderTop: '1px solid #dee2e6'
      }}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask about your ${connectionType === 'sql' ? 'Microsoft Fabric data' : 'Power BI model'}... (Press Enter to send, Shift+Enter for new line)`}
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '16px',
                border: '2px solid #dee2e6',
                borderRadius: '8px',
                resize: 'none',
                minHeight: '50px',
                maxHeight: '120px',
                fontFamily: 'inherit',
                outline: 'none',
                transition: 'border-color 0.2s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = '#007bff'}
              onBlur={(e) => e.target.style.borderColor = '#dee2e6'}
              rows={1}
            />
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: loading || !input.trim() ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              minHeight: '50px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {loading ? '⏳' : '🚀'}
            {loading ? 'Analyzing...' : 'Send'}
          </button>
        </div>
        
        <div style={{ 
          fontSize: '0.75rem', 
          color: '#666', 
          marginTop: '0.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>
            💡 Enhanced AI with auto-visualization and intelligent error correction
          </span>
          {conversationContext.length > 0 && (
            <span>
              💬 Context: {conversationContext.length} previous queries
            </span>
          )}
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}