import { useEffect, useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3000";

// Hook pour charger les filtres dynamiques depuis Neo4j
export const useGraphFilters = () => {
  const [organisms, setOrganisms] = useState([]);
  const [phenomena, setPhenomena] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        setLoading(true);
        
        // Charger les organisms
        const organismsRes = await fetch(`${API_URL}/api/filters/organisms`);
        if (!organismsRes.ok) throw new Error("Failed to fetch organisms");
        const organismsData = await organismsRes.json();
        setOrganisms(organismsData);

        // Charger les phenomena
        const phenomenaRes = await fetch(`${API_URL}/api/filters/phenomena`);
        if (!phenomenaRes.ok) throw new Error("Failed to fetch phenomena");
        const phenomenaData = await phenomenaRes.json();
        setPhenomena(phenomenaData);

        setError(null);
      } catch (err) {
        console.error("Error fetching graph filters:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchFilters();
  }, []);

  return {
    organisms,
    phenomena,
    loading,
    error,
  };
};
