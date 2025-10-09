// src/components/GraphControls.jsx
import React, { useState } from 'react';
import './GraphControls.css';

const GraphControls = ({ 
  onSearch, 
  onFilter, 
  onLoadFull, 
  onClear, 
  onCenter, 
  loading,
  stats 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState('hybrid');
  const [searchLimit, setSearchLimit] = useState(10);
  const [includeRelated, setIncludeRelated] = useState(true);
  
  // Tous les types de nœuds disponibles dans l'API
  const [nodeTypes, setNodeTypes] = useState({
    Publication: true,
    Organism: true,
    Phenomenon: true,
    Finding: false,
    Platform: false,
    Stressor: false,
    Author: false
  });
  
  const [organismFilter, setOrganismFilter] = useState('');
  const [phenomenonFilter, setPhenomenonFilter] = useState('');
  const [platformFilter, setPlatformFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [filterLimit, setFilterLimit] = useState(100);

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      alert('Please enter a search query');
      return;
    }

    onSearch({
      query: searchQuery,
      search_mode: searchMode,
      limit: searchLimit,
      include_related: includeRelated,
      max_depth: 2
    });
  };

  const handleFilter = () => {
    const selectedTypes = Object.entries(nodeTypes)
      .filter(([_, selected]) => selected)
      .map(([type, _]) => type);

    const filterParams = {
      node_types: selectedTypes.length > 0 ? selectedTypes : null,
      organism: organismFilter.trim() || null,
      phenomenon: phenomenonFilter.trim() || null,
      platform: platformFilter.trim() || null,
      date_from: dateFrom || null,
      date_to: dateTo || null,
      limit: filterLimit
    };

    onFilter(filterParams);
  };

  const handleNodeTypeChange = (type) => {
    setNodeTypes(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const clearAllFilters = () => {
    setNodeTypes({
      Publication: true,
      Organism: true,
      Phenomenon: true,
      Finding: false,
      Platform: false,
      Stressor: false,
      Author: false
    });
    setOrganismFilter('');
    setPhenomenonFilter('');
    setPlatformFilter('');
    setDateFrom('');
    setDateTo('');
    setFilterLimit(100);
  };

  const selectAllNodeTypes = () => {
    const allSelected = Object.values(nodeTypes).every(selected => selected);
    const newState = {};
    Object.keys(nodeTypes).forEach(type => {
      newState[type] = !allSelected;
    });
    setNodeTypes(newState);
  };

  // Calculer les années min/max pour les inputs de date
  const currentYear = new Date().getFullYear();
  const minYear = 1990; // Année minimale raisonnable pour les publications NASA

  return (
    <div className="graph-controls">
      {/* Search Controls */}
      <div className="control-group">
        <h3>Search Graph</h3>
        <div className="form-group">
          <label>Search Query</label>
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="e.g., bone loss microgravity"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <div className="form-group">
          <label>Search Mode</label>
          <select 
            value={searchMode}
            onChange={(e) => setSearchMode(e.target.value)}
          >
            <option value="hybrid">Hybrid</option>
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
          </select>
        </div>
        <div className="form-group">
          <label>Max Publications</label>
          <input 
            type="number" 
            value={searchLimit}
            onChange={(e) => setSearchLimit(parseInt(e.target.value) || 10)}
            min="1" 
            max="50"
          />
        </div>
        <div className="checkbox-item">
          <input 
            type="checkbox" 
            id="includeRelated"
            checked={includeRelated}
            onChange={(e) => setIncludeRelated(e.target.checked)}
          />
          <label htmlFor="includeRelated">Include Related Entities</label>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Filter Controls */}
      <div className="control-group">
        <h3>Filter Graph</h3>
        
        {/* Node Types */}
        <div className="form-group">
          <div className="label-with-actions">
            <label>Node Types</label>
            <button 
              type="button"
              className="btn-link"
              onClick={selectAllNodeTypes}
              title="Toggle all node types"
            >
              {Object.values(nodeTypes).every(selected => selected) ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          <div className="checkbox-group">
            {Object.entries(nodeTypes).map(([type, checked]) => (
              <div key={type} className="checkbox-item">
                <input 
                  type="checkbox" 
                  id={`node${type}`}
                  checked={checked}
                  onChange={() => handleNodeTypeChange(type)}
                />
                <label htmlFor={`node${type}`}>
                  {type}
                  {stats?.node_types?.[type] && (
                    <span className="type-count">({stats.node_types[type]})</span>
                  )}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Entity Filters */}
        <div className="form-group">
          <label>Organism Filter</label>
          <input 
            type="text" 
            value={organismFilter}
            onChange={(e) => setOrganismFilter(e.target.value)}
            placeholder="e.g., mouse, Arabidopsis"
          />
        </div>
        
        <div className="form-group">
          <label>Phenomenon Filter</label>
          <input 
            type="text" 
            value={phenomenonFilter}
            onChange={(e) => setPhenomenonFilter(e.target.value)}
            placeholder="e.g., bone loss, muscle atrophy"
          />
        </div>

        <div className="form-group">
          <label>Platform Filter</label>
          <input 
            type="text" 
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            placeholder="e.g., ISS, Space Shuttle"
          />
        </div>

        {/* Date Filters */}
        <div className="form-group">
          <label>Publication Date Range</label>
          <div className="date-range">
            <div className="date-input-group">
              <label htmlFor="dateFrom" className="date-label">From:</label>
              <input 
                type="date"
                id="dateFrom"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                min={`${minYear}-01-01`}
                max={`${currentYear}-12-31`}
                className="date-input"
              />
            </div>
            <div className="date-input-group">
              <label htmlFor="dateTo" className="date-label">To:</label>
              <input 
                type="date"
                id="dateTo"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                min={dateFrom || `${minYear}-01-01`}
                max={`${currentYear}-12-31`}
                className="date-input"
              />
            </div>
          </div>
          <div className="date-shortcuts">
            <button 
              type="button"
              className="btn-link"
              onClick={() => {
                setDateFrom(`${currentYear - 5}-01-01`);
                setDateTo(`${currentYear}-12-31`);
              }}
            >
              Last 5 years
            </button>
            <button 
              type="button"
              className="btn-link"
              onClick={() => {
                setDateFrom(`${currentYear - 10}-01-01`);
                setDateTo(`${currentYear}-12-31`);
              }}
            >
              Last 10 years
            </button>
            <button 
              type="button"
              className="btn-link"
              onClick={() => {
                setDateFrom('');
                setDateTo('');
              }}
            >
              Clear dates
            </button>
          </div>
        </div>

        {/* Max Nodes */}
        <div className="form-group">
          <label>Max Nodes</label>
          <input 
            type="number" 
            value={filterLimit}
            onChange={(e) => setFilterLimit(parseInt(e.target.value) || 100)}
            min="10" 
            max="1000"
          />
          <div className="limit-presets">
            {[50, 100, 200, 500].map(preset => (
              <button
                key={preset}
                type="button"
                className={`btn-preset ${filterLimit === preset ? 'active' : ''}`}
                onClick={() => setFilterLimit(preset)}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="filter-actions">
          <button 
            className="btn btn-primary" 
            onClick={handleFilter}
            disabled={loading}
          >
            {loading ? 'Filtering...' : 'Apply Filters'}
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={clearAllFilters}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="control-group">
        <h3>Quick Actions</h3>
        <div className="quick-actions">
          <button 
            className="btn btn-secondary" 
            onClick={onLoadFull}
            disabled={loading}
          >
            Load Full Graph
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={onCenter}
          >
            Center View
          </button>
          <button 
            className="btn btn-danger" 
            onClick={onClear}
          >
            Clear Graph
          </button>
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="stats">
          <h4>Graph Statistics</h4>
          <div className="stat-item">
            <span>Total Nodes:</span>
            <span>{stats.total_nodes || 0}</span>
          </div>
          <div className="stat-item">
            <span>Total Edges:</span>
            <span>{stats.total_edges || 0}</span>
          </div>
          
          {/* Node Types Breakdown */}
          {stats.node_types && Object.keys(stats.node_types).length > 0 && (
            <div className="stats-section">
              <h5>Node Types:</h5>
              {Object.entries(stats.node_types).map(([type, count]) => (
                <div key={type} className="stat-item">
                  <span>{type}:</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          )}
          
          {/* Edge Types Breakdown */}
          {stats.edge_types && Object.keys(stats.edge_types).length > 0 && (
            <div className="stats-section">
              <h5>Edge Types:</h5>
              {Object.entries(stats.edge_types).map(([type, count]) => (
                <div key={type} className="stat-item">
                  <span>{type}:</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          )}

          {/* Search Info */}
          {stats.search_query && (
            <div className="stats-section">
              <h5>Search Info:</h5>
              <div className="stat-item">
                <span>Query:</span>
                <span className="search-query">{stats.search_query}</span>
              </div>
              <div className="stat-item">
                <span>Mode:</span>
                <span>{stats.search_mode}</span>
              </div>
              {stats.publications_found && (
                <div className="stat-item">
                  <span>Publications:</span>
                  <span>{stats.publications_found}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GraphControls;