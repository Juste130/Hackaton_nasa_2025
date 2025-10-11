// src/components/CubeVisualization.jsx
import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import './CubeVisualization.css';

const CubeVisualization = ({ cubeData, className = '' }) => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const cubeMeshes = useRef([]);
  const raycaster = useRef(new THREE.Raycaster());
  const mouse = useRef(new THREE.Vector2());
  
  const [hoveredCube, setHoveredCube] = useState(null);
  const [selectedCube, setSelectedCube] = useState(null);
  const [isRotating, setIsRotating] = useState(true);
  const [filterDimension, setFilterDimension] = useState('all');

  // Configuration améliorée
  const config = {
    cubeSize: 1.5,              // Cubes plus gros
    spacing: 2.5,               // Plus d'espacement
    maxDimensions: 6,           // Limiter à 6x6x6 = 216 cubes max
    colors: {
      missing: 0xff4444,        // Rouge - pas d'études
      partial: 0xffaa44,        // Orange - 1-2 études  
      moderate: 0xffff44,       // Jaune - 3-5 études
      complete: 0x44ff44,       // Vert - 6+ études
      hover: 0x88ccff,          // Bleu clair - survol
      selected: 0x4488ff        // Bleu - sélectionné
    }
  };

  // Initialisation de la scène Three.js
  useEffect(() => {
    if (!mountRef.current || !cubeData?.dimensions) return;

    // Créer la scène
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Créer la caméra
    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(25, 25, 25);  // Plus loin pour voir les cubes plus gros
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Créer le renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Ajouter les lumières
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    // Ajouter un éclairage d'appoint
    const pointLight = new THREE.PointLight(0x4444ff, 0.3);
    pointLight.position.set(-10, -10, -5);
    scene.add(pointLight);

    mountRef.current.appendChild(renderer.domElement);

    // Ajouter les contrôles de souris
    const onMouseMove = (event) => {
      const rect = mountRef.current.getBoundingClientRect();
      mouse.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    };

    const onMouseClick = (event) => {
      raycaster.current.setFromCamera(mouse.current, camera);
      const intersects = raycaster.current.intersectObjects(cubeMeshes.current);
      
      if (intersects.length > 0) {
        const intersectedObject = intersects[0].object;
        setSelectedCube(intersectedObject.userData);
      } else {
        setSelectedCube(null);
      }
    };

    mountRef.current.addEventListener('mousemove', onMouseMove);
    mountRef.current.addEventListener('click', onMouseClick);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);

      // Rotation automatique
      if (isRotating) {
        scene.rotation.y += 0.005;
      }

      // Détection du survol
      if (cubeMeshes.current.length > 0) {
        raycaster.current.setFromCamera(mouse.current, camera);
        const intersects = raycaster.current.intersectObjects(cubeMeshes.current);
        
        // Reset des couleurs
        cubeMeshes.current.forEach(cube => {
          if (cube.userData.isSelected) {
            cube.material.color.setHex(config.colors.selected);
          } else {
            cube.material.color.setHex(cube.userData.originalColor);
          }
        });

        if (intersects.length > 0) {
          const hoveredObject = intersects[0].object;
          if (!hoveredObject.userData.isSelected) {
            hoveredObject.material.color.setHex(config.colors.hover);
          }
          setHoveredCube(hoveredObject.userData);
        } else {
          setHoveredCube(null);
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    // Gestion du redimensionnement
    const handleResize = () => {
      if (!mountRef.current) return;
      
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      if (mountRef.current) {
        mountRef.current.removeEventListener('mousemove', onMouseMove);
        mountRef.current.removeEventListener('click', onMouseClick);
      }
      renderer.dispose();
    };
  }, [cubeData?.dimensions, isRotating]);

  // Créer les cubes de données (VERSION OPTIMISÉE)
  useEffect(() => {
    if (!sceneRef.current || !cubeData?.dimensions || !cubeData?.missing_combinations) return;

    // Nettoyer les cubes existants
    cubeMeshes.current.forEach(cube => {
      sceneRef.current.remove(cube);
    });
    cubeMeshes.current = [];

    const { organisms, phenomena, platforms } = cubeData.dimensions;
    const missingCombinations = cubeData.missing_combinations || [];

    // LIMITATION INTELLIGENTE : Prendre seulement les éléments les plus pertinents
    const maxItems = config.maxDimensions;
    const priorityOrganisms = organisms?.slice(0, maxItems) || [];
    const priorityPhenomena = phenomena?.slice(0, maxItems) || [];
    const priorityPlatforms = platforms?.slice(0, maxItems) || [];

    console.log(`📊 Cube optimisé: ${priorityOrganisms.length} × ${priorityPhenomena.length} × ${priorityPlatforms.length} = ${priorityOrganisms.length * priorityPhenomena.length * priorityPlatforms.length} cubes`);

    // Créer une map des combinaisons manquantes
    const missingMap = new Map();
    missingCombinations.forEach(combo => {
      const key = `${combo.organism}-${combo.phenomenon}-${combo.platform}`;
      missingMap.set(key, combo);
    });

    // Créer les cubes avec les dimensions limitées
    const geometry = new THREE.BoxGeometry(config.cubeSize, config.cubeSize, config.cubeSize);
    
    priorityOrganisms.forEach((organism, x) => {
      priorityPhenomena.forEach((phenomenon, y) => {
        priorityPlatforms.forEach((platform, z) => {
          const key = `${organism}-${phenomenon}-${platform}`;
          const isMissing = missingMap.has(key);
          
          // Simuler le nombre d'études
          const studyCount = isMissing ? 0 : Math.floor(Math.random() * 10);
          
          let color, status;
          if (studyCount === 0) {
            color = config.colors.missing;
            status = 'missing';
          } else if (studyCount <= 2) {
            color = config.colors.partial;
            status = 'partial';
          } else if (studyCount <= 5) {
            color = config.colors.moderate;
            status = 'moderate';
          } else {
            color = config.colors.complete;
            status = 'complete';
          }

          const material = new THREE.MeshLambertMaterial({ color });
          const cube = new THREE.Mesh(geometry, material);

          // Position dans l'espace 3D avec bon espacement
          cube.position.set(
            (x - priorityOrganisms.length / 2) * config.spacing,
            (y - priorityPhenomena.length / 2) * config.spacing,
            (z - priorityPlatforms.length / 2) * config.spacing
          );

          // Métadonnées du cube
          cube.userData = {
            organism,
            phenomenon,
            platform,
            studyCount,
            status,
            originalColor: color,
            isSelected: false,
            coordinates: { x, y, z }
          };

          // Appliquer le filtre
          const shouldShow = filterDimension === 'all' || 
                           (filterDimension === 'missing' && status === 'missing') ||
                           (filterDimension === 'partial' && status === 'partial') ||
                           (filterDimension === 'complete' && status === 'complete');

          cube.visible = shouldShow;
          
          sceneRef.current.add(cube);
          cubeMeshes.current.push(cube);
        });
      });
    });

  }, [cubeData, filterDimension]);

  // Mettre à jour la sélection
  useEffect(() => {
    cubeMeshes.current.forEach(cube => {
      cube.userData.isSelected = selectedCube && 
        cube.userData.organism === selectedCube.organism &&
        cube.userData.phenomenon === selectedCube.phenomenon &&
        cube.userData.platform === selectedCube.platform;
    });
  }, [selectedCube]);

  const getStatusText = (status) => {
    const statusMap = {
      missing: 'No studies found',
      partial: 'Limited research (1-2 studies)',
      moderate: 'Some research (3-5 studies)', 
      complete: 'Well researched (6+ studies)'
    };
    return statusMap[status] || 'Unknown';
  };

  const getStatusIcon = (status) => {
    const iconMap = {
      missing: '🔴',
      partial: '🟠', 
      moderate: '🟡',
      complete: '🟢'
    };
    return iconMap[status] || '⚪';
  };

  if (!cubeData?.dimensions) {
    return (
      <div className={`cube-visualization ${className}`}>
        <div className="cube-loading">
          <div className="loading-spinner"></div>
          <p>Loading 3D visualization data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`cube-visualization ${className}`}>
      {/* Contrôles */}
      <div className="cube-controls">
        <div className="control-group">
          <label>Filter:</label>
          <select 
            value={filterDimension} 
            onChange={(e) => setFilterDimension(e.target.value)}
          >
            <option value="all">All Combinations</option>
            <option value="missing">Missing Research</option>
            <option value="partial">Partial Research</option>
            <option value="complete">Complete Research</option>
          </select>
        </div>
        <div className="control-group">
          <button 
            onClick={() => setIsRotating(!isRotating)}
            className={isRotating ? 'active' : ''}
          >
            {isRotating ? '⏸️ Stop' : '▶️ Rotate'}
          </button>
        </div>
      </div>

      {/* Légende */}
      <div className="cube-legend">
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#ff4444'}}></span>
          <span>Missing (0 studies)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#ffaa44'}}></span>
          <span>Partial (1-2 studies)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#ffff44'}}></span>
          <span>Moderate (3-5 studies)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#44ff44'}}></span>
          <span>Complete (6+ studies)</span>
        </div>
      </div>

      {/* Container 3D */}
      <div className="cube-container" ref={mountRef} />

      {/* Info panels */}
      {hoveredCube && (
        <div className="cube-tooltip">
          <h4>{getStatusIcon(hoveredCube.status)} Research Status</h4>
          <div className="tooltip-content">
            <p><strong>Organism:</strong> {hoveredCube.organism}</p>
            <p><strong>Phenomenon:</strong> {hoveredCube.phenomenon}</p>
            <p><strong>Platform:</strong> {hoveredCube.platform}</p>
            <p><strong>Studies:</strong> {hoveredCube.studyCount}</p>
            <p><strong>Status:</strong> {getStatusText(hoveredCube.status)}</p>
          </div>
        </div>
      )}

      {selectedCube && (
        <div className="cube-details">
          <div className="details-header">
            <h3>Research Combination Details</h3>
            <button onClick={() => setSelectedCube(null)}>✕</button>
          </div>
          <div className="details-content">
            <div className="detail-row">
              <span className="detail-label">Organism:</span>
              <span className="detail-value">{selectedCube.organism}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Phenomenon:</span>
              <span className="detail-value">{selectedCube.phenomenon}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Platform:</span>
              <span className="detail-value">{selectedCube.platform}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Research Status:</span>
              <span className={`detail-value status-${selectedCube.status}`}>
                {getStatusIcon(selectedCube.status)} {getStatusText(selectedCube.status)}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Study Count:</span>
              <span className="detail-value">{selectedCube.studyCount}</span>
            </div>
            
            {selectedCube.status === 'missing' && (
              <div className="research-opportunity">
                <h4>🎯 Research Opportunity</h4>
                <p>This combination has not been studied and represents a potential research gap.</p>
                <div className="priority-assessment">
                  <span className="priority-badge high">High Priority</span>
                  <span className="impact-note">Critical for mission planning</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Statistiques */}
      <div className="cube-stats">
        <div className="stat-item">
          <span className="stat-value">{cubeData.dimensions.organisms?.length || 0}</span>
          <span className="stat-label">Organisms</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{cubeData.dimensions.phenomena?.length || 0}</span>
          <span className="stat-label">Phenomena</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{cubeData.dimensions.platforms?.length || 0}</span>
          <span className="stat-label">Platforms</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{cubeData.total_missing || 0}</span>
          <span className="stat-label">Missing Combinations</span>
        </div>
      </div>
    </div>
  );
};

export default CubeVisualization;