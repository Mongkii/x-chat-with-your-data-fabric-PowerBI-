// frontend/app/components/PowerBIMCPConnection.tsx

'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface PowerBIMCPConnectionProps {
  onConnectionChange: (connected: boolean) => void;
  authConfigured: boolean;
}

export default function PowerBIMCPConnection({ onConnectionChange, authConfigured }: PowerBIMCPConnectionProps) {
  const [xmlaEndpoint, setXmlaEndpoint] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [workspaceName, setWorkspaceName] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(true);
  const [connectionInfo, setConnectionInfo] = useState<any>(null);
  const [tables, setTables] = useState<string[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/powerbi/status`);
      if (response.data.connected) {
        setConnected(true);
        setShowForm(false);
        setConnectionInfo(response.data);
        onConnectionChange(true);
        loadTables();
        loadSuggestedQuestions();
      }
    } catch (error) {
      console.error('Failed to check Power BI status');
    }
  };

  const connectToPowerBI = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/powerbi/connect`,
        { 
          xmla_endpoint: xmlaEndpoint,
          dataset_name: datasetName,
          workspace_name: workspaceName
        }
      );

      if (response.data.success) {
        setConnected(true);
        setShowForm(false);
        setConnectionInfo(response.data);
        onConnectionChange(true);
        loadTables();
        loadSuggestedQuestions();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Connection failed');
      onConnectionChange(false);
    }

    setLoading(false);
  };

  const loadTables = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/powerbi/tables`);
      if (response.data.success) {
        setTables(response.data.tables);
      }
    } catch (error) {
      console.error('Failed to load tables');
    }
  };

  const loadSuggestedQuestions = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/powerbi/suggest-questions`);
      if (response.data.success) {
        setSuggestedQuestions(response.data.questions);
      }
    } catch (error) {
      console.error('Failed to load suggested questions');
    }
  };

  const disconnect = () => {
    setConnected(false);
    setShowForm(true);
    setConnectionInfo(null);
    setTables([]);
    setSuggestedQuestions([]);
    onConnectionChange(false);
  };

  if (!authConfigured) {
    return (
      <div style={{
        padding: '1rem',
        backgroundColor: '#f8d7da',
        border: '1px solid #f5c6cb',
        borderRadius: '8px',
        marginBottom: '1rem'
      }}>
        <p>⚠️ Please configure OAuth2 authentication first</p>
      </div>
    );
  }

  return (
    <div style={{
      padding: '1rem',
      backgroundColor: connected ? '#d1ecf1' : '#f8f9fa',
      border: `1px solid ${connected ? '#bee5eb' : '#dee2e6'}`,
      borderRadius: '8px',
      marginBottom: '1rem'
    }}>
      {connected ? (
        <div>
          <h3>🔗 Power BI MCP: Connected</h3>
          <div style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            <p><strong>Dataset:</strong> {connectionInfo?.dataset_name || datasetName}</p>
            <p><strong>Workspace:</strong> {connectionInfo?.workspace_name || workspaceName || 'Default'}</p>
            <p><strong>Tables:</strong> {connectionInfo?.tables_count || tables.length}</p>
            <p><strong>Endpoint:</strong> {connectionInfo?.xmla_endpoint || xmlaEndpoint}</p>
          </div>

          {tables.length > 0 && (
            <details style={{ marginTop: '1rem' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                📊 Available Tables ({tables.length})
              </summary>
              <div style={{ marginTop: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
                {tables.map((table, idx) => (
                  <div key={idx} style={{ 
                    padding: '0.25rem 0.5rem',
                    backgroundColor: '#f8f9fa',
                    margin: '0.25rem 0',
                    borderRadius: '4px',
                    fontSize: '0.85rem'
                  }}>
                    {table}
                  </div>
                ))}
              </div>
            </details>
          )}

          {suggestedQuestions.length > 0 && (
            <details style={{ marginTop: '1rem' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                💡 Suggested Questions ({suggestedQuestions.length})
              </summary>
              <div style={{ marginTop: '0.5rem' }}>
                {suggestedQuestions.map((question, idx) => (
                  <div key={idx} style={{ 
                    padding: '0.5rem',
                    backgroundColor: '#e3f2fd',
                    margin: '0.25rem 0',
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    border: '1px solid #bbdefb'
                  }}
                  onClick={() => {
                    // You can add logic here to auto-fill the chat input
                    console.log('Selected question:', question);
                  }}
                  title="Click to use this question"
                  >
                    {question}
                  </div>
                ))}
              </div>
            </details>
          )}

          <button
            onClick={disconnect}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Disconnect
          </button>
        </div>
      ) : (
        <div>
          <h3>🔗 Connect to Power BI (MCP Style)</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', marginBottom: '1rem' }}>
            Connect to your Power BI semantic model using XMLA endpoint - just like the Power BI MCP server!
          </p>
          
          {showForm && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  XMLA Endpoint: <span style={{ color: '#dc3545' }}>*</span>
                </label>
                <input
                  type="text"
                  value={xmlaEndpoint}
                  onChange={(e) => setXmlaEndpoint(e.target.value)}
                  placeholder="powerbi://api.powerbi.com/v1.0/myorg/YourWorkspace"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    fontSize: '14px',
                    border: '1px solid #ced4da',
                    borderRadius: '4px'
                  }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  Dataset Name: <span style={{ color: '#dc3545' }}>*</span>
                </label>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  placeholder="Your Power BI Dataset Name"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    fontSize: '14px',
                    border: '1px solid #ced4da',
                    borderRadius: '4px'
                  }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  Workspace Name: <em>(optional)</em>
                </label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="Your Power BI Workspace Name"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    fontSize: '14px',
                    border: '1px solid #ced4da',
                    borderRadius: '4px'
                  }}
                />
              </div>

              {error && (
                <div style={{ color: '#dc3545', marginBottom: '1rem' }}>
                  {error}
                </div>
              )}

              <button
                onClick={connectToPowerBI}
                disabled={loading || !xmlaEndpoint || !datasetName}
                style={{
                  padding: '0.5rem 1.5rem',
                  backgroundColor: loading || !xmlaEndpoint || !datasetName ? '#ccc' : '#17a2b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !xmlaEndpoint || !datasetName ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Connecting...' : 'Connect to Power BI'}
              </button>

              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#6c757d' }}>
                <strong>📝 How to get these values:</strong>
                <ol style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                  <li>Enable XMLA endpoint in Power BI workspace settings (Premium required)</li>
                  <li>Copy the XMLA endpoint URL from workspace settings</li>
                  <li>Use the exact dataset name from Power BI service</li>
                  <li>Ensure your service principal has access to the workspace</li>
                </ol>
                
                <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
                  <strong>💡 Example:</strong><br/>
                  XMLA Endpoint: <code>powerbi://api.powerbi.com/v1.0/myorg/Sales Analytics</code><br/>
                  Dataset Name: <code>Sales Dashboard Dataset</code>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}