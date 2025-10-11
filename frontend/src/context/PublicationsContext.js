import React, { createContext, useContext, useEffect, useState } from 'react';

const PublicationsContext = createContext(null);

export const PublicationsProvider = ({ children }) => {
  const [publicationsCache, setPublicationsCache] = useState({
    data: [],
    loading: false,
    loaded: false,
    error: null
  });

  // 🔥 CHARGEMENT AU MONTAGE DU PROVIDER (début de l'app)
  useEffect(() => {
    const loadAllPublications = async () => {
      // Ne recharger que si pas déjà chargé
      if (publicationsCache.loaded || publicationsCache.loading) {
        return;
      }

      setPublicationsCache(prev => ({ ...prev, loading: true, error: null }));
      
      try {
        const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:3000";
        const allPublications = [];
        let skip = 0;
        const take = 100; // Batch de 100
        
        console.log('🚀 Starting pre-loading of all publications...');
        
        while (true) {
          const response = await fetch(
            `${baseUrl}/api/publications?skip=${skip}&take=${take}`
          );
          
          if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
          }
          
          const batch = await response.json();
          
          if (batch.length === 0) break;
          
          const mapped = batch.map((p) => {
            // Vérifications de sécurité
            if (!p || typeof p !== 'object') {
              console.warn('Skipping invalid publication:', p);
              return null;
            }
            
            return {
              id: p.id || `missing-id-${Math.random()}`,
              pmcid: p.pmcid || "",
              title: p.title || "No title available",
              date: p.publication_date ? new Date(p.publication_date).toISOString() : new Date().toISOString(),
              authors: (Array.isArray(p.publication_authors) ? p.publication_authors : []).map((pa) => {
                if (!pa || !pa.authors) return "Unknown";
                const first = pa.authors.firstname ? `${pa.authors.firstname} ` : "";
                const last = pa.authors.lastname || "";
                return `${first}${last}`.trim() || "Unknown";
              }),
              journal: p.journal || "No journal",
              abstract: p.abstract || "No abstract available",
              mesh_terms: (Array.isArray(p.publication_mesh_terms) ? p.publication_mesh_terms : [])
                .map((pm) => pm?.mesh_terms?.term)
                .filter(term => term && typeof term === 'string'),
              keywords: (Array.isArray(p.publication_keywords) ? p.publication_keywords : [])
                .map((pk) => pk?.keywords?.keyword)
                .filter(keyword => keyword && typeof keyword === 'string'),
              // Valeurs par défaut importantes
              phenomena: [],
              systems: [],
              mission: "",
              organisms: [],
            };
          }).filter(Boolean); // Filtrer les valeurs null

          allPublications.push(...mapped);
          skip += take;
          
          console.log(`📥 Loaded batch: ${batch.length} publications (total: ${allPublications.length})`);
          
          // Arrêter si on a moins de publications que le batch size
          if (batch.length < take) break;
        }

        console.log(`✅ Pre-loading completed: ${allPublications.length} publications loaded`);
        
        setPublicationsCache({
          data: allPublications,
          loading: false,
          loaded: true,
          error: null
        });
        
      } catch (error) {
        console.error('❌ Failed to pre-load publications:', error);
        setPublicationsCache({
          data: [],
          loading: false,
          loaded: false,
          error: error.message || 'Failed to load publications'
        });
      }
    };

    loadAllPublications();
  }, []); // 🔥 S'exécute une seule fois au démarrage de l'app

  return (
    <PublicationsContext.Provider value={publicationsCache}>
      {children}
    </PublicationsContext.Provider>
  );
};

export const usePublicationsCache = () => {
  const context = useContext(PublicationsContext);
  if (!context) {
    throw new Error('usePublicationsCache must be used within PublicationsProvider');
  }
  return context;
};