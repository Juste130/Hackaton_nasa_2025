import React, { useState } from 'react';
import SearchBar from '../components/SearchBar';
import { publications } from '../data/mockData';
import './Home.css';

const Home = ({ onNavigate }) => {
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = (query) => {
    const results = publications.filter(pub => 
      pub.title.toLowerCase().includes(query.toLowerCase()) ||
      pub.abstract.toLowerCase().includes(query.toLowerCase()) ||
      pub.authors.some(author => 
        author.toLowerCase().includes(query.toLowerCase())
      )
    );
    setSearchResults(results);
  };

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero fade-in">
        <div className="hero-content">
          <h1 className="hero-title">
            Explorez les <span className="highlight">secrets</span> de la biologie spatiale
          </h1>
          <p className="hero-subtitle">
            Découvrez 60 ans de recherche NASA grâce à l'intelligence artificielle
          </p>
          
          <SearchBar onSearch={handleSearch} />
          
          <div className="hero-actions">
            <button 
              className="btn btn-primary"
              onClick={() => onNavigate('explorer')}
            >
              Commencer l'Exploration
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => onNavigate('chat')}
            >
              🤖 Essayer le Chatbot
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
          <h3>Interrogez avec vos mots</h3>
          <p>Notre IA comprend vos questions et trouve les réponses dans les publications NASA</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>Découvrez des connexions</h3>
          <p>Visualisez les liens entre les études, les organismes et les effets spatiaux</p>
        </div>
        
        <div className="feature-card">
          <div className="feature-icon">📚</div>
          <h3>Sources fiables</h3>
          <p>Chaque information est sourcée avec les publications originales de la NASA</p>
        </div>
      </section>

      {/* Quick Results */}
      {searchResults.length > 0 && (
        <section className="quick-results fade-in">
          <h2>Résultats de recherche ({searchResults.length})</h2>
          <div className="results-grid">
            {searchResults.slice(0, 3).map(pub => (
              <div key={pub.id} className="result-card">
                <h4>{pub.title}</h4>
                <p className="authors">{pub.authors.join(', ')}</p>
                <p className="abstract">{pub.abstract.substring(0, 150)}...</p>
              </div>
            ))}
          </div>
          {searchResults.length > 3 && (
            <button 
              className="btn btn-secondary"
              onClick={() => onNavigate('explorer')}
            >
              Voir tous les résultats
            </button>
          )}
        </section>
      )}
    </div>
  );
};

export default Home;