# CV Optimizer - Justfile
# Commands for development, testing, and deployment

# Default recipe - show help
default:
    @just --list

# ============================================================================
# DOCKER - Container management
# ============================================================================

# Start Docker containers in background
docker-up:
    docker-compose up -d

# Stop Docker containers
docker-down:
    docker-compose down

# Restart Docker containers
docker-restart:
    docker-compose restart

# Reset database (drop and recreate)
docker-reset-db:
    docker exec -it cv-optimizer-db-1 psql -U admin -d job_db -c "DROP TABLE IF EXISTS job_offers CASCADE;"
    uv run python -m src.database.init_db

# Check database tables
docker-check-db:
    docker exec -it cv-optimizer-db-1 psql -U admin -d job_db -c "\dt"

# View sample data from database (first 10 rows)
docker-view-data:
    docker exec -i cv-optimizer-db-1 psql -U admin -d job_db -c "SELECT id, title, source FROM job_offers LIMIT 10;"

# ============================================================================
# DATA COLLECTION - Scraping and API integration
# ============================================================================

# Collect jobs from France Travail API
collect-france-travail:
    uv run python -m src.services.france_travail_collector

# Scrape jobs from Welcome to the Jungle
scrape-wttj:
    uv run python -m src.services.scrappe_wttj

# Scrape jobs from HelloWork
scrape-hw:
    uv run python -m src.services.scrappe_hw

# Collect from all sources
collect-all: collect-france-travail scrape-wttj scrape-hw

# ============================================================================
# PROCESSING & MATCHING
# ============================================================================

# Vectorize job offers for matching
process:
    uv run python -m src.services.processor

# Match CV against job offers
match:
    uv run python -m src.services.matcher

# Read and extract text from CV (PDF)
read-cv:
    uv run python -m src.services.cv_reader

# Get LLM recommendations
advise:
    uv run python -m src.services.llm_advisor

# ============================================================================
# API & UI SERVICES
# ============================================================================

# Start FastAPI server
backend:
    uvicorn app.main:app --reload

# Start Streamlit interface
frontend:
    streamlit run streamlit_app.py

# ============================================================================
# CODE QUALITY
# ============================================================================

# Run all code quality checks
check-all: lint typecheck
    @echo "✓ All checks passed!"

# Format code with ruff
format:
    ruff format .
    @echo "✓ Code formatted"

# Lint code with ruff
lint:
    ruff check .

# Type checking with mypy
typecheck:
    mypy .

# Run pre-commit hooks
pre-commit:
    pre-commit run --all-files

# ============================================================================
# DEVELOPMENT WORKFLOWS
# ============================================================================

# Setup: start Docker + API + UI
dev: docker-up
    @echo "✓ Docker started"
    @echo "Starting API and UI..."
    @echo "Run in separate terminals:"
    @echo "  - API:  just backend"
    @echo "  - UI:   just frontend"

# Full development setup with collection
dev-full: docker-up collect-all process
    @echo "✓ Full setup complete"
    @echo "Now run:"
    @echo "  - API:  just backend"
    @echo "  - UI:   just frontend"

# ============================================================================
# DATABASE - Direct management (requires psql)
# ============================================================================

# Connect to AWS RDS PostgreSQL (production)
db-connect:
    psql -h joboffers-db.cbas48y2g22e.eu-west-3.rds.amazonaws.com -U postgres -d cv_optimizer

# Truncate job offers table (keeps structure)
db-truncate:
    docker exec -i cv-optimizer-db-1 psql -U admin -d job_db -c "TRUNCATE TABLE job_offers;"

# Drop job offers table
db-drop:
    docker exec -i cv-optimizer-db-1 psql -U admin -d job_db -c "DROP TABLE job_offers;"

# Count rows in job_offers
db-count:
    docker exec -i cv-optimizer-db-1 psql -U admin -d job_db -c "SELECT COUNT(*) as total_offers FROM job_offers;"

# ============================================================================
# NOTES
# ============================================================================
# Database environment
# - Current: AWS RDS PostgreSQL (cv_optimizer)
# - pgvector extension: Enabled for embeddings (384 dimensions)
# - RDS Endpoint: joboffers-db.cbas48y2g22e.eu-west-3.rds.amazonaws.com
# - Never commit .env file (contains credentials)
#
# Usage examples:
#   just test data/CVs/CV.pdf "Data Scientist"
#   just full data/CVs/CV.pdf "Data Engineer" 
#   just backend
#   just frontend
#   just collect-all
#   just check-all
