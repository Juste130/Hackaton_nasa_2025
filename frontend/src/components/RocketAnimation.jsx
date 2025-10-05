import React, { useState, useEffect } from 'react';
import './RocketAnimation.css';

const RocketAnimation = ({ onAnimationComplete }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLaunching, setIsLaunching] = useState(false);
  const [showStars, setShowStars] = useState(false);

  useEffect(() => {
    // Séquence d'animation
    const timer = setTimeout(() => {
      setIsLaunching(true);
      setShowStars(true);
    }, 500);

    const completionTimer = setTimeout(() => {
      setIsLaunching(false);
      setTimeout(() => {
        setIsVisible(false);
        onAnimationComplete();
      }, 1000);
    }, 3000);

    return () => {
      clearTimeout(timer);
      clearTimeout(completionTimer);
    };
  }, [onAnimationComplete]);

  if (!isVisible) return null;

  return (
    <div className={`rocket-animation-overlay ${isLaunching ? 'launching' : ''}`}>
      {/* Étoiles de fond */}
      {showStars && (
        <div className="stars">
          {Array.from({ length: 50 }).map((_, i) => (
            <div 
              key={i} 
              className="star"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${1 + Math.random() * 2}s`
              }}
            />
          ))}
        </div>
      )}
      
      {/* Fusée */}
      <div className={`rocket ${isLaunching ? 'launching' : ''}`}>
        <div className="rocket-body">
          <div className="rocket-nose"></div>
          <div className="rocket-main">
            <div className="rocket-window"></div>
          </div>
          <div className="rocket-fins">
            <div className="fin fin-left"></div>
            <div className="fin fin-right"></div>
          </div>
        </div>
        
        {/* Flammes et particules */}
        <div className="exhaust">
          <div className="flame flame-main"></div>
          <div className="flame flame-1"></div>
          <div className="flame flame-2"></div>
          <div className="flame flame-3"></div>
          <div className="smoke-particles">
            {Array.from({ length: 15 }).map((_, i) => (
              <div 
                key={i} 
                className="smoke-particle"
                style={{
                  animationDelay: `${i * 0.1}s`,
                  left: `${20 + Math.random() * 60}%`
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Traînée de lumière */}
      <div className="light-trail"></div>

      {/* Message de bienvenue */}
      <div className={`welcome-message ${isLaunching ? 'fade-out' : ''}`}>
        <h1>Appolon</h1>
        <p>Launching into space biology research...</p>
      </div>

      {/* Effet de flash au décollage */}
      {isLaunching && <div className="launch-flash"></div>}
    </div>
  );
};

export default RocketAnimation;