#!/usr/bin/env python3
"""
Script de téléchargement des modèles Deep Learning locaux.

À exécuter une seule fois après clonage du projet pour initialiser
les modèles CamemBERT utilisés par le service AI Enrichment.

Usage:
    python setup_models.py
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("❌ huggingface_hub non installé. Exécutez: uv add huggingface-hub")
    sys.exit(1)


def download_models():
    """Télécharge et sauvegarde les modèles localement."""

    print("Téléchargement des modèles Deep Learning (843 MB)")

    # Créer les répertoires
    models_dir = Path("models")
    ner_dir = models_dir / "ner"
    classifier_dir = models_dir / "classifier"

    os.makedirs(ner_dir, exist_ok=True)
    os.makedirs(classifier_dir, exist_ok=True)

    models = {
        "NER (Token Classification)": {
            "repo": "leocooo/v2-camembert-ner-job-ads",
            "path": ner_dir,
            "size": "420 MB",
        },
        "Classifier (Sequence Classification)": {
            "repo": "leocooo/camembert-job-classifier",
            "path": classifier_dir,
            "size": "423 MB",
        },
    }

    for name, config in models.items():
        print(f"\nTéléchargement {name}...")
        print(f"   Repository: {config['repo']}")
        print(f"   Taille: {config['size']}")
        print(f"   Destination: {config['path']}")

        try:
            snapshot_download(
                config["repo"],
                local_dir=str(config["path"]),
                local_dir_use_symlinks=False,
                repo_type="model",
            )
            print(f"   ✓ {name} téléchargé avec succès!")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False

    print("✅ Tous les modèles sont prêts!")
    print("\nStockage:")
    print(f"  ./models/ner/        • {models['NER (Token Classification)']['size']}")
    print(
        f"  ./models/classifier/ • {models['Classifier (Sequence Classification)']['size']}"
    )
    print("\nProchain: Ajoutez 'models/' à .gitignore")
    print("Commande: just enrich-ai")

    return True


if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
