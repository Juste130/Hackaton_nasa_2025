import React, { useState, useEffect } from 'react';
import publicationApi from '../services/publicationApi';
import './PublicationTooltip.css';

const PublicationTooltip = ({ nodeData, position, onClose }) => {
  const [publication, setPublication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPublicationDetails = async () => {
      if (!nodeData) return;

      try {
        setLoading(true);
        setError(null);

        const pmcid = nodeData.properties?.pmcid || nodeData.pmcid;
        
        if (!pmcid) {
          throw new Error('No PMCID found in node data');
        }

        console.log('🔍 Loading publication details for PMCID:', pmcid);
        const data = await publicationApi.getPublicationByPMCID(pmcid);
        setPublication(data);
      } catch (err) {
        console.error('Error loading publication details:', err);
        setError(err.message || 'Failed to load publication details');
      } finally {
        setLoading(false);
      }
    };

    fetchPublicationDetails();
  }, [nodeData]);

  if (!nodeData) return null;

  const tooltipStyle = {
    left: `${position.x}px`,
    top: `${position.y}px`
  };

  // Loading state
  if (loading) {
    return (
      <div 
        className="publication-tooltip"
        style={tooltipStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <button 
          className="tooltip-close"
          onClick={onClose}
          aria-label="Close tooltip"
        >
          ×
        </button>
        <div className="tooltip-loading">
          <div className="loading-spinner-small"></div>
          <p>Loading publication details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div 
        className="publication-tooltip"
        style={tooltipStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <button 
          className="tooltip-close"
          onClick={onClose}
          aria-label="Close tooltip"
        >
          ×
        </button>
        <div className="tooltip-error">
          <p>❌ {error}</p>
          <p className="error-hint">PMCID: {nodeData.properties?.pmcid || nodeData.pmcid}</p>
        </div>
      </div>
    );
  }

  if (!publication) return null;

  const {
    title,
    pmcid,
    pmid,
    doi,
    abstract,
    journal,
    publication_date,
    publication_authors = [],
    publication_mesh_terms = [],
    publication_entities = []
  } = publication;

  const authors = publication_authors
    .sort((a, b) => a.author_order - b.author_order)
    .map(pa => pa.authors);

  const displayAuthors = authors.slice(0, 3);
  const remainingAuthors = authors.length - 3;

  const truncatedAbstract = abstract 
    ? abstract.length > 300 
      ? abstract.substring(0, 300) + '...'
      : abstract
    : 'No abstract available';

  const getArticleLinks = () => {
    const links = [];
    
    if (pmcid) {
      links.push({
        label: 'PubMed Central',
        url: `https://www.ncbi.nlm.nih.gov/pmc/articles/${pmcid}/`,
        icon: '📚'
      });
    }
    
    if (pmid) {
      links.push({
        label: 'PubMed',
        url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`,
        icon: '🔬'
      });
    }
    
    if (doi) {
      links.push({
        label: 'DOI',
        url: `https://doi.org/${doi}`,
        icon: '🔗'
      });
    }
    
    return links;
  };

  const articleLinks = getArticleLinks();

  const organisms = publication_entities
    .filter(pe => pe.entities.entity_type === 'Organism')
    .slice(0, 3);
  
  const phenomena = publication_entities
    .filter(pe => pe.entities.entity_type === 'Phenomenon')
    .slice(0, 3);

  return (
    <div 
      className="publication-tooltip"
      style={tooltipStyle}
      onClick={(e) => e.stopPropagation()}
    >
      <button 
        className="tooltip-close"
        onClick={onClose}
        aria-label="Close tooltip"
      >
        ×
      </button>

      <div className="tooltip-header">
        <h3 className="tooltip-title">{title || 'Untitled Publication'}</h3>
        {journal && (
          <div className="tooltip-journal">
            <span>📖</span>
            {journal}
          </div>
        )}
        {publication_date && (
          <div className="tooltip-date">
            <span>📅</span>
            {new Date(publication_date).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            })}
          </div>
        )}
      </div>

      <div className="tooltip-content">
        {authors.length > 0 && (
          <div className="tooltip-authors">
            <span className="authors-icon">👥</span>
            <div className="authors-list">
              {displayAuthors.map((author, idx) => (
                <span key={author.id} className="author-name">
                  {author.firstname ? `${author.firstname} ` : ''}{author.lastname}
                  {idx < displayAuthors.length - 1 && ', '}
                </span>
              ))}
              {remainingAuthors > 0 && (
                <span className="author-more">
                  +{remainingAuthors} more
                </span>
              )}
            </div>
          </div>
        )}

        <div className="tooltip-abstract">
          <h4 className="abstract-label">Abstract</h4>
          <p className="abstract-text">{truncatedAbstract}</p>
        </div>

        {(organisms.length > 0 || phenomena.length > 0) && (
          <div className="tooltip-entities">
            {organisms.length > 0 && (
              <div className="entity-group">
                <h4 className="entity-label">🧬 Organisms</h4>
                <div className="entity-tags">
                  {organisms.map(pe => (
                    <span key={pe.id} className="entity-tag organism-tag">
                      {pe.entities.entity_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {phenomena.length > 0 && (
              <div className="entity-group">
                <h4 className="entity-label">🔬 Phenomena</h4>
                <div className="entity-tags">
                  {phenomena.map(pe => (
                    <span key={pe.id} className="entity-tag phenomenon-tag">
                      {pe.entities.entity_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {publication_mesh_terms.length > 0 && (
          <div className="tooltip-mesh">
            <h4 className="mesh-label">🏷️ MeSH Terms</h4>
            <div className="mesh-tags">
              {publication_mesh_terms.slice(0, 5).map(pmt => (
                <span 
                  key={pmt.mesh_term_id} 
                  className={`mesh-tag ${pmt.is_major_topic ? 'major' : ''}`}
                >
                  {pmt.mesh_terms.term}
                  {pmt.is_major_topic && ' ⭐'}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="tooltip-ids">
          {pmcid && (
            <span className="tooltip-id">
              <strong>PMCID:</strong> {pmcid}
            </span>
          )}
          {pmid && (
            <span className="tooltip-id">
              <strong>PMID:</strong> {pmid}
            </span>
          )}
        </div>

        {articleLinks.length > 0 && (
          <div className="tooltip-links">
            <h4 className="links-label">View Article:</h4>
            <div className="links-buttons">
              {articleLinks.map((link, idx) => (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-button"
                >
                  <span className="link-icon">{link.icon}</span>
                  {link.label}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicationTooltip;