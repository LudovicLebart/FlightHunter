# Journal de Développement - FlightHunter

## [Date Initiale] - Lancement du Projet

**Contexte :**
Création de FlightHunter, inspiré de l'architecture de GuitarHunter, mais dédié à la recherche de vols.

**Décisions architecturales clés :**
1.  **Abandon du Scraping pour les API :** Contrairement à GuitarHunter qui utilisait Playwright pour scraper des sites web complexes, FlightHunter utilisera des API REST dédiées (comme Amadeus). Le scraping de vols est trop instable (captchas, changements constants d'UI).
2.  **Abandon de l'IA Générative (Gemini) :** Les données de vols sont déjà hautement structurées (JSON). Utiliser un LLM pour analyser un prix n'a pas de sens technique ni économique ici. La logique de "Deal" sera purement mathématique (comparaison avec un prix moyen ou un budget fixé).
3.  **Conservation de la "Coquille" Firebase :** Le système de pilotage asynchrone via Firestore (Frontend qui envoie des commandes, Backend qui écoute) est conservé car il est robuste et permet de créer un dashboard temps réel très réactif.

**Actions réalisées :**
*   Création de la structure du backend Python isolée dans un sous-dossier de GuitarHunter (pour l'instant, pour faciliter la migration, prévu pour être déplacé).
*   Génération des fichiers de base : `main.py`, `config.py`, `database.py`, `api_client.py` (préparé pour Amadeus), et `scheduler.py`.
*   Création de la documentation initiale.

**Prochaines étapes :**
*   Tester la connexion à l'API Amadeus avec des requêtes réelles.
*   Mettre en place la base du projet Frontend React.
