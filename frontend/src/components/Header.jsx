import React from 'react';
import './Header.css';

const Header = ({ currentPage, onNavigate, isDarkMode, onThemeToggle }) => {
  return (
    <header className="header fade-in">
      <div className="header-content">
        <div className="logo" onClick={() => onNavigate('home')}>
          <span className="logo-icon">
            <img src="/logoAppolon.png" alt="Apollon Logo" className="logo-design" />
          </span>
          <span className="logo-text">APOLLON</span>
        </div>
        
        <nav className="nav">
          {['home', 'explorer', 'about', 'resources'].map(page => (
            <button
              key={page}
              className={`nav-btn ${currentPage === page ? 'active' : ''}`}
              onClick={() => onNavigate(page)}
            >
              {page.charAt(0).toUpperCase() + page.slice(1)}
            </button>
          ))}
        </nav>

        <div className="header-actions">
          <button className="theme-toggle" onClick={onThemeToggle}>
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;