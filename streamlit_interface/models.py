"""
Modèles de données pour l'interface Streamlit CV-Optimizer.
Définit les structures de données utilisées pour la communication avec l'API.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
import re
from loguru import logger


@dataclass
class JobFilters:
    """Filtres pour la recherche d'offres d'emploi."""
    location: Optional[str] = None
    contract_type: Optional[str] = None
    experience_level: Optional[str] = None
    page: int = 1
    page_size: int = 20
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les filtres en dictionnaire pour les paramètres de requête."""
        filters = {}
        if self.location:
            filters["location"] = self.location
        if self.contract_type:
            filters["contract_type"] = self.contract_type
        if self.experience_level:
            filters["experience_level"] = self.experience_level
        filters["page"] = self.page
        filters["page_size"] = self.page_size
        return filters
    
    def to_json(self) -> str:
        """Sérialise les filtres en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobFilters':
        """Crée une instance JobFilters à partir d'un dictionnaire."""
        return cls(
            location=data.get("location"),
            contract_type=data.get("contract_type"),
            experience_level=data.get("experience_level"),
            page=max(1, int(data.get("page", 1))),
            page_size=max(1, min(100, int(data.get("page_size", 20))))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobFilters':
        """Crée une instance JobFilters à partir d'une chaîne JSON."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Erreur lors du parsing JSON des filtres: {e}")
            return cls()
    
    def is_empty(self) -> bool:
        """Vérifie si aucun filtre n'est appliqué."""
        return not any([self.location, self.contract_type, self.experience_level])
    
    def validate(self) -> Dict[str, bool]:
        """Valide les filtres et retourne les résultats de validation."""
        validation_results = {
            "page_valid": isinstance(self.page, int) and self.page >= 1,
            "page_size_valid": isinstance(self.page_size, int) and 1 <= self.page_size <= 100,
            "location_valid": self.location is None or (isinstance(self.location, str) and len(self.location.strip()) > 0),
            "contract_type_valid": self.contract_type is None or (isinstance(self.contract_type, str) and len(self.contract_type.strip()) > 0),
            "experience_level_valid": self.experience_level is None or (isinstance(self.experience_level, str) and len(self.experience_level.strip()) > 0)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results
    
    def sanitize(self) -> 'JobFilters':
        """Nettoie et normalise les filtres."""
        return JobFilters(
            location=self.location.strip() if self.location else None,
            contract_type=self.contract_type.strip() if self.contract_type else None,
            experience_level=self.experience_level.strip() if self.experience_level else None,
            page=max(1, self.page),
            page_size=max(1, min(100, self.page_size))
        )


@dataclass
class JobMatch:
    """Représente une offre d'emploi avec son score de correspondance."""
    job_id: str
    title: str
    company: str
    location: str
    contract_type: str
    match_score: float  # Score de 0.0 à 1.0
    summary: str
    
    def __post_init__(self):
        """Validation et normalisation après initialisation."""
        # Validation du score
        if not isinstance(self.match_score, (int, float)):
            logger.warning(f"Score de correspondance invalide: {self.match_score}, défini à 0.0")
            self.match_score = 0.0
        else:
            self.match_score = max(0.0, min(1.0, float(self.match_score)))
        
        # Validation des champs requis
        if not self.job_id or not isinstance(self.job_id, str):
            raise ValueError("job_id est requis et doit être une chaîne non vide")
        if not self.title or not isinstance(self.title, str):
            raise ValueError("title est requis et doit être une chaîne non vide")
        if not self.company or not isinstance(self.company, str):
            raise ValueError("company est requis et doit être une chaîne non vide")
    
    @property
    def match_percentage(self) -> int:
        """Retourne le score de correspondance en pourcentage."""
        return int(self.match_score * 100)
    
    @property
    def score_color(self) -> str:
        """Retourne la couleur appropriée selon le score."""
        if self.match_score >= 0.8:
            return "green"
        elif self.match_score >= 0.6:
            return "orange"
        else:
            return "red"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobMatch':
        """Crée une instance JobMatch à partir d'un dictionnaire."""
        return cls(
            job_id=str(data["job_id"]),
            title=str(data["title"]),
            company=str(data["company"]),
            location=str(data.get("location", "")),
            contract_type=str(data.get("contract_type", "")),
            match_score=float(data.get("match_score", 0.0)),
            summary=str(data.get("summary", ""))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobMatch':
        """Crée une instance JobMatch à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données de l'offre."""
        validation_results = {
            "job_id_valid": bool(self.job_id and isinstance(self.job_id, str) and len(self.job_id.strip()) > 0),
            "title_valid": bool(self.title and isinstance(self.title, str) and len(self.title.strip()) > 0),
            "company_valid": bool(self.company and isinstance(self.company, str) and len(self.company.strip()) > 0),
            "location_valid": isinstance(self.location, str),
            "contract_type_valid": isinstance(self.contract_type, str),
            "match_score_valid": isinstance(self.match_score, (int, float)) and 0.0 <= self.match_score <= 1.0,
            "summary_valid": isinstance(self.summary, str)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results


@dataclass
class JobDetails:
    """Détails complets d'une offre d'emploi."""
    job_id: str
    title: str
    company: str
    location: str
    contract_type: str
    experience_level: str
    description: str
    requirements: List[str]
    benefits: List[str]
    salary_range: Optional[str] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        """Validation et normalisation après initialisation."""
        # Validation des champs requis
        if not self.job_id or not isinstance(self.job_id, str):
            raise ValueError("job_id est requis et doit être une chaîne non vide")
        if not self.title or not isinstance(self.title, str):
            raise ValueError("title est requis et doit être une chaîne non vide")
        if not self.company or not isinstance(self.company, str):
            raise ValueError("company est requis et doit être une chaîne non vide")
        
        # Validation des listes
        if not isinstance(self.requirements, list):
            logger.warning("requirements n'est pas une liste, converti en liste vide")
            self.requirements = []
        if not isinstance(self.benefits, list):
            logger.warning("benefits n'est pas une liste, converti en liste vide")
            self.benefits = []
        
        # Nettoyage des listes
        self.requirements = [str(req).strip() for req in self.requirements if req]
        self.benefits = [str(benefit).strip() for benefit in self.benefits if benefit]
    
    def has_requirements(self) -> bool:
        """Vérifie si l'offre a des exigences définies."""
        return bool(self.requirements)
    
    def has_benefits(self) -> bool:
        """Vérifie si l'offre a des avantages définis."""
        return bool(self.benefits)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobDetails':
        """Crée une instance JobDetails à partir d'un dictionnaire."""
        return cls(
            job_id=str(data["job_id"]),
            title=str(data["title"]),
            company=str(data["company"]),
            location=str(data.get("location", "")),
            contract_type=str(data.get("contract_type", "")),
            experience_level=str(data.get("experience_level", "")),
            description=str(data.get("description", "")),
            requirements=data.get("requirements", []) if isinstance(data.get("requirements"), list) else [],
            benefits=data.get("benefits", []) if isinstance(data.get("benefits"), list) else [],
            salary_range=str(data["salary_range"]) if data.get("salary_range") else None,
            url=str(data["url"]) if data.get("url") else None
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobDetails':
        """Crée une instance JobDetails à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données des détails de l'offre."""
        validation_results = {
            "job_id_valid": bool(self.job_id and isinstance(self.job_id, str) and len(self.job_id.strip()) > 0),
            "title_valid": bool(self.title and isinstance(self.title, str) and len(self.title.strip()) > 0),
            "company_valid": bool(self.company and isinstance(self.company, str) and len(self.company.strip()) > 0),
            "location_valid": isinstance(self.location, str),
            "contract_type_valid": isinstance(self.contract_type, str),
            "experience_level_valid": isinstance(self.experience_level, str),
            "description_valid": isinstance(self.description, str),
            "requirements_valid": isinstance(self.requirements, list),
            "benefits_valid": isinstance(self.benefits, list),
            "salary_range_valid": self.salary_range is None or isinstance(self.salary_range, str),
            "url_valid": self.url is None or (isinstance(self.url, str) and self._is_valid_url(self.url))
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results
    
    def _is_valid_url(self, url: str) -> bool:
        """Valide une URL de manière simple."""
        if not url:
            return False
        return url.startswith(('http://', 'https://')) and len(url) > 10
    
    def get_summary(self, max_length: int = 200) -> str:
        """Retourne un résumé de la description."""
        if not self.description:
            return "Aucune description disponible"
        
        if len(self.description) <= max_length:
            return self.description
        
        return self.description[:max_length - 3].rstrip() + "..."


@dataclass
class AdviceSection:
    """Section de conseils personnalisés."""
    section_title: str
    content: str
    priority: str  # "high", "medium", "low"
    
    def __post_init__(self):
        """Validation après initialisation."""
        if not self.section_title or not isinstance(self.section_title, str):
            raise ValueError("section_title est requis et doit être une chaîne non vide")
        if not self.content or not isinstance(self.content, str):
            raise ValueError("content est requis et doit être une chaîne non vide")
        
        # Validation de la priorité
        valid_priorities = {"high", "medium", "low"}
        if self.priority not in valid_priorities:
            logger.warning(f"Priorité invalide '{self.priority}', définie à 'medium'")
            self.priority = "medium"
    
    @property
    def priority_color(self) -> str:
        """Retourne la couleur selon la priorité."""
        priority_colors = {
            "high": "red",
            "medium": "orange", 
            "low": "blue"
        }
        return priority_colors.get(self.priority, "gray")
    
    @property
    def priority_icon(self) -> str:
        """Retourne l'icône selon la priorité."""
        priority_icons = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵"
        }
        return priority_icons.get(self.priority, "⚪")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdviceSection':
        """Crée une instance AdviceSection à partir d'un dictionnaire."""
        return cls(
            section_title=str(data["section_title"]),
            content=str(data["content"]),
            priority=str(data.get("priority", "medium"))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AdviceSection':
        """Crée une instance AdviceSection à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données de la section de conseils."""
        valid_priorities = {"high", "medium", "low"}
        validation_results = {
            "section_title_valid": bool(self.section_title and isinstance(self.section_title, str) and len(self.section_title.strip()) > 0),
            "content_valid": bool(self.content and isinstance(self.content, str) and len(self.content.strip()) > 0),
            "priority_valid": self.priority in valid_priorities
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results


@dataclass
class AdviceResponse:
    """Réponse contenant les conseils personnalisés du LLM."""
    job_id: str
    advice_text: str
    overall_score: float
    improvement_areas: List[str]
    generated_at: str
    
    def __post_init__(self):
        """Validation et normalisation après initialisation."""
        # Validation des champs requis
        if not self.job_id or not isinstance(self.job_id, str):
            raise ValueError("job_id est requis et doit être une chaîne non vide")
        if not isinstance(self.advice_text, str):
            raise ValueError("advice_text doit être une chaîne")
        
        # Validation du score
        if not isinstance(self.overall_score, (int, float)):
            logger.warning(f"Score global invalide: {self.overall_score}, défini à 0.0")
            self.overall_score = 0.0
        else:
            self.overall_score = max(0.0, min(1.0, float(self.overall_score)))
        
        # Validation de la liste des zones d'amélioration
        if not isinstance(self.improvement_areas, list):
            logger.warning("improvement_areas n'est pas une liste, converti en liste vide")
            self.improvement_areas = []
        else:
            self.improvement_areas = [str(area).strip() for area in self.improvement_areas if area]
    
    @property
    def score_percentage(self) -> int:
        """Retourne le score global en pourcentage."""
        return int(self.overall_score * 100)
    
    def parse_advice_sections(self) -> List[AdviceSection]:
        """Parse le texte de conseils en sections structurées."""
        sections = []
        
        # Logique simple de parsing - peut être améliorée
        if "## " in self.advice_text:
            # Format avec headers markdown
            parts = self.advice_text.split("## ")
            for part in parts[1:]:  # Skip first empty part
                lines = part.strip().split("\n", 1)
                if len(lines) >= 2:
                    title = lines[0].strip()
                    content = lines[1].strip()
                    
                    # Détermination de la priorité basée sur des mots-clés
                    priority = "medium"
                    if any(word in title.lower() for word in ["urgent", "critique", "important"]):
                        priority = "high"
                    elif any(word in title.lower() for word in ["optionnel", "bonus", "plus"]):
                        priority = "low"
                    
                    try:
                        sections.append(AdviceSection(
                            section_title=title,
                            content=content,
                            priority=priority
                        ))
                    except ValueError as e:
                        logger.warning(f"Erreur lors de la création de la section '{title}': {e}")
        else:
            # Format simple - tout le texte dans une section
            try:
                sections.append(AdviceSection(
                    section_title="Conseils généraux",
                    content=self.advice_text,
                    priority="medium"
                ))
            except ValueError as e:
                logger.warning(f"Erreur lors de la création de la section générale: {e}")
        
        return sections
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdviceResponse':
        """Crée une instance AdviceResponse à partir d'un dictionnaire."""
        return cls(
            job_id=str(data["job_id"]),
            advice_text=str(data.get("advice_text", "")),
            overall_score=float(data.get("overall_score", 0.0)),
            improvement_areas=data.get("improvement_areas", []) if isinstance(data.get("improvement_areas"), list) else [],
            generated_at=str(data.get("generated_at", ""))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AdviceResponse':
        """Crée une instance AdviceResponse à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données de la réponse de conseils."""
        validation_results = {
            "job_id_valid": bool(self.job_id and isinstance(self.job_id, str) and len(self.job_id.strip()) > 0),
            "advice_text_valid": isinstance(self.advice_text, str),
            "overall_score_valid": isinstance(self.overall_score, (int, float)) and 0.0 <= self.overall_score <= 1.0,
            "improvement_areas_valid": isinstance(self.improvement_areas, list),
            "generated_at_valid": isinstance(self.generated_at, str)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results
    
    def has_advice(self) -> bool:
        """Vérifie si des conseils sont disponibles."""
        return bool(self.advice_text and self.advice_text.strip())
    
    def get_advice_summary(self, max_length: int = 100) -> str:
        """Retourne un résumé des conseils."""
        if not self.has_advice():
            return "Aucun conseil disponible"
        
        if len(self.advice_text) <= max_length:
            return self.advice_text
        
        return self.advice_text[:max_length - 3].rstrip() + "..."


@dataclass
class JobsResponse:
    """Réponse paginée pour la liste des offres d'emploi."""
    jobs: List[JobMatch]
    total: int
    page: int
    page_size: int
    has_next: bool
    
    def __post_init__(self):
        """Validation après initialisation."""
        # Validation des types
        if not isinstance(self.jobs, list):
            logger.warning("jobs n'est pas une liste, converti en liste vide")
            self.jobs = []
        
        # Validation des valeurs numériques
        self.total = max(0, int(self.total)) if isinstance(self.total, (int, float)) else 0
        self.page = max(1, int(self.page)) if isinstance(self.page, (int, float)) else 1
        self.page_size = max(1, int(self.page_size)) if isinstance(self.page_size, (int, float)) else 20
        self.has_next = bool(self.has_next)
    
    @property
    def total_pages(self) -> int:
        """Calcule le nombre total de pages."""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def start_index(self) -> int:
        """Index de début pour l'affichage."""
        return (self.page - 1) * self.page_size + 1
    
    @property
    def end_index(self) -> int:
        """Index de fin pour l'affichage."""
        return min(self.page * self.page_size, self.total)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            "jobs": [job.to_dict() for job in self.jobs],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next
        }
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobsResponse':
        """Crée une instance JobsResponse à partir d'un dictionnaire."""
        jobs_data = data.get("jobs", [])
        jobs = []
        for job_data in jobs_data:
            try:
                jobs.append(JobMatch.from_dict(job_data))
            except (ValueError, KeyError) as e:
                logger.warning(f"Erreur lors du parsing d'une offre: {e}")
        
        return cls(
            jobs=jobs,
            total=int(data.get("total", 0)),
            page=int(data.get("page", 1)),
            page_size=int(data.get("page_size", 20)),
            has_next=bool(data.get("has_next", False))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobsResponse':
        """Crée une instance JobsResponse à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données de la réponse."""
        validation_results = {
            "jobs_valid": isinstance(self.jobs, list) and all(isinstance(job, JobMatch) for job in self.jobs),
            "total_valid": isinstance(self.total, int) and self.total >= 0,
            "page_valid": isinstance(self.page, int) and self.page >= 1,
            "page_size_valid": isinstance(self.page_size, int) and self.page_size >= 1,
            "has_next_valid": isinstance(self.has_next, bool),
            "pagination_consistent": self.total >= len(self.jobs)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results
    
    def is_empty(self) -> bool:
        """Vérifie si la réponse ne contient aucune offre."""
        return len(self.jobs) == 0
    
    def get_page_info(self) -> str:
        """Retourne les informations de pagination formatées."""
        if self.is_empty():
            return "Aucun résultat"
        
        return f"Page {self.page} sur {self.total_pages} ({self.start_index}-{self.end_index} sur {self.total})"


@dataclass
class NavigationState:
    """État de navigation de l'application."""
    current_page: str = "home"  # "home", "job_details", "advice"
    selected_job_id: Optional[str] = None
    show_filters: bool = True
    
    def __post_init__(self):
        """Validation après initialisation."""
        valid_pages = {"home", "job_details", "advice"}
        if self.current_page not in valid_pages:
            logger.warning(f"Page invalide '{self.current_page}', définie à 'home'")
            self.current_page = "home"
    
    def reset(self):
        """Remet l'état de navigation à zéro."""
        self.current_page = "home"
        self.selected_job_id = None
        self.show_filters = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NavigationState':
        """Crée une instance NavigationState à partir d'un dictionnaire."""
        return cls(
            current_page=str(data.get("current_page", "home")),
            selected_job_id=str(data["selected_job_id"]) if data.get("selected_job_id") else None,
            show_filters=bool(data.get("show_filters", True))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NavigationState':
        """Crée une instance NavigationState à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> Dict[str, bool]:
        """Valide l'état de navigation."""
        valid_pages = {"home", "job_details", "advice"}
        validation_results = {
            "current_page_valid": self.current_page in valid_pages,
            "selected_job_id_valid": self.selected_job_id is None or (isinstance(self.selected_job_id, str) and len(self.selected_job_id.strip()) > 0),
            "show_filters_valid": isinstance(self.show_filters, bool)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results


@dataclass
class SessionData:
    """Données de session Streamlit."""
    uploaded_cv: Optional[bytes] = None
    cv_filename: Optional[str] = None
    job_matches: List[JobMatch] = None
    current_filters: JobFilters = None
    selected_job_details: Optional[JobDetails] = None
    current_advice: Optional[AdviceResponse] = None
    navigation: NavigationState = None
    
    def __post_init__(self):
        """Initialise les champs par défaut."""
        if self.job_matches is None:
            self.job_matches = []
        if self.current_filters is None:
            self.current_filters = JobFilters()
        if self.navigation is None:
            self.navigation = NavigationState()
    
    def has_cv(self) -> bool:
        """Vérifie si un CV est uploadé."""
        return self.uploaded_cv is not None and self.cv_filename is not None
    
    def clear_cv(self):
        """Supprime le CV de la session."""
        self.uploaded_cv = None
        self.cv_filename = None
        self.job_matches = []
        self.current_advice = None
    
    def clear_results(self):
        """Supprime les résultats de recherche."""
        self.job_matches = []
        self.selected_job_details = None
        self.current_advice = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire (sans les données binaires)."""
        return {
            "has_cv": self.has_cv(),
            "cv_filename": self.cv_filename,
            "job_matches_count": len(self.job_matches),
            "current_filters": self.current_filters.to_dict() if self.current_filters else None,
            "has_job_details": self.selected_job_details is not None,
            "has_advice": self.current_advice is not None,
            "navigation": self.navigation.to_dict() if self.navigation else None
        }
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON (sans les données binaires)."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def validate(self) -> Dict[str, bool]:
        """Valide les données de session."""
        validation_results = {
            "cv_data_consistent": (self.uploaded_cv is None) == (self.cv_filename is None),
            "job_matches_valid": isinstance(self.job_matches, list),
            "current_filters_valid": self.current_filters is None or isinstance(self.current_filters, JobFilters),
            "selected_job_details_valid": self.selected_job_details is None or isinstance(self.selected_job_details, JobDetails),
            "current_advice_valid": self.current_advice is None or isinstance(self.current_advice, AdviceResponse),
            "navigation_valid": self.navigation is None or isinstance(self.navigation, NavigationState)
        }
        validation_results["all_valid"] = all(validation_results.values())
        return validation_results
    
    def get_session_summary(self) -> str:
        """Retourne un résumé de l'état de la session."""
        summary_parts = []
        
        if self.has_cv():
            summary_parts.append(f"CV: {self.cv_filename}")
        
        if self.job_matches:
            summary_parts.append(f"{len(self.job_matches)} offres")
        
        if self.selected_job_details:
            summary_parts.append(f"Détails: {self.selected_job_details.title}")
        
        if self.current_advice:
            summary_parts.append("Conseils disponibles")
        
        return " | ".join(summary_parts) if summary_parts else "Session vide"


# Types utilitaires
FileUpload = tuple[bytes, str]  # (contenu, nom_fichier)
APIResponse = Dict[str, Any]


# Fonctions utilitaires pour la validation
def validate_file_upload(file_data: bytes, filename: str) -> Dict[str, Union[bool, str]]:
    """
    Valide un fichier uploadé en utilisant les fonctions de validation améliorées.
    
    Args:
        file_data: Contenu binaire du fichier
        filename: Nom du fichier
        
    Returns:
        Dictionnaire avec les résultats de validation (format compatible avec l'ancien)
    """
    from utils import validate_uploaded_file
    
    # Utilise la nouvelle fonction de validation complète
    validation_result = validate_uploaded_file(file_data, filename)
    
    # Conversion vers l'ancien format pour compatibilité
    legacy_result = {
        "is_valid": validation_result['is_valid'],
        "error_message": validation_result['error_message'],
        "file_size": len(file_data) if file_data else 0,
        "is_pdf": False,
        "size_valid": False,
        "name_valid": bool(filename and isinstance(filename, str))
    }
    
    # Extraction des détails pour compatibilité
    if validation_result.get('details'):
        pdf_details = validation_result['details'].get('pdf_validation', {}).get('details', {})
        size_details = validation_result['details'].get('size_validation', {}).get('details', {})
        
        legacy_result["is_pdf"] = pdf_details.get('has_pdf_extension', False)
        legacy_result["size_valid"] = validation_result['details'].get('size_validation', {}).get('is_valid', False)
    
    return legacy_result


def create_empty_session_data() -> SessionData:
    """Crée une instance SessionData vide avec des valeurs par défaut."""
    return SessionData()


def serialize_model_list(models: List[Union[JobMatch, JobDetails, AdviceSection]]) -> List[Dict[str, Any]]:
    """
    Sérialise une liste de modèles en liste de dictionnaires.
    
    Args:
        models: Liste de modèles à sérialiser
        
    Returns:
        Liste de dictionnaires
    """
    return [model.to_dict() for model in models if hasattr(model, 'to_dict')]


def deserialize_model_list(data_list: List[Dict[str, Any]], model_class) -> List:
    """
    Désérialise une liste de dictionnaires en liste de modèles.
    
    Args:
        data_list: Liste de dictionnaires
        model_class: Classe du modèle à créer
        
    Returns:
        Liste de modèles
    """
    models = []
    for data in data_list:
        try:
            if hasattr(model_class, 'from_dict'):
                models.append(model_class.from_dict(data))
        except (ValueError, KeyError) as e:
            logger.warning(f"Erreur lors de la désérialisation: {e}")
    
    return models