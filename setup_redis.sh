#!/bin/bash
# Script d'installation et de test du cache Redis

echo "=================================="
echo "  Installation Redis pour NASA KG"
echo "=================================="
echo ""

# Détection du système d'exploitation
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo " Système Linux détecté"
    
    # Vérifier si Redis est déjà installé
    if command -v redis-server &> /dev/null; then
        echo " Redis est déjà installé"
        redis-server --version
    else
        echo " Installation de Redis..."
        sudo apt update
        sudo apt install -y redis-server
        echo " Redis installé"
    fi
    
    # Démarrer Redis
    echo " Démarrage de Redis..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Vérifier le statut
    if sudo systemctl is-active --quiet redis-server; then
        echo " Redis est actif"
    else
        echo " Erreur : Redis n'a pas démarré"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo " macOS détecté"
    
    # Vérifier si Redis est déjà installé
    if command -v redis-server &> /dev/null; then
        echo " Redis est déjà installé"
        redis-server --version
    else
        echo " Installation de Redis via Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo " Homebrew n'est pas installé. Installez-le d'abord : https://brew.sh"
            exit 1
        fi
        brew install redis
        echo " Redis installé"
    fi
    
    # Démarrer Redis
    echo " Démarrage de Redis..."
    brew services start redis
    
    sleep 2
    
    # Vérifier le statut
    if brew services list | grep redis | grep started; then
        echo " Redis est actif"
    else
        echo " Erreur : Redis n'a pas démarré"
        exit 1
    fi
else
    echo " Système d'exploitation non supporté : $OSTYPE"
    echo "   Veuillez installer Redis manuellement"
    exit 1
fi

# Tester la connexion
echo ""
echo " Test de connexion à Redis..."
if redis-cli ping | grep -q PONG; then
    echo " Redis répond correctement (PONG)"
else
    echo " Redis ne répond pas"
    exit 1
fi

# Vérifier la configuration Python
echo ""
echo " Vérification des dépendances Python..."
if python3 -c "import redis" 2>/dev/null; then
    echo " Module Python 'redis' installé"
else
    echo " Installation du module Python 'redis'..."
    pip install redis
    echo " Module installé"
fi

# Configurer les variables d'environnement
echo ""
echo "  Configuration des variables d'environnement..."

if [ -f .env ]; then
    # Vérifier si REDIS_URL existe déjà
    if grep -q "REDIS_URL" .env; then
        echo " REDIS_URL déjà configuré dans .env"
    else
        echo "REDIS_URL=redis://localhost:6379/0" >> .env
        echo " REDIS_URL ajouté à .env"
    fi
    
    if grep -q "REDIS_ENABLED" .env; then
        echo " REDIS_ENABLED déjà configuré dans .env"
    else
        echo "REDIS_ENABLED=true" >> .env
        echo " REDIS_ENABLED ajouté à .env"
    fi
    
    if grep -q "CACHE_TTL" .env; then
        echo " CACHE_TTL déjà configuré dans .env"
    else
        echo "CACHE_TTL=3600" >> .env
        echo " CACHE_TTL ajouté à .env"
    fi
else
    echo "  Fichier .env non trouvé, création..."
    cat > .env << EOF
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
CACHE_TTL=3600
EOF
    echo " Fichier .env créé avec la configuration Redis"
fi

# Test de performance
echo ""
echo " Lancement du test de performance..."
echo ""

if [ -f test_redis_cache.py ]; then
    python3 test_redis_cache.py
else
    echo "  Fichier test_redis_cache.py non trouvé"
    echo "   Vous pouvez tester manuellement avec :"
    echo "   python3 test_redis_cache.py"
fi

echo ""
echo "=================================="
echo " Installation et configuration terminées!"
echo "=================================="
echo ""
echo " Informations utiles :"
echo "   - Redis URL: redis://localhost:6379/0"
echo "   - Redis CLI: redis-cli"
echo "   - Logs Redis: sudo tail -f /var/log/redis/redis-server.log"
echo "   - Documentation: voir REDIS_CACHE.md"
echo ""
echo " Commandes utiles :"
echo "   - Tester Redis: redis-cli ping"
echo "   - Voir les clés: redis-cli KEYS '*'"
echo "   - Vider le cache: redis-cli FLUSHDB"
echo "   - Statistiques: redis-cli INFO stats"
echo ""
