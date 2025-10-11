import { useState, useCallback } from "react";
import graphApi from "../services/graphApi";

const useGraphData = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGraph = useCallback(async (params = {}, mode = 'auto') => {
    console.log('🚀 useGraphData: Starting to fetch graph with params:', params, 'mode:', mode);
    
    try {
      setLoading(true);
      setError(null);

      let response;

      if (mode === 'search') {
        console.log('� Using SEARCH mode');
        response = await graphApi.searchGraph(params);
      } else if (mode === 'filter') {
        console.log('🎯 Using FILTER mode');
        response = await graphApi.filterGraph(params);
      } else {
        // Mode automatique - déterminer selon les paramètres
        const hasFilters = params.organism || params.phenomenon || params.platform;
        const hasSearchQuery = params.query;
        
        console.log('🔍 Auto mode check:', { 
          hasFilters, 
          hasSearchQuery,
          organism: params.organism, 
          phenomenon: params.phenomenon 
        });

        if (hasSearchQuery) {
          console.log('🔍 Auto -> SEARCH mode');
          response = await graphApi.searchGraph(params);
        } else if (hasFilters) {
          console.log('🎯 Auto -> FILTER mode');
          
          const filterData = {
            node_types: ["Publication", "Organism", "Phenomenon"],
            organism: params.organism || null,
            phenomenon: params.phenomenon || null,
            platform: params.platform || null,
            limit: params.limit || 100
          };

          response = await graphApi.filterGraph(filterData);
        } else {
          console.log('📊 Auto -> FULL graph mode');
          response = await graphApi.getFullGraph(params);
        }
      }

      console.log("✅ Graph data received:", {
        nodes: response.nodes?.length,
        links: response.links?.length || response.edges?.length,
        stats: response.stats
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
        links: response.links || response.edges || [],
        stats: response.stats || {}
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