# TODO List - FlightHunter

## Phase 1 : Initialisation & Backend Core (En cours)
- [x] Créer l'arborescence de base (Backend).
- [x] Initialiser les modules `database.py`, `api_client.py` (Amadeus), `scheduler.py`.
- [x] Créer les fichiers de documentation (README, TODO, JOURNAL, AI_BRIEFING).
- [ ] Connecter réellement le `main.py` à Firestore pour écouter les commandes (`SEARCH_FLIGHTS`, `START`, `STOP`).
- [ ] Finaliser l'intégration de l'API Amadeus (gestion des tokens, parsing des réponses complexes).
- [ ] Définir la structure de données des "Vols" dans Firestore (Collections: `searches`, `flight_results`, `logs`).
- [ ] Implémenter le logging distant vers Firestore.

## Phase 2 : Frontend (React/Vite)
- [ ] Initialiser le projet Vite/React avec Tailwind CSS dans `src/`.
- [ ] Mettre en place les contextes (Auth, Firebase, Settings).
- [ ] Créer le composant `Dashboard` de base.
- [ ] Créer le formulaire de création de recherche (Origine, Destination, Dates, Paramètres).
- [ ] Créer le composant d'affichage des résultats (`FlightCard`).
- [ ] Connecter le Frontend à Firestore pour envoyer des commandes au bot.

## Phase 3 : Logique Avancée & Tracking
- [ ] Implémenter l'historique des prix (storer l'évolution du prix pour un vol spécifique).
- [ ] Créer des alertes de baisse de prix (ex: via Ntfy ou email).
- [ ] (Optionnel) Ajouter des proxies si l'API a des limites strictes ou pour contourner du tracking géographique.
- [ ] Gérer les recherches flexibles (dates +/- 3 jours).

## Phase 4 : Déploiement
- [ ] Packager le bot backend pour un déploiement sur un VPS ou Docker.
- [ ] Déployer le frontend sur GitHub Pages, Vercel ou Firebase Hosting.
