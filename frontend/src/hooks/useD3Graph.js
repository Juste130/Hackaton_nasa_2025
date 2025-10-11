// src/hooks/useD3Graph.js
import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const NODE_COLORS = {
  'Publication': '#3498db',
  'Organism': '#27ae60',
  'Phenomenon': '#e74c3c',
  'Finding': '#f39c12',
  'Platform': '#9b59b6',
  'Stressor': '#e67e22',
  'Author': '#34495e',
  'MeshTerm': '#95a5a6',
  'Keyword': '#1abc9c'
};

export const useD3Graph = (containerRef, data, options = {}) => {
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const simulationRef = useRef(null);
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const {
    onNodeClick = () => {},
    onNodeHover = () => {},
    enableZoom = true,
    enableDrag = true,
    forceStrength = -300,
    linkDistance = 100
  } = options;

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [containerRef]);

  // Initialize or update graph
  useEffect(() => {
    if (!data || !data.nodes || !containerRef.current) return;

    const { width, height } = dimensions;
    const container = d3.select(containerRef.current);

    // Clear previous content
    container.selectAll('*').remove();

    // Create SVG
    const svg = container
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`);

    svgRef.current = svg;

    // Create main group for zoom/pan
    const g = svg.append('g').attr('class', 'graph-group');

    // Setup zoom behavior
    if (enableZoom) {
      const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });

      svg.call(zoom);
    }

    // Clone data to avoid mutation
    const nodes = data.nodes.map(d => ({ ...d }));
    const edges = (data.edges || data.links || []).map(d => ({ ...d }));
    console.log(nodes);

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges)
        .id(d => d.id)
        .distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(forceStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => (d.size || 10) + 5));

    simulationRef.current = simulation;

    // Create links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.weight || 1));

    // Create nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('class', 'node')
      .attr('r', d => d.size || 10)
      .attr('fill', d => d.color || NODE_COLORS[d.label] || '#95a5a6')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        
        // Si c'est une publication, afficher le tooltip
        if (d.label === 'Publication') {
          const rect = containerRef.current.getBoundingClientRect();
          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          
          // ✅ Largeur et hauteur du tooltip
          const tooltipWidth = 500;
          const tooltipHeight = 600; // Estimation de la hauteur max
          const margin = 20;
          
          // ✅ Position par défaut (à droite du curseur)
          let tooltipX = event.clientX + margin;
          let tooltipY = event.clientY - margin;
          
          // ✅ Vérifier si le tooltip dépasse à droite
          if (tooltipX + tooltipWidth > window.innerWidth) {
            tooltipX = event.clientX - tooltipWidth - margin;
          }
          
          // ✅ S'assurer qu'il ne dépasse pas à gauche
          if (tooltipX < margin) {
            tooltipX = margin;
          }
          
          // ✅ Vérifier si le tooltip dépasse en bas
          if (tooltipY + tooltipHeight > window.innerHeight) {
            tooltipY = window.innerHeight - tooltipHeight - margin;
          }
          
          // ✅ S'assurer qu'il ne dépasse pas en haut
          if (tooltipY < margin) {
            tooltipY = margin;
          }
          
          setTooltipPosition({ x: tooltipX, y: tooltipY });
          setSelectedNode(d);
        }
        
        onNodeClick(d, event);
      })
      .on('mouseover', (event, d) => {
        // Effet hover sur le nœud
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr('r', (d.size || 10) * 1.3)
          .attr('stroke-width', 3);
        
        onNodeHover(d, event, true);
      })
      .on('mouseout', (event, d) => {
        // Retour à la taille normale
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr('r', d.size || 10)
          .attr('stroke-width', 2);
        
        onNodeHover(d, event, false);
      });

    // Add drag behavior
    if (enableDrag) {
      const drag = d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        });

      node.call(drag);
    }

    // Create labels
    const label = g.append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .attr('class', 'node-label')
      .attr('text-anchor', 'middle')
      .attr('dy', d => (d.size || 10) + 15)
      .style('font-size', '10px')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .text(d => {
        if (d.label === 'Publication') {
          const title = d.properties?.title || d.id;
          return title.length > 30 ? title.substring(0, 30) + '...' : title;
        }
        return d.properties?.name || d.properties?.scientific_name || d.id;
      });

    // Close tooltip on background click
    svg.on('click', () => {
      setSelectedNode(null);
    });

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      label
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });

    // Cleanup function
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };

  }, [data, dimensions, onNodeClick, onNodeHover, enableZoom, enableDrag, forceStrength, linkDistance, containerRef]);

  // Utility methods
  const centerGraph = () => {
    if (svgRef.current) {
      const svg = svgRef.current;
      const { width, height } = dimensions;
      
      svg.transition().duration(750).call(
        d3.zoom().transform,
        d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
      );
    }
  };

  const zoomToFit = () => {
    if (svgRef.current && data?.nodes) {
      const svg = svgRef.current;
      const g = svg.select('.graph-group');
      
      try {
        const bounds = g.node().getBBox();
        const { width, height } = dimensions;
        
        const scale = Math.min(
          width / bounds.width,
          height / bounds.height
        ) * 0.9;
        
        const translate = [
          (width - bounds.width * scale) / 2 - bounds.x * scale,
          (height - bounds.height * scale) / 2 - bounds.y * scale
        ];
        
        svg.transition().duration(750).call(
          d3.zoom().transform,
          d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        );
      } catch (error) {
        console.warn('Could not zoom to fit:', error);
      }
    }
  };

  const closeTooltip = () => {
    setSelectedNode(null);
  };

  return {
    centerGraph,
    zoomToFit,
    selectedNode,
    tooltipPosition,
    closeTooltip,
    simulation: simulationRef.current
  };
};

// ✅ Export par défaut AUSSI pour compatibilité
export default useD3Graph;