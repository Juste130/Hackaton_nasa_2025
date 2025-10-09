import React, { useState, useEffect, useCallback } from 'react';
import { summarizeArticle, summarizeMultipleArticles, createSession, askRAGQuestion } from '../services/aiApi';
import MarkdownRenderer from './MarkdownRenderer';
import './AISummaryPanel.css';

const AISummaryPanel = ({ publications, onClose }) => {
  const [mode, setMode] = useState('summary'); // 'summary' or 'chat'
  const [summaryData, setSummaryData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Determine if single or multiple publications
  const isSinglePublication = publications.length === 1;
  const pmcids = publications.map(p => p.pmcid).filter(Boolean);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const serviceType = mode === 'summary' ? 'summarizer' : 'rag_assistant';
        const session = await createSession(serviceType);
        setSessionId(session.session_id);
      } catch (err) {
        console.error('Failed to create session:', err);
      }
    };

    initSession();
  }, [mode]);

  // Auto-generate summary when in summary mode
  useEffect(() => {
    if (mode === 'summary' && !summaryData && !isGenerating) {
      generateSummary();
    }
  }, [mode]);

  const generateSummary = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      if (isSinglePublication) {
        // Single publication summary
        const pub = publications[0];
        const summary = await summarizeArticle(pub.pmcid, sessionId);
        
        setSummaryData({
          type: 'single',
          publication: pub,
          summary: summary.summary
        });
      } else {
        // Multiple publications summary
        if (pmcids.length === 0) {
          throw new Error('No valid PMCIDs found in selected publications');
        }

        const summaries = await summarizeMultipleArticles(pmcids, sessionId);
        
        setSummaryData({
          type: 'multiple',
          publications: publications,
          summaries: summaries.map(s => s.summary)
        });
      }

      setIsGenerating(false);
    } catch (err) {
      console.error('Summary generation error:', err);
      setError(err.message || 'Failed to generate summary');
      setIsGenerating(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isSending) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }]);

    setIsSending(true);

    try {
      // Call RAG API with the selected PMCIDs
      const response = await askRAGQuestion(userMessage, pmcids, sessionId);
      
      // Add AI response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        citations: response.citations || [],
        tools_used: response.tools_used || [],
        confidence: response.confidence,
        timestamp: new Date().toISOString()
      }]);

      setIsSending(false);
    } catch (err) {
      console.error('Chat error:', err);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString()
      }]);

      setIsSending(false);
    }
  };

  const downloadSummary = useCallback(() => {
    if (!summaryData) return;

    let content = `NASA BioSpace AI Summary Report
Generated: ${new Date().toLocaleDateString()}
Publications Analyzed: ${publications.length}

`;

    if (summaryData.type === 'single') {
      const { publication, summary } = summaryData;
      content += `PUBLICATION: ${publication.title}
PMCID: ${publication.pmcid}

EXECUTIVE SUMMARY:
${summary.executive_summary}

KEY FINDINGS:
${summary.key_findings}

METHODOLOGY:
${summary.methodology}

ORGANISMS STUDIED:
${summary.organisms_studied}

SPACE RELEVANCE:
${summary.space_relevance}

FUTURE DIRECTIONS:
${summary.future_directions}
`;
    } else {
      content += `COMPARATIVE ANALYSIS\n\n`;
      summaryData.summaries.forEach((summary, idx) => {
        const pub = publications[idx];
        content += `\n${'='.repeat(70)}\nPUBLICATION ${idx + 1}: ${pub.title}\n${'='.repeat(70)}\n\n`;
        content += `Executive Summary:\n${summary.executive_summary}\n\n`;
        content += `Key Findings:\n${summary.key_findings}\n\n`;
      });
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nasa-biosummary-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [summaryData, publications]);

  const downloadChatHistory = useCallback(() => {
    const content = `NASA BioSpace RAG Chat History
Generated: ${new Date().toLocaleDateString()}
Publications Context: ${pmcids.join(', ')}

${'='.repeat(70)}

${messages.map(msg => `
[${msg.role.toUpperCase()}] ${new Date(msg.timestamp).toLocaleTimeString()}
${msg.content}
${msg.citations ? `\nSources: ${msg.citations.join(', ')}` : ''}
${msg.tools_used ? `\nTools Used: ${msg.tools_used.join(', ')}` : ''}
${'—'.repeat(70)}
`).join('\n')}
`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nasa-rag-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [messages, pmcids]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div className="ai-summary-overlay" onClick={onClose}>
      <div className="ai-summary-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-summary-header">
          <div className="ai-summary-header-content">
            <h2>🤖 AI Research Assistant</h2>
            <p>{publications.length} selected publication{publications.length !== 1 ? 's' : ''}</p>
          </div>
          
          {/* Mode Toggle */}
          <div className="mode-toggle">
            <button
              className={`mode-btn ${mode === 'summary' ? 'active' : ''}`}
              onClick={() => setMode('summary')}
            >
              📋 Summary
            </button>
            <button
              className={`mode-btn ${mode === 'chat' ? 'active' : ''}`}
              onClick={() => setMode('chat')}
            >
              💬 Chat RAG
            </button>
          </div>

          <button 
            className="close-button" 
            onClick={onClose}
            aria-label="Close panel"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="ai-summary-content">
          {mode === 'summary' ? (
            // SUMMARY MODE
            <>
              {isGenerating ? (
                <div className="generating-state">
                  <div className="loading-spinner"></div>
                  <h3>Generating AI Summary...</h3>
                  <p>Analyzing patterns across selected publications</p>
                </div>
              ) : error ? (
                <div className="error-state">
                  <div className="error-icon">⚠️</div>
                  <h3>Summary Generation Failed</h3>
                  <p>{error}</p>
                  <button className="btn btn-primary" onClick={generateSummary}>
                    Retry
                  </button>
                </div>
              ) : summaryData?.type === 'single' ? (
                <SinglePublicationSummary 
                  publication={summaryData.publication}
                  summary={summaryData.summary}
                />
              ) : (
                <MultiplePublicationsSummary 
                  publications={publications}
                  summaries={summaryData?.summaries || []}
                />
              )}
            </>
          ) : (
            // CHAT MODE
            <div className="chat-mode">
              <div className="chat-context-banner">
                <span className="context-icon">📚</span>
                <span>Chat context: {pmcids.join(', ')}</span>
              </div>

              <div className="chat-messages">
                {messages.length === 0 ? (
                  <div className="chat-welcome">
                    <h3>💬 Ask questions about the selected articles</h3>
                    <p>I can help you explore:</p>
                    <ul>
                      <li>Key findings and methodologies</li>
                      <li>Comparisons between articles</li>
                      <li>Space biology relevance</li>
                      <li>Organisms and systems studied</li>
                      <li>Future research directions</li>
                    </ul>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <ChatMessage key={idx} message={msg} />
                  ))
                )}
                
                {isSending && (
                  <div className="chat-message assistant thinking">
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <form className="chat-input-form" onSubmit={handleSendMessage}>
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask a question about the selected articles..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={isSending}
                />
                <button 
                  type="submit" 
                  className="chat-send-btn"
                  disabled={!inputMessage.trim() || isSending}
                >
                  {isSending ? '⏳' : '🚀'}
                </button>
              </form>
            </div>
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
          
          {mode === 'summary' && !isGenerating && !error && (
            <button 
              className="btn btn-primary"
              onClick={downloadSummary}
            >
              📥 Download Summary
            </button>
          )}
          
          {mode === 'chat' && messages.length > 0 && (
            <button 
              className="btn btn-primary"
              onClick={downloadChatHistory}
            >
              📥 Download Chat
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Chat Message Component
const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`chat-message ${message.role} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <MarkdownRenderer content={message.content} />
        
        {message.citations && message.citations.length > 0 && (
          <div className="message-citations">
            <strong>📚 Sources:</strong> {message.citations.join(', ')}
          </div>
        )}
        
        {message.tools_used && message.tools_used.length > 0 && (
          <div className="message-tools">
            <strong>🔧 Tools used:</strong> {message.tools_used.join(', ')}
          </div>
        )}
        
        {message.confidence && (
          <div className="message-confidence">
            <strong>Confidence:</strong> {message.confidence}
          </div>
        )}
        
        <div className="message-timestamp">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

// Single publication summary component
const SinglePublicationSummary = ({ publication, summary }) => (
  <>
    <section className="summary-section">
      <h3>📄 {publication.title}</h3>
      <p className="publication-meta">
        PMCID: {publication.pmcid} • {publication.journal} • {publication.publication_date ? new Date(publication.publication_date).getFullYear() : 'N/A'}
      </p>
    </section>

    <section className="summary-section">
      <h3>📋 Executive Summary</h3>
      <MarkdownRenderer content={summary.executive_summary} />
    </section>

    <section className="summary-section">
      <h3>🔍 Key Findings</h3>
      <MarkdownRenderer content={summary.key_findings} />
    </section>

    <section className="summary-section">
      <h3>🔬 Methodology</h3>
      <MarkdownRenderer content={summary.methodology} />
    </section>

    <section className="summary-section">
      <h3>🧬 Organisms Studied</h3>
      <MarkdownRenderer content={summary.organisms_studied} />
    </section>

    <section className="summary-section">
      <h3>🚀 Space Relevance</h3>
      <MarkdownRenderer content={summary.space_relevance} />
    </section>

    <section className="summary-section">
      <h3>🔮 Future Directions</h3>
      <MarkdownRenderer content={summary.future_directions} />
    </section>
  </>
);

// Multiple publications summary component
const MultiplePublicationsSummary = ({ publications, summaries }) => (
  <>
    <section className="summary-section">
      <h3>📚 Comparative Analysis</h3>
      <p>Analysis of {publications.length} publications</p>
    </section>

    {summaries.map((summary, idx) => (
      <div key={idx} className="publication-summary-block">
        <h4>📄 Publication {idx + 1}: {publications[idx].title}</h4>
        
        <div className="summary-subsection">
          <h5>Executive Summary</h5>
          <MarkdownRenderer content={summary.executive_summary} />
        </div>

        <div className="summary-subsection">
          <h5>Key Findings</h5>
          <MarkdownRenderer content={summary.key_findings} />
        </div>

        <div className="summary-subsection">
          <h5>Space Relevance</h5>
          <MarkdownRenderer content={summary.space_relevance} />
        </div>
      </div>
    ))}
  </>
);

export default AISummaryPanel;