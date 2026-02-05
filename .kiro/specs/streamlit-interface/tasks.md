# Plan d'Implémentation : Interface Streamlit CV-Optimizer

## Vue d'Ensemble

Ce plan d'implémentation convertit la conception de l'interface Streamlit en une série de tâches de développement incrémentales. Chaque tâche construit sur les précédentes et se termine par l'intégration complète de tous les composants.

## Tâches

- [x] 1. Configuration du projet et structure de base
  - Créer la structure de fichiers du projet Streamlit
  - Configurer les dépendances Python (requirements.txt)
  - Implémenter la configuration de base et les constantes
  - _Exigences: 6.4, 7.1_

- [ ] 2. Implémentation du client API et gestion d'erreurs
  - [x] 2.1 Créer le module client API (api_client.py)
    - Implémenter la classe APIClient avec tous les endpoints
    - Ajouter la gestion des timeouts et retry
    - _Exigences: 1.2, 2.2, 3.1, 4.2, 6.1, 6.3_
  
  - [ ]* 2.2 Écrire les tests de propriété pour le client API
    - **Propriété 2: Appels API corrects pour matching**
    - **Propriété 5: Appels API avec filtres**
    - **Propriété 8: Navigation vers les détails**
    - **Propriété 11: Appels API pour conseils**
    - **Valide: Exigences 1.2, 2.2, 3.1, 4.2**
  
  - [x] 2.3 Implémenter le gestionnaire d'erreurs (error_handler.py)
    - Créer les mappings d'erreurs HTTP vers messages français
    - Implémenter la logique de retry et recovery
    - _Exigences: 1.4, 3.4, 4.5, 6.1, 6.2, 6.5_
  
  - [ ]* 2.4 Écrire les tests de propriété pour la gestion d'erreurs
    - **Propriété 4: Gestion d'erreurs API**
    - **Propriété 16: Mécanisme de retry**
    - **Propriété 18: Aide contextuelle pour erreurs de validation**
    - **Valide: Exigences 1.4, 6.2, 6.3, 6.5**

- [ ] 3. Modèles de données et validation
  - [x] 3.1 Créer les modèles de données (models.py)
    - Implémenter les dataclasses pour JobFilters, JobMatch, JobDetails, AdviceResponse
    - Ajouter les méthodes de validation et sérialisation
    - _Exigences: 2.1, 3.2, 4.3_
  
  - [-] 3.2 Implémenter la validation de fichiers
    - Créer les fonctions de validation PDF et taille de fichier
    - Ajouter la validation des formats et contenus
    - _Exigences: 1.1, 7.4_
  
  - [ ]* 3.3 Écrire les tests de propriété pour la validation
    - **Propriété 1: Validation de fichiers PDF**
    - **Propriété 20: Limitation de taille de fichier**
    - **Valide: Exigences 1.1, 7.4**

- [~] 4. Checkpoint - Vérifier la base technique
  - S'assurer que tous les tests passent, demander à l'utilisateur si des questions se posent.

- [ ] 5. Gestionnaire d'état et cache
  - [~] 5.1 Implémenter le gestionnaire d'état (state_manager.py)
    - Créer la classe StateManager pour la gestion de session Streamlit
    - Implémenter la persistance du CV et des filtres
    - _Exigences: 5.4_
  
  - [~] 5.2 Implémenter le système de cache
    - Ajouter le cache TTL pour les requêtes API
    - Implémenter l'invalidation intelligente du cache
    - _Exigences: 7.3_
  
  - [ ]* 5.3 Écrire les tests de propriété pour l'état et le cache
    - **Propriété 15: Persistance d'état de session**
    - **Propriété 19: Cache des résultats de recherche**
    - **Valide: Exigences 5.4, 7.3**

- [ ] 6. Composants UI de base
  - [~] 6.1 Créer les composants UI (ui_components.py)
    - Implémenter le widget d'upload de CV avec validation
    - Créer les contrôles de filtrage (localisation, contrat, expérience)
    - _Exigences: 1.1, 2.1, 2.5_
  
  - [~] 6.2 Implémenter l'affichage des listes d'offres
    - Créer le composant de liste avec scores de matching
    - Ajouter la pagination et l'optimisation d'affichage
    - _Exigences: 1.3, 2.4, 7.5_
  
  - [ ]* 6.3 Écrire les tests unitaires pour les composants UI
    - Tester la présence des contrôles de filtre
    - Tester le bouton de reset des filtres
    - Tester le bouton de retour dans les détails
    - _Exigences: 2.1, 2.5, 3.3_

- [ ] 7. Interface principale et navigation
  - [~] 7.1 Créer l'application principale (main.py)
    - Implémenter la configuration de page Streamlit
    - Créer la structure de navigation principale
    - Ajouter la vérification de santé au démarrage
    - _Exigences: 5.1, 6.4, 7.1_
  
  - [~] 7.2 Implémenter la page d'accueil avec upload et matching
    - Intégrer l'upload de CV avec validation
    - Connecter au backend pour le matching
    - Afficher les résultats avec gestion d'erreurs
    - _Exigences: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 7.3 Écrire les tests de propriété pour le matching
    - **Propriété 3: Affichage des résultats de matching**
    - **Propriété 17: Vérification de santé au démarrage**
    - **Valide: Exigences 1.3, 6.4**

- [ ] 8. Fonctionnalité de filtrage
  - [~] 8.1 Implémenter le système de filtrage complet
    - Connecter les contrôles de filtre aux appels API
    - Implémenter la mise à jour réactive des résultats
    - Ajouter la réinitialisation des filtres
    - _Exigences: 2.2, 2.3, 2.4, 2.5_
  
  - [ ]* 8.2 Écrire les tests de propriété pour le filtrage
    - **Propriété 6: Mise à jour réactive des filtres**
    - **Propriété 7: Affichage des résultats filtrés**
    - **Valide: Exigences 2.3, 2.4**

- [ ] 9. Page de détails d'offre
  - [~] 9.1 Créer la page de détails d'offre
    - Implémenter la navigation depuis la liste
    - Afficher tous les détails de manière structurée
    - Ajouter le bouton de retour
    - _Exigences: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 9.2 Écrire les tests de propriété pour les détails
    - **Propriété 9: Affichage structuré des détails**
    - **Valide: Exigences 3.2**

- [ ] 10. Fonctionnalité de conseils personnalisés
  - [~] 10.1 Implémenter la section conseils
    - Ajouter l'affichage conditionnel du bouton conseils
    - Connecter au backend pour récupérer les conseils
    - Implémenter l'affichage structuré des recommandations
    - _Exigences: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 10.2 Écrire les tests de propriété pour les conseils
    - **Propriété 10: Affichage conditionnel du bouton conseils**
    - **Propriété 12: Affichage des conseils**
    - **Valide: Exigences 4.1, 4.3**

- [ ] 11. Indicateurs de chargement et UX
  - [~] 11.1 Implémenter les indicateurs de progression
    - Ajouter les spinners pour toutes les opérations longues
    - Implémenter les messages de statut en français
    - Optimiser l'expérience utilisateur
    - _Exigences: 4.4, 5.2, 5.3, 7.2_
  
  - [ ]* 11.2 Écrire les tests de propriété pour l'UX
    - **Propriété 13: Indicateurs de chargement**
    - **Propriété 14: Messages en français**
    - **Valide: Exigences 5.2, 5.3**

- [ ] 12. Checkpoint final - Intégration complète
  - [~] 12.1 Intégrer tous les composants
    - Connecter toutes les pages et fonctionnalités
    - Vérifier la cohérence de l'état global
    - Tester les flux utilisateur complets
    - _Exigences: Toutes_
  
  - [ ]* 12.2 Tests d'intégration complets
    - Tester les scénarios utilisateur de bout en bout
    - Vérifier la gestion d'erreurs dans tous les contextes
    - Valider la performance et la réactivité
    - _Exigences: Toutes_

- [~] 13. Checkpoint final - S'assurer que tous les tests passent
  - S'assurer que tous les tests passent, demander à l'utilisateur si des questions se posent.

## Notes

- Les tâches marquées avec `*` sont optionnelles et peuvent être ignorées pour un MVP plus rapide
- Chaque tâche référence des exigences spécifiques pour la traçabilité
- Les checkpoints assurent une validation incrémentale
- Les tests de propriété valident les propriétés de correction universelles
- Les tests unitaires valident des exemples spécifiques et des cas limites
- L'implémentation utilise Python avec Streamlit comme framework principal