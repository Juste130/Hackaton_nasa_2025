import React from 'react';
import './About.css';

const About = () => {
  const teamMembers = [
    { name: "Obed", role: "Frontend Developer" },
    { name: "Juste", role: "Frontend & Design" },
    { name: "Regis", role: "Backend Developer" },
    { name: "Romuald", role: "Data Scientist / IA" },
    { name: "Ghilth", role: "IA Engineer & Presenter" }
  ];

  return (
    <div className="about">
      <div className="about-header fade-in">
        <h1>À Propos du Projet</h1>
        <p>Notre mission est de rendre la recherche spatiale accessible à tous</p>
      </div>

      <div className="about-content">
        <section className="about-section">
          <h2>🚀 Le Défi NASA Space Apps 2025</h2>
          <p>
            Ce projet a été développé dans le cadre du hackathon NASA Space Apps 2025 
            pour le défi "Construire un moteur de connaissances en biologie spatiale".
          </p>
          <p>
            Notre objectif est de transformer 608 publications scientifiques de la NASA 
            en une base de connaissances interactive et accessible.
          </p>
        </section>

        <section className="about-section">
          <h2>🎯 Notre Mission</h2>
          <div className="mission-grid">
            <div className="mission-card">
              <h3>Accessibilité</h3>
              <p>Rendre la recherche spatiale compréhensible pour tous les publics</p>
            </div>
            <div className="mission-card">
              <h3>Innovation</h3>
              <p>Utiliser l'IA pour découvrir des insights cachés dans les données</p>
            </div>
            <div className="mission-card">
              <h3>Collaboration</h3>
              <p>Faciliter la découverte et la collaboration scientifique</p>
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>👥 Notre Équipe</h2>
          <div className="team-grid">
            {teamMembers.map((member, index) => (
              <div key={index} className="team-card fade-in">
                <div className="member-avatar">
                  {member.name.charAt(0)}
                </div>
                <h3>{member.name}</h3>
                <p>{member.role}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="about-section disclaimer">
          <h2>📝 Disclaimer</h2>
          <p>
            Cette plateforme a été créée dans le cadre d'un hackathon et n'est pas 
            un produit officiel de la NASA. Les données sources sont fournies par 
            la NASA et accessibles au public.
          </p>
        </section>
      </div>
    </div>
  );
};

export default About;