import React from "react";
import GraphVisualization from "./GraphVisualization";
import "./KnowledgeGraph.css";

const KnowledgeGraph = ({ graphData, loading, error, onNodeClick }) => {
  return (
    <div className="knowledge-graph" style={{ height: "100vh", width: "100%" }}>
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
