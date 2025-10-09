import React, { useEffect } from "react";
import GraphVisualization from "./GraphVisualization";
import "./KnowledgeGraph.css";

const KnowledgeGraph = ({ graphData, loading, error }) => {
  // Log pour debug
  useEffect(() => {
    console.log("Graph data in KnowledgeGraph:", graphData);
  }, [graphData]);

  return (
    <div className="knowledge-graph">
      <GraphVisualization
        graphData={graphData}
        loading={loading}
        error={error}
      />
    </div>
  );
};

export default KnowledgeGraph;
