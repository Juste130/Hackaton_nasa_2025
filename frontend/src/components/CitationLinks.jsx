import React from 'react';
import './CitationLinks.css';

const CitationLinks = ({ citations = [] }) => {
  if (!citations || citations.length === 0) {
    return null;
  }

  const formatCitation = (pmcid) => {
    // Assure-toi que le PMCID est au bon format
    const cleanPmcid = pmcid.startsWith('PMC') ? pmcid : `PMC${pmcid}`;
    return {
      pmcid: cleanPmcid,
      url: `https://pmc.ncbi.nlm.nih.gov/articles/${cleanPmcid}/`,
      displayText: cleanPmcid
    };
  };

  const handleCitationClick = (url, pmcid) => {
    // Ouvrir dans un nouvel onglet
    window.open(url, '_blank', 'noopener,noreferrer');
    
    // Optionnel : tracking analytics
    console.log(`Citation clicked: ${pmcid}`);
  };

  return (
    <div className="citation-links">
      <div className="citation-header">
        <span className="citation-icon">📚</span>
        <strong>Sources ({citations.length}):</strong>
      </div>
      <div className="citation-list">
        {citations.map((citation, index) => {
          const { pmcid, url, displayText } = formatCitation(citation);
          return (
            <button
              key={`${pmcid}-${index}`}
              className="citation-link"
              onClick={() => handleCitationClick(url, pmcid)}
              title={`Open ${pmcid} in PubMed Central`}
            >
              <span className="citation-text">{displayText}</span>
              <span className="external-link-icon">↗</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CitationLinks;