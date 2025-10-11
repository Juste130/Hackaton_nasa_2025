import { useState, useCallback } from "react";
import graphApi from "../services/graphApi";
import publicationApi from "../services/publicationApi";

const useGraphData = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 🔥 VERSION PARALLÈLE - 10x plus rapide
  const fetchPublicationTitlesParallel = async (publicationNodes) => {
    console.log(`⚡ Fetching ${publicationNodes.length} titles in parallel...`);
    
    // Limiter à 10 requêtes simultanées maximum
    const BATCH_SIZE = 10;
    const batches = [];
    
    for (let i = 0; i < publicationNodes.length; i += BATCH_SIZE) {
      batches.push(publicationNodes.slice(i, i + BATCH_SIZE));
    }
    
    const allResults = [];
    
    for (const batch of batches) {
      const batchPromises = batch.map(async (node) => {
        try {
          const pmcid = node.properties?.pmcid || node.pmcid;
          
          if (!pmcid) {
            return {
              ...node,
              properties: {
                ...node.properties,
                title: node.properties?.title || node.title || 'Untitled Publication'
              }
            };
          }
          
          const publicationData = await publicationApi.getPublicationByPMCID(pmcid);
          return {
            ...node,
            properties: {
              ...node.properties,
              title: publicationData.title || node.properties?.title || 'Untitled Publication',
              fullTitle: publicationData.title
            }
          };
        } catch (err) {
          console.warn(`⚠️ Could not fetch title for ${node.id}:`, err.message);
          return {
            ...node,
            properties: {
              ...node.properties,
              title: node.properties?.title || node.title || 'Untitled Publication'
            }
          };
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      allResults.push(...batchResults);
    }
    
    return allResults;
  };

  const fetchGraph = useCallback(async (params = {}, mode = 'auto') => {
    console.log('🚀 useGraphData: Starting to fetch graph with params:', params, 'mode:', mode);
    
    try {
      setLoading(true);
      setError(null);

      let response;

      if (mode === 'search') {
        console.log('🔍 Using SEARCH mode');
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
            filters: { // 🔥 CORRECTION: Ajouter la clé 'filters'
              organisms: params.organism ? [params.organism] : [],
              phenomena: params.phenomenon ? [params.phenomenon] : [],
            },
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

      // 🔥 Étape 2: Transformation initiale RAPIDE
      const initialTransformedData = {
        nodes: (response.nodes || []).map(node => {
          if (node.label === 'Publication' || node.type === 'Publication') {
            return {
              ...node,
              properties: {
                ...node.properties,
                title: node.properties?.title || node.title || node.name || 'Loading title...'
              }
            };
          }
          return node;
        }),
        links: response.links || response.edges || [],
        stats: response.stats || {}
      };

      // 🔥 AFFICHER IMMÉDIATEMENT le graphe sans attendre les titres
      setGraphData(initialTransformedData);

      // 🔥 Étape 3: Récupérer les titres en ARRIÈRE-PLAN
      const publicationNodes = initialTransformedData.nodes.filter(n => 
        n.label === 'Publication' || n.type === 'Publication'
      );
      
      if (publicationNodes.length > 0) {
        console.log(`📚 Found ${publicationNodes.length} publication nodes, fetching titles in background...`);
        
        // Ne pas attendre cette promesse - laisser tourner en background
        fetchPublicationTitlesParallel(publicationNodes).then(publicationNodesWithTitles => {
          console.log('✅ Titles loaded in background, updating graph...');
          
          // Mettre à jour SILENCIEUSEMENT avec les titres complets
          const finalTransformedData = {
            nodes: initialTransformedData.nodes.map(node => {
              if (node.label === 'Publication' || node.type === 'Publication') {
                const nodeWithTitle = publicationNodesWithTitles.find(n => n.id === node.id);
                return nodeWithTitle || node;
              }
              return node;
            }),
            links: initialTransformedData.links,
            stats: initialTransformedData.stats
          };
          
          setGraphData(finalTransformedData);
        }).catch(err => {
          console.warn('❌ Background title loading failed, but graph is already displayed:', err);
        });
      }
      
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