"""
Analyse heuristique des compétences attendues vs visibles dans un CV.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from src.database.models import JobOffer


TECH_SKILLS = [
    "Python",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "dbt",
    "Airflow",
    "Spark",
    "Hadoop",
    "Kafka",
    "Databricks",
    "Snowflake",
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Linux",
    "Git",
    "CI/CD",
    "API REST",
    "FastAPI",
    "Django",
    "Flask",
    "Java",
    "JavaScript",
    "TypeScript",
    "Node.js",
    "React",
    "Vue.js",
    "Power BI",
    "Tableau",
    "Excel",
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "TensorFlow",
    "PyTorch",
    "scikit-learn",
    "Pandas",
    "NumPy",
    "ETL",
    "Data Visualization",
    "Business Intelligence",
    "Statistiques",
]

SOFT_SKILLS = [
    "Communication",
    "Travail d'équipe",
    "Autonomie",
    "Rigueur",
    "Organisation",
    "Leadership",
    "Résolution de problèmes",
    "Esprit d'analyse",
    "Curiosité",
    "Adaptabilité",
    "Gestion de projet",
    "Pédagogie",
]

LANGUAGE_SKILLS = [
    "Français",
    "Anglais",
    "Espagnol",
    "Allemand",
    "Italien",
    "Néerlandais",
]

ALIASES = {
    "API REST": ["api rest", "rest api"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "Business Intelligence": ["business intelligence", "bi"],
    "CI/CD": ["ci/cd", "ci cd", "cicd"],
    "Data Visualization": ["data visualization", "dataviz", "visualisation de donnees"],
    "Deep Learning": ["deep learning"],
    "ETL": ["etl"],
    "FastAPI": ["fastapi"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Machine Learning": ["machine learning", "ml"],
    "NLP": ["nlp", "natural language processing", "traitement du langage"],
    "Node.js": ["node.js", "node js", "nodejs"],
    "Power BI": ["power bi", "powerbi"],
    "PyTorch": ["pytorch"],
    "React": ["react", "reactjs", "react js"],
    "SQL": ["sql"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "Tableau": ["tableau"],
    "TensorFlow": ["tensorflow", "tensor flow"],
    "Travail d'équipe": ["travail d equipe", "esprit d equipe", "teamwork"],
    "Vue.js": ["vue.js", "vue js", "vuejs"],
    "Anglais": ["anglais", "english"],
    "Français": ["francais", "français", "french"],
    "Espagnol": ["espagnol", "spanish"],
    "Allemand": ["allemand", "german"],
    "Italien": ["italien", "italian"],
    "Néerlandais": ["neerlandais", "dutch"],
    "Autonomie": ["autonomie", "autonome"],
    "Rigueur": ["rigueur", "rigoureux", "rigoureuse"],
    "Communication": ["communication"],
    "Organisation": ["organisation", "organise", "organisée"],
    "Adaptabilité": ["adaptabilite", "adaptabilité", "adaptable"],
    "Résolution de problèmes": [
        "resolution de problemes",
        "résolution de problèmes",
        "problem solving",
    ],
    "Esprit d'analyse": ["esprit d analyse", "analyse", "analytique"],
}


@dataclass
class SkillGroupComparison:
    label: str
    required: list[str]
    matched: list[str]
    missing: list[str]


class SkillGapAnalyzer:
    """Compare les compétences d'une offre avec celles visibles dans un CV."""

    def compare(self, cv_text: str, offer: JobOffer) -> dict:
        normalized_cv = self._normalize_text(cv_text)

        hard_required = self._build_required_skills(
            explicit_value=offer.hard_skills,
            fallback_texts=[offer.title, offer.description, offer.job_profile],
            vocabulary=TECH_SKILLS,
        )
        soft_required = self._build_required_skills(
            explicit_value=offer.soft_skills,
            fallback_texts=[offer.description, offer.job_profile],
            vocabulary=SOFT_SKILLS,
        )
        language_required = self._build_required_skills(
            explicit_value=offer.languages,
            fallback_texts=[offer.description, offer.job_profile],
            vocabulary=LANGUAGE_SKILLS,
        )

        hard_matched = self._detect_present_skills(normalized_cv, hard_required)
        soft_matched = self._detect_present_skills(normalized_cv, soft_required)
        language_matched = self._detect_present_skills(normalized_cv, language_required)

        hard_missing = [skill for skill in hard_required if skill not in hard_matched]
        soft_missing = [skill for skill in soft_required if skill not in soft_matched]
        language_missing = [
            skill for skill in language_required if skill not in language_matched
        ]

        detected_candidate_skills = self._detect_present_skills(
            normalized_cv,
            self._dedupe(hard_required + TECH_SKILLS + soft_required + SOFT_SKILLS + language_required + LANGUAGE_SKILLS),
        )

        required_total = len(hard_required) + len(soft_required) + len(language_required)
        matched_total = len(hard_matched) + len(soft_matched) + len(language_matched)
        missing_total = len(hard_missing) + len(soft_missing) + len(language_missing)

        bonus_skills = [
            skill
            for skill in detected_candidate_skills
            if skill not in hard_required
            and skill not in soft_required
            and skill not in language_required
        ][:8]

        overall_score = round((matched_total / required_total) * 100, 1) if required_total else 0.0
        fit_label = self._fit_label(overall_score, matched_total, required_total)
        summary = self._build_summary(
            fit_label=fit_label,
            matched_total=matched_total,
            required_total=required_total,
            hard_missing=hard_missing,
        )

        positive_signals = self._build_positive_signals(
            hard_required=hard_required,
            hard_matched=hard_matched,
            soft_required=soft_required,
            soft_matched=soft_matched,
            language_required=language_required,
            language_matched=language_matched,
            bonus_skills=bonus_skills,
        )
        watchouts = self._build_watchouts(
            hard_missing=hard_missing,
            soft_missing=soft_missing,
            language_missing=language_missing,
            required_total=required_total,
        )

        groups = [
            SkillGroupComparison(
                label="Compétences techniques",
                required=hard_required,
                matched=hard_matched,
                missing=hard_missing,
            ),
            SkillGroupComparison(
                label="Compétences comportementales",
                required=soft_required,
                matched=soft_matched,
                missing=soft_missing,
            ),
            SkillGroupComparison(
                label="Langues",
                required=language_required,
                matched=language_matched,
                missing=language_missing,
            ),
        ]

        return {
            "job_id": str(offer.id),
            "job_title": str(offer.title),
            "company": str(offer.company),
            "overall_score": overall_score,
            "fit_label": fit_label,
            "summary": summary,
            "matched_count": matched_total,
            "missing_count": missing_total,
            "bonus_count": len(bonus_skills),
            "positive_signals": positive_signals,
            "watchouts": watchouts,
            "groups": [group.__dict__ for group in groups],
            "bonus_skills": bonus_skills,
            "detected_candidate_skills": detected_candidate_skills[:20],
        }

    def _build_required_skills(
        self, explicit_value: str | None, fallback_texts: list[str | None], vocabulary: list[str]
    ) -> list[str]:
        explicit_skills = self._split_skills(explicit_value)
        if explicit_skills:
            return explicit_skills

        combined_text = " ".join(text for text in fallback_texts if text)
        normalized_text = self._normalize_text(combined_text)
        return self._detect_present_skills(normalized_text, vocabulary)

    def _split_skills(self, value: str | None) -> list[str]:
        if not value:
            return []

        items = re.split(r"[,;\n|]", str(value))
        cleaned = []
        for item in items:
            skill = item.strip(" -•\t\r")
            if len(skill) < 2:
                continue
            cleaned.append(self._canonicalize(skill))
        return self._dedupe(cleaned)

    def _detect_present_skills(self, normalized_text: str, skills: list[str]) -> list[str]:
        matches: list[str] = []
        padded_text = f" {normalized_text} "
        for skill in skills:
            canonical = self._canonicalize(skill)
            aliases = self._aliases_for(canonical)
            if any(f" {alias} " in padded_text for alias in aliases if alias):
                matches.append(canonical)
        return self._dedupe(matches)

    def _aliases_for(self, skill: str) -> list[str]:
        aliases = ALIASES.get(skill, [skill])
        return self._dedupe([self._normalize_text(alias) for alias in aliases if alias])

    def _canonicalize(self, skill: str) -> str:
        normalized = " ".join(skill.replace("/", " / ").split())
        normalized_key = self._normalize_text(normalized)

        for canonical, aliases in ALIASES.items():
            normalized_aliases = [
                self._normalize_text(alias) for alias in [canonical, *aliases]
            ]
            if normalized_key in normalized_aliases:
                return canonical

        for vocabulary in [TECH_SKILLS, SOFT_SKILLS, LANGUAGE_SKILLS]:
            for item in vocabulary:
                if normalized_key == self._normalize_text(item):
                    return item

        return normalized.strip().title()

    def _normalize_text(self, text: str | None) -> str:
        raw = unicodedata.normalize("NFKD", text or "")
        raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
        raw = raw.lower()
        raw = raw.replace("&", " et ")
        raw = re.sub(r"[^a-z0-9+#/\. ]+", " ", raw)
        raw = raw.replace(".", " ")
        raw = raw.replace("/", " ")
        raw = re.sub(r"\s+", " ", raw)
        return raw.strip()

    def _fit_label(self, overall_score: float, matched_total: int, required_total: int) -> str:
        if required_total == 0:
            return "Lecture indicative"
        if overall_score >= 80:
            return "Très bon alignement"
        if overall_score >= 60:
            return "Alignement solide"
        if overall_score >= 40:
            return "Alignement partiel"
        if matched_total > 0:
            return "Base intéressante mais à renforcer"
        return "Écart important"

    def _build_summary(
        self,
        fit_label: str,
        matched_total: int,
        required_total: int,
        hard_missing: list[str],
    ) -> str:
        if required_total == 0:
            return (
                "L'offre n'explicite pas assez de compétences structurées pour produire une "
                "comparaison forte. La lecture ci-dessous reste indicative."
            )

        if not hard_missing:
            return (
                f"{fit_label}: le CV couvre {matched_total} compétence(s) attendue(s) sur "
                f"{required_total}, sans manque technique majeur détecté."
            )

        first_gap = ", ".join(hard_missing[:3])
        return (
            f"{fit_label}: le CV couvre {matched_total} compétence(s) attendue(s) sur "
            f"{required_total}. Les principaux écarts techniques repérés sont: {first_gap}."
        )

    def _build_positive_signals(
        self,
        hard_required: list[str],
        hard_matched: list[str],
        soft_required: list[str],
        soft_matched: list[str],
        language_required: list[str],
        language_matched: list[str],
        bonus_skills: list[str],
    ) -> list[str]:
        signals: list[str] = []
        if hard_required:
            signals.append(
                f"{len(hard_matched)}/{len(hard_required)} compétence(s) technique(s) attendue(s) apparaissent déjà dans le CV."
            )
        if soft_required and soft_matched:
            signals.append(
                f"Le CV rend visibles {len(soft_matched)} compétence(s) comportementale(s) utiles: {', '.join(soft_matched[:3])}."
            )
        if language_required and language_matched:
            signals.append(
                f"Les langues demandées présentes dans le CV sont: {', '.join(language_matched[:3])}."
            )
        if bonus_skills:
            signals.append(
                f"Le candidat montre aussi des atouts additionnels: {', '.join(bonus_skills[:4])}."
            )
        return signals[:4]

    def _build_watchouts(
        self,
        hard_missing: list[str],
        soft_missing: list[str],
        language_missing: list[str],
        required_total: int,
    ) -> list[str]:
        watchouts: list[str] = []
        if hard_missing:
            watchouts.append(
                f"Compétences techniques à renforcer ou mieux expliciter: {', '.join(hard_missing[:5])}."
            )
        if soft_missing:
            watchouts.append(
                f"Soft skills peu visibles dans le CV: {', '.join(soft_missing[:4])}."
            )
        if language_missing:
            watchouts.append(
                f"Langues attendues non détectées dans le CV: {', '.join(language_missing[:3])}."
            )
        if required_total == 0:
            watchouts.append(
                "L'offre manque de signaux structurés, donc l'analyse repose davantage sur la description libre."
            )
        return watchouts[:4]

    def _dedupe(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            clean_item = item.strip()
            if not clean_item:
                continue
            key = self._normalize_text(clean_item)
            if key in seen:
                continue
            seen.add(key)
            result.append(clean_item)
        return result
