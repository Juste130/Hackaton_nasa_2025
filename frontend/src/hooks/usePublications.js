import { useEffect, useMemo, useState, useCallback } from "react";

// Cache global pour partager les données entre les instances du hook
const globalCache = {
  publications: new Map(), // Cache les publications par ID
  filters: new Map(), // Cache les résultats de filtrage
};

// Handles fetching and mapping publications from backend API with progressive loading
export const usePublications = (organism = null, phenomenon = null) => {
  const [publications, setPublications] = useState([]);
  const [loadingPublications, setLoadingPublications] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  const currentYear = useMemo(() => new Date().getFullYear(), []);

  // Clé unique pour le cache basée sur les filtres
  const cacheKey = useMemo(() => 
    `${organism || 'all'}-${phenomenon || 'all'}`, 
    [organism, phenomenon]
  );

  // Récupérer le compte total pour les filtres actuels
  const fetchTotalCount = useCallback(async () => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:3000";
      const params = new URLSearchParams();
      if (organism) params.append("organism", organism);
      if (phenomenon) params.append("phenomenon", phenomenon);
      
      const url = `${baseUrl}/api/publications/count?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      
      return data.count || 0;
    } catch (error) {
      console.error("Failed to fetch total count:", error);
      return 0;
    }
  }, [organism, phenomenon]);

  // Charger les publications par batch
  const loadPublicationsBatch = useCallback(async (skip = 0, take = 50) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:3000";
      const params = new URLSearchParams();
      if (organism) params.append("organism", organism);
      if (phenomenon) params.append("phenomenon", phenomenon);
      params.append("skip", skip.toString());
      params.append("take", take.toString());
      
      const url = `${baseUrl}/api/publications?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const apiData = await res.json();

      const mapped = (apiData || []).map((p) => {
        const meshTermsFlat = (p.publication_mesh_terms || [])
          .map((pm) => pm?.mesh_terms?.term)
          .filter(Boolean);

        return {
          id: p.id,
          pmcid: p.pmcid || "",
          title: p.title || "",
          date: p.publication_date
            ? new Date(p.publication_date).toISOString()
            : p.created_at || new Date().toISOString(),
          citations: 0,
          authors: Array.isArray(p.publication_authors)
            ? p.publication_authors.map((pa) => {
                const first = pa?.authors?.firstname
                  ? `${pa.authors.firstname} `
                  : "";
                const last = pa?.authors?.lastname || "";
                const full = `${first}${last}`.trim();
                return full || "Unknown";
              })
            : [],
          journal: p.journal || "",
          abstract: p.abstract || "",
          mesh_terms: meshTermsFlat,
          keywords: p.publication_keywords.map((pk) => pk?.keywords?.keyword).filter(Boolean) || [],
          entities: p.publication_entities || [],
          text_sections: p.text_sections || [],
          organisms: [],
          phenomena: [],
          systems: [],
          mission: "",
        };
      });

      return mapped;
    } catch (error) {
      console.error("Failed to fetch publications batch:", error);
      return [];
    }
  }, [organism, phenomenon]);

  // Chargement initial
  useEffect(() => {
    const controller = new AbortController();
    
    const initializeData = async () => {
      try {
        setLoadingPublications(true);
        
        // 1. Récupérer le compte total
        const count = await fetchTotalCount();
        setTotalCount(count);
        
        // 2. Charger le premier batch
        if (count > 0) {
          const firstBatch = await loadPublicationsBatch(0, 50);
          setPublications(firstBatch);
          setHasMore(firstBatch.length === 50 && count > 50);
        } else {
          setPublications([]);
          setHasMore(false);
        }
        
      } catch (error) {
        console.error("Failed to initialize publications:", error);
      } finally {
        setLoadingPublications(false);
      }
    };

    initializeData();
    
    return () => controller.abort();
  }, [organism, phenomenon, fetchTotalCount, loadPublicationsBatch]);

  // Fonction pour charger plus de données
  const loadMore = useCallback(async () => {
    if (loadingPublications || !hasMore) return;
    
    setLoadingPublications(true);
    try {
      const nextBatch = await loadPublicationsBatch(publications.length, 50);
      if (nextBatch.length > 0) {
        setPublications(prev => [...prev, ...nextBatch]);
        setHasMore(nextBatch.length === 50);
      } else {
        setHasMore(false);
      }
    } catch (error) {
      console.error("Failed to load more publications:", error);
    } finally {
      setLoadingPublications(false);
    }
  }, [publications.length, loadingPublications, hasMore, loadPublicationsBatch]);

  const { minYear, maxYear } = useMemo(() => {
    if (publications.length === 0)
      return { minYear: currentYear, maxYear: currentYear };
    
    const years = publications
      .map((pub) => new Date(pub.date).getFullYear())
      .filter((y) => !Number.isNaN(y));
    
    const computedMin = Math.min(...years);
    const computedMax = Math.max(...years);
    
    return {
      minYear: Number.isFinite(computedMin) ? computedMin : currentYear,
      maxYear: Number.isFinite(computedMax) ? computedMax : currentYear,
    };
  }, [publications, currentYear]);

  return {
    publications,
    loadingPublications,
    currentYear,
    minYear,
    maxYear,
    totalCount,
    hasMore,
    loadMore,
  };
};

export default usePublications;