import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css';
import { useChat } from '../context/ChatContext';

const ChatWidget = () => {
    const { isChatOpen, closeChat } = useChat();
//   const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your space biology assistant. Ask me anything about NASA's research.",
      isBot: true,
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        text: `I'm processing your question: "${inputMessage}". While waiting for backend integration, here's a sample response based on NASA data.`,
        isBot: true,
        timestamp: new Date(),
        sources: [
          { id: 1, title: "Effects of Microgravity on Human Bone Density" },
          { id: 2, title: "Immune System Response to Space Radiation" }
        ]
      };
      setMessages(prev => [...prev, botResponse]);
      setIsLoading(false);
    }, 2000);
  };

  const suggestedQuestions = [
    "What are the effects of microgravity on bone density?",
    "How do plants grow in space?",
    "What are the radiation risks for astronauts going to Mars?"
  ];

//   const toggleChat = () => {
//     setIsOpen(!isOpen);
//   };
    const { toggleChat } = useChat();

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
                  <p>Space Biology Expert</p>
                </div>
              </div>
              <button className="close-button" onClick={closeChat}>
                ×
              </button>
            </div>

            {/* Messages */}
            <div className="chat-messages">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`message ${message.isBot ? 'bot-message' : 'user-message'}`}
                >
                  <div className="message-content">
                    <p>{message.text}</p>
                    {message.sources && (
                      <div className="sources">
                        <strong>Sources:</strong>
                        {message.sources.map(source => (
                          <span key={source.id} className="source-tag">
                            {source.title}
                          </span>
                        ))}
                      </div>
                    )}
                    <span className="timestamp">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="message bot-message">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {messages.length <= 2 && (
              <div className="chat-suggestions">
                <p>Suggested questions:</p>
                <div className="suggestion-chips">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      className="suggestion-chip"
                      onClick={() => setInputMessage(question)}
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
                  placeholder="Ask about space biology..."
                  className="message-input"
                  disabled={isLoading}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isLoading || !inputMessage.trim()}
                >
                  ➤
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