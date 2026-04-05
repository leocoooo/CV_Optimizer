# CV Optimizer - Justfile
# Commands for development, testing, and deployment

# Import .env variables
set dotenv-load := true

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

homogenize-db:
    uv run python -m src.services.homogenize_database

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

# Transform DATABASE_URL for psql (handle special characters)
db_url := env_var("DATABASE_URL")

# Connect to AWS RDS
db-connect:
    psql -d "{{db_url}}"

# Count rows in job_offers
db-count:
    psql -d "{{db_url}}" -c "SELECT COUNT(*) as total_offers FROM job_offers;"

db-sample:
    psql -d "{{db_url}}" -c "SELECT id, title, source FROM job_offers LIMIT 10;"
