import React, { useEffect, useState } from "react";
import AISummaryPanel from "../components/AISummaryPanel";
import DataTable from "../components/DataTable";
import GraphControls from "../components/GraphControls";
import KnowledgeGraph from "../components/KnowledgeGraph";
import PublicationCard from "../components/PublicationCard";
import { filters } from "../data/mockData";
import { useExplorerFilters } from "../hooks/useExplorerFilters";
import { useGraphData } from "../hooks/useGraphData";
import { usePublications } from "../hooks/usePublications";
import { useSelection } from "../hooks/useSelection";
import "./Explorer.css";

const Explorer = () => {
  const [activeView, setActiveView] = useState("cards"); // 'cards', 'graph', 'table'
  const [showAIPanel, setShowAIPanel] = useState(false);

  const { publications, loadingPublications, currentYear, minYear, maxYear } =
    usePublications();
  const {
    searchQuery,
    setSearchQuery,
    selectedFilters,
    filteredPublications,
    handleFilterToggle,
    handleYearRangeChange,
    clearAllFilters,
  } = useExplorerFilters({ publications, currentYear, minYear, maxYear });
  const {
    selectedPublications,
    setSelectedPublications,
    visibleCount,
    setVisibleCount,
    visiblePublications,
    handlePublicationSelect,
    handleSelectAll,
  } = useSelection(filteredPublications);
  const {
    graphData,
    graphLoading,
    graphError,
    search,
    filter,
    loadFull,
    clear,
    dismissError,
  } = useGraphData();
  console.log(publications.map((pub) => pub.mesh_terms));

  useEffect(() => {
    if (activeView !== "graph") {
      setVisibleCount(6);
    }
  }, [selectedFilters, searchQuery, activeView]);

  const handleGraphSearch = async (searchParams) => search(searchParams);
  const handleGraphFilter = async (filterParams) => filter(filterParams);
  const handleGraphLoadFull = async () => loadFull({ limit: 100 });
  const handleGraphClear = () => clear();

  const handleGraphCenter = () => {};

  const selectedPubData = publications.filter((pub) =>
    selectedPublications.includes(pub.id)
  );

  useEffect(() => {
    handleGraphLoadFull();
  }, []);

  return (
    <div className="explorer">
      <div className="explorer-header fade-in">
        <h1>Explore Knowledge Base</h1>
        <p>
          {activeView === "graph"
            ? `${graphData?.stats?.total_nodes || 0} nodes • ${
                graphData?.stats?.total_edges || 0
              } edges`
            : loadingPublications
            ? "Loading publications..."
            : `${filteredPublications.length} publications found • ${selectedPublications.length} selected`}
        </p>
      </div>

      <div className={`explorer-content ${activeView === "graph" ? "graph-mode" : ""}`}>
        <aside className="filters-sidebar slide-in">
          {/* Barre de recherche commune */}
          <div className="search-box">
            <input
              type="text"
              placeholder="Search publications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {/* Filtres communs */}
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
                    newStart = Math.max(
                      minYear,
                      Math.min(newStart, selectedFilters.yearRange[1])
                    );
                    handleYearRangeChange([
                      newStart,
                      selectedFilters.yearRange[1],
                    ]);
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
                    newEnd = Math.max(
                      selectedFilters.yearRange[0],
                      Math.min(newEnd, maxYear)
                    );
                    handleYearRangeChange([
                      selectedFilters.yearRange[0],
                      newEnd,
                    ]);
                  }}
                  className="year-input"
                  placeholder={maxYear.toString()}
                />
              </div>
            </div>
          </div>

          {Object.entries(filters).map(([category, options]) => (
            <div key={category} className="filter-group">
              <h3>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </h3>
              <div className="filter-options">
                {options.map((option) => (
                  <label key={option} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedFilters[category].includes(option)}
                      onChange={() => handleFilterToggle(category, option)}
                    />
                    <span>{option}</span>
                    <span className="filter-count">
                      (
                      {
                        publications.filter((pub) =>
                          pub[category]?.includes(option)
                        ).length
                      }
                      )
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}

          {/* Bouton commun pour réinitialiser les filtres */}
          <button className="clear-filters-btn" onClick={clearAllFilters}>
            Clear All Filters
          </button>

          {/* Contrôles spécifiques à la vue graph */}
          {activeView === "graph" && (
            <GraphControls
              onSearch={handleGraphSearch}
              onFilter={handleGraphFilter}
              onLoadFull={handleGraphLoadFull}
              onClear={handleGraphClear}
              onCenter={handleGraphCenter}
              loading={graphLoading}
              stats={graphData?.stats}
            />
          )}
        </aside>

        {/* Main Content Area */}
        <main className="results-main">
          {/* View Toggles */}
          <div className="view-controls">
            <div className="view-toggles">
              <button
                className={`view-toggle ${activeView === "cards" ? "active" : ""}`}
                onClick={() => setActiveView("cards")}
              >
                 Cards
              </button>
              <button
                className={`view-toggle ${activeView === "graph" ? "active" : ""}`}
                onClick={() => setActiveView("graph")}
              >
                 Graph
              </button>
              <button
                className={`view-toggle ${activeView === "table" ? "active" : ""}`}
                onClick={() => setActiveView("table")}
              >
                 Table
              </button>
            </div>

            {/* Selection Controls - seulement pour Cards et Table */}
            {activeView !== "graph" && filteredPublications.length > 0 && (
              <div className="selection-controls">
                <label className="select-all-checkbox">
                  <input
                    type="checkbox"
                    checked={visiblePublications
                      .map((p) => p.id)
                      .every((id) => selectedPublications.includes(id))}
                    onChange={handleSelectAll}
                  />
                  Select All ({visiblePublications.length})
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

            {/* Graph Error Display */}
            {activeView === "graph" && graphError && (
              <div className="graph-error">
                <span>⚠️ {graphError}</span>
                <button onClick={dismissError}>✕</button>
              </div>
            )}
          </div>

          {/* Results Area */}
          <div className="results-area">
            {activeView === "cards" && (
              <div className="cards-view">
                {loadingPublications ? (
                  <div className="loading">Loading publications…</div>
                ) : (
                  <>
                    <div className="results-grid">
                      {visiblePublications.map((publication) => (
                        <PublicationCard
                          key={publication.id}
                          publication={publication}
                          isSelected={selectedPublications.includes(
                            publication.id
                          )}
                          onSelect={() =>
                            handlePublicationSelect(publication.id)
                          }
                          onClickForSummary={() => {
                            setSelectedPublications([publication.id]);
                            setShowAIPanel(true);
                          }}
                        />
                      ))}
                    </div>
                    {visibleCount < filteredPublications.length && (
                      <div className="load-more">
                        <button
                          className="btn btn-primary"
                          onClick={() => setVisibleCount((c) => c + 6)}
                          disabled={loadingPublications}
                        >
                          Voir plus
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {activeView === "graph" && (
              <div className="graph-view">
                <KnowledgeGraph
                  graphData={graphData}
                  loading={graphLoading}
                  error={graphError}
                  onNodeClick={(node) => console.log("Node clicked:", node)}
                />
              </div>
            )}

            {activeView === "table" && (
              <div className="table-view">
                <DataTable
                  publications={filteredPublications}
                  selectedPublications={selectedPublications}
                  onPublicationSelect={handlePublicationSelect}
                />
              </div>
            )}

            {/* No Results - seulement pour Cards et Table */}
            {activeView !== "graph" && filteredPublications.length === 0 && (
              <div className="no-results">
                <div className="no-results-icon">🔍</div>
                <h3>No publications found</h3>
                <p>Try adjusting your search criteria or filters</p>
                <button className="btn btn-secondary" onClick={clearAllFilters}>
                  Clear All Filters
                </button>
              </div>
            )}

            {/* Graph No Data */}
            {activeView === "graph" && !graphData && !graphLoading && (
              <div className="graph-no-data">
                <div className="no-results-icon">🌐</div>
                <h3>No graph data loaded</h3>
                <p>
                  Use the controls on the left to search or load the knowledge
                  graph
                </p>
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
