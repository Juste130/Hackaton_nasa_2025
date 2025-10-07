import { useEffect, useMemo, useState } from "react";

// Handles fetching and mapping publications from backend API
export const usePublications = () => {
  const [publications, setPublications] = useState([]);
  const [loadingPublications, setLoadingPublications] = useState(true);

  const currentYear = useMemo(() => new Date().getFullYear(), []);

  const getMeshTerms = async (id) => {
    const baseUrl = process.env.REACT_APP_API_URL || "http://localhost:3000";
    try {
      const res = await fetch(`${baseUrl}/api/mesh_terms/${id}`);
      if (!res.ok) {
        console.error(
          `[mesh_terms] fetch failed id=${id} status=${res.status}`
        );
        return [];
      }
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error(`[mesh_terms] exception id=${id}`, err);
      return [];
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        setLoadingPublications(true);
        const baseUrl =
          process.env.REACT_APP_API_URL || "http://localhost:3000";
        const res = await fetch(`${baseUrl}/api/publications`);
        if (!res.ok) throw new Error(`API error ${res.status}`);
        const apiData = await res.json();

        const mapped = await Promise.all(
          (apiData || []).map(async (p) => {
            const meshTermArrays = await Promise.all(
              (p.publication_mesh_terms || []).map((pm) =>
                getMeshTerms(pm.mesh_term_id)
              )
            );
            const meshTermsFlat = meshTermArrays
              .flat()
              .map((mt) => (typeof mt === "string" ? mt : mt?.term || ""))
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
              keywords: p.publication_keywords.map((pk) => pk.keyword_id) || [],
              entities: p.publication_entities || [],
              text_sections: p.text_sections || [],
              organisms: [],
              phenomena: [],
              systems: [],
              mission: "",
            };
          })
        );

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
  }, []);

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
