import React, { useState } from "react";
import "./PublicationCard.css";

const PublicationCard = ({
  publication,
  isSelected,
  onSelect,
  onClickForSummary,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAllAuthors, setShowAllAuthors] = useState(false);
  
  // 🔥 VÉRIFICATIONS DE SÉCURITÉ
  if (!publication) {
    return (
      <div className="publication-card error">
        <div>❌ Publication data missing</div>
      </div>
    );
  }

  // Valeurs par défaut sécurisées
  const {
    title = "No title available",
    authors = [],
    journal = "No journal",
    abstract = "No abstract available",
    date = new Date().toISOString(),
    mesh_terms = [],
    phenomena = [], // 🔥 Valeur par défaut
    systems = [],   // 🔥 Valeur par défaut
    mission = "",
    pmcid = ""
  } = publication;

  // Limiter à 3 auteurs par défaut
  const MAX_AUTHORS = 3;
  const displayedAuthors = showAllAuthors ? authors : authors.slice(0, MAX_AUTHORS);
  const hasMoreAuthors = authors.length > MAX_AUTHORS;

  return (
    <div className={`publication-card fade-in ${isSelected ? "selected" : ""}`}>
      <div>
        <div className="card-header">
          <h3 className="publication-title">{title}</h3>
          <div className="publication-meta">
            <span className="date">
              {new Date(date).toLocaleDateString()}
            </span>
          </div>
        </div>

        <div className="authors">
          {displayedAuthors.join(", ")}
          {hasMoreAuthors && !showAllAuthors && (
            <>
              {" "}
              <button 
                className="see-more-authors"
                onClick={() => setShowAllAuthors(true)}
              >
                +{authors.length - MAX_AUTHORS} more
              </button>
            </>
          )}
          {showAllAuthors && hasMoreAuthors && (
            <>
              {" "}
              <button 
                className="see-more-authors"
                onClick={() => setShowAllAuthors(false)}
              >
                Show less
              </button>
            </>
          )}
        </div>

        <p className="journal">{journal}</p>

        <div className="abstract">
          <p>
            {isExpanded
              ? abstract
              : `${abstract.substring(0, 200)}...`}
          </p>
          {abstract.length > 200 && (
            <button
              className="expand-btn"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? "See less" : "See more"}
            </button>
          )}
        </div>

        {/* Mesh Terms Section */}
        {mesh_terms.length > 0 && (
          <div className="mesh-terms-section">
            <span className="mesh-terms-label">Medical Subject Headings:</span>
            <div className="mesh-terms-container">
              {mesh_terms.map((kw, idx) => {
                const text = typeof kw === "string" ? kw : kw && kw.term ? kw.term : "";
                if (!text) return null;
                return (
                  <span key={`${text}-${idx}`} className="mesh-term-tag">
                    {text}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Other Tags Section - 🔥 CORRIGÉ avec vérifications */}
        {(phenomena.length > 0 || systems.length > 0 || mission) && (
          <div className="tags">
            {phenomena.map((phen, index) => (
              <span key={index} className="tag phenomenon">
                ⚡ {phen}
              </span>
            ))}
            {systems.map((sys, index) => (
              <span key={index} className="tag system">
                🔬 {sys}
              </span>
            ))}
            {mission && (
              <span className="tag mission">🚀 {mission}</span>
            )}
          </div>
        )}
      </div>

      <div className="card-actions">
        {pmcid && (
          <button
            className="action-btn"
            onClick={() =>
              window.open(
                `https://pmc.ncbi.nlm.nih.gov/articles/${pmcid}`,
                "_blank"
              )
            }
          >
            📖 View NASA Publication
          </button>
        )}
        <button className="action-btn" onClick={onClickForSummary}>
          🤖 Research Summary
        </button>
      </div>
    </div>
  );
};

export default PublicationCard;