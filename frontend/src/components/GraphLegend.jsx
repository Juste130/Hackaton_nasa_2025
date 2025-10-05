// src/components/GraphLegend.jsx
import React from 'react';

const NODE_COLORS = {
  'Publication': '#3498db',
  'Organism': '#27ae60',
  'Phenomenon': '#e74c3c',
  'Finding': '#f39c12',
  'Platform': '#9b59b6',
  'Stressor': '#e67e22',
  'Author': '#34495e'
};

const GraphLegend = () => {
  return (
    <div className="graph-legend">
      <h4>Node Types</h4>
      {Object.entries(NODE_COLORS).map(([type, color]) => (
        <div key={type} className="legend-item">
          <div 
            className="legend-color" 
            style={{ backgroundColor: color }}
          />
          <span>{type}</span>
        </div>
      ))}
    </div>
  );
};

export default GraphLegend;