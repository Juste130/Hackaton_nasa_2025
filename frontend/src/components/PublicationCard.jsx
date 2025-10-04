import React, { useState } from 'react';
import './PublicationCard.css';

const PublicationCard = ({ publication }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="publication-card fade-in">
      <div className="card-header">
        <h3 className="publication-title">{publication.title}</h3>
        <div className="publication-meta">
          <span className="date">{new Date(publication.date).toLocaleDateString()}</span>
          <span className="citations">📊 {publication.citations} citations</span>
        </div>
      </div>

      <div className="authors">
        {publication.authors.join(', ')}
      </div>

      <p className="journal">{publication.journal}</p>

      <div className="abstract">
        <p>
          {isExpanded 
            ? publication.abstract 
            : `${publication.abstract.substring(0, 200)}...`
          }
        </p>
        <button 
          className="expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'See less' : 'See more'}
        </button>
      </div>

      <div className="tags">
        {publication.organisms.map(org => (
          <span key={org} className="tag organism">🧬 {org}</span>
        ))}
        {publication.phenomena.map(phen => (
          <span key={phen} className="tag phenomenon">⚡ {phen}</span>
        ))}
        {publication.systems.map(sys => (
          <span key={sys} className="tag system">🔬 {sys}</span>
        ))}
        <span className="tag mission">🚀 {publication.mission}</span>
      </div>

      <div className="card-actions">
        <button className="action-btn">📖 View NASA Publication</button>
        <button className="action-btn">🤖 Research Summary</button>
      </div>
    </div>
  );
};

export default PublicationCard;