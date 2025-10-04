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
            Explore the <span className="highlight">mysteries</span> of space biology
          </h1>
          <p className="hero-subtitle">
            Discover 60 years of NASA research
          </p>
          
          <SearchBar onSearch={handleSearch} />
          
          <div className="hero-actions">
            <button 
              className="btn btn-primary"
              onClick={() => onNavigate('explorer')}
            >
              Start Exploring
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => onNavigate('chat')}
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

      {/* Quick Results */}
      {searchResults.length > 0 && (
        <section className="quick-results fade-in">
          <h2>Search Results ({searchResults.length})</h2>
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
              See All Results
            </button>
          )}
        </section>
      )}
    </div>
  );
};

export default Home;