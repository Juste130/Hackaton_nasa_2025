import React, { useState, useEffect } from 'react';
import { publications, filters } from '../data/mockData';
import PublicationCard from '../components/PublicationCard';
import './Explorer.css';

const Explorer = () => {
  const [filteredPublications, setFilteredPublications] = useState(publications);
  const [selectedFilters, setSelectedFilters] = useState({
    organisms: [],
    phenomena: [],
    systems: [],
    missions: []
  });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let results = publications;

    // Filtre par recherche texte
    if (searchQuery) {
      results = results.filter(pub => 
        pub.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pub.abstract.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filtres par catégorie
    Object.keys(selectedFilters).forEach(key => {
      if (selectedFilters[key].length > 0) {
        results = results.filter(pub => 
          selectedFilters[key].some(filter => 
            pub[key]?.includes(filter)
          )
        );
      }
    });

    setFilteredPublications(results);
  }, [selectedFilters, searchQuery]);

  const handleFilterToggle = (category, value) => {
    setSelectedFilters(prev => {
      const newFilters = { ...prev };
      if (newFilters[category].includes(value)) {
        newFilters[category] = newFilters[category].filter(item => item !== value);
      } else {
        newFilters[category] = [...newFilters[category], value];
      }
      return newFilters;
    });
  };

  return (
    <div className="explorer">
      <div className="explorer-header fade-in">
        <h1>Explorer la Base de Connaissances</h1>
        <p>{filteredPublications.length} publications trouvées</p>
      </div>

      <div className="explorer-content">
        {/* Sidebar des filtres */}
        <aside className="filters-sidebar slide-in">
          <div className="search-box">
            <input
              type="text"
              placeholder="Rechercher des publications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {Object.entries(filters).map(([category, options]) => (
            <div key={category} className="filter-group">
              <h3>{category.charAt(0).toUpperCase() + category.slice(1)}</h3>
              <div className="filter-options">
                {options.map(option => (
                  <label key={option} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedFilters[category].includes(option)}
                      onChange={() => handleFilterToggle(category, option)}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </aside>

        {/* Résultats */}
        <main className="results-main">
          <div className="results-grid">
            {filteredPublications.map(publication => (
              <PublicationCard 
                key={publication.id} 
                publication={publication} 
              />
            ))}
          </div>
          
          {filteredPublications.length === 0 && (
            <div className="no-results">
              <p>Aucune publication ne correspond à vos critères de recherche.</p>
              <button 
                className="btn btn-secondary"
                onClick={() => {
                  setSelectedFilters({
                    organisms: [],
                    phenomena: [],
                    systems: [],
                    missions: []
                  });
                  setSearchQuery('');
                }}
              >
                Réinitialiser les filtres
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Explorer;