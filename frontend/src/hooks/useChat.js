import { useState, useEffect, useCallback } from 'react';
import chatApiService from '../services/chatApi';

export const useChat = () => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialiser la session au premier rendu
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setError(null);
      const sessionData = await chatApiService.createSession('generic_rag');
      setSessionId(sessionData.session_id);
      
      // Message de bienvenue
      setMessages([{
        id: 1,
        text: "Hello! I'm your NASA space biology assistant. I can help you explore research on microgravity effects, space medicine, plant biology in space, and much more. What would you like to know?",
        isBot: true,
        timestamp: new Date(),
        citations: [],
        toolsUsed: []
      }]);
      
      setIsInitialized(true);
    } catch (err) {
      console.error('Failed to initialize chat session:', err);
      setError('Failed to connect to AI assistant. Please try again.');
    }
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isLoading) return;

    // Ajouter le message utilisateur
    const userMessage = {
      id: Date.now(),
      text: messageText,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Appeler l'API IA
      const response = await chatApiService.askQuestion(messageText, sessionId);
      
      // Ajouter la réponse de l'IA
      const botMessage = {
        id: Date.now() + 1,
        text: response.answer,
        isBot: true,
        timestamp: new Date(),
        citations: response.citations || [],
        toolsUsed: response.tools_used || [],
        confidence: response.confidence,
        reasoningTrace: response.reasoning_trace || []
      };

      setMessages(prev => [...prev, botMessage]);
      
    } catch (err) {
      console.error('Error sending message:', err);
      
      // Message d'erreur
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I encountered an error processing your question. Please try again or rephrase your question.",
        isBot: true,
        timestamp: new Date(),
        isError: true,
        citations: []
      };
      
      setMessages(prev => [...prev, errorMessage]);
      setError('Failed to get response from AI assistant');
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = useCallback(async () => {
    try {
      if (sessionId) {
        await chatApiService.deleteSession(sessionId);
      }
      await initializeSession();
    } catch (err) {
      console.error('Error clearing chat:', err);
      // Fallback: clear locally
      setMessages([{
        id: 1,
        text: "Chat cleared. I'm ready to help with your space biology questions!",
        isBot: true,
        timestamp: new Date(),
        citations: []
      }]);
    }
  }, [sessionId]);

  const retryLastMessage = useCallback(() => {
    const lastUserMessage = messages
      .filter(msg => !msg.isBot)
      .pop();
    
    if (lastUserMessage) {
      sendMessage(lastUserMessage.text);
    }
  }, [messages, sendMessage]);

  return {
    messages,
    isLoading,
    error,
    isInitialized,
    sessionId,
    sendMessage,
    clearChat,
    retryLastMessage
  };
};