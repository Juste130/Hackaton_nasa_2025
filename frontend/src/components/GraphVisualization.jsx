// src/components/GraphVisualization.jsx
import React, { useRef, useState, useCallback } from 'react';
import { useD3Graph } from '../hooks/useD3Graph';
import GraphLegend from './GraphLegend';
import NodeTooltip from './NodeTooltip';
import './GraphVisualization.css';

const GraphVisualization = ({ graphData, loading, error, onNodeClick }) => {
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, node: null });

  const handleNodeClick = useCallback((node, event) => {
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
    console.log('Node clicked:', node);
  }, [onNodeClick]);

  const handleNodeHover = useCallback((node, event, isHover) => {
    if (isHover) {
      setTooltip({
        visible: true,
        x: event.pageX + 10,
        y: event.pageY - 10,
        node
      });
    } else {
      setTooltip({ visible: false, x: 0, y: 0, node: null });
    }
  }, []);

  const { centerGraph, zoomToFit } = useD3Graph(containerRef, graphData, {
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
    enableZoom: true,
    enableDrag: true,
    forceStrength: -300,
    linkDistance: 100
  });

  return (
    <div className="graph-visualization-content">
      {error && (
        <div className="graph-error-message">
          <p>Error: {error}</p>
        </div>
      )}

      {loading && (
        <div className="graph-loading-overlay">
          <div className="graph-loading-spinner">
            <h3>Loading Graph...</h3>
            <p>Fetching data from knowledge base</p>
          </div>
        </div>
      )}

      <div 
        ref={containerRef} 
        className="graph-container"
      />

      <GraphLegend />

      <div className="graph-toolbar">
        <button onClick={centerGraph} title="Center View">
          🎯
        </button>
        <button onClick={zoomToFit} title="Zoom to Fit">
          🔍
        </button>
      </div>

      {tooltip.visible && (
        <NodeTooltip
          node={tooltip.node}
          x={tooltip.x}
          y={tooltip.y}
        />
      )}
    </div>
  );
};

export default GraphVisualization;