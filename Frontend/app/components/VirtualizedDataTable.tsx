// Install: npm install react-window react-window-infinite-loader
// Enhanced data table component with virtualization for large datasets

import React, { useMemo, useState, useCallback } from 'react';
import { FixedSizeList as List, VariableSizeList } from 'react-window';

interface VirtualizedDataTableProps {
  data: any[];
  columns: string[];
  maxHeight?: number;
  rowHeight?: number;
  showExportButton?: boolean;
  onExport?: () => void;
}

export const VirtualizedDataTable: React.FC<VirtualizedDataTableProps> = ({
  data,
  columns,
  maxHeight = 400,
  rowHeight = 35,
  showExportButton = true,
  onExport
}) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [filterText, setFilterText] = useState('');

  // Memoized filtered and sorted data
  const processedData = useMemo(() => {
    let filtered = data;

    // Apply filter
    if (filterText) {
      filtered = data.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(filterText.toLowerCase())
        )
      );
    }

    // Apply sort
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        
        if (aVal === bVal) return 0;
        
        const comparison = aVal < bVal ? -1 : 1;
        return sortConfig.direction === 'desc' ? comparison * -1 : comparison;
      });
    }

    return filtered;
  }, [data, sortConfig, filterText]);

  const handleSort = useCallback((columnKey: string) => {
    setSortConfig(current => {
      if (current?.key === columnKey) {
        return {
          key: columnKey,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key: columnKey, direction: 'asc' };
    });
  }, []);

  const exportToCSV = useCallback(() => {
    if (!processedData.length) return;

    const csvContent = [
      columns.join(','),
      ...processedData.map(row =>
        columns.map(col => `"${String(row[col] || '').replace(/"/g, '""')}"`).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `data_export_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    if (onExport) onExport();
  }, [processedData, columns, onExport]);

  // Row renderer for virtualization
  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = processedData[index];
    const isEven = index % 2 === 0;

    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          backgroundColor: isEven ? '#ffffff' : '#f8f9fa',
          borderBottom: '1px solid #e9ecef',
          fontSize: '0.875rem'
        }}
      >
        {columns.map((col, colIndex) => (
          <div
            key={col}
            style={{
              flex: 1,
              padding: '8px 12px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              borderRight: colIndex < columns.length - 1 ? '1px solid #e9ecef' : 'none',
              minWidth: '100px'
            }}
            title={String(row[col] || '')}
          >
            {String(row[col] || '')}
          </div>
        ))}
      </div>
    );
  }, [processedData, columns]);

  // Header component
  const TableHeader = () => (
    <div
      style={{
        display: 'flex',
        backgroundColor: '#e9ecef',
        borderBottom: '2px solid #dee2e6',
        fontWeight: 'bold',
        fontSize: '0.875rem',
        position: 'sticky',
        top: 0,
        zIndex: 1
      }}
    >
      {columns.map((col, index) => (
        <div
          key={col}
          onClick={() => handleSort(col)}
          style={{
            flex: 1,
            padding: '12px',
            cursor: 'pointer',
            borderRight: index < columns.length - 1 ? '1px solid #dee2e6' : 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            minWidth: '100px',
            userSelect: 'none'
          }}
        >
          <span>{col}</span>
          <span style={{ marginLeft: '4px', fontSize: '0.75rem', opacity: 0.7 }}>
            {sortConfig?.key === col ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '↕'}
          </span>
        </div>
      ))}
    </div>
  );

  if (!data.length) {
    return (
      <div style={{
        padding: '2rem',
        textAlign: 'center',
        color: '#6c757d',
        border: '1px solid #dee2e6',
        borderRadius: '8px',
        backgroundColor: '#f8f9fa'
      }}>
        No data to display
      </div>
    );
  }

  return (
    <div style={{
      border: '1px solid #dee2e6',
      borderRadius: '8px',
      overflow: 'hidden',
      backgroundColor: 'white'
    }}>
      {/* Controls */}
      <div style={{
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderBottom: '1px solid #dee2e6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>
            📊 {processedData.length.toLocaleString()} rows
            {filterText && ` (filtered from ${data.length.toLocaleString()})`}
          </span>
          
          <input
            type="text"
            placeholder="Filter data..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{
              padding: '4px 8px',
              fontSize: '0.875rem',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              minWidth: '150px'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {showExportButton && (
            <button
              onClick={exportToCSV}
              style={{
                padding: '4px 12px',
                fontSize: '0.875rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              📥 Export CSV
            </button>
          )}
          
          {sortConfig && (
            <button
              onClick={() => setSortConfig(null)}
              style={{
                padding: '4px 12px',
                fontSize: '0.875rem',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Clear Sort
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div>
        <TableHeader />
        <List
          height={Math.min(maxHeight, processedData.length * rowHeight)}
          itemCount={processedData.length}
          itemSize={rowHeight}
          width="100%"
        >
          {Row}
        </List>
      </div>

      {/* Footer with summary */}
      <div style={{
        padding: '8px 12px',
        backgroundColor: '#f8f9fa',
        borderTop: '1px solid #dee2e6',
        fontSize: '0.75rem',
        color: '#6c757d',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>
          Showing {processedData.length} of {data.length} rows
          {columns.length > 0 && ` • ${columns.length} columns`}
        </span>
        
        {processedData.length > 1000 && (
          <span style={{ fontStyle: 'italic' }}>
            ⚡ Virtualized for performance
          </span>
        )}
      </div>
    </div>
  );
};

// Enhanced usage in message component
export const EnhancedDataDisplay: React.FC<{
  data: any[];
  columns?: string[];
  title?: string;
  subtitle?: string;
}> = ({ data, columns, title, subtitle }) => {
  const detectedColumns = columns || (data.length > 0 ? Object.keys(data[0]) : []);

  if (!data.length) {
    return (
      <div style={{
        padding: '1rem',
        textAlign: 'center',
        color: '#6c757d',
        fontStyle: 'italic'
      }}>
        No data available
      </div>
    );
  }

  return (
    <div style={{ marginTop: '1rem' }}>
      {title && (
        <h4 style={{
          margin: '0 0 0.5rem 0',
          fontSize: '1rem',
          fontWeight: 'bold',
          color: '#343a40'
        }}>
          {title}
        </h4>
      )}
      
      {subtitle && (
        <p style={{
          margin: '0 0 1rem 0',
          fontSize: '0.875rem',
          color: '#6c757d'
        }}>
          {subtitle}
        </p>
      )}

      <VirtualizedDataTable
        data={data}
        columns={detectedColumns}
        maxHeight={350}
        showExportButton={true}
      />
    </div>
  );
};