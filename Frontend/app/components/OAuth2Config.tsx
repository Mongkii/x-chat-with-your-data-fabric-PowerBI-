'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface OAuth2ConfigProps {
  onAuthChange: (authenticated: boolean) => void;
}

export default function OAuth2Config({ onAuthChange }: OAuth2ConfigProps) {
  const [tenantId, setTenantId] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/status`
      );
      if (response.data.configured) {
        setAuthenticated(true);
        setShowForm(false);
        onAuthChange(true);
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
    }
  };

  const configureAuth = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/configure`,
        {
          tenant_id: tenantId,
          client_id: clientId,
          client_secret: clientSecret
        }
      );

      if (response.data.success) {
        setAuthenticated(true);
        setShowForm(false);
        onAuthChange(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Configuration failed');
      onAuthChange(false);
    }

    setLoading(false);
  };

  const resetAuth = () => {
    setAuthenticated(false);
    setShowForm(true);
    onAuthChange(false);
    setClientSecret('');
  };

  return (
    <div style={{
      padding: '1rem',
      backgroundColor: authenticated ? '#d4edda' : '#fff3cd',
      border: `1px solid ${authenticated ? '#c3e6cb' : '#ffeaa7'}`,
      borderRadius: '8px',
      marginBottom: '1rem'
    }}>
      {authenticated ? (
        <div>
          <h3>🔐 OAuth2 Authentication: Configured</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Your app is authenticated with Microsoft Fabric
          </p>
          <button
            onClick={resetAuth}
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
            Reconfigure
          </button>
        </div>
      ) : (
        <div>
          <h3>🔐 Configure OAuth2 Authentication</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', marginBottom: '1rem' }}>
            Enter your Azure AD app registration details
          </p>
          {showForm && (
            <div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                  Tenant ID:
                </label>
                <input
                  type="text"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
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
                  Client ID (Application ID):
                </label>
                <input
                  type="text"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
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
                  Client Secret:
                </label>
                <input
                  type="password"
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  placeholder="Your client secret value"
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
                onClick={configureAuth}
                disabled={loading || !tenantId || !clientId || !clientSecret}
                style={{
                  padding: '0.5rem 1.5rem',
                  backgroundColor: loading || !tenantId || !clientId || !clientSecret ? '#ccc' : '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !tenantId || !clientId || !clientSecret ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Configuring...' : 'Configure Authentication'}
              </button>

              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#6c757d' }}>
                <strong>How to get these values:</strong>
                <ol style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                  <li>Go to Azure Portal → Azure Active Directory</li>
                  <li>App registrations → New registration</li>
                  <li>After registration, copy the Application (client) ID and Directory (tenant) ID</li>
                  <li>Go to Certificates & secrets → New client secret</li>
                  <li>Copy the secret value immediately</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}