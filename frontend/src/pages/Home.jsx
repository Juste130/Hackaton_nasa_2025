import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { useChat } from '../context/ChatContext';
import './Home.css';

const Home = ({ onNavigate }) => {
  const { openChat } = useChat();
  
  // Références pour les éléments à animer
  const heroRef = useRef();
  const titleRef = useRef();
  const subtitleRef = useRef();
  const buttonsRef = useRef();
  const floatingCardsRef = useRef([]);
  const starsRef = useRef();
  const planetsRef = useRef([]);
  const solarSystemRef = useRef();

  useEffect(() => {
    // Créer les étoiles dynamiquement
    createStars();
    
    // Timeline principale pour l'interface
    const tl = gsap.timeline({
      defaults: { ease: "power3.out" }
    });

    // Animation du système solaire en premier
    tl.fromTo(planetsRef.current,
      {
        rotation: 0,
        scale: 0,
        opacity: 0
      },
      {
        rotation: 360,
        scale: 1,
        opacity: 1,
        duration: 3,
        stagger: 0.5,
        ease: "back.out(1.7)"
      }
    )
    // Animation d'entrée séquentielle de l'interface
    .fromTo(titleRef.current, 
      { 
        y: 100, 
        opacity: 0,
        rotationX: 90
      },
      { 
        y: 0, 
        opacity: 1,
        rotationX: 0,
        duration: 1.2
      },
      "-=1.5"
    )
    .fromTo(subtitleRef.current,
      {
        y: 50,
        opacity: 0,
        scale: 0.8
      },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 1
      },
      "-=0.5"
    )
    .fromTo(buttonsRef.current,
      {
        y: 30,
        opacity: 0,
        stagger: 0.1
      },
      {
        y: 0,
        opacity: 1,
        stagger: 0.1,
        duration: 0.8
      },
      "-=0.3"
    )
    .fromTo(floatingCardsRef.current,
      {
        y: 100,
        opacity: 0,
        rotation: 180,
        scale: 0
      },
      {
        y: 0,
        opacity: 1,
        rotation: 0,
        scale: 1,
        stagger: 0.2,
        duration: 1,
        ease: "back.out(1.7)"
      },
      "-=0.5"
    );

    // Animations continues
    startContinuousAnimations();

  }, []);

  const createStars = () => {
    if (!starsRef.current) return;
    
    // Créer des étoiles dynamiquement
    const starsContainer = starsRef.current;
    const starCount = 150;
    
    for (let i = 0; i < starCount; i++) {
      const star = document.createElement('div');
      star.className = 'star';
      star.style.cssText = `
        position: absolute;
        width: ${Math.random() * 2 + 1}px;
        height: ${Math.random() * 2 + 1}px;
        background: white;
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: ${Math.random() * 0.7 + 0.3};
      `;
      starsContainer.appendChild(star);
      
      // Animation scintillement
      gsap.to(star, {
        opacity: Math.random() * 0.5 + 0.2,
        duration: Math.random() * 3 + 1,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    }
  };

  const startContinuousAnimations = () => {
    // Animations des cartes flottantes
    floatingCardsRef.current.forEach((card, index) => {
      gsap.to(card, {
        y: index % 2 === 0 ? -20 : -15,
        rotation: index % 2 === 0 ? 5 : -5,
        duration: 2 + index * 0.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: index * 0.3
      });
    });

    // Animation du système solaire
    gsap.to(planetsRef.current, {
      rotation: 360,
      duration: 20,
      repeat: -1,
      ease: "none",
      stagger: 2
    });

    // Orbites des planètes autour du soleil
    planetsRef.current.forEach((planet, index) => {
      const orbitRadius = 80 + index * 40;
      const orbitDuration = 30 + index * 10;
      
      gsap.to(planet, {
        rotation: 360,
        duration: orbitDuration,
        repeat: -1,
        ease: "none"
      });

      // Mouvement orbital
      gsap.to(planet, {
        x: `+=${orbitRadius}`,
        y: `+=${orbitRadius}`,
        duration: orbitDuration,
        repeat: -1,
        ease: "none",
        modifiers: {
          x: (x) => {
            const time = performance.now() * 0.001;
            return Math.cos(time * (2 * Math.PI / orbitDuration) + index) * orbitRadius + "px";
          },
          y: (y) => {
            const time = performance.now() * 0.001;
            return Math.sin(time * (2 * Math.PI / orbitDuration) + index) * orbitRadius + "px";
          }
        }
      });
    });

    // Effet de particules pour le titre
    gsap.to(".highlight", {
      backgroundPositionX: "100%",
      duration: 3,
      repeat: -1,
      ease: "none"
    });
  };

  // Fonctions pour les interactions (restent identiques)
  const handleButtonHover = (e) => {
    gsap.to(e.target, {
      scale: 1.05,
      y: -2,
      duration: 0.3,
      ease: "power2.out"
    });
  };

  const handleButtonHoverOut = (e) => {
    gsap.to(e.target, {
      scale: 1,
      y: 0,
      duration: 0.3,
      ease: "power2.out"
    });
  };

  const handleExploreClick = () => {
    const tl = gsap.timeline({
      onComplete: () => onNavigate('explorer')
    });

    tl.to(".hero-content > *", {
      y: -50,
      opacity: 0,
      stagger: 0.1,
      duration: 0.5
    })
    .to(floatingCardsRef.current, {
      y: -100,
      opacity: 0,
      rotation: 45,
      stagger: 0.1,
      duration: 0.6
    }, "-=0.3")
    .to(planetsRef.current, {
      scale: 0,
      opacity: 0,
      duration: 0.8
    }, "-=0.5");
  };

  const handleChatClick = () => {
    gsap.to(".btn-secondary", {
      scale: 0.95,
      duration: 0.1,
      yoyo: true,
      repeat: 1,
      ease: "power2.inOut",
      onComplete: openChat
    });
  };

  return (
    <div className="home cosmic-background" ref={heroRef}>
      {/* Fond spatial avec étoiles */}
      <div className="stars-container" ref={starsRef}></div>
      
      {/* Système solaire animé */}
      <div className="solar-system" ref={solarSystemRef}>
        <div className="sun"></div>
        <div className="planet mercury" ref={el => planetsRef.current[0] = el}></div>
        <div className="planet venus" ref={el => planetsRef.current[1] = el}></div>
        <div className="planet earth" ref={el => planetsRef.current[2] = el}></div>
        <div className="planet mars" ref={el => planetsRef.current[3] = el}></div>
        <div className="planet jupiter" ref={el => planetsRef.current[4] = el}></div>
        <div className="planet saturn" ref={el => planetsRef.current[5] = el}>
          <div className="saturn-ring"></div>
        </div>
      </div>

      {/* Nébuleuse d'arrière-plan */}
      <div className="nebula nebula-1"></div>
      <div className="nebula nebula-2"></div>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title" ref={titleRef}>
            Explore the <span className="highlight">mysteries</span> of space biology
          </h1>
          <p className="hero-subtitle" ref={subtitleRef}>
            Discover 60 years of NASA research
          </p>
          
          <div className="hero-actions" ref={buttonsRef}>
            <button 
              className="btn btn-primary"
              onMouseEnter={handleButtonHover}
              onMouseLeave={handleButtonHoverOut}
              onClick={handleExploreClick}
            >
              Start Exploring
            </button>
            <button 
              className="btn btn-secondary"
              onMouseEnter={handleButtonHover}
              onMouseLeave={handleButtonHoverOut}
              onClick={handleChatClick}
            >
              🤖 Ask Questions Here
            </button>
          </div>
        </div>
        
        <div className="hero-visual">
          <div 
            className="floating-card" 
            ref={el => floatingCardsRef.current[0] = el}
          >
            🔬
          </div>
          <div 
            className="floating-card" 
            ref={el => floatingCardsRef.current[1] = el}
          >
            🧬
          </div>
          <div 
            className="floating-card" 
            ref={el => floatingCardsRef.current[2] = el}
          >
            🚀
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;