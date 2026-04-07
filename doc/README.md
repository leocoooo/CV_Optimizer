# Documentation de refonte UI

Ce dossier sert de journal de travail pour la branche `new_interface`.

Objectif:

- garder `app/` comme source de données et d'endpoints
- concentrer toute l'expérience utilisateur dans `ui/`
- tracer clairement ce qui a été fait, pourquoi et comment

Tickets disponibles:

- `tickets/CVO-101-ui-foundation.md`
- `tickets/CVO-102-user-flows.md`
- `tickets/CVO-103-data-integration.md`
- `tickets/CVO-104-skills-comparison.md`
- `tickets/CVO-105-llm-chatbot.md`
- `tickets/CVO-106-color-refresh.md`
- `tickets/CVO-107-layout-polish.md`
- `tickets/CVO-108-commercial-redesign.md`
- `tickets/CVO-109-navigation-and-offers-layout.md`
- `tickets/CVO-110-remove-architecture-tab.md`
- `tickets/CVO-111-top-tabs-navigation.md`
- `tickets/CVO-112-professional-shell.md`
- `tickets/CVO-113-navigation-state-cleanup.md`
- `tickets/CVO-114-sticky-top-navigation.md`
- `tickets/CVO-115-fixed-viewport-navigation.md`
- `tickets/CVO-116-shell-cleanup-and-compact-nav.md`
- `tickets/CVO-117-top-bar-art-direction.md`
- `tickets/CVO-118-color-alignment-warm-theme.md`
- `tickets/CVO-119-header-logo-wordmark.md`
- `tickets/CVO-120-cover-letter-tab.md`
- `tickets/CVO-121-cover-letter-tab-rename.md`
- `tickets/CVO-122-cover-letter-pdf-export.md`
- `tickets/CVO-123-market-analysis-top-skills.md`
- `tickets/CVO-124-cover-letter-error-hardening.md`
- `tickets/CVO-125-jobs-tab-rename.md`
- `tickets/CVO-126-home-hero-copy-adjustment.md`
- `tickets/CVO-127-home-hero-centering.md`
- `tickets/CVO-128-home-cta-wording.md`
- `tickets/CVO-129-tag-spacing-polish.md`
- `tickets/CVO-130-jobs-tab-plural.md`

Lecture recommandée:

1. commencer par `CVO-101` pour comprendre le nouveau socle UI
2. lire `CVO-102` pour voir les parcours candidat et admin
3. lire `CVO-103` pour les liens avec `app/` et la validation technique
4. finir par `CVO-104` pour la comparaison compétences offre vs candidat
5. puis `CVO-105` pour le chatbot de modification CV avec le LLM
6. enfin `CVO-106` pour l’ajustement des couleurs et de l’ambiance visuelle
7. puis `CVO-107` pour la correction de mise en page et du rendu cassé
8. puis `CVO-108` pour la refonte commerciale de l'accueil et la suppression des details techniques visibles
9. puis `CVO-109` pour la correction des boutons de navigation et du layout des offres Explorer
10. puis `CVO-110` pour la suppression de l'onglet Architecture devenu inutile
11. puis `CVO-111` pour l'ajout d'une barre d'onglets de navigation en haut
12. puis `CVO-112` pour la stabilisation de la navigation haute et la transformation du shell en interface plus professionnelle
13. puis `CVO-113` pour le nettoyage des anciens etats Streamlit qui bloquaient encore la navigation
14. puis `CVO-114` pour le passage a une barre de navigation sticky en haut avec routage via URL
15. puis `CVO-115` pour faire passer la navigation en bandeau fixe viewport visible pendant tout le scroll
16. puis `CVO-116` pour compacter le shell, raccourcir les onglets et reduire les messages systeme parasites
17. puis `CVO-117` pour rapprocher le haut de page d'une DA SaaS plus premium avec barre info, nav blanche et hero centre
18. puis `CVO-118` pour conserver la nouvelle structure du haut de page tout en revenant a la palette chaude historique du projet
19. puis `CVO-119` pour remplacer le bloc texte du header par un vrai logo wordmark en haut a gauche
20. puis `CVO-120` pour ajouter un onglet de generation de lettre de motivation base sur le CV, l'offre et une structure LaTeX proche du modele fourni
21. puis `CVO-121` pour renommer l'onglet `LM` en `Lettre de Motivation` dans la navigation
22. puis `CVO-122` pour ajouter le telechargement PDF de la lettre en plus du fichier LaTeX
23. puis `CVO-123` pour ajouter dans l'accueil une analyse de marche avec les competences techniques qui ressortent le plus dans les offres
24. puis `CVO-124` pour durcir la generation de lettre face aux erreurs LaTeX et renvoyer des messages backend plus propres
25. puis `CVO-125` pour renommer l'onglet `Marche` en `Offre d'emploi`
26. puis `CVO-126` pour ajuster la phrase du hero d'accueil en ajoutant la mention `grace a l'IA`
27. puis `CVO-127` pour recentrer plus proprement le texte du hero d'accueil
28. puis `CVO-128` pour remplacer `Explorer le marche` par `Explorer les offres d'emploi` dans le CTA accueil
29. puis `CVO-129` pour aérer davantage les tags et éviter que le texte paraisse collé dans la colonne de droite
30. puis `CVO-130` pour passer l'onglet `Offre d'emploi` au pluriel `Offres d'emploi`
