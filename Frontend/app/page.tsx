// frontend/app/page.tsx

'use client';

import { useState, useEffect } from 'react';
import ConfigStatus from './components/ConfigStatus';
import OAuth2Config from './components/OAuth2Config';
import FabricConnection from './components/FabricConnection';
import PowerBIMCPConnection from './components/PowerBIMCPConnection';
import SchemaExplorer from './components/SchemaExplorer';
import EnhancedChatInterface from './components/EnhancedChatInterface';
import axios from 'axios';

export default function Home() {
  const [authConfigured, setAuthConfigured] = useState(false);
  const [fabricConnected, setFabricConnected] = useState(false);
  const [semanticModelConnected, setSemanticModelConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'schema'>('chat');
  const [connectionType, setConnectionType] = useState<'sql' | 'semantic_model' | null>(null);
  const [dataSourceType, setDataSourceType] = useState<'sql' | 'semantic_model'>('sql');

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/connection/status`);
      setFabricConnected(response.data.sql_connected);
      setSemanticModelConnected(response.data.semantic_model_connected);
      
      if (response.data.sql_connected) {
        setConnectionType('sql');
      } else if (response.data.semantic_model_connected) {
        setConnectionType('semantic_model');
      }
    } catch (error) {
      console.error('Failed to check connection status:', error);
    }
  };

  const handleConnectionChange = (type: 'sql' | 'semantic_model', connected: boolean) => {
    if (type === 'sql') {
      setFabricConnected(connected);
      if (connected) {
        setConnectionType('sql');
        setSemanticModelConnected(false);
      }
    } else {
      setSemanticModelConnected(connected);
      if (connected) {
        setConnectionType('semantic_model');
        setFabricConnected(false);
      }
    }
  };

  return (
    <main style={{ 
      padding: '2rem', 
      maxWidth: '1400px', 
      margin: '0 auto',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <h1 style={{ marginBottom: '2rem', textAlign: 'center' }}>
        💬 Chat with Your Data
      </h1>
      
      <ConfigStatus />
      <OAuth2Config onAuthChange={setAuthConfigured} />
      
      {authConfigured && (
        <div style={{ marginBottom: '1rem' }}>
          <h3>Select Data Source Type:</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                value="sql"
                checked={dataSourceType === 'sql'}
                onChange={(e) => setDataSourceType('sql')}
              />
              SQL Endpoint (Lakehouse/Warehouse)
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                value="semantic_model"
                checked={dataSourceType === 'semantic_model'}
                onChange={(e) => setDataSourceType('semantic_model')}
              />
              Power BI Semantic Model (XMLA)
            </label>
          </div>
        </div>
      )}
      
      {authConfigured && dataSourceType === 'sql' && (
        <FabricConnection 
          onConnectionChange={(connected) => handleConnectionChange('sql', connected)} 
          authConfigured={authConfigured}
        />
      )}
      
      {authConfigured && dataSourceType === 'semantic_model' && (
        <PowerBIMCPConnection
          onConnectionChange={(connected) => handleConnectionChange('semantic_model', connected)}
          authConfigured={authConfigured}
        />
      )}
      
      {(fabricConnected || semanticModelConnected) && (
        <>
          <div style={{ marginBottom: '1rem' }}>
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                padding: '0.5rem 1rem',
                marginRight: '0.5rem',
                backgroundColor: activeTab === 'chat' ? '#007bff' : '#f8f9fa',
                color: activeTab === 'chat' ? 'white' : 'black',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: activeTab === 'schema' ? '#007bff' : '#f8f9fa',
                color: activeTab === 'schema' ? 'white' : 'black',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {connectionType === 'sql' ? 'Schema Explorer' : 'Model Explorer'}
            </button>
          </div>
          
          <div style={{ marginTop: '2rem' }}>
            {activeTab === 'chat' && (
              <EnhancedChatInterface connectionType={connectionType} />
            )}
            
            {activeTab === 'schema' && connectionType === 'sql' && (
              <SchemaExplorer connected={fabricConnected} />
            )}
            
            {activeTab === 'schema' && connectionType === 'semantic_model' && (
              <div style={{ padding: '2rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <h3>Power BI Model Structure</h3>
                <p>Connected to: {semanticModelConnected ? 'Power BI Semantic Model' : 'Not connected'}</p>
                <p style={{ fontSize: '0.9rem', color: '#666' }}>
                  Model explorer UI coming soon. For now, use the chat interface to explore your data.
                </p>
              </div>
            )}
          </div>
          
          <div style={{ 
            marginTop: '2rem', 
            padding: '1rem',
            backgroundColor: '#e3f2fd',
            borderRadius: '8px'
          }}>
            <h3>Sample Questions:</h3>
            {connectionType === 'sql' ? (
              <ul style={{ marginLeft: '1.5rem', lineHeight: '1.8' }}>
                <li>Show me the top 5 resellers by revenue</li>
                <li>What's the total sales amount this year?</li>
                <li>Which products have the highest profit margin?</li>
                <li>Show me customer distribution by country</li>
              </ul>
            ) : (
              <ul style={{ marginLeft: '1.5rem', lineHeight: '1.8' }}>
                <li>What are the key measures in this model?</li>
                <li>Show me sales by product category</li>
                <li>What's the total revenue for this year?</li>
                <li>Which region has the highest sales?</li>
              </ul>
            )}
          </div>
        </>
      )}
    </main>
  );
}