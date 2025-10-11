import React, { useState, useEffect } from 'react';
import './GapAnalysis.css';
import StatCard from '../components/StatCard';

const GapAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [gapData, setGapData] = useState({
    missingCombinations: [],
    completenessMatrix: {},
    marsCriticalGaps: [],
    priorityMatrix: {},
    cubeData: {}
  });

  const [activeTab, setActiveTab] = useState('overview');
  const [displayCount, setDisplayCount] = useState(20);

  useEffect(() => {
    fetchGapAnalysisData();
  }, []);

  const fetchGapAnalysisData = async () => {
    try {
      setLoading(true);
      
      // Fetch all gap analysis endpoints in parallel
      const [
        missingResponse,
        completenessResponse,
        marsResponse,
        priorityResponse,
        cubeResponse
      ] = await Promise.all([
        fetch('http://localhost:8000/api/graph/gap-analysis/missing-combinations'),
        fetch('http://localhost:8000/api/graph/gap-analysis/completeness-matrix'),
        fetch('http://localhost:8000/api/graph/gap-analysis/mars-critical-gaps'),
        fetch('http://localhost:8000/api/graph/gap-analysis/priority-matrix'),
        fetch('http://localhost:8000/api/graph/gap-analysis/3d-cube-data')
      ]);

      const missingData = await missingResponse.json();
      const completenessData = await completenessResponse.json();
      const marsData = await marsResponse.json();
      const priorityData = await priorityResponse.json();
      const cubeData = await cubeResponse.json();

      setGapData({
        missingCombinations: missingData.data || [],
        completenessMatrix: completenessData.data || {},
        marsCriticalGaps: marsData.data || [],
        priorityMatrix: priorityData.data || {},
        cubeData: cubeData.data || {}
      });

    } catch (err) {
      console.error('Error fetching gap analysis data:', err);
      setError('Failed to load gap analysis data');
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => {
    return (
      <div className="gap-overview">
        <div className="stats-grid">
          <StatCard
            title="Missing Combinations"
            value={gapData.missingCombinations.length}
            description="Unstudied organism × phenomenon × platform combinations"
            color="#e74c3c"
          />
          <StatCard
            title="Mars Critical Gaps"
            value={gapData.marsCriticalGaps.length}
            description="High-priority gaps for Mars mission preparation"
            color="#f39c12"
          />
          <StatCard
            title="Research Areas"
            value={Array.isArray(gapData.completenessMatrix) 
              ? gapData.completenessMatrix.length 
              : (gapData.completenessMatrix?.data?.length || 0)}
            description="Biological systems analyzed for completeness"
            color="#3498db"
          />
          <StatCard
            title="Average Completeness"
            value={`${calculateAverageCompleteness()}%`}
            description="Overall research coverage across all areas"
            color="#27ae60"
          />
        </div>

        <div className="gap-summary">
          <h3>Dashboard Navigation Guide</h3>
          <div className="guide-intro">
            <p>
              This Gap Analysis Dashboard identifies research investment opportunities within NASA's 
              bioscience publication database. Each section provides specific insights for strategic 
              research planning and mission preparation.
            </p>
          </div>
          
          <div className="summary-content">
            <div className="summary-item">
              <h4>Overview Dashboard</h4>
              <p>
                Provides high-level metrics and key performance indicators for research coverage 
                analysis. Use this section to quickly assess the overall state of NASA's bioscience 
                research portfolio and identify primary areas requiring attention.
              </p>
            </div>
            
            <div className="summary-item">
              <h4>Missing Combinations Analysis</h4>
              <p>
                Systematically identifies unstudied organism-phenomenon-platform combinations 
                within the research database. These gaps represent unexplored research opportunities 
                that could yield significant scientific insights for space mission applications.
              </p>
            </div>

            <div className="summary-item">
              <h4>Biological System Completeness</h4>
              <p>
                Quantifies research completeness across major biological systems relevant to 
                space exploration. Percentage scores indicate coverage depth, helping prioritize 
                which physiological systems require additional investigation for mission success.
              </p>
            </div>

            <div className="summary-item">
              <h4>Mars Mission Critical Gaps</h4>
              <p>
                Highlights research deficiencies that directly impact Mars mission viability 
                and crew safety. These gaps require immediate attention as they represent 
                potential mission-critical failure points for long-duration space exploration.
              </p>
            </div>

            <div className="summary-item">
              <h4>3D Research Space Visualization</h4>
              <p>
                Interactive three-dimensional representation of the research landscape showing 
                organism-phenomenon-platform relationships. Visual coding enables rapid 
                identification of research density patterns and unexplored territories.
              </p>
            </div>

            <div className="summary-item research-strategy">
              <h4>Strategic Research Investment</h4>
              <p>
                This analysis enables data-driven budget allocation by identifying high-impact, 
                low-coverage research areas. Focus investment on gaps with maximum scientific 
                return and direct mission relevance to optimize research portfolio outcomes.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMissingCombinations = () => {
    const combinationsData = gapData.missingCombinations;
    const hasData = combinationsData.length > 0;

    if (!hasData) {
      return (
        <div className="missing-combinations">
          <h3>Missing Research Combinations</h3>
          <div className="no-data-message">
            <p>No missing combinations data available. Please ensure the Neo4j API is running and gap analysis has been performed.</p>
            <button onClick={fetchGapAnalysisData} className="retry-button">
              Retry Data Load
            </button>
          </div>
        </div>
      );
    }

    const handleLoadMore = () => {
      setDisplayCount(prev => Math.min(prev + 20, combinationsData.length));
    };

    const remainingCount = combinationsData.length - displayCount;

    return (
      <div className="missing-combinations">
        <h3>Missing Research Combinations</h3>
        <p className="section-description">
          These combinations represent unstudied research areas that could be critical 
          for space missions. Each card shows a specific research opportunity.
        </p>
        <div className="combinations-grid">
          {combinationsData.slice(0, displayCount).map((gap, index) => (
            <div key={index} className="combination-card">
              <div className="combination-header">
                <span className={`gap-priority priority-${gap.priority?.toLowerCase() || 'medium'}`}>
                  Priority: {gap.priority || 'Medium'}
                </span>
                {gap.impact_score && (
                  <span className="impact-badge">Impact: {gap.impact_score}/10</span>
                )}
              </div>
              <div className="combination-details">
                <div className="detail-item inline">
                  <strong>Organism:</strong> 
                  <span className="detail-value">{gap.organism || 'Not specified'}</span>
                </div>
                <div className="detail-item inline">
                  <strong>Phenomenon:</strong> 
                  <span className="detail-value">{gap.phenomenon || 'Not specified'}</span>
                </div>
                <div className="detail-item inline">
                  <strong>Platform:</strong> 
                  <span className="detail-value">{gap.platform || 'Not specified'}</span>
                </div>
              </div>
              <div className="combination-score">
                <span>Research Opportunity</span>
              </div>
            </div>
          ))}
        </div>
        
        {remainingCount > 0 && (
          <div className="load-more">
            <button onClick={handleLoadMore}>
              Load More ({remainingCount} remaining)
            </button>
            <div className="progress-indicator">
              Showing {displayCount} of {combinationsData.length} combinations
            </div>
          </div>
        )}
      </div>
    );
  };

  // Corrigeons la section Completeness Matrix pour utiliser les vraies données
  const renderCompletenessMatrix = () => {
    if (loading) {
      return <div className="chart-loading">Loading completeness analysis...</div>;
    }

    // Corrigeons la vérification du type de données
    const completenessData = Array.isArray(gapData.completenessMatrix) 
      ? gapData.completenessMatrix 
      : gapData.completenessMatrix?.data || [];

    if (!completenessData || completenessData.length === 0) {
      return (
        <div className="chart-empty">
          <p>No completeness data available</p>
          <p>Verify that the Neo4j service is running and contains data</p>
          <button onClick={fetchGapAnalysisData} className="retry-btn">Retry Data Load</button>
        </div>
      );
    }

    return (
      <div className="completeness-grid">
        {completenessData.map((item, index) => (
          <div key={index} className="completeness-card">
            <div className="completeness-header">
              <h3>{item.system?.charAt(0).toUpperCase() + item.system?.slice(1) || 'Unknown'} System</h3>
              <div className="completeness-percentage">
                {(item.completeness_percentage || 0).toFixed(1)}%
              </div>
            </div>
            
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${item.completeness_percentage || 0}%` }}
              />
            </div>
            
            <div className="completeness-details">
              <div className="detail-row">
                <span className="detail-label">Organisms:</span>
                <span className="detail-value">{item.total_organisms || 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Phenomena:</span>
                <span className="detail-value">{item.total_phenomena || 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Studied:</span>
                <span className="detail-value">{(item.studied_combinations || 0).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Possible:</span>
                <span className="detail-value">{(item.possible_combinations || 0).toLocaleString()}</span>
              </div>
            </div>
            
            <div className={`completeness-status ${getCompletenessStatus(item.completeness_percentage || 0)}`}>
              {getCompletenessLabel(item.completeness_percentage || 0)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Fonctions utilitaires pour le statut de complétude
  const getCompletenessStatus = (percentage) => {
    if (percentage >= 85) return 'high';
    if (percentage >= 60) return 'medium';
    return 'low';
  };

  const getCompletenessLabel = (percentage) => {
    if (percentage >= 85) return 'Well Covered';
    if (percentage >= 60) return 'Moderately Covered';
    return 'Needs Research';
  };

  const renderMarsCriticalGaps = () => {
    const marsGapsData = gapData.marsCriticalGaps;
    const hasData = marsGapsData.length > 0;

    if (!hasData) {
      return (
        <div className="mars-critical-gaps">
          <h3>Mars Mission Critical Gaps</h3>
          <div className="no-data-message">
            <p>No Mars critical gaps data available. Please ensure the Neo4j API is running and Mars-specific analysis has been performed.</p>
            <button onClick={fetchGapAnalysisData} className="retry-button">
              Retry Data Load
            </button>
          </div>
        </div>
      );
    }

    // Grouper par phénomène et prendre les organismes les plus pertinents
    const groupedGaps = groupMarsCriticalGaps(gapData.marsCriticalGaps);

    return (
      <div className="mars-gaps-grid">
        {groupedGaps.map((gap, index) => (
          <div key={index} className="mars-gap-card">
            <div className="gap-header">
              <h3>{gap.phenomenon}</h3>
              <div className={`gap-priority priority-${gap.priority.toLowerCase()}`}>
                {gap.priority}
              </div>
            </div>
            
            <div className="gap-details">
              <div className="detail-row">
                <span className="detail-label">Biological System:</span>
                <span className="detail-value">{gap.biological_system}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Key Organisms:</span>
                <span className="detail-value">{gap.key_organisms.join(', ')}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Total Organisms:</span>
                <span className="detail-value">{gap.organism_count}</span>
              </div>
            </div>
            
            <div className="gap-rationale">
              <strong>Research Need:</strong> {gap.rationale}
            </div>
            
            <div className="gap-impact">
              <span className="impact-badge">Mission Critical</span>
              <span className="timeline-badge">Long-duration missions</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Fonction pour grouper et traiter les gaps Mars
  const groupMarsCriticalGaps = (gaps) => {
    // Grouper par phénomène
    const grouped = gaps.reduce((acc, gap) => {
      const key = gap.phenomenon;
      if (!acc[key]) {
        acc[key] = {
          phenomenon:   gap.phenomenon,
          biological_system: gap.biological_system,
          priority: gap.priority_level.replace('CRITICAL_', ''),
          rationale: gap.rationale,
          organisms: [],
          organism_count: 0
        };
      }
      acc[key].organisms.push(gap.organism);
      acc[key].organism_count++;
      return acc;
    }, {});

    // Convertir en array et prendre les organismes les plus pertinents
    return Object.values(grouped).map(group => ({
      ...group,
      key_organisms: group.organisms
        .filter((org, index, arr) => arr.indexOf(org) === index) // Enlever duplicatas
        .filter(org => ['human', 'Arabidopsis thaliana', 'fruit fly', 'yeast'].includes(org)) // Prendre les plus pertinents
        .slice(0, 3) // Limiter à 3
    })).slice(0, 6); // Limiter à 6 gaps principaux
  };

  const render3DCube = () => (
    <div className="cube-visualization">
      <h3>3D Research Gap Visualization</h3>
      <div className="cube-placeholder">
        <div className="cube-info">
          <h4>Interactive 3D Cube</h4>
          <p>
            This visualization will show the organism × phenomenon × platform 
            research space as an interactive 3D cube, where:
          </p>
          <ul>
            <li><strong>Red cubes:</strong> Missing research combinations</li>
            <li><strong>Green cubes:</strong> Well-researched areas</li>
            <li><strong>Yellow cubes:</strong> Partially covered areas</li>
          </ul>
          <p>
            <strong>Dimensions:</strong><br/>
            • Organisms: {gapData.cubeData.dimensions?.organisms?.length || 0}<br/>
            • Phenomena: {gapData.cubeData.dimensions?.phenomena?.length || 0}<br/>
            • Platforms: {gapData.cubeData.dimensions?.platforms?.length || 0}
          </p>
        </div>
        <div className="cube-stats">
          <div className="cube-stat">
            <span className="stat-value">{gapData.cubeData.total_missing || 0}</span>
            <span className="stat-label">Missing Combinations</span>
          </div>
        </div>
      </div>
    </div>
  );

  const calculateAverageCompleteness = () => {
    // Corriger pour utiliser les vraies données avec vérification de type
    const completenessData = Array.isArray(gapData.completenessMatrix) 
      ? gapData.completenessMatrix 
      : gapData.completenessMatrix?.data || [];
    
    if (!completenessData || completenessData.length === 0) return 0;
    
    const average = completenessData.reduce((sum, item) => 
      sum + (item.completeness_percentage || 0), 0) / completenessData.length;
    return Math.round(average);
  };

  if (loading) {
    return (
      <div className="gap-analysis">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Analyzing research gaps...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="gap-analysis">
        <div className="error-state">
          <h3>Error Loading Gap Analysis</h3>
          <p>{error}</p>
          <button onClick={fetchGapAnalysisData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="gap-analysis">
      <div className="gap-header">
        <h1>Gap Analysis Dashboard</h1>
        <p>Identify research investment opportunities in NASA bioscience</p>
      </div>

      <div className="gap-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'missing' ? 'active' : ''}`}
          onClick={() => setActiveTab('missing')}
        >
          Missing Combinations
        </button>
        <button 
          className={`tab ${activeTab === 'completeness' ? 'active' : ''}`}
          onClick={() => setActiveTab('completeness')}
        >
          Completeness Matrix
        </button>
        <button 
          className={`tab ${activeTab === 'mars' ? 'active' : ''}`}
          onClick={() => setActiveTab('mars')}
        >
          Mars Critical
        </button>
        <button 
          className={`tab ${activeTab === 'cube' ? 'active' : ''}`}
          onClick={() => setActiveTab('cube')}
        >
          3D Visualization
        </button>
      </div>

      <div className="gap-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'missing' && renderMissingCombinations()}
        {activeTab === 'completeness' && renderCompletenessMatrix()}
        {activeTab === 'mars' && renderMarsCriticalGaps()}
        {activeTab === 'cube' && render3DCube()}
      </div>
    </div>
  );
};

export default GapAnalysis;