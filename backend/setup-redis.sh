#!/bin/bash

# Script d'installation et configuration Redis pour NASA Hackathon 2025

echo "🚀 Installation Redis pour NASA Hackathon 2025..."

# Vérifier si Redis est déjà installé
if command -v redis-server &> /dev/null; then
    echo "✅ Redis est déjà installé"
    redis-server --version
else
    echo "📦 Installation de Redis..."
    
    # Détecter l'OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y redis
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "❌ Homebrew non trouvé. Installez Redis manuellement."
            exit 1
        fi
    else
        echo "❌ OS non supporté pour l'installation automatique"
        echo "ℹ️  Installez Redis manuellement : https://redis.io/download"
        exit 1
    fi
fi

# Installer les dépendances Node.js
echo "📦 Installation des dépendances Node.js..."
npm install

# Démarrer Redis (si ce n'est pas déjà fait)
echo "🔧 Configuration de Redis..."

# Créer un fichier de configuration Redis pour le développement
cat > redis-dev.conf << EOF
# Configuration Redis pour développement NASA Hackathon 2025
port 6379
bind 127.0.0.1
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF

# Démarrer Redis avec la configuration
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🚀 Démarrage de Redis..."
    redis-server redis-dev.conf &
    REDIS_PID=$!
    echo "Redis démarré avec PID: $REDIS_PID"
    
    # Attendre que Redis soit prêt
    sleep 2
    
    # Tester la connexion
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis fonctionne correctement"
    else
        echo "❌ Erreur : Redis ne répond pas"
        exit 1
    fi
else
    echo "✅ Redis est déjà en cours d'exécution"
fi

# Copier .env.example vers .env si il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé. Veuillez le configurer selon vos besoins."
fi

echo ""
echo "🎉 Installation terminée !"
echo ""
echo "📋 Commandes utiles :"
echo "  - Démarrer le serveur: npm run dev"
echo "  - Arrêter Redis: redis-cli shutdown"
echo "  - Monitorer Redis: redis-cli monitor"
echo "  - Vider le cache: redis-cli flushall"
echo ""
echo "🔗 URLs :"
echo "  - API: http://localhost:3000"
echo "  - Health check: http://localhost:3000/health/cache"
echo ""
echo "⚙️  Configuration Redis :"
echo "  - Port: 6379"
echo "  - Max Memory: 256MB"
echo "  - Éviction: allkeys-lru"
echo "  - TTL par défaut: 10 heures"