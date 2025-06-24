// Real-time monitoring dashboard component
// Install: npm install recharts lucide-react

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Database, Zap, Users, TrendingUp, AlertCircle, CheckCircle, Clock, Cpu, HardDrive } from 'lucide-react';
import axios from 'axios';

interface SystemHealth {
  score: number;
  status: string;
  issues: string[];
}

interface CacheStats {
  hit_rate_percentage: number;
  total_hits: number;
  total_misses: number;
  cached_schemas: number;
  cache_size_limit: number;
}

interface MonitoringData {
  health: {
    timestamp: string;
    overall_health: SystemHealth;
    services: {
      claude: { available: boolean; status: string };
      fabric: { connected: boolean; server?: string; database?: string };
      semantic_model: { connected: boolean; endpoint?: string };
    };
    cache: CacheStats;
    performance: {
      cpu_usage_percent: number;
      memory_usage_percent: number;
      python_memory_mb: number;
    };
  };
}

interface HistoricalMetric {
  timestamp: string;
  value: number;
  label?: string;
}

export const RealTimeMonitoringDashboard: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [historicalData, setHistoricalData] = useState<{
    cacheHitRate: HistoricalMetric[];
    systemHealth: HistoricalMetric[];
    performance: HistoricalMetric[];
  }>({
    cacheHitRate: [],
    systemHealth: [],
    performance: []
  });
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch monitoring data
  const fetchMonitoringData = useCallback(async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/system-health`);
      
      if (response.data.success) {
        const newData = response.data;
        setMonitoringData(newData);
        setLastUpdate(new Date());
        setError(null);
        setIsConnected(true);

        // Update historical data
        const timestamp = new Date().toISOString();
        setHistoricalData(prev => ({
          cacheHitRate: [
            ...prev.cacheHitRate.slice(-19), // Keep last 20 points
            {
              timestamp,
              value: newData.health.cache.hit_rate_percentage,
              label: `${newData.health.cache.hit_rate_percentage.toFixed(1)}%`
            }
          ],
          systemHealth: [
            ...prev.systemHealth.slice(-19),
            {
              timestamp,
              value: newData.health.overall_health.score,
              label: newData.health.overall_health.status
            }
          ],
          performance: [
            ...prev.performance.slice(-19),
            {
              timestamp,
              value: newData.health.performance.cpu_usage_percent,
              label: `CPU: ${newData.health.performance.cpu_usage_percent.toFixed(1)}%`
            }
          ]
        }));
      } else {
        throw new Error(response.data.error || 'Failed to fetch monitoring data');
      }
    } catch (err: any) {
      setError(err.message);
      setIsConnected(false);
      console.error('Monitoring fetch error:', err);
    }
  }, []);

  // Setup polling
  useEffect(() => {
    fetchMonitoringData(); // Initial fetch
    
    const interval = setInterval(fetchMonitoringData, 10000); // Every 10 seconds
    
    return () => clearInterval(interval);
  }, [fetchMonitoringData]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'excellent': return '#28a745';
      case 'good': return '#17a2b8';
      case 'fair': return '#ffc107';
      case 'poor': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (available: boolean, status?: string) => {
    if (!available) return <AlertCircle size={16} color="#dc3545" />;
    return <CheckCircle size={16} color="#28a745" />;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (!monitoringData) {
    return (
      <div style={{
        padding: '2rem',
        textAlign: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <Activity className="animate-spin" size={32} style={{ marginBottom: '1rem' }} />
        <p>Loading monitoring data...</p>
        {error && (
          <p style={{ color: '#dc3545', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Error: {error}
          </p>
        )}
      </div>
    );
  }

  const { health } = monitoringData;

  return (
    <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        marginBottom: '2rem',
        padding: '1rem',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold' }}>
            🖥️ AI Data Analysis - System Monitoring
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#6c757d', fontSize: '0.875rem' }}>
            Real-time system health and performance metrics
          </p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isConnected ? '#28a745' : '#dc3545'
            }} />
            <span style={{ fontSize: '0.875rem', color: '#6c757d' }}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {lastUpdate && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Clock size={14} />
              <span style={{ fontSize: '0.875rem', color: '#6c757d' }}>
                {lastUpdate.toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* System Health Overview */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        {/* Overall Health Score */}
        <div style={{
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6',
          textAlign: 'center'
        }}>
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(health.overall_health.status),
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            fontWeight: 'bold',
            margin: '0 auto 0.5rem'
          }}>
            {health.overall_health.score}
          </div>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem' }}>System Health</h3>
          <p style={{ margin: 0, color: '#6c757d', fontSize: '0.875rem', textTransform: 'capitalize' }}>
            {health.overall_health.status}
          </p>
          {health.overall_health.issues.length > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#dc3545' }}>
              {health.overall_health.issues.length} issues detected
            </div>
          )}
        </div>

        {/* Cache Performance */}
        <div style={{
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Zap size={20} color="#ffc107" />
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Cache Performance</h3>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007bff', marginBottom: '0.5rem' }}>
            {health.cache.hit_rate_percentage.toFixed(1)}%
          </div>
          <p style={{ margin: 0, color: '#6c757d', fontSize: '0.875rem' }}>
            Hit Rate ({health.cache.total_hits} hits, {health.cache.total_misses} misses)
          </p>
          <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#6c757d' }}>
            {health.cache.cached_schemas}/{health.cache.cache_size_limit} schemas cached
          </div>
        </div>

        {/* Services Status */}
        <div style={{
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Database size={20} color="#17a2b8" />
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Services</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.875rem' }}>Claude AI</span>
              {getStatusIcon(health.services.claude.available)}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.875rem' }}>Fabric SQL</span>
              {getStatusIcon(health.services.fabric.connected)}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.875rem' }}>Power BI</span>
              {getStatusIcon(health.services.semantic_model.connected)}
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div style={{
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Cpu size={20} color="#28a745" />
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Performance</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>CPU Usage</span>
                <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>
                  {health.performance.cpu_usage_percent.toFixed(1)}%
                </span>
              </div>
              <div style={{ width: '100%', height: '4px', backgroundColor: '#e9ecef', borderRadius: '2px' }}>
                <div style={{
                  width: `${health.performance.cpu_usage_percent}%`,
                  height: '100%',
                  backgroundColor: health.performance.cpu_usage_percent > 80 ? '#dc3545' : 
                                 health.performance.cpu_usage_percent > 60 ? '#ffc107' : '#28a745',
                  borderRadius: '2px'
                }} />
              </div>
            </div>
            
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Memory Usage</span>
                <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>
                  {health.performance.memory_usage_percent.toFixed(1)}%
                </span>
              </div>
              <div style={{ width: '100%', height: '4px', backgroundColor: '#e9ecef', borderRadius: '2px' }}>
                <div style={{
                  width: `${health.performance.memory_usage_percent}%`,
                  height: '100%',
                  backgroundColor: health.performance.memory_usage_percent > 85 ? '#dc3545' : 
                                 health.performance.memory_usage_percent > 70 ? '#ffc107' : '#28a745',
                  borderRadius: '2px'
                }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Charts */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        {/* Cache Hit Rate Trend */}
        <div style={{
          padding: '1rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>Cache Hit Rate Trend</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={historicalData.cacheHitRate}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                labelFormatter={(value) => `Time: ${formatTimestamp(value)}`}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Hit Rate']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#ffc107"
                fill="#ffc107"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* System Health Trend */}
        <div style={{
          padding: '1rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>System Health Score</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={historicalData.systemHealth}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                labelFormatter={(value) => `Time: ${formatTimestamp(value)}`}
                formatter={(value: number) => [`${value}/100`, 'Health Score']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#28a745"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Issues */}
      {health.overall_health.issues.length > 0 && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#fff5f5',
          border: '1px solid #fed7d7',
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertCircle size={20} color="#dc3545" />
            <h3 style={{ margin: 0, fontSize: '1rem', color: '#dc3545' }}>System Issues</h3>
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {health.overall_health.issues.map((issue, index) => (
              <li key={index} style={{ fontSize: '0.875rem', color: '#dc3545', marginBottom: '0.25rem' }}>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Actions */}
      <div style={{
        padding: '1rem',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>Quick Actions</h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            🔄 Refresh Dashboard
          </button>
          
          <button
            onClick={() => fetchMonitoringData()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            📊 Update Metrics
          </button>
          
          <button
            onClick={() => window.open(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/cache-performance`, '_blank')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            📈 View Cache Analytics
          </button>
        </div>
      </div>
    </div>
  );
};