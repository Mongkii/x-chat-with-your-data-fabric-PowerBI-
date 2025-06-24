'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

export default function ConfigStatus() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkConfig();
  }, []);

  const checkConfig = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/config`
      );
      setConfig(response.data);
    } catch (error) {
      console.error('Config check failed:', error);
    }
    setLoading(false);
  };

  if (loading) return <div>Checking configuration...</div>;

  return (
    <div style={{
      padding: '1rem',
      backgroundColor: config?.claude_configured ? '#d4edda' : '#f8d7da',
      border: `1px solid ${config?.claude_configured ? '#c3e6cb' : '#f5c6cb'}`,
      borderRadius: '8px',
      marginBottom: '1rem'
    }}>
      <h3>Configuration Status</h3>
      <p>Claude AI: {config?.claude_configured ? '✅ Connected' : '❌ Not configured'}</p>
      {!config?.claude_configured && (
        <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
          Add your ANTHROPIC_API_KEY to the backend .env file
        </p>
      )}
    </div>
  );
}