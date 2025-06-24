// frontend/app/components/SemanticModelConnection.tsx

'use client';

import { useState } from 'react';
import axios from 'axios';

interface SemanticModelConnectionProps {
  onConnectionChange: (connected: boolean) => void;
  authConfigured: boolean;
}

export default function SemanticModelConnection({ onConnectionChange, authConfigured }: SemanticModelConnectionProps) {
  const [xmlaEndpoint, setXmlaEndpoint] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(true);
  const [modelInfo, setModelInfo] = useState<any>(null);

  const testConnection = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/semantic-model/connect`,
        { 
          xmla_endpoint: xmlaEndpoint,
          workspace_id: workspaceId,
          dataset_id: datasetId
        }
      );

      if (response.data.success) {
        setConnected(true);
        setShowForm(false);
        setModelInfo(response.data);
        onConnectionChange(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Connection failed');
      onConnectionChange(false);
    }

    setLoading(false);
  };

  const disconnect = () => {
    setConnected(false);
    setShowForm(true);
    setModelInfo(null);
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
          <h3>📊 Power BI Semantic Model: Connected</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Dataset: {datasetId}<br/>
            Tables: {modelInfo?.table_count || 0}<br/>
            Measures: {modelInfo?.measure_count || 0}
          </p>
          <button
            onClick={disconnect}
            style={{
              marginTop: '0.5rem',
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
          <h3>📊 Connect to Power BI Semantic Model</h3>
          {showForm && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  XMLA Endpoint:
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
                  Workspace ID:
                </label>
                <input
                  type="text"
                  value={workspaceId}
                  onChange={(e) => setWorkspaceId(e.target.value)}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
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
                  Dataset ID:
                </label>
                <input
                  type="text"
                  value={datasetId}
                  onChange={(e) => setDatasetId(e.target.value)}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
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
                onClick={testConnection}
                disabled={loading || !xmlaEndpoint || !workspaceId || !datasetId}
                style={{
                  padding: '0.5rem 1.5rem',
                  backgroundColor: loading || !xmlaEndpoint || !workspaceId || !datasetId ? '#ccc' : '#17a2b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !xmlaEndpoint || !workspaceId || !datasetId ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Connecting...' : 'Connect to Semantic Model'}
              </button>

              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#6c757d' }}>
                <strong>How to get these values:</strong>
                <ol style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                  <li>Go to Power BI workspace settings</li>
                  <li>Enable XMLA endpoint (Premium required)</li>
                  <li>Copy the XMLA endpoint URL</li>
                  <li>Get workspace and dataset IDs from URLs</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}