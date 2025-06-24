// Install: npm install recharts lucide-react
// Intelligent visualization component that auto-generates appropriate charts

import React, { useMemo, useState } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter
} from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieIcon, Activity, Download } from 'lucide-react';

interface DataVisualizationProps {
  data: any[];
  question?: string;
  autoDetect?: boolean;
  preferredType?: 'auto' | 'bar' | 'line' | 'pie' | 'scatter' | 'area';
  title?: string;
}

interface ChartAnalysis {
  recommendedType: string;
  reasoning: string;
  confidence: number;
  alternatives: string[];
  xAxis: string;
  yAxis: string[];
  groupBy?: string;
  timeColumn?: string;
}

export const IntelligentVisualization: React.FC<DataVisualizationProps> = ({
  data,
  question = '',
  autoDetect = true,
  preferredType = 'auto',
  title
}) => {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  // Analyze data structure and recommend chart type
  const chartAnalysis = useMemo((): ChartAnalysis => {
    if (!data || data.length === 0) {
      return {
        recommendedType: 'bar',
        reasoning: 'No data available',
        confidence: 0,
        alternatives: [],
        xAxis: '',
        yAxis: []
      };
    }

    const columns = Object.keys(data[0]);
    const numericColumns = columns.filter(col => 
      data.some(row => typeof row[col] === 'number' && !isNaN(row[col]))
    );
    const dateColumns = columns.filter(col =>
      data.some(row => row[col] && (
        row[col] instanceof Date ||
        /^\d{4}-\d{2}-\d{2}/.test(String(row[col])) ||
        /^\d{1,2}\/\d{1,2}\/\d{4}/.test(String(row[col]))
      ))
    );
    const textColumns = columns.filter(col => 
      !numericColumns.includes(col) && !dateColumns.includes(col)
    );

    // Question-based analysis
    const questionLower = question.toLowerCase();
    const isTimeSeriesQuestion = /\b(trend|over time|by (year|month|quarter|day)|timeline|progression)\b/.test(questionLower);
    const isComparisonQuestion = /\b(compare|versus|vs|difference|top|bottom|highest|lowest)\b/.test(questionLower);
    const isDistributionQuestion = /\b(breakdown|distribution|split|percentage|share)\b/.test(questionLower);
    const isCorrelationQuestion = /\b(relationship|correlation|scatter|versus)\b/.test(questionLower);

    let recommendedType = 'bar';
    let reasoning = 'Default bar chart for categorical data';
    let confidence = 50;
    let alternatives: string[] = ['line', 'pie'];
    let xAxis = textColumns[0] || columns[0];
    let yAxis = numericColumns.slice(0, 2);
    let timeColumn = dateColumns[0];

    // Decision tree for chart type
    if (isTimeSeriesQuestion && dateColumns.length > 0 && numericColumns.length > 0) {
      recommendedType = 'line';
      reasoning = 'Time series data detected with date column';
      confidence = 90;
      alternatives = ['area', 'bar'];
      xAxis = dateColumns[0];
      yAxis = numericColumns.slice(0, 1);
    } else if (isCorrelationQuestion && numericColumns.length >= 2) {
      recommendedType = 'scatter';
      reasoning = 'Correlation analysis requires scatter plot';
      confidence = 85;
      alternatives = ['line', 'bar'];
      xAxis = numericColumns[0];
      yAxis = [numericColumns[1]];
    } else if (isDistributionQuestion && textColumns.length > 0 && numericColumns.length > 0) {
      if (textColumns.filter(col => new Set(data.map(row => row[col])).size <= 8).length > 0) {
        recommendedType = 'pie';
        reasoning = 'Distribution analysis with limited categories';
        confidence = 80;
        alternatives = ['bar', 'area'];
        xAxis = textColumns.find(col => new Set(data.map(row => row[col])).size <= 8) || textColumns[0];
        yAxis = numericColumns.slice(0, 1);
      } else {
        recommendedType = 'bar';
        reasoning = 'Distribution analysis with many categories';
        confidence = 75;
        alternatives = ['line', 'area'];
      }
    } else if (isComparisonQuestion && textColumns.length > 0 && numericColumns.length > 0) {
      recommendedType = 'bar';
      reasoning = 'Comparison analysis works best with bar charts';
      confidence = 85;
      alternatives = ['line', 'area'];
      xAxis = textColumns[0];
      yAxis = numericColumns.slice(0, 2);
    } else if (dateColumns.length > 0 && numericColumns.length > 0) {
      recommendedType = 'line';
      reasoning = 'Date column present, likely time series';
      confidence = 70;
      alternatives = ['area', 'bar'];
      xAxis = dateColumns[0];
      yAxis = numericColumns.slice(0, 1);
    } else if (numericColumns.length >= 2) {
      recommendedType = 'scatter';
      reasoning = 'Multiple numeric columns for correlation analysis';
      confidence = 65;
      alternatives = ['bar', 'line'];
      xAxis = numericColumns[0];
      yAxis = [numericColumns[1]];
    } else if (textColumns.length > 0 && numericColumns.length > 0) {
      const uniqueCategories = new Set(data.map(row => row[textColumns[0]])).size;
      if (uniqueCategories <= 6) {
        recommendedType = 'pie';
        reasoning = 'Few categories suitable for pie chart';
        confidence = 70;
        alternatives = ['bar', 'area'];
      } else {
        recommendedType = 'bar';
        reasoning = 'Many categories better shown as bar chart';
        confidence = 75;
        alternatives = ['line', 'area'];
      }
      xAxis = textColumns[0];
      yAxis = numericColumns.slice(0, 1);
    }

    return {
      recommendedType,
      reasoning,
      confidence,
      alternatives,
      xAxis,
      yAxis,
      timeColumn
    };
  }, [data, question]);

  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];

    return data.slice(0, 100).map(row => {
      const processed: any = {};
      
      // Process each column
      Object.keys(row).forEach(key => {
        let value = row[key];
        
        // Convert date strings to proper format for charts
        if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
          const date = new Date(value);
          processed[key] = date.toLocaleDateString();
          processed[`${key}_timestamp`] = date.getTime();
        } else if (typeof value === 'number') {
          processed[key] = Number(value.toFixed(2));
        } else {
          processed[key] = String(value || '');
        }
      });
      
      return processed;
    });
  }, [data]);

  const currentType = selectedType || (preferredType !== 'auto' ? preferredType : chartAnalysis.recommendedType);

  const chartColors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1',
    '#d084d0', '#ffb347', '#87ceeb', '#dda0dd', '#98fb98'
  ];

  const exportChart = () => {
    // In a real implementation, you'd use a library like html2canvas
    console.log('Exporting chart...', currentType, processedData.length, 'data points');
  };

  const renderChart = () => {
    if (!processedData.length) {
      return (
        <div style={{
          height: '300px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#6c757d',
          border: '2px dashed #dee2e6',
          borderRadius: '8px'
        }}>
          No data available for visualization
        </div>
      );
    }

    const commonProps = {
      data: processedData,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    switch (currentType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartAnalysis.xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartAnalysis.yAxis.map((col, index) => (
                <Line
                  key={col}
                  type="monotone"
                  dataKey={col}
                  stroke={chartColors[index]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartAnalysis.xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartAnalysis.yAxis.map((col, index) => (
                <Area
                  key={col}
                  type="monotone"
                  dataKey={col}
                  stackId="1"
                  stroke={chartColors[index]}
                  fill={chartColors[index]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartAnalysis.xAxis} />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartAnalysis.yAxis.map((col, index) => (
                <Bar
                  key={col}
                  dataKey={col}
                  fill={chartColors[index]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
        const pieData = processedData.map(row => ({
          name: row[chartAnalysis.xAxis],
          value: row[chartAnalysis.yAxis[0]],
        })).slice(0, 8); // Limit to 8 slices for readability

        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartAnalysis.xAxis} />
              <YAxis dataKey={chartAnalysis.yAxis[0]} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter
                dataKey={chartAnalysis.yAxis[0]}
                fill={chartColors[0]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return renderChart(); // Fallback to bar chart
    }
  };

  const chartTypes = [
    { id: 'bar', name: 'Bar Chart', icon: BarChart3 },
    { id: 'line', name: 'Line Chart', icon: TrendingUp },
    { id: 'pie', name: 'Pie Chart', icon: PieIcon },
    { id: 'area', name: 'Area Chart', icon: Activity },
    { id: 'scatter', name: 'Scatter Plot', icon: Activity }
  ];

  return (
    <div style={{
      border: '1px solid #dee2e6',
      borderRadius: '8px',
      backgroundColor: 'white',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        backgroundColor: '#f8f9fa',
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap'
      }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 'bold' }}>
            {title || 'Data Visualization'}
          </h4>
          {autoDetect && chartAnalysis.confidence > 0 && (
            <p style={{
              margin: '4px 0 0 0',
              fontSize: '0.75rem',
              color: '#6c757d'
            }}>
              🤖 AI Recommendation: {chartAnalysis.recommendedType} chart 
              ({chartAnalysis.confidence}% confidence)
            </p>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            style={{
              padding: '4px 8px',
              fontSize: '0.75rem',
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {showAnalysis ? 'Hide' : 'Show'} Analysis
          </button>
          
          <button
            onClick={exportChart}
            style={{
              padding: '4px 8px',
              fontSize: '0.75rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Download size={12} />
            Export
          </button>
        </div>
      </div>

      {/* Analysis Panel */}
      {showAnalysis && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#e3f2fd',
          borderBottom: '1px solid #dee2e6',
          fontSize: '0.875rem'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <strong>AI Analysis:</strong> {chartAnalysis.reasoning}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Data Structure:</strong> {processedData.length} rows, 
            X-axis: {chartAnalysis.xAxis}, Y-axis: {chartAnalysis.yAxis.join(', ')}
          </div>
          <div>
            <strong>Alternative Charts:</strong> {chartAnalysis.alternatives.join(', ')}
          </div>
        </div>
      )}

      {/* Chart Type Selector */}
      <div style={{
        padding: '8px 16px',
        backgroundColor: '#f8f9fa',
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        gap: '4px',
        flexWrap: 'wrap'
      }}>
        {chartTypes.map(type => {
          const Icon = type.icon;
          const isSelected = currentType === type.id;
          const isRecommended = chartAnalysis.recommendedType === type.id;
          
          return (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              style={{
                padding: '4px 8px',
                fontSize: '0.75rem',
                backgroundColor: isSelected ? '#007bff' : isRecommended ? '#28a745' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                opacity: isSelected ? 1 : 0.8
              }}
            >
              <Icon size={12} />
              {type.name}
              {isRecommended && !isSelected && ' ⭐'}
            </button>
          );
        })}
      </div>

      {/* Chart */}
      <div style={{ padding: '16px' }}>
        {renderChart()}
      </div>

      {/* Footer */}
      <div style={{
        padding: '8px 16px',
        backgroundColor: '#f8f9fa',
        borderTop: '1px solid #dee2e6',
        fontSize: '0.75rem',
        color: '#6c757d',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>
          Showing {Math.min(processedData.length, 100)} of {data.length} data points
        </span>
        <span>
          Chart: {currentType} • Confidence: {chartAnalysis.confidence}%
        </span>
      </div>
    </div>
  );
};