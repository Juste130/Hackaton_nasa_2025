import { useEffect, useMemo, useState } from "react";

// Handles fetching and mapping publications from backend API
export const usePublications = (organism = null, phenomenon = null) => {
  const [publications, setPublications] = useState([]);
  const [loadingPublications, setLoadingPublications] = useState(true);

  const currentYear = useMemo(() => new Date().getFullYear(), []);

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        setLoadingPublications(true);
        const baseUrl =
          process.env.REACT_APP_API_URL || "http://localhost:3000";
        
        // Construire l'URL avec les paramètres de filtre
        const params = new URLSearchParams();
        if (organism) params.append("organism", organism);
        if (phenomenon) params.append("phenomenon", phenomenon);
        
        const url = `${baseUrl}/api/publications${params.toString() ? `?${params.toString()}` : ''}`;
        const res = await fetch(url, { signal: controller.signal });
        if (!res.ok) throw new Error(`API error ${res.status}`);
        const apiData = await res.json();

        const mapped = (apiData || []).map((p) => {
          // Les mesh terms sont déjà inclus dans la réponse
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

        setPublications(mapped);
      } catch (e) {
        if (e.name !== "AbortError") {
          console.error("Failed to fetch publications:", e);
        }
      } finally {
        setLoadingPublications(false);
      }
    };
    fetchData();
    return () => controller.abort();
  }, [organism, phenomenon]); // Re-fetch when filters change

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
  };
};

export default usePublications;
