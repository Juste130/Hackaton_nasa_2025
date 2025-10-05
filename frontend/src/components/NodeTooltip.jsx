// src/components/NodeTooltip.jsx
import React from 'react';

const NodeTooltip = ({ node, x, y }) => {
  if (!node) return null;

  const style = {
    position: 'fixed',
    left: x,
    top: y,
    backgroundColor: 'rgba(0,0,0,0.8)',
    color: 'white',
    padding: '0.5rem',
    borderRadius: '4px',
    fontSize: '0.8rem',
    pointerEvents: 'none',
    zIndex: 1000,
    maxWidth: '300px'
  };

  return (
    <div style={style}>
      <strong>{node.label}: {node.id}</strong>
      <br />
      {node.properties?.title && (
        <>Title: {node.properties.title}<br /></>
      )}
      {node.properties?.name && (
        <>Name: {node.properties.name}<br /></>
      )}
      {node.properties?.scientific_name && (
        <>Scientific Name: {node.properties.scientific_name}<br /></>
      )}
      {node.properties?.journal && (
        <>Journal: {node.properties.journal}<br /></>
      )}
      {node.properties?.search_score && (
        <>Relevance: {node.properties.search_score.toFixed(3)}<br /></>
      )}
    </div>
  );
};

export default NodeTooltip;