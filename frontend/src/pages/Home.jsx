import React from 'react';
import { useChat } from '../context/ChatContext';
import './Home.css';

const Home = ({ onNavigate }) => {
  const { openChat } = useChat();

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero fade-in">
        <div className="hero-content">
          <h1 className="hero-title">
            Explore the <span className="highlight">mysteries</span> of space biology
          </h1>
          <p className="hero-subtitle">
            Discover 60 years of NASA research
          </p>
          
          <div className="hero-actions">
            <button 
              className="btn btn-primary"
              onClick={() => onNavigate('explorer')}
            >
              Start Exploring
            </button>
            <button 
              className="btn btn-secondary"
              onClick={openChat}
            >
              🤖 Ask Questions Here
            </button>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="floating-card">🔬</div>
          <div className="floating-card">🧬</div>
          <div className="floating-card">🚀</div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="feature-card">
          <div className="feature-icon">🤖</div>
          <h3>Ask in Your Own Words</h3>
          <p>Our technology understands natural language and locates relevant NASA science</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>Discover Connections</h3>
          <p>Explore connections between space science and living things</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">📚</div>
          <h3>Credible References</h3>
          <p>All content is referenced to primary NASA publications</p>
        </div>
      </section>
    </div>
  );
};

export default Home;