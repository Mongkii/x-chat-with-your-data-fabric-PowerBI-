'use client';

import { useState } from 'react';
import axios from 'axios';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  sqlQuery?: string;
  data?: any[];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm Claude. I can help you analyze your data. What would you like to know?",
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Use the data-aware endpoint
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/chat/data-query`,
        { message: input }
      );

      const assistantMessage: Message = {
        id: messages.length + 2,
        text: response.data.response,
        sender: 'assistant',
        timestamp: new Date(),
        sqlQuery: response.data.sql_query,
        data: response.data.data
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error. Please make sure you are connected to Fabric.',
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '600px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        backgroundColor: '#f5f5f5'
      }}>
        {messages.map(message => (
          <div
            key={message.id}
            style={{
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '70%',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              backgroundColor: message.sender === 'user' ? '#0070f3' : 'white',
              color: message.sender === 'user' ? 'white' : 'black',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontSize: '0.9rem' }}>{message.text}</div>
              
              {/* Show SQL query if available */}
              {message.sqlQuery && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ cursor: 'pointer', fontSize: '0.8rem', opacity: 0.7 }}>
                    View SQL Query
                  </summary>
                  <pre style={{ 
                    fontSize: '0.75rem', 
                    backgroundColor: '#f5f5f5', 
                    padding: '0.5rem',
                    borderRadius: '4px',
                    marginTop: '0.5rem',
                    overflowX: 'auto',
                    color: message.sender === 'user' ? 'white' : 'black'
                  }}>
                    {message.sqlQuery}
                  </pre>
                </details>
              )}

              {/* Show data preview if available */}
              {message.data && message.data.length > 0 && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ cursor: 'pointer', fontSize: '0.8rem', opacity: 0.7 }}>
                    View Data ({message.data.length} rows)
                  </summary>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    backgroundColor: '#f5f5f5', 
                    padding: '0.5rem',
                    borderRadius: '4px',
                    marginTop: '0.5rem',
                    overflowX: 'auto',
                    color: message.sender === 'user' ? 'white' : 'black'
                  }}>
                    <pre>{JSON.stringify(message.data, null, 2)}</pre>
                  </div>
                </details>
              )}
              
              <div style={{
                fontSize: '0.75rem',
                marginTop: '0.25rem',
                opacity: 0.7
              }}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'center', color: '#666' }}>
            Claude is thinking...
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{
        padding: '1rem',
        backgroundColor: 'white',
        borderTop: '1px solid #ddd'
      }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your data..."
            style={{
              flex: 1,
              padding: '0.5rem',
              fontSize: '16px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'none',
              minHeight: '40px',
              maxHeight: '100px'
            }}
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              padding: '0.5rem 1.5rem',
              backgroundColor: loading || !input.trim() ? '#ccc' : '#0070f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
