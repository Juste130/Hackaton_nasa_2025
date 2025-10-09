import { useState } from "react";
import graphApi from "../services/graphApi";

const useGraphData = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGraph = async (params = {}) => {
    console.log('🚀 useGraphData: Starting to fetch graph with params:', params);
    
    try {
      setLoading(true);
      setError(null);

      const response = await graphApi.getFullGraph(params);
      console.log("✅ useGraphData: Fetched graph data:", response);

      // ✅ Transformer "edges" en "links" si nécessaire
      const transformedData = {
        nodes: response.nodes || [],
        links: response.links || response.edges || []  // Support both formats
      };

      // Valider la structure des données
      if (!transformedData.nodes || !transformedData.links) {
        console.error('❌ Invalid graph data structure:', response);
        throw new Error("Invalid graph data structure");
      }

      // S'assurer que nodes et links sont des tableaux
      const validatedData = {
        nodes: Array.isArray(transformedData.nodes) ? transformedData.nodes : [],
        links: Array.isArray(transformedData.links) ? transformedData.links : [],
      };

      console.log(`✅ Validated graph data: ${validatedData.nodes.length} nodes, ${validatedData.links.length} links`);
      
      // Vérifier que les données ne sont pas vides
      if (validatedData.nodes.length === 0) {
        console.warn('⚠️ No nodes in graph data');
      }
      
      setGraphData(validatedData);
    } catch (err) {
      console.error("❌ useGraphData: Error fetching graph:", err);
      setError(err.message || "Failed to load graph");
      // Définir des données vides en cas d'erreur
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  };

  return {
    graphData,
    loading,
    error,
    fetchGraph,
  };
};

export default useGraphData;
