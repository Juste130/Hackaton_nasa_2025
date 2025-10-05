import React from 'react';
import './Resources.css';

const Resources = () => {
  const nasaResources = [
    {
      title: "Référentiel des Publications en Biosciences",
      description: "Les 608 publications scientifiques utilisées dans ce projet",
      link: "https://github.com/jgalazka/SB_publications/tree/main",
      category: "📚 Publications"
    },
    {
      title: "NASA Open Science Data Repository (OSDR)",
      description: "Données primaires et métadonnées des études biologiques",
      link: "https://www.nasa.gov/osdr/",
      category: "💾 Données"
    },
    {
      title: "Bibliothèque des Sciences de la Vie Spatiale",
      description: "Publications supplémentaires pertinentes sur la biologie spatiale",
      link: "https://public.ksc.nasa.gov/nslsl/",
      category: "📚 Publications"
    },
    {
      title: "Cahier des Tâches de la NASA (NSPIRES)",
      description: "Informations sur les subventions ayant financé ces études",
      link: "https://taskbook.nasaprs.com/tbp/welcome.cfm",
      category: "📋 Administration"
    }
  ];

  return (
    <div className="resources">
      <div className="resources-header fade-in">
        <h1>Ressources NASA</h1>
        <p>Accédez aux sources officielles de données et publications</p>
      </div>

      <div className="resources-content">
        <section className="resources-intro">
          <h2>📖 Sources de Données</h2>
          <p>
            Cette plateforme s'appuie sur des données officielles de la NASA. 
            Voici les principales ressources utilisées pour alimenter notre moteur de connaissances.
          </p>
        </section>

        <div className="resources-grid">
          {nasaResources.map((resource, index) => (
            <div key={index} className="resource-card fade-in">
              <div className="resource-category">{resource.category}</div>
              <h3>{resource.title}</h3>
              <p>{resource.description}</p>
              <a 
                href={resource.link} 
                className="resource-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                🔗 Accéder à la ressource
              </a>
            </div>
          ))}
        </div>

        <section className="api-section">
          <h2>🔧 API & Développement</h2>
          <div className="api-card">
            <h3>API du Moteur de Connaissances</h3>
            <p>
              Notre API REST permet aux développeurs d'intégrer les fonctionnalités 
              de recherche et d'analyse dans leurs propres applications.
            </p>
            <div className="api-endpoints">
              <div className="endpoint">
                <code>GET /api/search?q=microgravity</code>
                <span>Recherche sémantique</span>
              </div>
              <div className="endpoint">
                <code>POST /api/chat</code>
                <span>Interface conversationnelle</span>
              </div>
              <div className="endpoint">
                <code>GET /api/publications</code>
                <span>Liste des publications</span>
              </div>
            </div>
            <button className="btn btn-primary">
              📚 Voir la Documentation
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Resources;