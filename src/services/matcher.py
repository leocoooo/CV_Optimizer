from sqlalchemy import text
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.services.embedder import Embedder
from loguru import logger
from datetime import datetime, timedelta
from app.config import get_settings

settings = get_settings()


class JobMatcher:
    def __init__(self):
        self.embedder = Embedder()
        self.db: Session = SessionLocal()

    def find_matches(
        self,
        profile_text: str,
        days_limit: int | None = None,
        top_n: int | None = None,
        location: str | None = None,
        contract_type: str | None = None,
        experience: str | None = None,
    ):
        """
        Prend un texte (CV/Profil) et retourne les N offres les plus pertinentes
        en appliquant des filtres stricts si fournis.
        """
        # Utiliser les valeurs par défaut si non fournies
        if days_limit is None:
            days_limit = settings.DEFAULT_DAYS_LIMIT
        if top_n is None:
            top_n = settings.DEFAULT_TOP_N

        logger.info("Génération du vecteur pour le profil utilisateur...")
        profile_vector = self.embedder.get_embedding(profile_text)

        if not profile_vector:
            return []

        # Construction de la requête avec bind parameters (pas d'interpolation directe)
        limit_date = datetime.now() - timedelta(days=days_limit)

        # Convertir le vecteur en format string pour PostgreSQL
        vector_str = str(profile_vector)

        # Requête SQL avec bind parameters pour toutes les entrées utilisateur
        # Les filtres optionnels utilisent la forme (:param IS NULL OR condition)
        sql_query = text("""
        SELECT
            job_offers.id,
            job_offers.title,
            job_offers.company,
            job_offers.city,
            job_offers.department,
            job_offers.region,
            job_offers.contract_type,
            job_offers.required_experience,
            job_offers.url,
            job_offers.date_publication,
            job_offers.source,
            (1 - (job_offers.embedding <=> CAST(:vector AS vector))) AS similarity_score
        FROM job_offers
        WHERE (
            job_offers.date_publication >= :limit_date
            OR (job_offers.date_publication IS NULL AND job_offers.date_scraping >= :limit_date)
        )
        AND (:location IS NULL OR (
            job_offers.city ILIKE '%' || :location || '%'
            OR job_offers.department ILIKE '%' || :location || '%'
            OR job_offers.region ILIKE '%' || :location || '%'
        ))
        AND (:contract_type IS NULL OR job_offers.contract_type = :contract_type)
        AND (:experience IS NULL OR job_offers.required_experience ILIKE '%' || :experience || '%')
        ORDER BY similarity_score DESC
        LIMIT :top_n
        """)

        logger.info(f"Recherche des {top_n} meilleures correspondances avec filtres...")

        # Exécuter la requête avec les bind parameters
        results = self.db.execute(
            sql_query,
            {
                "vector": vector_str,
                "limit_date": limit_date,
                "location": location,
                "contract_type": contract_type,
                "experience": experience,
                "top_n": top_n,
            },
        ).fetchall()

        # Post-process: construire la propriété 'location' pour chaque résultat
        # Convertir les RowTuple en dictionnaires pour ajouter la propriété calculée
        processed_results = []
        for row in results:
            # Accéder aux colonnes par indice: id, title, company, city, dept, region, contract, exp, url, pub_date, source, similarity_score
            row_dict: dict[str, object] = {
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "city": row[3],
                "department": row[4],
                "region": row[5],
                "contract_type": row[6],
                "required_experience": row[7],
                "url": row[8],
                "date_publication": row[9],
                "source": row[10],
                "similarity_score": row[11]
                if row[11] is not None
                else 0.0,  # Fallback si None
            }
            # Construire la propriété location
            location_parts: list[str] = [
                str(row_dict[k])
                for k in ["city", "department", "region"]
                if row_dict.get(k) is not None
            ]
            row_dict["location"] = (
                " - ".join(location_parts) if location_parts else None
            )

            # Convertir en objet simple pour que match.py puisse y accéder
            processed_results.append(type("Row", (), row_dict)())

        return processed_results


if __name__ == "__main__":
    matcher = JobMatcher()

    #  TEST
    test_profile = """
    Je suis un jeune diplômé en Data Science, je maîtrise Python, 
    le machine learning avec scikit-learn et la manipulation de données avec Pandas.
    """

    # Exemple d'utilisation avec filtres
    city_filter = "Paris"
    contract_filter = "CDI"
    experience_level = "D"

    matches = matcher.find_matches(
        profile_text=test_profile,
        top_n=5,
        location=city_filter,
        contract_type=contract_filter,
        experience=experience_level,
    )

    print(
        f"\n--- TOP MATCHES (Filtres: {city_filter}, {contract_filter}, {experience_level}) ---"
    )
    if not matches:
        print("Aucune offre ne correspond à ces critères stricts.")
    else:
        for row in matches:
            score = round(row.similarity_score * 100, 2)
            print(f"[{score}%] {row.title}")
            print(f"      Entreprise: {row.company} | Ville: {row.location}")
            print(
                f"      Contrat: {row.contract_type} | Exp: {row.required_experience}\n"
            )
            print(f"      Lien: {row.url} | ID: {row.id}\n")
