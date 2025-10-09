import React from 'react';
import './MarkdownMessage.css';

const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  // Parse markdown-like text and convert to JSX
  const parseMarkdown = (text) => {
    if (typeof text !== 'string') return text;

    // Split by double newlines for paragraphs
    const paragraphs = text.split('\n\n');

    return paragraphs.map((para, idx) => {
      // Handle headers
      if (para.startsWith('###')) {
        return <h3 key={idx}>{para.replace(/^###\s*/, '')}</h3>;
      }
      if (para.startsWith('##')) {
        return <h2 key={idx}>{para.replace(/^##\s*/, '')}</h2>;
      }
      if (para.startsWith('#')) {
        return <h1 key={idx}>{para.replace(/^#\s*/, '')}</h1>;
      }

      // Handle bold text
      const lines = para.split('\n').map((line, lineIdx) => {
        // Handle bullet points
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return (
            <li key={lineIdx}>
              {line.replace(/^[-•]\s*/, '').split('**').map((part, i) => 
                i % 2 === 1 ? <strong key={i}>{part}</strong> : part
              )}
            </li>
          );
        }

        // Handle bold text in regular lines
        const parts = line.split('**');
        return (
          <span key={lineIdx}>
            {parts.map((part, i) => 
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
            {lineIdx < para.split('\n').length - 1 && <br />}
          </span>
        );
      });

      // Check if all lines are list items
      const allListItems = lines.every(line => line.type === 'li');

      if (allListItems) {
        return <ul key={idx}>{lines}</ul>;
      }

      return <p key={idx}>{lines}</p>;
    });
  };

  return (
    <div className="markdown-content">
      {parseMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer;