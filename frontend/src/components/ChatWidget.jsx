import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';
import { useChat as useChatContext } from '../context/ChatContext';
import { useChat } from '../hooks/useChat';
import CitationLinks from './CitationLinks';
import MarkdownMessage from './MarkdownMessage';

const ChatWidget = () => {
  const { isChatOpen, closeChat, toggleChat } = useChatContext();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  
  // Hook personnalisé pour la logique chat
  const {
    messages,
    isLoading,
    error,
    isInitialized,
    sendMessage,
    clearChat,
    retryLastMessage
  } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const messageToSend = inputMessage;
    setInputMessage('');
    await sendMessage(messageToSend);
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
  };

  const suggestedQuestions = [
    "What are the effects of microgravity on bone density?",
    "How do plants grow in space?",
    "What are the radiation risks for astronauts on Mars missions?",
    "How does the immune system respond to spaceflight?",
    "What are the cardiovascular effects of long-duration spaceflight?"
  ];

  const formatToolsUsed = (tools) => {
    if (!tools || tools.length === 0) return null;
    
    return tools.map(tool => {
      // Nettoyer les noms d'outils pour l'affichage
      return tool.replace(/[()]/g, '').replace(/_/g, ' ');
    }).join(', ');
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button 
        className={`chat-widget-button ${isChatOpen ? 'hidden' : ''}`}
        onClick={toggleChat}
      >
        <span className="chat-icon">🤖</span>
        <span className="chat-label">AI Assistant</span>
      </button>

      {/* Chat Modal */}
      {isChatOpen && (
        <div className="chat-modal-overlay" onClick={closeChat}>
          <div className="chat-modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="chat-header">
              <div className="chat-header-info">
                <div className="chat-avatar">🤖</div>
                <div>
                  <h3>NASA Bio Assistant</h3>
                  <p>{isInitialized ? 'Space Biology Expert' : 'Connecting...'}</p>
                </div>
              </div>
              <div className="header-actions">
                <button 
                  className="clear-button" 
                  onClick={clearChat}
                  title="Clear conversation"
                >
                  🗑️
                </button>
                <button className="close-button" onClick={closeChat}>
                  ×
                </button>
              </div>
            </div>

            {/* Connection Error */}
            {error && !isInitialized && (
              <div className="connection-error">
                <p>⚠️ {error}</p>
                <button onClick={() => window.location.reload()}>
                  Retry Connection
                </button>
              </div>
            )}

            {/* Messages */}
            <div className="chat-messages">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`message ${message.isBot ? 'bot-message' : 'user-message'} ${message.isError ? 'error-message' : ''}`}
                >
                  <div className="message-content">
                    {/* Rendu Markdown pour les messages */}
                    <MarkdownMessage 
                      content={message.text} 
                      isBot={message.isBot}
                    />
                    
                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <CitationLinks citations={message.citations} />
                    )}
                    
                    {/* Tools Used */}
                    {message.toolsUsed && message.toolsUsed.length > 0 && (
                      <div className="tools-used">
                        <span className="tools-icon">🔧</span>
                        <small>Tools: {formatToolsUsed(message.toolsUsed)}</small>
                      </div>
                    )}
                    
                    {/* Confidence */}
                    {message.confidence && (
                      <div className="confidence-indicator">
                        <span className={`confidence-badge ${message.confidence}`}>
                          {message.confidence} confidence
                        </span>
                      </div>
                    )}
                    
                    {/* Timestamp */}
                    <span className="timestamp">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  
                  {/* Retry button for error messages */}
                  {message.isError && (
                    <button 
                      className="retry-button"
                      onClick={retryLastMessage}
                    >
                      🔄 Retry
                    </button>
                  )}
                </div>
              ))}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="message bot-message">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <p className="loading-text">Searching knowledge base...</p>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions - only show for new conversations */}
            {messages.length <= 2 && !isLoading && (
              <div className="chat-suggestions">
                <p>Try asking about:</p>
                <div className="suggestion-chips">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="suggestion-chip"
                      onClick={() => handleSuggestionClick(question)}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSendMessage} className="chat-input-form">
              <div className="input-container">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={isInitialized ? "Ask about space biology..." : "Connecting..."}
                  className="message-input"
                  disabled={isLoading || !isInitialized}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isLoading || !inputMessage.trim() || !isInitialized}
                >
                  {isLoading ? '⏳' : '➤'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;