import React, { useState, useEffect, useCallback, useMemo } from 'react';
import './AISummaryPanel.css';

const AISummaryPanel = ({ publications, onClose }) => {
  const [summary, setSummary] = useState('');
  const [isGenerating, setIsGenerating] = useState(true);
  const [keyInsights, setKeyInsights] = useState([]);
  const [consensusPoints, setConsensusPoints] = useState([]);
  const [knowledgeGaps, setKnowledgeGaps] = useState([]);

  // Memoize unique themes and systems to avoid recalculation
  const { uniquePhenomena, uniqueSystems } = useMemo(() => {
    const phenomena = Array.from(new Set(publications.flatMap(pub => pub.phenomena || [])));
    const systems = Array.from(new Set(publications.flatMap(pub => pub.systems || [])));
    return { uniquePhenomena: phenomena, uniqueSystems: systems };
  }, [publications]);

  // Use useCallback to prevent unnecessary re-renders
  const generateAISummary = useCallback(async () => {
    setIsGenerating(true);
    
    // Simulate AI API call with cleanup
    const timeoutId = setTimeout(() => {
      const mockSummary = `Based on analysis of ${publications.length} selected publications, I've identified several key patterns in space biology research:

**Main Research Areas:**
${publications.map(pub => `- ${pub.title}`).join('\n')}

**Common Themes:**
- ${uniquePhenomena.join(', ')}
- ${uniqueSystems.join(', ')}

**Research Impact:**
The selected studies demonstrate significant advances in understanding how space environments affect biological systems, with particular focus on long-duration mission preparedness.`;

      const mockInsights = [
        'Microgravity shows consistent impact on skeletal systems across multiple studies',
        'Radiation effects vary significantly between biological systems',
        'Plant growth in space demonstrates remarkable adaptability',
        'Immune system responses show time-dependent patterns'
      ];

      const mockConsensus = [
        'Universal agreement on bone density loss in microgravity',
        'Consistent findings on plant growth challenges in space soil',
        'Agreement on radiation shielding requirements'
      ];

      const mockGaps = [
        'Long-term effects beyond 1 year in space',
        'Combined impact of multiple space stressors',
        'Species-specific variations in space adaptation'
      ];

      setSummary(mockSummary);
      setKeyInsights(mockInsights);
      setConsensusPoints(mockConsensus);
      setKnowledgeGaps(mockGaps);
      setIsGenerating(false);
    }, 3000);

    // Cleanup function
    return () => clearTimeout(timeoutId);
  }, [publications, uniquePhenomena, uniqueSystems]);

  useEffect(() => {
    const cleanup = generateAISummary();
    return cleanup;
  }, [generateAISummary]);

  const downloadSummary = useCallback(() => {
    const content = `
NASA BioSpace AI Summary Report
Generated: ${new Date().toLocaleDateString()}
Publications Analyzed: ${publications.length}

SUMMARY:
${summary}

KEY INSIGHTS:
${keyInsights.map(insight => `• ${insight}`).join('\n')}

CONSENSUS POINTS:
${consensusPoints.map(point => `• ${point}`).join('\n')}

KNOWLEDGE GAPS:
${knowledgeGaps.map(gap => `• ${gap}`).join('\n')}

SELECTED PUBLICATIONS:
${publications.map(pub => {
  const firstAuthor = pub.authors?.[0] || 'Unknown';
  const year = pub.date ? new Date(pub.date).getFullYear() : 'N/A';
  return `- ${pub.title} (${firstAuthor} et al., ${year})`;
}).join('\n')}
    `;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nasa-biosummary-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [publications, summary, keyInsights, consensusPoints, knowledgeGaps]);

  // Handle escape key to close panel
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Render summary paragraphs
  const renderSummaryText = useMemo(() => {
    return summary.split('\n').map((paragraph, index) => (
      paragraph.trim() && <p key={index}>{paragraph}</p>
    ));
  }, [summary]);

  return (
    <div className="ai-summary-overlay" onClick={onClose}>
      <div className="ai-summary-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-summary-header">
          <div className="header-content">
            <h2>🤖 AI Research Summary</h2>
            <p>Analysis of {publications.length} selected publication{publications.length !== 1 ? 's' : ''}</p>
          </div>
          <button 
            className="close-button" 
            onClick={onClose}
            aria-label="Close summary panel"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="ai-summary-content">
          {isGenerating ? (
            <div className="generating-state">
              <div className="loading-spinner"></div>
              <h3>Generating AI Summary...</h3>
              <p>Analyzing patterns across selected publications</p>
            </div>
          ) : (
            <>
              {/* Executive Summary */}
              <section className="summary-section">
                <h3>Executive Summary</h3>
                <div className="summary-text">
                  {renderSummaryText}
                </div>
              </section>

              {/* Key Insights */}
              <section className="insights-section">
                <h3>🔍 Key Insights</h3>
                <div className="insights-grid">
                  {keyInsights.map((insight, index) => (
                    <div key={index} className="insight-card">
                      <div className="insight-number">{index + 1}</div>
                      <p>{insight}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* Consensus & Gaps */}
              <div className="analysis-grid">
                <section className="consensus-section">
                  <h3>✅ Consensus Points</h3>
                  <ul>
                    {consensusPoints.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </section>

                <section className="gaps-section">
                  <h3>🔬 Knowledge Gaps</h3>
                  <ul>
                    {knowledgeGaps.map((gap, index) => (
                      <li key={index}>{gap}</li>
                    ))}
                  </ul>
                </section>
              </div>

              {/* Selected Publications */}
              <section className="publications-section">
                <h3>📚 Analyzed Publications</h3>
                <div className="selected-pubs-list">
                  {publications.map(pub => (
                    <div key={pub.id} className="selected-pub">
                      <strong>{pub.title}</strong>
                      <span>
                        {pub.authors?.[0] || 'Unknown'} et al. • {pub.date ? new Date(pub.date).getFullYear() : 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="ai-summary-footer">
          <button 
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
          {!isGenerating && (
            <button 
              className="btn btn-primary"
              onClick={downloadSummary}
            >
              📥 Download Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AISummaryPanel;