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
# AI ENRICHMENT - Deep Learning models for data extraction
# ============================================================================

# Enrich all job offers with NER and Classification models
enrich-ai:
    uv run python -m src.services.ai_enrich_database

# Enrich single job offer (requires job_id parameter)
enrich-ai-test job_id:
    uv run python -m src.services.ai_enrich_database --test-id {{job_id}}

# Re-enrich single job offer (force reprocessing)
enrich-ai-test-force job_id:
    uv run python -m src.services.ai_enrich_database --test-id {{job_id}} --force

# Enrich jobs with limit (for testing performance)
enrich-ai-limit limit='100':
    uv run python -m src.services.ai_enrich_database --limit {{limit}}

# Force re-enrich all job offers
enrich-ai-force:
    uv run python -m src.services.ai_enrich_database --force

# Retry failed/error enrichments (status != SUCCESS)
enrich-ai-retry:
    uv run python -m src.services.ai_enrich_database --retry

# Retry with limit
enrich-ai-retry-limit limit='100':
    uv run python -m src.services.ai_enrich_database --retry --limit {{limit}}

# ============================================================================
# MAINTENANCE - Full database reprocessing (use with caution!)
# ============================================================================

# Re-homogenize entire database (all job offers)
homogenize-all:
    @echo "⚠️  Re-homogenizing entire database..."
    uv run python -c "from src.services.homogenize_database import run_homogenization; run_homogenization()"

# Re-enrich entire database with IA models (all job offers)
enrich-all-db:
    @echo "⚠️  Re-enriching entire database with IA models..."
    @echo "This may take a long time on CPU. Press Ctrl+C to cancel."
    uv run python -c "from src.services.ai_enrich_database import run_ai_enrichment; run_ai_enrichment(force_reprocess=True)"

# Re-vectorize entire database (regenerate all embeddings)
vectorize-all:
    @echo "⚠️  Re-vectorizing entire database..."
    uv run python -c "from src.services.processor import process_embeddings; process_embeddings(regenerate_content=True)"

# Full reprocessing: homogenize + enrich + vectorize (use after major changes)
reprocess-all: homogenize-all enrich-all-db vectorize-all
    @echo "✅ Full database reprocessing complete!"

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
    @echo "All checks passed!"

# Format code with ruff
format:
    ruff format .
    @echo "Code formatted"

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
    @echo "Docker started"
    @echo "Starting API and UI..."
    @echo "Run in separate terminals:"
    @echo "  - API:  just backend"
    @echo "  - UI:   just frontend"

# Full development setup with collection
dev-full: docker-up collect-all process
    @echo "Full setup complete"
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
