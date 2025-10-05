// import React, { useEffect, useRef, useCallback, useMemo } from 'react';
// import './KnowledgeGraph.css';

// const KnowledgeGraph = ({ publications, onNodeClick }) => {
//   const graphRef = useRef(null);

//   // Memoize graph data to avoid recalculation on every render
//   const graphData = useMemo(() => {
//     // Concept nodes
//     const conceptNodes = [
//       { id: 'microgravity', name: 'Microgravity', type: 'concept', size: 40 },
//       { id: 'radiation', name: 'Radiation', type: 'concept', size: 35 },
//       { id: 'bone', name: 'Bone Density', type: 'concept', size: 30 },
//       { id: 'immune', name: 'Immune System', type: 'concept', size: 25 },
//       { id: 'plants', name: 'Plant Growth', type: 'concept', size: 20 },
//     ];

//     // Publication nodes
//     const publicationNodes = publications.map(pub => ({
//       id: `pub-${pub.id}`,
//       name: pub.title.substring(0, 30) + '...',
//       type: 'publication',
//       publication: pub,
//       size: 15
//     }));

//     const allNodes = [...conceptNodes, ...publicationNodes];

//     // Helper function to normalize IDs
//     const normalizeId = (str) => str.toLowerCase().replace(/\s+/g, '-');

//     // Create links from publications to concepts
//     const links = [];
    
//     publications.forEach(pub => {
//       const pubId = `pub-${pub.id}`;
      
//       // Links from phenomena
//       if (pub.phenomena && Array.isArray(pub.phenomena)) {
//         pub.phenomena.forEach(phenomenon => {
//           const sourceId = normalizeId(phenomenon);
//           if (allNodes.find(n => n.id === sourceId)) {
//             links.push({
//               source: sourceId,
//               target: pubId,
//               strength: 1
//             });
//           }
//         });
//       }
      
//       // Links from systems
//       if (pub.systems && Array.isArray(pub.systems)) {
//         pub.systems.forEach(system => {
//           const sourceId = normalizeId(system);
//           if (allNodes.find(n => n.id === sourceId)) {
//             links.push({
//               source: sourceId,
//               target: pubId,
//               strength: 1
//             });
//           }
//         });
//       }
      
//       // Links from organisms
//       if (pub.organisms && Array.isArray(pub.organisms)) {
//         pub.organisms.forEach(organism => {
//           const sourceId = normalizeId(organism);
//           if (allNodes.find(n => n.id === sourceId)) {
//             links.push({
//               source: sourceId,
//               target: pubId,
//               strength: 1
//             });
//           }
//         });
//       }
//     });

//     return { nodes: allNodes, links };
//   }, [publications]);

//   // Calculate node position
//   const getNodePosition = useCallback((index, totalNodes) => {
//     const cols = 5;
//     const x = 100 + (index % cols) * 150;
//     const y = 100 + Math.floor(index / cols) * 120;
//     return { x, y };
//   }, []);

//   // Draw the graph
//   const drawGraph = useCallback(() => {
//     const svg = graphRef.current;
//     if (!svg) return;

//     // Clear previous content
//     svg.innerHTML = '';

//     // Create links first (so they appear behind nodes)
//     graphData.links.forEach(link => {
//       const sourceNode = graphData.nodes.find(n => n.id === link.source);
//       const targetNode = graphData.nodes.find(n => n.id === link.target);
      
//       if (sourceNode && targetNode) {
//         const sourceIndex = graphData.nodes.indexOf(sourceNode);
//         const targetIndex = graphData.nodes.indexOf(targetNode);
        
//         const sourcePos = getNodePosition(sourceIndex);
//         const targetPos = getNodePosition(targetIndex);

//         const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
//         line.setAttribute('x1', sourcePos.x);
//         line.setAttribute('y1', sourcePos.y);
//         line.setAttribute('x2', targetPos.x);
//         line.setAttribute('y2', targetPos.y);
//         line.setAttribute('class', 'graph-link');
//         line.setAttribute('stroke-width', link.strength);
        
//         svg.appendChild(line);
//       }
//     });

//     // Create nodes and labels
//     graphData.nodes.forEach((node, index) => {
//       const position = getNodePosition(index);
      
//       // Create circle
//       const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
//       circle.setAttribute('cx', position.x);
//       circle.setAttribute('cy', position.y);
//       circle.setAttribute('r', node.size);
//       circle.setAttribute('class', `graph-node graph-node-${node.type}`);
//       circle.setAttribute('data-id', node.id);
      
//       // Add click handler for publication nodes
//       if (node.type === 'publication' && node.publication) {
//         circle.style.cursor = 'pointer';
//         circle.addEventListener('click', () => {
//           if (onNodeClick) {
//             onNodeClick(node.publication);
//           }
//         });
        
//         // Add hover effect
//         circle.addEventListener('mouseenter', () => {
//           circle.setAttribute('r', node.size + 3);
//         });
//         circle.addEventListener('mouseleave', () => {
//           circle.setAttribute('r', node.size);
//         });
//       }

//       svg.appendChild(circle);

//       // Create label
//       const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
//       text.setAttribute('x', position.x);
//       text.setAttribute('y', position.y + node.size + 15);
//       text.setAttribute('text-anchor', 'middle');
//       text.setAttribute('class', 'graph-label');
//       text.textContent = node.name;
//       svg.appendChild(text);
//     });
//   }, [graphData, getNodePosition, onNodeClick]);

//   // Effect to draw graph and handle resize
//   useEffect(() => {
//     drawGraph();
    
//     const handleResize = () => {
//       drawGraph();
//     };
    
//     window.addEventListener('resize', handleResize);
    
//     return () => {
//       window.removeEventListener('resize', handleResize);
//     };
//   }, [drawGraph]);

//   // Calculate statistics
//   const stats = useMemo(() => {
//     const conceptCount = graphData.nodes.filter(n => n.type === 'concept').length;
//     const publicationCount = graphData.nodes.filter(n => n.type === 'publication').length;
//     const linkCount = graphData.links.length;
    
//     return { conceptCount, publicationCount, linkCount };
//   }, [graphData]);

//   return (
//     <div className="knowledge-graph">
//       <div className="graph-header">
//         <h3>Knowledge Graph</h3>
//         <p>Explore connections between concepts and research papers</p>
//         <div className="graph-legend">
//           <div className="legend-item">
//             <span className="legend-color concept"></span>
//             Concepts ({stats.conceptCount})
//           </div>
//           <div className="legend-item">
//             <span className="legend-color publication"></span>
//             Publications ({stats.publicationCount})
//           </div>
//           <div className="legend-item" style={{ marginLeft: '10px', opacity: 0.7 }}>
//             {stats.linkCount} connections
//           </div>
//         </div>
//       </div>
//       <div className="graph-container">
//         <svg 
//           ref={graphRef} 
//           className="graph-svg"
//           viewBox="0 0 800 600"
//           preserveAspectRatio="xMidYMid meet"
//           role="img"
//           aria-label="Knowledge graph showing connections between concepts and publications"
//         ></svg>
//       </div>
//       <div className="graph-tips">
//         <p>💡 <strong>Tip:</strong> Click on publication nodes to select them for AI analysis</p>
//       </div>
//     </div>
//   );
// };

// export default KnowledgeGraph;

// src/components/KnowledgeGraph.jsx - Mise à jour
import React from 'react';
import GraphVisualization from './GraphVisualization';
import './KnowledgeGraph.css';

const KnowledgeGraph = ({ graphData, loading, error, onNodeClick }) => {
  return (
    <div className="knowledge-graph" style={{ height: '100vh', width: '100%' }}>
      <GraphVisualization 
        graphData={graphData}
        loading={loading}
        error={error}
        onNodeClick={onNodeClick}
      />
    </div>
  );
};

export default KnowledgeGraph;