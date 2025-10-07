// src/services/graphApi.js
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://46.62.215.105:8000";

class GraphApiService {
  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE}/api/graph`,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async getFullGraph(params = {}) {
    try {
      const { limit = 100, includeIsolated = false } = params;
      const response = await this.client.get("/full", {
        params: {
          limit,
          include_isolated: includeIsolated,
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching full graph:", error);
      throw error;
    }
  }

  async searchGraph(searchData) {
    try {
      const response = await this.client.post("/search", searchData);
      return response.data;
    } catch (error) {
      console.error("Error searching graph:", error);
      throw error;
    }
  }

  async filterGraph(filterData) {
    try {
      const response = await this.client.post("/filter", filterData);
      return response.data;
    } catch (error) {
      console.error("Error filtering graph:", error);
      throw error;
    }
  }

  async getNodeDetails(nodeId, params = {}) {
    try {
      const { includeNeighbors = true, maxNeighbors = 20 } = params;
      const response = await this.client.get(`/node/${nodeId}`, {
        params: {
          include_neighbors: includeNeighbors,
          max_neighbors: maxNeighbors,
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching node details:", error);
      throw error;
    }
  }

  async getGraphStats() {
    try {
      const response = await this.client.get("/stats");
      return response.data;
    } catch (error) {
      console.error("Error fetching graph stats:", error);
      throw error;
    }
  }
}

export default new GraphApiService();
