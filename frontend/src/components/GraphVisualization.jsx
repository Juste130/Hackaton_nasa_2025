// src/components/GraphVisualization.jsx
import React, { useRef, useState, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useD3Graph } from '../hooks/useD3Graph';
import GraphLegend from './GraphLegend';
import NodeTooltip from './NodeTooltip';
import PublicationTooltip from './PublicationTooltip';
import './GraphVisualization.css';

const GraphVisualization = ({ graphData, loading, error, onNodeClick }) => {
  const containerRef = useRef(null);
  const [selectedNodeLocal, setSelectedNodeLocal] = useState(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, node: null });

  const handleNodeClick = useCallback((node, event) => {
    setSelectedNodeLocal(node);
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

  const { 
    centerGraph,
    zoomToFit,
    selectedNode,
    tooltipPosition,
    closeTooltip
  } = useD3Graph(containerRef, graphData, {
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
    enableZoom: true,
    enableDrag: true,
    forceStrength: -300,
    linkDistance: 100
  });

  // Empêcher le scroll du body quand le tooltip est ouvert
  useEffect(() => {
    const isOpen = selectedNode && selectedNode.label === 'Publication';
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [selectedNode]);

  // Calculer la position optimale du tooltip
  const getOptimalTooltipPosition = () => {
    if (!tooltipPosition) return { x: 100, y: 100 };
    
    const margin = 20;
    const tooltipWidth = 500;
    const tooltipHeight = 600;
    
    let x = tooltipPosition.x;
    let y = tooltipPosition.y;
    
    // Ajuster X si dépasse à droite
    if (x + tooltipWidth > window.innerWidth - margin) {
      x = window.innerWidth - tooltipWidth - margin;
    }
    
    // Ajuster X si dépasse à gauche
    if (x < margin) {
      x = margin;
    }
    
    // Ajuster Y si dépasse en bas
    if (y + tooltipHeight > window.innerHeight - margin) {
      y = window.innerHeight - tooltipHeight - margin;
    }
    
    // Ajuster Y si dépasse en haut
    if (y < margin) {
      y = margin;
    }
    
    return { x, y };
  };

  return (
    <div className="graph-visualization-content" style={{ 
      position: 'relative',
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div 
        ref={containerRef} 
        className="graph-container"
        style={{
          flex: 1,
          width: '100%',
          height: '100%',
          position: 'relative',
          zIndex: 1
        }}
      />

      {/* Warning if no edges */}
      {/* {graphData?.nodes?.length > 0 && (!graphData?.edges || graphData?.edges?.length === 0) && !loading && (
        <div style={{
          position: 'absolute',
          top: '70px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(255, 193, 7, 0.9)',
          color: '#000',
          padding: '10px 20px',
          borderRadius: '8px',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
        }}>
          ⚠️ Graph loaded with {graphData.nodes.length} nodes but no relationships. Try increasing the limit.
        </div>
      )} */}

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

      <GraphLegend />

      <div className="graph-toolbar">
        <button onClick={centerGraph} title="Center View">
          🎯
        </button>
        <button onClick={zoomToFit} title="Zoom to Fit">
          🔍
        </button>
      </div>

      {/* Tooltip normal pour hover */}
      {tooltip.visible && tooltip.node && tooltip.node.label !== 'Publication' && (
        <NodeTooltip
          node={tooltip.node}
          x={tooltip.x}
          y={tooltip.y}
        />
      )}

      {/* Publication Tooltip avec Portal */}
      {selectedNode && selectedNode.label === 'Publication' && createPortal(
        <>
          {/* Overlay */}
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.4)',
              zIndex: 9999,
              animation: 'fadeIn 0.2s ease-out'
            }}
            onClick={closeTooltip}
          />
          
          {/* Tooltip */}
          <PublicationTooltip
            nodeData={selectedNode}
            position={getOptimalTooltipPosition()}
            onClose={closeTooltip}
          />
        </>,
        document.body
      )}
    </div>
  );
};

export default GraphVisualization;