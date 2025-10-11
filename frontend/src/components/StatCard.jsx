import React from 'react';
import './StatCard.css';

const StatCard = ({ title, value, icon, loading = false }) => {
  return (
    <div className="stat-card">
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-content">
        <h3 className="stat-card-title">{title}</h3>
        {loading ? (
          <div className="stat-card-loading">Loading...</div>
        ) : (
          <p className="stat-card-value">{value}</p>
        )}
      </div>
    </div>
  );
};

export default StatCard;
