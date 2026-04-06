"""
Service d'enrichissement IA pour les offres d'emploi.

Utilise deux modèles Deep Learning :
1. NER (leocooo/v2-camembert-ner-job-ads) — Extraction d'entités
2. Classification (leocooo/camembert-job-classifier) — Détection "MISSIONS"
"""

import re
import json
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import nltk
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
)
from loguru import logger
from sqlalchemy import text, inspect

from src.database.database import engine, SessionLocal
from src.services.processor import build_content_to_vectorize
from app.config import get_settings

# Télécharger les modèles NLTK pour tokenization
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    logger.info("Downloading NLTK punkt_tab...")
    nltk.download("punkt_tab", quiet=True)
    logger.info("NLTK punkt_tab downloaded")


# ===== CONFIGURATION =====
settings = get_settings()

# Chemins des modèles stockés localement
BASE_DIR = Path(__file__).parent.parent.parent  # retourner à la racine
MODEL_NER = BASE_DIR / "models" / "ner"
MODEL_CLASSIFIER = BASE_DIR / "models" / "classifier"

# Vérifier que les modèles existent
if not MODEL_NER.exists():
    raise FileNotFoundError(f"Modèle NER non trouvé: {MODEL_NER}")
if not MODEL_CLASSIFIER.exists():
    raise FileNotFoundError(f"Modèle Classifier non trouvé: {MODEL_CLASSIFIER}")

logger.info(f"Modèles locaux: NER={MODEL_NER}, Classifier={MODEL_CLASSIFIER}")

# Configuration
BATCH_SIZE = 16
DEVICE = -1  # -1 pour CPU

# Mapping des tags NER
NER_MAPPING = {
    "company_name": "COMPANY",
    "contract_type": "CONTRACT",
    "job_title": "JOB",
    "hard_skills": "SKILL",
    "soft_skills": "SOFT",
    "experience_phrase": "EXP",
    "education_phrase": "EDUC",
    "location": "LOC",
    "languages_phrase": "LANG",
    "sector_phrase": "SECTOR",
    "remote_phrase": "REMOTE",
}

# Stop words pour le nettoyage NER
STOP_WORDS = {
    "chez",
    "le",
    "la",
    "les",
    "au",
    "du",
    "des",
    "avec",
    "pour",
    "dans",
    "un",
    "une",
    "et",
    "sur",
    "avez",
    "par",
    "ou",
    "ce",
    "est",
    "sont",
    "qui",
    "que",
}

# Pipelines globaux (chargés une seule fois)
_ner_pipe = None
_class_pipe = None


# ===== INITIALISATION =====
def initialize_pipelines():
    """Charge les modèles HuggingFace une seule fois au démarrage."""
    global _ner_pipe, _class_pipe

    if _ner_pipe is not None and _class_pipe is not None:
        logger.info("Pipelines déjà chargés")
        return _ner_pipe, _class_pipe

    logger.info("Chargement des modèles HuggingFace...")

    try:
        # Charger le modèle NER
        logger.info("Charger NER model...")
        ner_tokenizer = AutoTokenizer.from_pretrained(
            str(MODEL_NER), local_files_only=True
        )
        ner_model = AutoModelForTokenClassification.from_pretrained(
            str(MODEL_NER), local_files_only=True
        )

        _ner_pipe = pipeline(
            "token-classification",
            model=ner_model,
            tokenizer=ner_tokenizer,
            aggregation_strategy="simple",
            device=DEVICE,
        )
        logger.info("Modèle NER chargé")

        # Charger le modèle de classification
        logger.info("Charger Classification model...")
        class_tokenizer = AutoTokenizer.from_pretrained(
            str(MODEL_CLASSIFIER), local_files_only=True
        )
        class_model = AutoModelForSequenceClassification.from_pretrained(
            str(MODEL_CLASSIFIER), local_files_only=True
        )

        _class_pipe = pipeline(
            "text-classification",
            model=class_model,
            tokenizer=class_tokenizer,
            device=DEVICE,
        )
        logger.info("Modèle Classifier chargé")

        return _ner_pipe, _class_pipe

    except Exception as e:
        logger.error(f"Erreur lors du chargement des modèles: {e}")
        raise


# ===== FONCTIONS UTILITAIRES =====
def clean_and_split_text(text: str) -> List[str]:
    """
    Nettoie et split le texte en phrases.
    - Répare les points collés
    - Traite les sauts de ligne
    - Retourne liste de phrases
    """
    if not isinstance(text, str):
        return []

    # Réparation des points collés
    text = re.sub(r"([\.!\?;\:])\s*([A-Z])", r"\1 \2", text)

    # Standardisation des sauts de ligne
    text = text.replace("•", "\n").replace("- ", "\n- ").replace("<br />", "\n")

    lines = text.split("\n")
    all_sentences = []

    for line in lines:
        line = line.strip()
        if line:
            # Tokenize en phrases
            sentences = nltk.sent_tokenize(line)
            all_sentences.extend(sentences)

    return all_sentences


def clean_ner_output(ner_results: List[Dict[str, Any]]) -> List[str]:
    """
    Nettoie les résultats du NER.
    - Enlève les stop words
    - Filtre les mots trop courts
    - Nettoie la ponctuation
    """
    final = []

    for ent in ner_results:
        word = ent.get("word", "").strip(",.;: \n\t")

        # Garder si c'est pas un stop word et assez long
        if word.lower() not in STOP_WORDS and len(word) > 1:
            final.append(word)

    return final


def extract_by_entity_group(
    ner_results: List[Dict[str, Any]], entity_type: str
) -> List[str]:
    """
    Agrège les entités par type (SKILL, SOFT, LOC, etc.).
    Déduplique avec match exact (case-insensitive).
    """
    entities = []

    for ent in ner_results:
        if ent.get("entity_group") == entity_type:
            word = ent.get("word", "").strip(",.;: \n\t")
            if word and word.lower() not in STOP_WORDS and len(word) > 1:
                entities.append(word)

    # Dédupliquer (case-insensitive)
    seen = set()
    unique_entities = []
    for ent in entities:
        ent_lower = ent.lower()
        if ent_lower not in seen:
            seen.add(ent_lower)
            unique_entities.append(ent)

    return unique_entities


def merge_skills(existing: Optional[str], new_list: List[str]) -> str:
    """
    Fusionne les compétences existantes avec les nouvelles.
    Déduplique (case-insensitive).
    Retourne string séparé par ", ".
    """
    all_skills = []

    # Ajouter les compétences existantes
    if existing:
        for skill in existing.split(","):
            skill = skill.strip()
            if skill:
                all_skills.append(skill)

    # Ajouter les nouvelles
    all_skills.extend(new_list)

    # Déduplicate (case-insensitive)
    seen = set()
    unique_skills = []
    for skill in all_skills:
        skill_lower = skill.lower()
        if skill_lower not in seen:
            seen.add(skill_lower)
            unique_skills.append(skill)

    return ", ".join(unique_skills)


def generate_chunks(
    text: str,
    tokenizer,
    max_tokens: int = 512,
    overlap_chars: int = 256,
) -> list[str]:
    """
    Génère N chunks dynamiquement basé sur le nombre de tokens RÉELS.

    Les modèles CamemBERT ont une limite de 512 tokens stricte.
    Tokenise réellement pour chaque chunk et s'arrête à max_tokens.

    Avec overlap pour contexte BERT bidirectionnel.

    Args:
        text: Texte brut à diviser
        tokenizer: Tokenizer pour compter les tokens réels
        max_tokens: Limite de tokens par chunk (défaut: 512)
        overlap_chars: Nombre de caractères d'overlap entre chunks (défaut: 256)

    Returns:
        Liste de chunks, chacun avec <= max_tokens (strictement)
    """
    if not text.strip():
        return []

    chunks = []
    start = 0

    while start < len(text):
        # Commencer par une estimation (chars ≈ 4 tokens en français)
        # Mais on va vérifier réellement
        est_chars = max_tokens * 4
        end = min(start + est_chars, len(text))

        # Vérifier combien de tokens on a vraiment
        potential_chunk = text[start:end].strip()
        token_count = len(tokenizer.encode(potential_chunk))

        # Si trop de tokens, réduire progressivement
        while token_count > max_tokens and end > start + 100:
            # Réduire de 10%
            end = int(end * 0.9)
            potential_chunk = text[start:end].strip()
            token_count = len(tokenizer.encode(potential_chunk))

        # Ne pas découper un mot : trouver le dernier espace
        if end < len(text):
            last_space = potential_chunk.rfind(" ")
            if last_space > 0:
                potential_chunk = potential_chunk[:last_space].strip()

        if potential_chunk:
            chunks.append(potential_chunk)
            # Avancer au-delà du chunk actuel
            start = start + len(potential_chunk)

            # Ajouter overlap pour le prochain chunk (contexte BERT)
            if start < len(text):
                start = max(0, start - overlap_chars)
        else:
            break

    return chunks if chunks else [text]


# ===== COLONNES DE BASE DE DONNÉES =====
def column_exists(table_name: str, column_name: str) -> bool:
    """Vérifie si une colonne existe dans une table."""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def create_ai_columns():
    """Crée les colonnes ai_* s'elles n'existent pas."""
    ai_columns = [
        "output_ner",
        "output_missions",
        "ai_location",
        "ai_job_title",
        "ai_company_name",
        "ai_sector",
        "ai_contract_type",
        "ai_languages",
        "ai_remote_phrase",
        "ai_experience_phrase",
        "ai_education_phrase",
        "ai_hard_skills",
        "ai_soft_skills",
        "ai_missions",
        "ai_enrichment_date",
        "ai_enrichment_status",
    ]

    with engine.connect() as connection:
        for col_name in ai_columns:
            if not column_exists("job_offers", col_name):
                logger.info(f"Creating column {col_name}...")

                # Déterminer le type de colonne
                if col_name in [
                    "output_ner",
                    "output_missions",
                    "ai_experience_phrase",
                    "ai_education_phrase",
                    "ai_hard_skills",
                    "ai_soft_skills",
                    "ai_missions",
                ]:
                    col_type = "TEXT"
                elif col_name == "ai_enrichment_date":
                    col_type = "TIMESTAMP"
                else:
                    col_type = "VARCHAR(255)"

                alter_query = text(
                    f"ALTER TABLE job_offers ADD COLUMN {col_name} {col_type} DEFAULT NULL;"
                )
                connection.execute(alter_query)
                connection.commit()
                logger.info(f"Column {col_name} created")
            else:
                logger.info(f"Column {col_name} already exists")


# ===== ENRICHISSEMENT =====
def enrich_job_offer(job: Any, ner_pipe, class_pipe) -> Dict[str, Any]:
    """
    Enrichit une offre d'emploi avec les modèles IA.

    Retourne dict avec status et données enrichies.
    """
    try:
        # Préparer le texte
        full_text = ""
        if job.description:
            full_text += job.description
        if job.job_profile:
            full_text += " " + job.job_profile

        if not full_text.strip():
            return {
                "status": "SKIPPED",
                "reason": "empty_text",
                "data": None,
            }

        # Générer N chunks dynamiquement (pas juste 2)
        tokenizer = ner_pipe.tokenizer
        chunks = generate_chunks(
            full_text, tokenizer, max_tokens=512, overlap_chars=256
        )

        # === LOGGING DES TOKENS ===
        full_tokens = tokenizer.encode(full_text)
        total_tokens = len(full_tokens)

        # Logs détaillés par chunk
        chunk_log = ", ".join(
            f"chunk{i + 1}={len(tokenizer.encode(c))}t" for i, c in enumerate(chunks)
        )
        logger.info(
            f"Job {job.id}: full_text={total_tokens} tokens, "
            f"chunks_count={len(chunks)}, {chunk_log}"
        )

        # Alerte si le texte original dépasse la limite d'un seul chunk
        if total_tokens > 512:
            logger.warning(
                f"Job {job.id}: Texte original de {total_tokens} tokens "
                f"(> limite modèle 512). Traité en {len(chunks)} chunk(s)."
            )

        # Phase 1 : Classification (phrases MISSIONS)
        # Utilise le split par sentences (pas par tokens) - phrases rarement > 512 tokens
        logger.debug(f"Classification pour job {job.id}...")
        sentences = []
        for chunk in chunks:
            sentences.extend(clean_and_split_text(chunk))

        if not sentences:
            return {
                "status": "SKIPPED",
                "reason": "no_sentences",
                "data": None,
            }

        class_preds = class_pipe(sentences)

        missions_sentences = [
            sent
            for sent, pred in zip(sentences, class_preds)
            if pred.get("label", "").upper() == "MISSION"
        ]
        output_missions = "\n".join(missions_sentences) if missions_sentences else None

        # Phase 2 : NER (traiter TOUS les chunks et fusionner les résultats)
        logger.debug(f"NER pour job {job.id} ({len(chunks)} chunks)...")
        ner_results = []

        for i, chunk in enumerate(chunks):
            logger.debug(f"Job {job.id}: NER chunk {i + 1}/{len(chunks)}")
            # Chaque chunk est garanti <= 512 tokens, pas besoin de params additionnels
            chunk_ner = ner_pipe(chunk)
            ner_results.extend(chunk_ner)

        # Aggréger par entity_group
        ner_by_type = {}
        for entity_type in set(ent.get("entity_group") for ent in ner_results):
            if entity_type:
                ner_by_type[entity_type] = extract_by_entity_group(
                    ner_results, entity_type
                )

        # Stocker résultat brut NER
        output_ner = json.dumps(ner_by_type, ensure_ascii=False, indent=2)

        # Phase 3 : Remplissage des colonnes
        ai_data = {
            "output_ner": output_ner,
            "output_missions": output_missions,
            "ai_missions": output_missions,  # Copier dans ai_missions pour cohérence avec autres colonnes ai_*
            "ai_enrichment_date": datetime.now(),
            "ai_enrichment_status": "SUCCESS",
        }

        # Colonnes "si vide" (condition de remplissage)
        if_empty_mapping = {
            "ai_location": ("LOC", None),
            "ai_job_title": ("JOB", None),
            "ai_company_name": ("COMPANY", None),
            "ai_sector": ("SECTOR", None),
            "ai_contract_type": ("CONTRACT", None),
            "ai_languages": ("LANG", None),
            "ai_remote_phrase": ("REMOTE", "remote_mode"),
            "ai_experience_phrase": ("EXP", None),
            "ai_education_phrase": ("EDUC", None),
        }

        for col_name, (entity_type, existing_col) in if_empty_mapping.items():
            # Vérifier si la colonne est vide
            existing_value = getattr(job, existing_col) if existing_col else None
            if not existing_value and entity_type in ner_by_type:
                ai_data[col_name] = ", ".join(ner_by_type[entity_type])

        # Colonnes "fusion" (hard_skills, soft_skills)
        ai_data["ai_hard_skills"] = merge_skills(
            job.hard_skills,
            ner_by_type.get("SKILL", []),
        )
        ai_data["ai_soft_skills"] = merge_skills(
            job.soft_skills,
            ner_by_type.get("SOFT", []),
        )

        return {
            "status": "SUCCESS",
            "reason": None,
            "data": ai_data,
        }

    except Exception as e:
        logger.error(f"Erreur enrichissement job {job.id}: {e}")
        return {
            "status": "ERROR",
            "reason": str(e),
            "data": {
                "ai_enrichment_date": datetime.now(),
                "ai_enrichment_status": f"ERROR: {str(e)[:100]}",
            },
        }


# ===== BATCH PROCESSING =====
def run_ai_enrichment(
    force_reprocess: bool = False,
    retry_failed: bool = False,
    batch_size: int = BATCH_SIZE,
    limit: Optional[int] = None,
):
    """
    Lance l'enrichissement IA pour toutes les offres.

    Args:
        force_reprocess : Si True, retraite même les offres déjà enrichies
        retry_failed : Si True, retraite seulement les offres avec statut != SUCCESS (ERROR ou SKIPPED)
        batch_size : Nombre d'offres par batch
        limit : Nombre max d'offres à traiter (pour tests)
    """
    logger.info("=" * 60)
    logger.info("Starting AI enrichment...")
    logger.info("=" * 60)

    # Créer les colonnes
    logger.info("[STEP 1] Creating AI columns...")
    create_ai_columns()

    # Initialiser les modèles
    logger.info("[STEP 2] Initializing models (CPU mode)...")
    ner_pipe, class_pipe = initialize_pipelines()

    # Requêter les offres à traiter
    logger.info("[STEP 3] Querying job offers...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        if force_reprocess:
            query = session.query(JobOffer)
        elif retry_failed:
            # Traiter uniquement les offres avec statut != SUCCESS (ERROR, SKIPPED, ou NULL)
            query = session.query(JobOffer).filter(
                (JobOffer.ai_enrichment_status != "SUCCESS")
                | (JobOffer.ai_enrichment_status.is_(None))
            )
        else:
            # Traiter les offres jamais enrichies
            query = session.query(JobOffer).filter(JobOffer.output_ner.is_(None))

        if limit:
            query = query.limit(limit)

        jobs = query.all()
        total_jobs = len(jobs)

        logger.info(f"Found {total_jobs} jobs to process")

        if total_jobs == 0:
            logger.info("No jobs to process. Exiting.")
            return

        # Traiter par batch
        logger.info(f"[STEP 4] Processing by batch (size={batch_size})...")

        count_success = 0
        count_errors = 0
        count_skipped = 0

        for batch_idx in range(0, total_jobs, batch_size):
            batch_end = min(batch_idx + batch_size, total_jobs)
            batch = jobs[batch_idx:batch_end]
            batch_num = batch_idx // batch_size + 1
            total_batches = (total_jobs + batch_size - 1) // batch_size

            logger.info(
                f"\nBatch {batch_num}/{total_batches} ({batch_end}/{total_jobs})"
            )

            batch_success = 0
            batch_errors = 0
            batch_skipped = 0

            for job in batch:
                result = enrich_job_offer(job, ner_pipe, class_pipe)

                if result["status"] == "SUCCESS":
                    # Mettre à jour l'offre avec les données enrichies
                    for key, value in result["data"].items():
                        setattr(job, key, value)
                    # Construire content_to_vectorize (concaténation intelligente)
                    content = build_content_to_vectorize(job)
                    setattr(job, "content_to_vectorize", content)
                    batch_success += 1
                    count_success += 1
                elif result["status"] == "SKIPPED":
                    batch_skipped += 1
                    count_skipped += 1
                else:  # ERROR
                    for key, value in result["data"].items():
                        setattr(job, key, value)
                    batch_errors += 1
                    count_errors += 1

            # Commit le batch
            session.commit()
            logger.info(
                f"  Batch done: {batch_success} OK, {batch_errors} errors, {batch_skipped} skipped"
            )

        logger.info("\n" + "=" * 60)
        logger.info("AI enrichment completed!")
        logger.info(
            f"Total: {count_success} OK, {count_errors} errors, {count_skipped} skipped"
        )
        logger.info("=" * 60)

    finally:
        session.close()


def enrich_single_job_offer(job_id: str, force: bool = False):
    """Enrichit une seule offre (pour tests)."""
    logger.info(f"Testing enrichment for job {job_id}...")

    # Initialiser les modèles
    ner_pipe, class_pipe = initialize_pipelines()

    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        job = session.query(JobOffer).filter(JobOffer.id == job_id).first()

        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Skip si déjà traité (sauf si force=True)
        if job.output_ner and not force:
            logger.info(f"Job {job_id} already enriched. Use --force to re-enrich.")
            return

        logger.info(f"Enriching job {job_id}...")
        result = enrich_job_offer(job, ner_pipe, class_pipe)

        logger.info(f"Status: {result['status']}")
        if result["reason"]:
            logger.info(f"Reason: {result['reason']}")

        if result["data"]:
            # Mettre à jour
            for key, value in result["data"].items():
                setattr(job, key, value)

            session.commit()

            # Afficher les résultats
            logger.info("\n" + "=" * 60)
            logger.info("Enrichment results:")
            logger.info("=" * 60)
            logger.info(f"AI Location: {job.ai_location}")
            logger.info(f"AI Job Title: {job.ai_job_title}")
            logger.info(f"AI Company: {job.ai_company_name}")
            logger.info(f"AI Hard Skills: {job.ai_hard_skills}")
            logger.info(f"AI Soft Skills: {job.ai_soft_skills}")
            logger.info(f"Missions found: {bool(job.output_missions)}")
            logger.info("=" * 60)

    finally:
        session.close()


# ===== MAIN =====
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Enrichment Service for Job Offers")
    parser.add_argument(
        "--test-id",
        type=str,
        help="Test mode: enrich a single job offer by ID",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-enrichment of already processed offers",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of offers to process (for testing)",
    )
    parser.add_argument(
        "--retry",
        action="store_true",
        help="Retry failed/error enrichments (ai_enrichment_status != SUCCESS)",
    )

    args = parser.parse_args()

    if args.test_id:
        # Mode test : traiter une seule offre
        enrich_single_job_offer(args.test_id, force=args.force)
    else:
        # Mode production : traiter toutes les offres
        run_ai_enrichment(
            force_reprocess=args.force, retry_failed=args.retry, limit=args.limit
        )
