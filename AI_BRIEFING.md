# AI Briefing - FlightHunter

Ce fichier sert de contexte aux assistants IA travaillant sur ce projet. Lisez-le avant de proposer des modifications d'architecture.

## Nature du Projet
**FlightHunter** est un bot de tracking de prix de billets d'avion couplé à un dashboard React. Il est inspiré d'un projet précédent appelé "GuitarHunter", MAIS il diffère sur des points cruciaux.

## Principes Directeurs (CRITIQUES)

1.  **API Only, No Scraping :** Le projet récupère ses données via l'API **Amadeus**. Ne proposez PAS d'utiliser Selenium, Playwright ou BeautifulSoup pour extraire des prix de billets d'avion. C'est un anti-pattern ici.
2.  **No AI/LLM for Parsing :** Les données reçues (JSON) sont déjà structurées. N'utilisez pas de LLM (comme Gemini ou OpenAI) pour analyser si un vol est "intéressant". Utilisez des algorithmes classiques (min, max, moyennes).
3.  **Command Pattern via Firestore :** Le frontend ne communique jamais directement avec l'API Amadeus. Le frontend écrit une "Commande" (ex: `SEARCH_FLIGHTS`) dans Firestore. Le backend Python, qui écoute cette collection, exécute la commande et écrit le résultat en retour.
4.  **Data Volatility :** Les prix des vols changent constamment. Ne stockez dans Firestore que les résultats des recherches actives de l'utilisateur ou l'historique des meilleurs prix, pas la totalité de la réponse de l'API.

## Stack Technologique
*   **Backend :** Python 3.10+, `requests`, `amadeus` (SDK), `firebase-admin`, `schedule`.
*   **Frontend :** React, Vite, Tailwind CSS, Firebase Web SDK.
*   **Infrastructure :** Firebase (Firestore pour les données et commandes, Auth si nécessaire).

## État Actuel
Le projet en est à sa phase d'initialisation. La coquille du backend est créée, et l'intégration de base avec l'API Amadeus est préparée. Le frontend reste à implémenter.
