import { useState, useCallback } from "react";
import graphApi from "../services/graphApi";

const useGraphData = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGraph = useCallback(async (params = {}) => {
    console.log('🚀 useGraphData: Starting to fetch graph with params:', params);
    
    try {
      setLoading(true);
      setError(null);

      let response;

      // 🔥 LOGIQUE DE FILTRAGE
      const hasFilters = params.organism || params.phenomenon;
      console.log('🔍 Filter check:', { 
        hasFilters, 
        organism: params.organism, 
        phenomenon: params.phenomenon 
      });

      if (hasFilters) {
        console.log('🎯 Using FILTER mode');
        
        const filterData = {
          node_types: ["Publication", "Organism", "Phenomenon"],
          filters: {
            organisms: params.organism ? [params.organism] : [],
            phenomena: params.phenomenon ? [params.phenomenon] : [],
          },
          limit: params.limit || 100
        };

        response = await graphApi.filterGraph(filterData);
      } else {
        console.log('📊 Using FULL graph mode');
        response = await graphApi.getFullGraph(params);
      }

      console.log("✅ Graph data received:", {
        nodes: response.nodes?.length,
        links: response.links?.length || response.edges?.length
      });

      // Transformation des données
      const transformedData = {
        nodes: (response.nodes || []).map(node => {
          // Pour les publications, s'assurer d'avoir le titre dans properties
          if (node.label === 'Publication' || node.type === 'Publication') {
            return {
              ...node,
              properties: {
                ...node.properties,
                // Extraire le titre de différents champs possibles
                title: node.properties?.title || node.title || node.name || node.id
              }
            };
          }
          return node;
        }),
        links: response.links || response.edges || []
      };

       // 🔍 DEBUG: Vérifier les nœuds Publication transformés

      const publicationNodes = transformedData.nodes.filter(n => 
        n.label === 'Publication' || n.type === 'Publication'
      );
      console.log('📚 Transformed Publication nodes:', publicationNodes);

      setGraphData(transformedData);
      
    } catch (err) {
      console.error("❌ Error fetching graph:", err);
      setError(err.message || "Failed to load graph");
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    graphData,
    loading,
    error,
    fetchGraph,
  };
};

export default useGraphData;