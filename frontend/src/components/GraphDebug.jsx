import React from 'react';

const GraphDebug = ({ graphData, loading, error }) => {
  return (
    <div style={{
      position: 'absolute',
      top: '10px',
      left: '10px',
      background: 'rgba(0,0,0,0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '4px',
      zIndex: 1000,
      fontSize: '12px',
      maxWidth: '300px'
    }}>
      <div>Graph Debug Info:</div>
      <div>Loading: {loading ? 'YES' : 'NO'}</div>
      <div>Error: {error || 'NONE'}</div>
      <div>Data: {graphData ? 'YES' : 'NO'}</div>
      {graphData && (
        <>
          <div>Nodes: {graphData?.nodes?.length || 0}</div>
          <div>Edges: {graphData?.edges?.length || 0}</div>
        </>
      )}
      <div>Timestamp: {new Date().toLocaleTimeString()}</div>
    </div>
  );
};

export default GraphDebug;