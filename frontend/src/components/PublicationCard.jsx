import React, { useState } from "react";
import "./PublicationCard.css";

const PublicationCard = ({
  publication,
  isSelected,
  onSelect,
  onClickForSummary,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

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

        <div className="authors">{publication.authors.join(", ")}</div>

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

        <div className="tags">
          {Array.isArray(publication.mesh_terms) &&
            publication.mesh_terms.map((kw, idx) => {
              const text =
                typeof kw === "string" ? kw : kw && kw.term ? kw.term : "";
              if (!text) return null;
              return (
                <span key={`${text}-${idx}`} className="tag mesh_term">
                  🏷️ {text}
                </span>
              );
            })}
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
          <span className=""> {publication.mission}</span>
        </div>
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
