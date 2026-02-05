# Document d'Exigences

## Introduction

Cette spécification définit les exigences pour une interface utilisateur Streamlit qui se connecte au backend FastAPI CV-Optimizer existant. L'interface permettra aux utilisateurs d'uploader leurs CV, de rechercher des offres d'emploi correspondantes, de filtrer les résultats, et d'obtenir des conseils personnalisés pour améliorer leurs candidatures.

## Glossaire

- **Interface_Streamlit** : L'application web frontend développée avec Streamlit
- **Backend_API** : Le service FastAPI CV-Optimizer existant
- **CV** : Curriculum Vitae au format PDF uploadé par l'utilisateur
- **Offre** : Une offre d'emploi disponible dans le système
- **Match** : Correspondance calculée entre un CV et une offre d'emploi
- **Conseils_LLM** : Recommandations personnalisées générées par l'IA pour améliorer une candidature
- **Filtre** : Critère de recherche (localisation, type de contrat, expérience)

## Exigences

### Exigence 1 : Upload et Matching de CV

**User Story :** En tant qu'utilisateur, je veux uploader mon CV et voir les offres d'emploi correspondantes, afin de découvrir les opportunités qui correspondent à mon profil.

#### Critères d'Acceptation

1. WHEN un utilisateur sélectionne un fichier PDF, THE Interface_Streamlit SHALL valider que le fichier est au format PDF
2. WHEN un CV valide est uploadé, THE Interface_Streamlit SHALL envoyer le fichier au Backend_API via l'endpoint POST /api/match
3. WHEN le Backend_API retourne des offres matchées, THE Interface_Streamlit SHALL afficher la liste des offres avec leurs scores de correspondance
4. IF l'upload échoue ou le Backend_API retourne une erreur, THEN THE Interface_Streamlit SHALL afficher un message d'erreur explicite
5. WHEN aucune offre n'est trouvée, THE Interface_Streamlit SHALL informer l'utilisateur qu'aucun match n'a été trouvé

### Exigence 2 : Filtrage des Offres d'Emploi

**User Story :** En tant qu'utilisateur, je veux filtrer les offres d'emploi par critères spécifiques, afin de trouver les opportunités qui correspondent à mes préférences.

#### Critères d'Acceptation

1. THE Interface_Streamlit SHALL afficher des contrôles de filtre pour la localisation, le type de contrat, et le niveau d'expérience
2. WHEN un utilisateur applique des filtres, THE Interface_Streamlit SHALL envoyer une requête GET /api/jobs avec les paramètres de filtre appropriés
3. WHEN les filtres sont modifiés, THE Interface_Streamlit SHALL mettre à jour automatiquement la liste des offres affichées
4. WHEN le Backend_API retourne des résultats filtrés, THE Interface_Streamlit SHALL afficher les offres correspondant aux critères sélectionnés
5. THE Interface_Streamlit SHALL permettre de réinitialiser tous les filtres en un clic

### Exigence 3 : Consultation des Détails d'Offre

**User Story :** En tant qu'utilisateur, je veux consulter les détails complets d'une offre d'emploi, afin de comprendre les exigences et responsabilités du poste.

#### Critères d'Acceptation

1. WHEN un utilisateur clique sur une offre dans la liste, THE Interface_Streamlit SHALL récupérer les détails via GET /api/jobs/{job_id}
2. WHEN les détails sont récupérés, THE Interface_Streamlit SHALL afficher toutes les informations de l'offre de manière structurée
3. THE Interface_Streamlit SHALL inclure un bouton de retour vers la liste des offres
4. IF la récupération des détails échoue, THEN THE Interface_Streamlit SHALL afficher un message d'erreur et permettre de retourner à la liste

### Exigence 4 : Conseils Personnalisés LLM

**User Story :** En tant qu'utilisateur, je veux obtenir des conseils personnalisés pour améliorer ma candidature à une offre spécifique, afin d'augmenter mes chances de succès.

#### Critères d'Acceptation

1. WHEN un utilisateur consulte les détails d'une offre ET qu'un CV a été uploadé, THE Interface_Streamlit SHALL afficher un bouton "Obtenir des conseils"
2. WHEN l'utilisateur clique sur "Obtenir des conseils", THE Interface_Streamlit SHALL envoyer une requête POST /api/advice avec le CV et l'ID de l'offre
3. WHEN le Backend_API retourne des conseils, THE Interface_Streamlit SHALL afficher les recommandations de manière claire et lisible
4. THE Interface_Streamlit SHALL indiquer le statut de chargement pendant la génération des conseils
5. IF la génération de conseils échoue, THEN THE Interface_Streamlit SHALL afficher un message d'erreur approprié

### Exigence 5 : Navigation et Interface Utilisateur

**User Story :** En tant qu'utilisateur, je veux une interface simple et intuitive, afin de naviguer facilement entre les différentes fonctionnalités.

#### Critères d'Acceptation

1. THE Interface_Streamlit SHALL organiser les fonctionnalités en sections logiques avec une navigation claire
2. THE Interface_Streamlit SHALL afficher des indicateurs de progression pour les opérations longues
3. THE Interface_Streamlit SHALL utiliser des messages en français pour toutes les interactions utilisateur
4. THE Interface_Streamlit SHALL maintenir l'état de l'application (CV uploadé, filtres appliqués) pendant la session
5. THE Interface_Streamlit SHALL être responsive et fonctionner correctement sur différentes tailles d'écran

### Exigence 6 : Gestion des Erreurs et Connectivité

**User Story :** En tant qu'utilisateur, je veux être informé clairement des problèmes de connexion ou d'erreurs, afin de comprendre ce qui se passe et comment résoudre les problèmes.

#### Critères d'Acceptation

1. WHEN le Backend_API n'est pas accessible, THE Interface_Streamlit SHALL afficher un message d'erreur de connexion
2. WHEN une requête API échoue, THE Interface_Streamlit SHALL afficher le message d'erreur approprié en français
3. THE Interface_Streamlit SHALL implémenter un mécanisme de retry pour les requêtes échouées
4. THE Interface_Streamlit SHALL valider la connectivité au Backend_API au démarrage via l'endpoint GET /health
5. WHEN une erreur de validation survient, THE Interface_Streamlit SHALL guider l'utilisateur vers la correction

### Exigence 7 : Performance et Expérience Utilisateur

**User Story :** En tant qu'utilisateur, je veux une interface réactive et performante, afin d'avoir une expérience fluide lors de l'utilisation de l'application.

#### Critères d'Acceptation

1. THE Interface_Streamlit SHALL charger la page principale en moins de 3 secondes
2. WHEN des données sont en cours de chargement, THE Interface_Streamlit SHALL afficher des indicateurs visuels appropriés
3. THE Interface_Streamlit SHALL mettre en cache les résultats de recherche pour éviter les requêtes répétées
4. THE Interface_Streamlit SHALL limiter la taille des fichiers PDF uploadés à une taille raisonnable
5. THE Interface_Streamlit SHALL optimiser l'affichage des listes longues avec pagination ou scroll virtuel