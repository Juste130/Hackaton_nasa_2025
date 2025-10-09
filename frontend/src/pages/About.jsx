import React from 'react';
import './About.css';

const About = () => {
  const teamMembers = [
    { name: "Obed AGBOHOUN", role: "Frontend Developer" },
    { name: "Juste HOUEZO", role: "Frontend & Design" },
    { name: "Régis KIKI", role: "Backend Developer" },
    { name: "Romuald AMEGBEDJI", role: "Data Scientist / IA" },
    { name: "Ghilth GBAGUIDI", role: "IA Engineer & Presenter" }
  ];

  return (
    <div className="about">
      <div className="about-header fade-in">
        <h1>About the Project</h1>
        <p>Our mission is to make space research accessible to everyone</p>
      </div>

      <div className="about-content">
        <section className="about-section">
          <h2>🚀 NASA Space Apps Challenge 2025</h2>
          <p>
            This project was developed for the NASA Space Apps 2025 hackathon 
            for the challenge "Building a Space Biology Knowledge Engine".
          </p>
          <p>
            Our goal is to transform 608 NASA scientific publications into an interactive and accessible knowledge base.
          </p>
        </section>

        <section className="about-section">
          <h2>🎯 Our Mission</h2>
          <div className="mission-grid">
            <div className="mission-card">
              <h3>Accessibility</h3>
              <p>Making space research understandable for all audiences</p>
            </div>
            <div className="mission-card">
              <h3>Innovation</h3>
              <p>Using AI to uncover hidden insights in data</p>
            </div>
            <div className="mission-card">
              <h3>Collaboration</h3>
              <p>Facilitating scientific discovery and collaboration</p>
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>👥 Our Team</h2>
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
            This platform was created during a hackathon and is not an official NASA product. Source data is provided by NASA and publicly accessible.
          </p>
        </section>
      </div>
    </div>
  );
};

export default About;