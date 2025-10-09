import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:3000";

class PublicationApiService {
  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE}/api`,
      timeout: 10000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  /**
   * Obtenir une publication par ID
   */
  async getPublicationById(id) {
    try {
      console.log('📚 Fetching publication by ID:', id);
      const response = await this.client.get(`/publications/${id}`);
      console.log('✅ Publication fetched:', response.data);
      return response.data;
    } catch (error) {
      console.error("❌ Error fetching publication by ID:", error);
      throw error;
    }
  }

  /**
   * Obtenir une publication par PMCID
   */
  async getPublicationByPMCID(pmcid) {
    try {
      console.log('📚 Fetching publication by PMCID:', pmcid);
      const response = await this.client.get(`/publications/pmcid/${pmcid}`);
      console.log('✅ Publication fetched:', response.data);
      return response.data;
    } catch (error) {
      console.error("❌ Error fetching publication by PMCID:", error);
      throw error;
    }
  }

  /**
   * Obtenir toutes les publications avec filtres
   */
  async getPublications(filters = {}) {
    try {
      console.log('📚 Fetching publications with filters:', filters);
      const response = await this.client.get('/publications', {
        params: filters
      });
      console.log('✅ Publications fetched:', response.data.length);
      return response.data;
    } catch (error) {
      console.error("❌ Error fetching publications:", error);
      throw error;
    }
  }
}

export default new PublicationApiService();