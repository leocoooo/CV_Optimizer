#!/usr/bin/env python3
"""
Script de vérification et configuration de la base de données PostgreSQL.
Usage: uv run python scripts/check_db.py
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Ajouter le répertoire racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration du logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

# Import après avoir ajouté le chemin
try:
    from src.database.database import test_connection as db_test_connection
except ImportError as e:
    logger.warning(f"Impossible d'importer le module de base de données : {e}")
    db_test_connection = None

def check_docker():
    """Vérifie si Docker est disponible et si le conteneur tourne."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=cv-optimizer", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "cv-optimizer" in result.stdout or "db" in result.stdout:
            return True, "Docker conteneur détecté"
        return False, "Docker disponible mais conteneur non démarré"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False, "Docker non disponible"

def check_postgres_local():
    """Vérifie si PostgreSQL est installé localement."""
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "PostgreSQL local détecté"
        return False, "PostgreSQL non trouvé"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False, "PostgreSQL non disponible"

def check_env_file():
    """Vérifie si le fichier .env existe et contient DATABASE_URL."""
    env_path = Path(".env")
    if not env_path.exists():
        return False, "Fichier .env introuvable"
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False, "DATABASE_URL non défini dans .env"
    
    return True, f"DATABASE_URL trouvé: {database_url[:30]}..."

def test_connection():
    """Teste la connexion à la base de données."""
    if db_test_connection is None:
        return False, "Module de base de données non disponible"
    try:
        if db_test_connection():
            return True, "Connexion réussie"
        return False, "Échec de la connexion"
    except Exception as e:
        return False, f"Erreur: {str(e)[:100]}"

def main():
    logger.info("🔍 Vérification de la configuration de la base de données\n")
    
    # 1. Vérifier le fichier .env
    logger.info("1. Vérification du fichier .env...")
    env_ok, env_msg = check_env_file()
    if env_ok:
        logger.success(f"   ✅ {env_msg}")
    else:
        logger.error(f"   ❌ {env_msg}")
        logger.info("\n📝 Solution : Créez un fichier .env à la racine avec :")
        logger.info("   DATABASE_URL=postgresql://admin:secret@localhost:5432/job_db")
        return 1
    
    # 2. Vérifier Docker
    logger.info("\n2. Vérification de Docker...")
    docker_ok, docker_msg = check_docker()
    if docker_ok:
        logger.success(f"   ✅ {docker_msg}")
    else:
        logger.warning(f"   ⚠️  {docker_msg}")
        if "non disponible" not in docker_msg:
            logger.info("   💡 Démarrez le conteneur : docker-compose up -d")
    
    # 3. Vérifier PostgreSQL local
    logger.info("\n3. Vérification de PostgreSQL local...")
    pg_ok, pg_msg = check_postgres_local()
    if pg_ok:
        logger.success(f"   ✅ {pg_msg}")
    else:
        logger.warning(f"   ⚠️  {pg_msg}")
    
    # 4. Tester la connexion
    logger.info("\n4. Test de connexion à la base de données...")
    conn_ok, conn_msg = test_connection()
    if conn_ok:
        logger.success(f"   ✅ {conn_msg}")
        logger.info("\n🎉 La base de données est correctement configurée !")
        return 0
    else:
        logger.error(f"   ❌ {conn_msg}")
        logger.info("\n📝 Solutions possibles :")
        logger.info("   1. Si vous utilisez Docker :")
        logger.info("      docker-compose up -d")
        logger.info("   2. Si vous utilisez PostgreSQL local :")
        logger.info("      psql -U postgres -c \"CREATE ROLE admin WITH LOGIN PASSWORD 'secret';\"")
        logger.info("      psql -U postgres -c \"CREATE DATABASE job_db OWNER admin;\"")
        logger.info("   3. Vérifiez que DATABASE_URL dans .env correspond à votre configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
