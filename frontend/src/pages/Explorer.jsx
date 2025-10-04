import React, { useState, useEffect } from 'react';
import { publications, filters } from '../data/mockData';
import PublicationCard from '../components/PublicationCard';
import KnowledgeGraph from '../components/KnowledgeGraph';
import DataTable from '../components/DataTable';
import AISummaryPanel from '../components/AISummaryPanel';
import './Explorer.css';

const Explorer = () => {
  const [activeView, setActiveView] = useState('cards'); // 'cards', 'graph', 'table'
  const [filteredPublications, setFilteredPublications] = useState(publications);
  const years = publications.map(pub => new Date(pub.date).getFullYear());
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);
  const currentYear = new Date().getFullYear();
  const [selectedFilters, setSelectedFilters] = useState({
    organisms: [],
    phenomena: [],
    systems: [],
    missions: [],
    yearRange: [minYear, currentYear]
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPublications, setSelectedPublications] = useState([]);
  const [showAIPanel, setShowAIPanel] = useState(false);

  // Year range for slider

  useEffect(() => {
    let results = publications;

    // Text search filter
    if (searchQuery) {
      results = results.filter(pub => 
        pub.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pub.abstract.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pub.authors.some(author =>
          author.toLowerCase().includes(searchQuery.toLowerCase())
        ) ||
        pub.journal.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Category filters
    Object.keys(selectedFilters).forEach(key => {
      if (selectedFilters[key].length > 0 && key !== 'yearRange') {
        results = results.filter(pub => 
          selectedFilters[key].some(filter => 
            pub[key]?.includes(filter)
          )
        );
      }
    });

    // Year range filter
    results = results.filter(pub => {
      const pubYear = new Date(pub.date).getFullYear();
      return pubYear >= selectedFilters.yearRange[0] && 
             pubYear <= selectedFilters.yearRange[1];
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

  const handleYearRangeChange = (newRange) => {
    setSelectedFilters(prev => ({
      ...prev,
      yearRange: newRange
    }));
  };

  const handlePublicationSelect = (pubId) => {
    setSelectedPublications(prev => {
      if (prev.includes(pubId)) {
        return prev.filter(id => id !== pubId);
      } else {
        return [...prev, pubId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedPublications.length === filteredPublications.length) {
      setSelectedPublications([]);
    } else {
      setSelectedPublications(filteredPublications.map(pub => pub.id));
    }
  };

  const clearAllFilters = () => {
    setSelectedFilters({
      organisms: [],
      phenomena: [],
      systems: [],
      missions: [],
      yearRange: [minYear, currentYear]
    });
    setSearchQuery('');
    setSelectedPublications([]);
  };

  const selectedPubData = publications.filter(pub => 
    selectedPublications.includes(pub.id)
  );

  return (
    <div className="explorer">
      <div className="explorer-header fade-in">
        <h1>Explore Knowledge Base</h1>
        <p>{filteredPublications.length} publications found • {selectedPublications.length} selected</p>
      </div>

      <div className="explorer-content">
        {/* Filters Sidebar */}
        <aside className="filters-sidebar slide-in">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search publications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {/* Year Range Filter */}
          <div className="filter-group">
            <h3>Publication Year</h3>
            <div className="year-inputs">
              <div className="year-input-group">
                <label htmlFor="year-from">From:</label>
                <input
                  id="year-from"
                  type="number"
                  min={minYear}
                  max={maxYear}
                  value={selectedFilters.yearRange[0]}
                  onChange={(e) => {
                    let newStart = parseInt(e.target.value) || minYear;
                    // Validation : s'assurer que l'année est dans la plage valide
                    newStart = Math.max(minYear, Math.min(newStart, selectedFilters.yearRange[1]));
                    handleYearRangeChange([newStart, selectedFilters.yearRange[1]]);
                  }}
                  className="year-input"
                  placeholder={minYear.toString()}
                />
              </div>
              
              <div className="year-input-group">
                <label htmlFor="year-to">To:</label>
                <input
                  id="year-to"
                  type="number"
                  min={minYear}
                  max={maxYear}
                  value={selectedFilters.yearRange[1]}
                  onChange={(e) => {
                    let newEnd = parseInt(e.target.value) || maxYear;
                    // Validation : s'assurer que l'année est dans la plage valide
                    newEnd = Math.max(selectedFilters.yearRange[0], Math.min(newEnd, maxYear));
                    handleYearRangeChange([selectedFilters.yearRange[0], newEnd]);
                  }}
                  className="year-input"
                  placeholder={maxYear.toString()}
                />
              </div>
            </div>
          </div>
          {/* Dynamic Filters */}
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
                    <span className="filter-count">
                      ({publications.filter(pub => pub[category]?.includes(option)).length})
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}

          <button className="clear-filters-btn" onClick={clearAllFilters}>
            Clear All Filters
          </button>
        </aside>

        {/* Main Content Area */}
        <main className="results-main">
          {/* View Toggles */}
          <div className="view-controls">
            <div className="view-toggles">
              <button 
                className={`view-toggle ${activeView === 'cards' ? 'active' : ''}`}
                onClick={() => setActiveView('cards')}
              >
                📄 Cards
              </button>
              <button 
                className={`view-toggle ${activeView === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveView('graph')}
              >
                🔗 Graph
              </button>
              <button 
                className={`view-toggle ${activeView === 'table' ? 'active' : ''}`}
                onClick={() => setActiveView('table')}
              >
                📊 Table
              </button>
            </div>

            {/* Selection Controls */}
            {filteredPublications.length > 0 && (
              <div className="selection-controls">
                <label className="select-all-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedPublications.length === filteredPublications.length}
                    onChange={handleSelectAll}
                  />
                  Select All ({filteredPublications.length})
                </label>
                {selectedPublications.length > 0 && (
                  <button 
                    className="ai-summary-btn"
                    onClick={() => setShowAIPanel(true)}
                  >
                    🤖 Summary ({selectedPublications.length})
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Results Area */}
          <div className="results-area">
            {activeView === 'cards' && (
              <div className="cards-view">
                <div className="results-grid">
                  {filteredPublications.map(publication => (
                    <PublicationCard 
                      key={publication.id} 
                      publication={publication}
                      isSelected={selectedPublications.includes(publication.id)}
                      onSelect={() => handlePublicationSelect(publication.id)}
                      onClickForSummary={() => {
                        setSelectedPublications([publication.id]);
                        setShowAIPanel(true);
                      }
                      }
                    />
                  ))}
                </div>
              </div>
            )}

            {activeView === 'graph' && (
              <div className="graph-view">
                <KnowledgeGraph 
                  publications={filteredPublications}
                  onNodeClick={(publication) => handlePublicationSelect(publication.id)}
                />
              </div>
            )}

            {activeView === 'table' && (
              <div className="table-view">
                <DataTable 
                  publications={filteredPublications}
                  selectedPublications={selectedPublications}
                  onPublicationSelect={handlePublicationSelect}
                />
              </div>
            )}

            {filteredPublications.length === 0 && (
              <div className="no-results">
                <div className="no-results-icon">🔍</div>
                <h3>No publications found</h3>
                <p>Try adjusting your search criteria or filters</p>
                <button className="btn btn-secondary" onClick={clearAllFilters}>
                  Clear All Filters
                </button>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* AI Summary Panel */}
      {showAIPanel && (
        <AISummaryPanel
          publications={selectedPubData}
          onClose={() => setShowAIPanel(false)}
        />
      )}
    </div>
  );
};

export default Explorer;