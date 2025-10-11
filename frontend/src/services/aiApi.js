const AI_API_BASE = process.env.REACT_APP_AI_API_URL || 'http://localhost:8000';

/**
 * Create a new AI session
 */
export const createSession = async (serviceType = 'summarizer') => {
  try {
    const response = await fetch(`${AI_API_BASE}/api/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        service_type: serviceType,
        metadata: {
          source: 'nasa-biospace-frontend',
          timestamp: new Date().toISOString()
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Session creation failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
};

/**
 * Summarize a single article by PMCID
 */
export const summarizeArticle = async (pmcid, sessionId = null) => {
  try {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (sessionId) {
      headers['X-Session-ID'] = sessionId;
    }

    const response = await fetch(`${AI_API_BASE}/api/summarize`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ pmcid })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Summarization failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error summarizing article:', error);
    throw error;
  }
};

/**
 * Summarize multiple articles (batch)
 */
export const summarizeMultipleArticles = async (pmcids, sessionId = null) => {
  try {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (sessionId) {
      headers['X-Session-ID'] = sessionId;
    }

    // Call summarize for each PMCID
    const summaries = await Promise.all(
      pmcids.map(pmcid => summarizeArticle(pmcid, sessionId))
    );

    return summaries;
  } catch (error) {
    console.error('Error summarizing multiple articles:', error);
    throw error;
  }
};

/**
 * Ask RAG assistant a question about specific articles
 */
export const askRAGQuestion = async (question, pmcids, sessionId) => {
  try {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (sessionId) {
      headers['X-Session-ID'] = sessionId;
    }

    const response = await fetch(`${AI_API_BASE}/api/rag/ask`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ 
        question,
        pmcids 
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `RAG query failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error asking RAG question:', error);
    throw error;
  }
};

/**
 * Get session history
 */
export const getSessionHistory = async (sessionId) => {
  try {
    const response = await fetch(`${AI_API_BASE}/api/sessions/${sessionId}/history`);

    if (!response.ok) {
      throw new Error(`Failed to get history: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting session history:', error);
    throw error;
  }
};