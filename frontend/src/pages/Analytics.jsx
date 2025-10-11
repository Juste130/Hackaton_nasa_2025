import React, { useState, useEffect } from 'react';
import StatCard from '../components/StatCard';
import './Analytics.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000';

const Analytics = () => {
  const [overview, setOverview] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [keywordsDist, setKeywordsDist] = useState([]);
  const [meshTermsDist, setMeshTermsDist] = useState([]);
  const [entitiesDist, setEntitiesDist] = useState([]);
  const [topEntities, setTopEntities] = useState([]);
  const [yearRanges, setYearRanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntityType, setSelectedEntityType] = useState('');

  useEffect(() => {
    fetchAllData();
  }, []);

  useEffect(() => {
    if (selectedEntityType) {
      fetchTopEntities(selectedEntityType);
    }
  }, [selectedEntityType]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [
        overviewRes,
        timelineRes,
        keywordsRes,
        meshTermsRes,
        entitiesRes,
        topEntitiesRes,
        yearRangesRes
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/api/analytics/overview`),
        fetch(`${API_BASE_URL}/api/analytics/timeline`),
        fetch(`${API_BASE_URL}/api/analytics/distribution/keywords?limit=15`),
        fetch(`${API_BASE_URL}/api/analytics/distribution/mesh-terms?limit=15`),
        fetch(`${API_BASE_URL}/api/analytics/distribution/entities`),
        fetch(`${API_BASE_URL}/api/analytics/top-entities?limit=15`),
        fetch(`${API_BASE_URL}/api/analytics/publications-by-year-range`)
      ]);

      const overviewData = await overviewRes.json();
      const timelineData = await timelineRes.json();
      const keywordsData = await keywordsRes.json();
      const meshTermsData = await meshTermsRes.json();
      const entitiesData = await entitiesRes.json();
      const topEntitiesData = await topEntitiesRes.json();
      const yearRangesData = await yearRangesRes.json();

      setOverview(overviewData);
      setTimeline(timelineData);
      setKeywordsDist(keywordsData);
      setMeshTermsDist(meshTermsData);
      setEntitiesDist(entitiesData);
      setTopEntities(topEntitiesData);
      setYearRanges(yearRangesData);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTopEntities = async (entityType) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/analytics/top-entities?type=${entityType}&limit=15`
      );
      const data = await response.json();
      setTopEntities(data);
    } catch (error) {
      console.error('Error fetching top entities:', error);
    }
  };

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Research Analytics</h1>
        <p>Comprehensive analysis of NASA's 608 bioscience publications</p>
      </div>

      <div className="analytics-content">
        {/* Cartes de statistiques */}
        <div className="stats-grid">
          <StatCard
            title="Total Publications"
            value={overview?.totalPublications || 0}
            icon="📄"
            loading={loading}
          />
          <StatCard
            title="Keywords"
            value={overview?.uniqueKeywords || 0}
            icon="🔑"
            loading={loading}
          />
          <StatCard
            title="MeSH Terms"
            value={overview?.uniqueMeshTerms || 0}
            icon="🏷️"
            loading={loading}
          />
          <StatCard
            title="Time Span"
            value={overview?.timeSpan || 'N/A'}
            icon="📅"
            loading={loading}
          />
        </div>

        {/* Timeline */}
        <div className="chart-section">
          <h2>Publications Over Time</h2>
          <div className="chart-container">
            {loading ? (
              <div className="chart-loading">Loading timeline...</div>
            ) : timeline.length > 0 ? (
              <div className="timeline-chart">
                {timeline.map((item) => {
                  const maxCount = Math.max(...timeline.map(t => t.count));
                  const minCount = Math.min(...timeline.map(t => t.count));
                  const range = maxCount - minCount;
                  
                  // Calcul proportionnel : la plus petite barre fait 15% et la plus grande 85%
                  const heightPercent = range > 0 
                    ? 15 + ((item.count - minCount) / range) * 70
                    : 50; // Si toutes les valeurs sont identiques
                  
                  return (
                    <div key={item.year} className="timeline-bar">
                      <div
                        className="timeline-bar-fill"
                        style={{
                          height: `${heightPercent}%`
                        }}
                        title={`${item.year}: ${item.count} publications`}
                      />
                      <div className="timeline-bar-label">{item.year}</div>
                      <div className="timeline-bar-count">{item.count}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="chart-loading">No timeline data available</div>
            )}
          </div>
        </div>

        {/* Publications par période */}
        <div className="chart-section">
          <h2>Publications by Era</h2>
          <div className="chart-container">
            {loading ? (
              <div className="chart-loading">Loading data...</div>
            ) : (
              <div className="bar-chart-horizontal">
                {yearRanges.map((item) => (
                  <div key={item.range} className="bar-item">
                    <div className="bar-label">{item.range}</div>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(item.count / Math.max(...yearRanges.map(r => r.count))) * 100}%`
                        }}
                      />
                      <div className="bar-value">{item.count}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Distribution des entités et Top entités côte à côte */}
        <div className="two-columns">
          <div className="chart-section">
            <h2>Entity Types Distribution</h2>
            <div className="chart-container">
              {loading ? (
                <div className="chart-loading">Loading data...</div>
              ) : entitiesDist.length > 0 ? (
                <div className="bar-chart-horizontal">
                  {entitiesDist.map((item) => (
                    <div
                      key={item.name}
                      className={`bar-item ${selectedEntityType === item.name ? 'active' : ''}`}
                      onClick={() => setSelectedEntityType(item.name)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="bar-label">{item.name}</div>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${(item.count / Math.max(1, ...entitiesDist.map(e => e.count))) * 100}%`
                          }}
                        />
                        <div className="bar-value">{item.count}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="chart-empty">
                  <p>📊 Entity data not available yet</p>
                  <p>This feature will be activated once entity extraction is completed.</p>
                </div>
              )}
            </div>
          </div>

          <div className="chart-section">
            <h2>
              Top Entities
              {selectedEntityType && ` (${selectedEntityType})`}
            </h2>
            <div className="chart-container">
              {loading ? (
                <div className="chart-loading">Loading data...</div>
              ) : topEntities.length > 0 ? (
                <div className="list-items">
                  {topEntities.map((item, index) => (
                    <div key={`${item.name}-${index}`} className="list-item">
                      <span className="list-item-rank">{index + 1}</span>
                      <span className="list-item-name">{item.name}</span>
                      <span className="list-item-badge">{item.type}</span>
                      <span className="list-item-count">{item.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="chart-empty">
                  <p>🏷️ Entity details not available yet</p>
                  <p>Select an entity type from the left to see top items.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Top Keywords et MeSH Terms côte à côte */}
        <div className="two-columns">
          <div className="chart-section">
            <h2>Top Keywords</h2>
            <div className="chart-container">
              {loading ? (
                <div className="chart-loading">Loading data...</div>
              ) : (
                <div className="list-items">
                  {keywordsDist.map((item, index) => (
                    <div key={item.name} className="list-item">
                      <span className="list-item-rank">{index + 1}</span>
                      <span className="list-item-name">{item.name}</span>
                      <span className="list-item-count">{item.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="chart-section">
            <h2>Top MeSH Terms</h2>
            <div className="chart-container">
              {loading ? (
                <div className="chart-loading">Loading data...</div>
              ) : (
                <div className="list-items">
                  {meshTermsDist.map((item, index) => (
                    <div key={item.name} className="list-item">
                      <span className="list-item-rank">{index + 1}</span>
                      <span className="list-item-name">{item.name}</span>
                      <span className="list-item-count">{item.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
