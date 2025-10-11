import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './MarkdownMessage.css';

const MarkdownMessage = ({ content, isBot = false }) => {
  const components = {
    // Personnaliser les composants Markdown
    h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
    h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
    h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
    h4: ({ children }) => <h4 className="md-h4">{children}</h4>,
    h5: ({ children }) => <h5 className="md-h5">{children}</h5>,
    h6: ({ children }) => <h6 className="md-h6">{children}</h6>,
    
    p: ({ children }) => <p className="md-paragraph">{children}</p>,
    
    strong: ({ children }) => <strong className="md-bold">{children}</strong>,
    em: ({ children }) => <em className="md-italic">{children}</em>,
    
    ul: ({ children }) => <ul className="md-list">{children}</ul>,
    ol: ({ children }) => <ol className="md-list md-ordered">{children}</ol>,
    li: ({ children }) => <li className="md-list-item">{children}</li>,
    
    blockquote: ({ children }) => (
      <blockquote className="md-blockquote">{children}</blockquote>
    ),
    
    code: ({ inline, children, className }) => {
      if (inline) {
        return <code className="md-inline-code">{children}</code>;
      }
      return (
        <pre className="md-code-block">
          <code className={className}>{children}</code>
        </pre>
      );
    },
    
    a: ({ href, children }) => (
      <a 
        href={href} 
        className="md-link" 
        target="_blank" 
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
    
    table: ({ children }) => (
      <div className="md-table-wrapper">
        <table className="md-table">{children}</table>
      </div>
    ),
    
    thead: ({ children }) => <thead className="md-table-head">{children}</thead>,
    tbody: ({ children }) => <tbody className="md-table-body">{children}</tbody>,
    tr: ({ children }) => <tr className="md-table-row">{children}</tr>,
    th: ({ children }) => <th className="md-table-header">{children}</th>,
    td: ({ children }) => <td className="md-table-cell">{children}</td>,
    
    hr: () => <hr className="md-divider" />,
    
    // Personnaliser les images si nécessaire
    img: ({ src, alt }) => (
      <img 
        src={src} 
        alt={alt} 
        className="md-image"
        loading="lazy"
      />
    )
  };

  return (
    <div className={`markdown-content ${isBot ? 'bot-markdown' : 'user-markdown'}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownMessage;