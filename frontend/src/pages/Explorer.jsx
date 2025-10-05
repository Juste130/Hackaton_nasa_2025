import React, { useEffect, useState } from "react";
import AISummaryPanel from "../components/AISummaryPanel";
import DataTable from "../components/DataTable";
import GraphControls from "../components/GraphControls";
import KnowledgeGraph from "../components/KnowledgeGraph";
import PublicationCard from "../components/PublicationCard";
import { filters } from "../data/mockData";
import graphApiService from "../services/graphApi";
import "./Explorer.css";

const Explorer = () => {
  const [activeView, setActiveView] = useState("cards"); // 'cards', 'graph', 'table'
  const [publications, setPublications] = useState([]);
  const [filteredPublications, setFilteredPublications] = useState([]);

  // States pour les filtres classiques (Cards/Table)
  const currentYear = new Date().getFullYear();
  const [minYear, setMinYear] = useState(currentYear);
  const [maxYear, setMaxYear] = useState(currentYear);
  const [selectedFilters, setSelectedFilters] = useState({
    organisms: [],
    phenomena: [],
    systems: [],
    missions: [],
    yearRange: [currentYear, currentYear],
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPublications, setSelectedPublications] = useState([]);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [visibleCount, setVisibleCount] = useState(6);
  const [loadingPublications, setLoadingPublications] = useState(true);

  // States pour le graphe
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);

  // Chargement initial depuis l'API backend et mapping vers le format UI
  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        setLoadingPublications(true);
        const baseUrl =
          process.env.REACT_APP_API_URL || "http://localhost:3000";
        const res = await fetch(`${baseUrl}/api/publications`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`API error ${res.status}`);
        const apiData = await res.json();

        const mapped = (apiData || []).map((p) => ({
          id: p.id,
          pmcid: p.pmcid || "",
          title: p.title || "",
          date: p.publication_date
            ? new Date(p.publication_date).toISOString()
            : p.created_at || new Date().toISOString(),
          citations: 0,
          authors: Array.isArray(p.publication_authors)
            ? p.publication_authors.map((pa) => {
                const first = pa?.authors?.firstname
                  ? `${pa.authors.firstname} `
                  : "";
                const last = pa?.authors?.lastname || "";
                const full = `${first}${last}`.trim();
                return full || "Unknown";
              })
            : [],
          journal: p.journal || "",
          abstract: p.abstract || "",
          mesh_terms: p.publication_mesh_terms || [],
          keywords: p.publication_keywords || [],
          entities: p.publication_entities || [],
          text_sections: p.text_sections || [],
          organisms: [],
          phenomena: [],
          systems: [],
          mission: "",
        }));

        setPublications(mapped);
        setFilteredPublications(mapped);

        if (mapped.length > 0) {
          const years = mapped
            .map((pub) => new Date(pub.date).getFullYear())
            .filter((y) => !Number.isNaN(y));
          const computedMin = Math.min(...years);
          const computedMax = Math.max(...years);
          setMinYear(Number.isFinite(computedMin) ? computedMin : currentYear);
          setMaxYear(Number.isFinite(computedMax) ? computedMax : currentYear);
          setSelectedFilters((prev) => ({
            ...prev,
            yearRange: [
              Number.isFinite(computedMin) ? computedMin : currentYear,
              Number.isFinite(computedMax) ? computedMax : currentYear,
            ],
          }));
        }
      } catch (e) {
        if (e.name !== "AbortError") {
          console.error("Failed to fetch publications:", e);
        }
      } finally {
        setLoadingPublications(false);
      }
    };
    fetchData();
    return () => controller.abort();
  }, []);

  // Filtrage pour Cards et Table uniquement
  useEffect(() => {
    if (activeView === "graph") return;

    let results = publications;

    // Text search filter
    if (searchQuery) {
      results = results.filter(
        (pub) =>
          pub.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          pub.abstract.toLowerCase().includes(searchQuery.toLowerCase()) ||
          pub.authors.some((author) =>
            author.toLowerCase().includes(searchQuery.toLowerCase())
          ) ||
          pub.journal.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Category filters
    Object.keys(selectedFilters).forEach((key) => {
      if (selectedFilters[key].length > 0 && key !== "yearRange") {
        results = results.filter((pub) =>
          selectedFilters[key].some((filter) => pub[key]?.includes(filter))
        );
      }
    });

    // Year range filter
    results = results.filter((pub) => {
      const pubYear = new Date(pub.date).getFullYear();
      return (
        pubYear >= selectedFilters.yearRange[0] &&
        pubYear <= selectedFilters.yearRange[1]
      );
    });

    setFilteredPublications(results);
    setVisibleCount(6);
  }, [selectedFilters, searchQuery, activeView]);

  // Handlers pour filtres classiques
  const handleFilterToggle = (category, value) => {
    setSelectedFilters((prev) => {
      const newFilters = { ...prev };
      if (newFilters[category].includes(value)) {
        newFilters[category] = newFilters[category].filter(
          (item) => item !== value
        );
      } else {
        newFilters[category] = [...newFilters[category], value];
      }
      return newFilters;
    });
  };

  const handleYearRangeChange = (newRange) => {
    setSelectedFilters((prev) => ({
      ...prev,
      yearRange: newRange,
    }));
  };

  const handlePublicationSelect = (pubId) => {
    setSelectedPublications((prev) => {
      if (prev.includes(pubId)) {
        return prev.filter((id) => id !== pubId);
      } else {
        return [...prev, pubId];
      }
    });
  };

  const handleSelectAll = () => {
    const visible = filteredPublications.slice(0, visibleCount);
    const visibleIds = visible.map((pub) => pub.id);
    const allVisibleSelected = visibleIds.every((id) =>
      selectedPublications.includes(id)
    );
    if (allVisibleSelected) {
      setSelectedPublications((prev) =>
        prev.filter((id) => !visibleIds.includes(id))
      );
    } else {
      setSelectedPublications((prev) =>
        Array.from(new Set([...prev, ...visibleIds]))
      );
    }
  };

  const clearAllFilters = () => {
    setSelectedFilters({
      organisms: [],
      phenomena: [],
      systems: [],
      missions: [],
      yearRange: [minYear, currentYear],
    });
    setSearchQuery("");
    setSelectedPublications([]);
  };

  // Handlers pour le graphe
  const handleGraphSearch = async (searchParams) => {
    setGraphLoading(true);
    setGraphError(null);
    try {
      const data = await graphApiService.searchGraph(searchParams);
      setGraphData(data);
    } catch (err) {
      setGraphError(err.message);
      console.error("Graph search error:", err);
    } finally {
      setGraphLoading(false);
    }
  };

  const handleGraphFilter = async (filterParams) => {
    setGraphLoading(true);
    setGraphError(null);
    try {
      const data = await graphApiService.filterGraph(filterParams);
      setGraphData(data);
    } catch (err) {
      setGraphError(err.message);
      console.error("Graph filter error:", err);
    } finally {
      setGraphLoading(false);
    }
  };

  const handleGraphLoadFull = async () => {
    setGraphLoading(true);
    setGraphError(null);
    try {
      const data = await graphApiService.getFullGraph({ limit: 100 });
      setGraphData(data);
    } catch (err) {
      setGraphError(err.message);
      console.error("Graph load error:", err);
    } finally {
      setGraphLoading(false);
    }
  };

  const handleGraphClear = () => {
    setGraphData(null);
    setGraphError(null);
  };

  const handleGraphCenter = () => {
    // Cette fonction sera appelée depuis KnowledgeGraph
    console.log("Center graph view");
  };

  const selectedPubData = publications.filter((pub) =>
    selectedPublications.includes(pub.id)
  );
  const visiblePublications = filteredPublications.slice(0, visibleCount);

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

      <div
        className={`explorer-content ${
          activeView === "graph" ? "graph-mode" : ""
        }`}
      >
        {/* Sidebar conditionnel */}
        <aside className="filters-sidebar slide-in">
          {activeView === "graph" ? (
            // Contrôles du graphe
            <GraphControls
              onSearch={handleGraphSearch}
              onFilter={handleGraphFilter}
              onLoadFull={handleGraphLoadFull}
              onClear={handleGraphClear}
              onCenter={handleGraphCenter}
              loading={graphLoading}
              stats={graphData?.stats}
            />
          ) : (
            // Filtres classiques pour Cards et Table
            <>
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

              {/* Dynamic Filters */}
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

              <button className="clear-filters-btn" onClick={clearAllFilters}>
                Clear All Filters
              </button>
            </>
          )}
        </aside>

        {/* Main Content Area */}
        <main className="results-main">
          {/* View Toggles */}
          <div className="view-controls">
            <div className="view-toggles">
              <button
                className={`view-toggle ${
                  activeView === "cards" ? "active" : ""
                }`}
                onClick={() => setActiveView("cards")}
              >
                📄 Cards
              </button>
              <button
                className={`view-toggle ${
                  activeView === "graph" ? "active" : ""
                }`}
                onClick={() => setActiveView("graph")}
              >
                🔗 Graph
              </button>
              <button
                className={`view-toggle ${
                  activeView === "table" ? "active" : ""
                }`}
                onClick={() => setActiveView("table")}
              >
                📊 Table
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
                <button onClick={() => setGraphError(null)}>✕</button>
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
