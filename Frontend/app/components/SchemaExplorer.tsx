'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface SchemaExplorerProps {
  connected: boolean;
}

export default function SchemaExplorer({ connected }: SchemaExplorerProps) {
  const [schema, setSchema] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTable, setSelectedTable] = useState('');
  const [sampleData, setSampleData] = useState<any>(null);

  useEffect(() => {
    if (connected) {
      loadSchema();
    }
  }, [connected]);

  const loadSchema = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/fabric/schema`
      );
      if (response.data.success) {
        setSchema(response.data.tables);
      }
    } catch (error) {
      console.error('Failed to load schema:', error);
    }
    setLoading(false);
  };

  const loadSampleData = async (tableName: string) => {
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/fabric/sample`,
        { table_name: tableName, limit: 5 }
      );
      if (response.data.success) {
        setSampleData(response.data);
        setSelectedTable(tableName);
      }
    } catch (error) {
      console.error('Failed to load sample data:', error);
    }
  };

  if (!connected) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: '#6c757d' }}>
        Connect to Microsoft Fabric to explore your data
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center' }}>
        Loading schema...
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h3>📊 Database Schema</h3>
      {schema && (
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <div style={{ flex: '1', maxHeight: '400px', overflowY: 'auto' }}>
            {Object.entries(schema).map(([tableName, tableInfo]: [string, any]) => (
              <div
                key={tableName}
                onClick={() => loadSampleData(tableName)}
                style={{
                  padding: '0.5rem',
                  marginBottom: '0.5rem',
                  backgroundColor: selectedTable === tableName ? '#e3f2fd' : '#f8f9fa',
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                <strong>{tableName}</strong>
                <div style={{ fontSize: '0.85rem', color: '#6c757d' }}>
                  {tableInfo.columns.length} columns
                </div>
              </div>
            ))}
          </div>
          
          {selectedTable && sampleData && (
            <div style={{ flex: '2' }}>
              <h4>{selectedTable}</h4>
              <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                <strong>Columns:</strong>
                <ul style={{ marginTop: '0.5rem' }}>
                  {schema[selectedTable].columns.map((col: any) => (
                    <li key={col.name}>
                      {col.name} ({col.type})
                    </li>
                  ))}
                </ul>
              </div>
              
              {sampleData.preview && sampleData.preview.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <strong>Sample Data:</strong>
                  <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
                    <table style={{ fontSize: '0.85rem', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          {sampleData.columns.map((col: string) => (
                            <th key={col} style={{ 
                              border: '1px solid #dee2e6', 
                              padding: '0.5rem',
                              backgroundColor: '#f8f9fa'
                            }}>
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sampleData.preview.map((row: any, idx: number) => (
                          <tr key={idx}>
                            {sampleData.columns.map((col: string) => (
                              <td key={col} style={{ 
                                border: '1px solid #dee2e6', 
                                padding: '0.5rem' 
                              }}>
                                {row[col]?.toString() || 'NULL'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}