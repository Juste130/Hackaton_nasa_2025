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
  
  // Limiter à 3 auteurs par défaut
  const MAX_AUTHORS = 3;
  const authors = publication.authors || [];
  const displayedAuthors = showAllAuthors ? authors : authors.slice(0, MAX_AUTHORS);
  const hasMoreAuthors = authors.length > MAX_AUTHORS;

  return (
    <div className={`publication-card fade-in ${isSelected ? "selected" : ""}`}>
      <div>
        <div className="card-header">
          <h3 className="publication-title">{publication.title}</h3>
          <div className="publication-meta">
            <span className="date">
              {new Date(publication.date).toLocaleDateString()}
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

        <p className="journal">{publication.journal}</p>

        <div className="abstract">
          <p>
            {isExpanded
              ? publication.abstract
              : `${publication.abstract.substring(0, 200)}...`}
          </p>
          <button
            className="expand-btn"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? "See less" : "See more"}
          </button>
        </div>

        {/* Mesh Terms Section */}
        {Array.isArray(publication.mesh_terms) && publication.mesh_terms.length > 0 && (
          <div className="mesh-terms-section">
            <span className="mesh-terms-label">Medical Subject Headings:</span>
            <div className="mesh-terms-container">
              {publication.mesh_terms.map((kw, idx) => {
                const text =
                  typeof kw === "string" ? kw : kw && kw.term ? kw.term : "";
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

        {/* Other Tags Section */}
        {(publication.phenomena.length > 0 || publication.systems.length > 0 || publication.mission) && (
          <div className="tags">
            {publication.phenomena.map((phen) => (
              <span key={phen} className="tag phenomenon">
                ⚡ {phen}
              </span>
            ))}
            {publication.systems.map((sys) => (
              <span key={sys} className="tag system">
                🔬 {sys}
              </span>
            ))}
            {publication.mission && (
              <span className="tag mission">🚀 {publication.mission}</span>
            )}
          </div>
        )}
      </div>

      <div className="card-actions">
        <button
          className="action-btn"
          onClick={() =>
            window.open(
              `https://pmc.ncbi.nlm.nih.gov/articles/${publication.pmcid}`,
              "_blank"
            )
          }
        >
          📖 View NASA Publication
        </button>
        <button className="action-btn" onClick={onClickForSummary}>
          🤖 Research Summary
        </button>
      </div>
    </div>
  );
};

export default PublicationCard;
