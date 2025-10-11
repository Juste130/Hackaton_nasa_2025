import { useMemo } from "react";
import { usePublicationsCache } from "../context/PublicationsContext";

// Handles filtering cached publications - INSTANT filtering
export const useCachedPublications = (organism = null, phenomenon = null) => {
  const cache = usePublicationsCache();
  
  // 🔥 Filtrer côté client - INSTANTANÉ
  const filteredPublications = useMemo(() => {
    if (!cache.data || !Array.isArray(cache.data) || cache.data.length === 0) {
      return [];
    }
    
    let filtered = cache.data.filter(pub => {
      // Vérifier que chaque publication a les propriétés nécessaires
      if (!pub || typeof pub !== 'object') return false;
      if (!pub.id) return false; // Publication doit avoir un ID
      
      return true;
    });
    
    // Appliquer les filtres
    if (organism) {
      filtered = filtered.filter(pub => {
        // Vérifications de sécurité pour chaque propriété
        const meshTerms = Array.isArray(pub.mesh_terms) ? pub.mesh_terms : [];
        const keywords = Array.isArray(pub.keywords) ? pub.keywords : [];
        const abstract = pub.abstract || "";
        
        return (
          meshTerms.some(term => 
            term && typeof term === 'string' && 
            term.toLowerCase().includes(organism.toLowerCase())
          ) ||
          keywords.some(keyword => 
            keyword && typeof keyword === 'string' &&
            keyword.toLowerCase().includes(organism.toLowerCase())
          ) ||
          abstract.toLowerCase().includes(organism.toLowerCase())
        );
      });
    }
    
    if (phenomenon) {
      filtered = filtered.filter(pub => {
        const meshTerms = Array.isArray(pub.mesh_terms) ? pub.mesh_terms : [];
        const keywords = Array.isArray(pub.keywords) ? pub.keywords : [];
        const abstract = pub.abstract || "";
        
        return (
          meshTerms.some(term => 
            term && typeof term === 'string' &&
            term.toLowerCase().includes(phenomenon.toLowerCase())
          ) ||
          keywords.some(keyword => 
            keyword && typeof keyword === 'string' &&
            keyword.toLowerCase().includes(phenomenon.toLowerCase())
          ) ||
          abstract.toLowerCase().includes(phenomenon.toLowerCase())
        );
      });
    }
    
    return filtered;
  }, [cache.data, organism, phenomenon]);

  // Calcul des années
  const { minYear, maxYear } = useMemo(() => {
    if (!filteredPublications.length) {
      const currentYear = new Date().getFullYear();
      return { minYear: currentYear, maxYear: currentYear };
    }
    
    const years = filteredPublications
      .map(pub => new Date(pub.date).getFullYear())
      .filter(y => !isNaN(y));
      
    return {
      minYear: years.length ? Math.min(...years) : new Date().getFullYear(),
      maxYear: years.length ? Math.max(...years) : new Date().getFullYear()
    };
  }, [filteredPublications]);

  const currentYear = new Date().getFullYear();

  return {
    publications: filteredPublications,
    loadingPublications: cache.loading,
    currentYear,
    minYear, 
    maxYear,
    totalCount: filteredPublications.length,
    allPublicationsCount: cache.data.length,
    cacheState: {
      loaded: cache.loaded,
      error: cache.error
    }
  };
};

export default useCachedPublications;