import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Bonjour ! Je suis votre assistant en biologie spatiale. Posez-moi vos questions sur les recherches de la NASA.",
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

    // Simulation de réponse IA
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        text: `Je traite votre question : "${inputMessage}". En attendant l'intégration avec le backend, voici un exemple de réponse synthétique basée sur les données NASA.`,
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
    "Quels sont les effets de la microgravité sur la densité osseuse ?",
    "Comment les plantes poussent-elles dans l'espace ?",
    "Quels sont les risques des radiations pour les astronautes ?"
  ];

  return (
    <div className="chat-page">
      <div className="chat-header fade-in">
        <h1>Assistant Biologie Spatiale</h1>
        <p>Posez vos questions sur les recherches NASA</p>
      </div>

      <div className="chat-container">
        {/* Messages */}
        <div className="messages-container">
          {messages.map(message => (
            <div
              key={message.id}
              className={`message ${message.isBot ? 'bot-message' : 'user-message'} fade-in`}
            >
              <div className="message-content">
                <p>{message.text}</p>
                {message.sources && (
                  <div className="sources">
                    <strong>Sources :</strong>
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
            <div className="message bot-message fade-in">
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
          <div className="suggestions">
            <p>Questions suggérées :</p>
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
        <form onSubmit={handleSendMessage} className="message-input-form">
          <div className="input-container">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Posez votre question sur la biologie spatiale..."
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
  );
};

export default Chat;