import { Router } from "express";
import axios from "axios";

const router = Router();

// URL de l'API Neo4j (Python sur port 8000)
const NEO4J_API_URL = process.env.NEO4J_API_URL || "http://localhost:8000";

// GET /api/filters/organisms - Récupère la liste des organismes depuis Neo4j
router.get("/organisms", async (req, res) => {
  try {
    // Appel à l'API Neo4j pour obtenir les top organismes étudiés
    const response = await axios.get(`${NEO4J_API_URL}/api/graph/stats`);
    console.log(response.data);
    
    // Extraire les organismes des stats
    const organisms = response.data.analytics.top_organisms || [];
    
    // Formater pour le frontend
    const formattedOrganisms = organisms.map((org: any) => ({
      name: org.organism || org.name,
      scientific_name: org.scientific_name,
      category: org.category,
      study_count: org.study_count,
    }));

    res.json(formattedOrganisms);
  } catch (error: any) {
    console.error("Error fetching organisms from Neo4j:", error.message);
    res.status(500).json({ 
      error: "Failed to fetch organisms",
      message: error.message 
    });
  }
});

// GET /api/filters/phenomena - Récupère la liste des phénomènes depuis Neo4j
router.get("/phenomena", async (req, res) => {
  try {
    // Appel à l'API Neo4j pour obtenir les top phénomènes investigués
    const response = await axios.get(`${NEO4J_API_URL}/api/graph/stats`);
    
    // Extraire les phénomènes des stats
    const phenomena = response.data.analytics.top_phenomena || [];
    
    // Formater pour le frontend
    const formattedPhenomena = phenomena.map((phen: any) => ({
      name: phen.phenomenon || phen.name,
      system: phen.biological_system || phen.system,
      investigation_count: phen.investigation_count,
    }));

    res.json(formattedPhenomena);
  } catch (error: any) {
    console.error("Error fetching phenomena from Neo4j:", error.message);
    res.status(500).json({ 
      error: "Failed to fetch phenomena",
      message: error.message 
    });
  }
});

// POST /api/filters/publications-by-graph - Filtre les publications via Neo4j
router.post("/publications-by-graph", async (req, res) => {
  try {
    const { organisms, phenomena } = req.body;

    // Construire la requête pour Neo4j
    const filterRequest = {
      node_types: ["Publication"],
      filters: {
        organisms: organisms || [],
        phenomena: phenomena || [],
      },
      limit: 100,
    };

    // Appel à l'API Neo4j pour obtenir les publications filtrées
    const response = await axios.post(
      `${NEO4J_API_URL}/api/graph/filter`,
      filterRequest
    );

    // Extraire les PMCIDs des publications correspondantes
    const nodes = response.data.nodes || [];
    const pmcids = nodes
      .filter((node: any) => node.label === "Publication")
      .map((node: any) => node.properties.pmcid)
      .filter(Boolean);

    res.json({ pmcids });
  } catch (error: any) {
    console.error("Error filtering publications via Neo4j:", error.message);
    res.status(500).json({ 
      error: "Failed to filter publications",
      message: error.message 
    });
  }
});

export default router;
