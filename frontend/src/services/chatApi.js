import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://46.62.215.105:8000/';

class ChatApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 60000, // 60 secondes pour les requêtes IA
      headers: {
        'Content-Type': 'application/json',
      }
    });
  }

  async createSession(serviceType = 'generic_rag') {
    try {
      const response = await this.client.post('/api/sessions', {
        service_type: serviceType,
        metadata: {
          client: 'web_chat',
          timestamp: new Date().toISOString()
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating chat session:', error);
      throw error;
    }
  }

  async askQuestion(question, sessionId = null) {
    try {
      const headers = {};
      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }

      const response = await this.client.post('/api/rag/generic', {
        question: question
      }, { headers });

      return response.data;
    } catch (error) {
      console.error('Error asking question:', error);
      throw error;
    }
  }

  async getSessionHistory(sessionId) {
    try {
      const response = await this.client.get(`/api/sessions/${sessionId}/history`);
      return response.data;
    } catch (error) {
      console.error('Error getting session history:', error);
      throw error;
    }
  }

  async deleteSession(sessionId) {
    try {
      const response = await this.client.delete(`/api/sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }

  async getHealthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }
}

export default new ChatApiService();