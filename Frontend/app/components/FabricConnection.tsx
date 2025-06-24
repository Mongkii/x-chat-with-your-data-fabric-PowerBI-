'use client';

import { useState } from 'react';
import axios from 'axios';

interface FabricConnectionProps {
  onConnectionChange: (connected: boolean) => void;
  authConfigured: boolean;
}

export default function FabricConnection({ onConnectionChange, authConfigured }: FabricConnectionProps) {
  const [server, setServer] = useState('');
  const [database, setDatabase] = useState('');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(true);

  const testConnection = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/fabric/connect`,
        { server, database }
      );

      if (response.data.success) {
        setConnected(true);
        setShowForm(false);
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
      backgroundColor: connected ? '#d4edda' : '#f8f9fa',
      border: `1px solid ${connected ? '#c3e6cb' : '#dee2e6'}`,
      borderRadius: '8px',
      marginBottom: '1rem'
    }}>
      {connected ? (
        <div>
          <h3>🗄️ Microsoft Fabric: Connected</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Server: {server}<br/>
            Database: {database}
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
          <h3>🗄️ Connect to Microsoft Fabric</h3>
          {showForm && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  Server:
                </label>
                <input
                  type="text"
                  value={server}
                  onChange={(e) => setServer(e.target.value)}
                  placeholder="your-workspace.datawarehouse.fabric.microsoft.com"
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
                  Database:
                </label>
                <input
                  type="text"
                  value={database}
                  onChange={(e) => setDatabase(e.target.value)}
                  placeholder="your-database-name"
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
                disabled={loading || !server || !database}
                style={{
                  padding: '0.5rem 1.5rem',
                  backgroundColor: loading || !server || !database ? '#ccc' : '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !server || !database ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Connecting...' : 'Connect to Fabric'}
              </button>

              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#6c757d' }}>
                <strong>Where to find these values:</strong>
                <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                  <li>Server: In Fabric workspace → SQL endpoint → Connection string</li>
                  <li>Database: Your lakehouse or warehouse name</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}