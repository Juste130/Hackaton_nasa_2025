import React from 'react';
import { useInfinitePublications } from '../hooks/usePublications';
import PublicationCard from './PublicationCard';
import './PublicationsList.css';

const PublicationsList = ({ filters = {} }) => {
  const {
    publications,
    loading,
    loadingMore,
    error,
    pagination,
    stats,
    reload,
    refresh,
    hasMore
  } = useInfinitePublications(filters);

  if (loading) {
    return (
      <div className="publications-loading">
        <div className="loading-spinner"></div>
        <p>Chargement des publications...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="publications-error">
        <h3>Erreur de chargement</h3>
        <p>{error}</p>
        <button onClick={refresh} className="retry-btn">
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="publications-container">
      {/* Statistiques */}
      {stats && (
        <div className="publications-stats">
          <p>
            {pagination.totalItems.toLocaleString()} publications trouvées
            {stats.totalPublications !== pagination.totalItems && 
              ` sur ${stats.totalPublications.toLocaleString()} au total`
            }
          </p>
        </div>
      )}

      {/* Liste des publications */}
      <div className="publications-grid">
        {publications.map((publication, index) => (
          <PublicationCard 
            key={`${publication.id}-${index}`} 
            publication={publication} 
          />
        ))}
      </div>

      {/* Indicateur de chargement pour pagination */}
      {loadingMore && (
        <div className="loading-more">
          <div className="loading-spinner small"></div>
          <p>Chargement de plus de publications...</p>
        </div>
      )}

      {/* Message de fin */}
      {!hasMore && publications.length > 0 && (
        <div className="no-more-publications">
          <p>✅ Toutes les publications ont été chargées</p>
        </div>
      )}

      {/* Message vide */}
      {publications.length === 0 && !loading && (
        <div className="no-publications">
          <h3>Aucune publication trouvée</h3>
          <p>Essayez de modifier vos critères de recherche</p>
        </div>
      )}
    </div>
  );
};

export default PublicationsList;