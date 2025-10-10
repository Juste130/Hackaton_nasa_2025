import React, { useState } from "react";
import "./GraphFilters.css";

const GraphFilters = ({ 
  organisms, 
  phenomena, 
  selectedOrganism, 
  selectedPhenomenon,
  onOrganismChange,
  onPhenomenonChange,
  loading 
}) => {
  const [organismSearch, setOrganismSearch] = useState("");
  const [phenomenonSearch, setPhenomenonSearch] = useState("");
  const [customOrganism, setCustomOrganism] = useState("");
  const [customPhenomenon, setCustomPhenomenon] = useState("");

  const filteredOrganisms = organisms.filter(org => 
    org.name?.toLowerCase().includes(organismSearch.toLowerCase()) ||
    org.scientific_name?.toLowerCase().includes(organismSearch.toLowerCase())
  );

  const filteredPhenomena = phenomena.filter(phen =>
    phen.name?.toLowerCase().includes(phenomenonSearch.toLowerCase()) ||
    phen.system?.toLowerCase().includes(phenomenonSearch.toLowerCase())
  );

  // Toujours afficher la structure, même pendant le chargement
  return (
    <div className={`graph-filters ${loading ? 'is-loading' : ''}`}>
      {loading ? (
        <>
          <div className="filter-skeleton"></div>
          <div className="filter-skeleton"></div>
        </>
      ) : (
        <>
          {/* Organism Filter */}
          <div className="filter-section">
            <label className="filter-label">
              <span className="filter-icon">🧬</span>
              Organism
            </label>
            <div className="filter-select-wrapper">
              <select
                className="filter-select"
                value={selectedOrganism}
                onChange={(e) => onOrganismChange(e.target.value)}
              >
                <option value="">All Organisms</option>
                {filteredOrganisms.map((org) => (
                  <option key={org.scientific_name || org.name} value={org.name}>
                    {org.name}
                    {org.scientific_name && ` (${org.scientific_name})`}
                    {org.study_count && ` • ${org.study_count} studies`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Phenomenon Filter */}
          <div className="filter-section">
            <label className="filter-label">
              <span className="filter-icon">⚡</span>
              Phenomenon
            </label>
            <div className="filter-select-wrapper">
              <select
                className="filter-select"
                value={selectedPhenomenon}
                onChange={(e) => onPhenomenonChange(e.target.value)}
              >
                <option value="">All Phenomena</option>
                {filteredPhenomena.map((phen) => (
                  <option key={phen.name} value={phen.name}>
                    {phen.name}
                    {phen.system && ` • ${phen.system}`}
                    {phen.investigation_count && ` • ${phen.investigation_count} studies`}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default GraphFilters;
