// src/services/graphApi.js
import axios from "axios";

// API Python Neo4j sur le port 8000
const AI_API_BASE = process.env.REACT_APP_AI_API_URL || "http://localhost:8000";

class GraphApiService {
  constructor() {
    this.client = axios.create({
      baseURL: `${AI_API_BASE}/api`, // Utiliser l'API Python
      timeout: 300000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async getFullGraph(params = {}) {
    try {
      const { limit = 100, includeIsolated = false } = params;
      
      console.log('Fetching full graph with params:', { limit, includeIsolated });
      
      const response = await this.client.get("/graph/full?limit=100", {
        params: {
          limit,
          include_isolated: includeIsolated,
        },
      });
      
      console.log('Graph API response:', response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching full graph:", error);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
      throw error;
    }
  }

  async searchGraph(searchData) {
    try {
      console.log('Searching graph with:', searchData);
      const response = await this.client.post("/graph/search", searchData);
      console.log('Search response:', response.data);
      return response.data;
    } catch (error) {
      console.error("Error searching graph:", error);
      throw error;
    }
  }

  async filterGraph(filterData) {
    try {
      console.log('Filtering graph with:', filterData);
      const response = await this.client.post("/graph/filter", filterData);
      console.log('Filter response:', response.data);
      return response.data;
    } catch (error) {
      console.error("Error filtering graph:", error);
      throw error;
    }
  }

  async getNodeDetails(nodeId, params = {}) {
    try {
      const { includeNeighbors = true, maxNeighbors = 20 } = params;
      console.log('Fetching node details for:', nodeId);
      
      const response = await this.client.get(`/graph/node/${nodeId}`, {
        params: {
          include_neighbors: includeNeighbors,
          max_neighbors: maxNeighbors,
        },
      });
      
      console.log('Node details response:', response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching node details:", error);
      throw error;
    }
  }

  async getGraphStats() {
    try {
      console.log('Fetching graph stats');
      const response = await this.client.get("/graph/stats");
      console.log('Stats response:', response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching graph stats:", error);
      throw error;
    }
  }
}

export default new GraphApiService();
