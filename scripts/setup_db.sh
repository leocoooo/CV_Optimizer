#!/bin/bash

# Script d'aide pour configurer la base de données PostgreSQL
# Usage: ./scripts/setup_db.sh

echo "🔧 Configuration de la base de données PostgreSQL pour CV-Optimizer"
echo ""

# Vérifier si Docker est disponible
if command -v docker &> /dev/null; then
    echo "✅ Docker détecté"
    
    # Vérifier si docker-compose est disponible
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo "✅ Docker Compose détecté"
        echo ""
        echo "📦 Option 1 : Utiliser Docker (recommandé)"
        echo "   Pour démarrer le conteneur PostgreSQL :"
        echo "   docker-compose up -d"
        echo ""
        echo "   La configuration dans docker-compose.yml utilise :"
        echo "   - Utilisateur: admin"
        echo "   - Mot de passe: secret"
        echo "   - Base de données: job_db"
        echo "   - Port: 5432"
        echo ""
        echo "   Créez un fichier .env avec :"
        echo "   DATABASE_URL=postgresql://admin:secret@localhost:5432/job_db"
        echo ""
    fi
fi

# Vérifier si PostgreSQL est installé localement
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL détecté localement"
    echo ""
    echo "📦 Option 2 : Utiliser PostgreSQL local"
    echo "   Pour créer le rôle 'admin' dans PostgreSQL local :"
    echo ""
    echo "   psql -U postgres -c \"CREATE ROLE admin WITH LOGIN PASSWORD 'secret';\""
    echo "   psql -U postgres -c \"CREATE DATABASE job_db OWNER admin;\""
    echo ""
    echo "   Ou utilisez un utilisateur existant (ex: postgres) :"
    echo "   Créez un fichier .env avec :"
    echo "   DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/job_db"
    echo ""
fi

echo "📝 Après configuration, initialisez la base de données avec :"
echo "   uv run python -m src.database.init_db"
echo ""
