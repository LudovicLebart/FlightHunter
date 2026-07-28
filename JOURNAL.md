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

## [2026-07-28] - Scraper brute force tout-inclus (exception assumée à l'AI_BRIEFING)

**Contexte :**
Besoin ponctuel et urgent : trouver un séjour tout-inclus au départ de YUL,
départ dans les 2 jours, 10 à 14 nuits, budget max 12 000 $ CAD (2 pax),
chez des voyagistes qui ne vendent pas leurs forfaits via API publique
(donc hors du périmètre Amadeus du backend officiel).

**Décision :** l'utilisateur a explicitement demandé d'ignorer le principe
"API only, no scraping" de `AI_BRIEFING.md` pour ce besoin. Plutôt que de
modifier l'architecture du backend officiel, le scraping a été isolé dans
un module séparé et non intégré : `scraper/` (voir `scraper/README.md`
pour le détail). Le reste du projet (backend Amadeus, principes de
l'AI_BRIEFING) n'est pas remis en cause par ce module.

**Contenu du module `scraper/` :**
*   Recherche combinatoire (destination x date de départ) chez Air Transat
    et Vacances Air Canada. Sunwing et WestJet exclus explicitement
    (préavis de grève sur des vacances déjà payées par l'utilisateur).
*   Destinations filtrées pour exclure celles à fort risque de sargasses
    en saison (Cancún/Riviera Maya, Punta Cana) ; celles à risque modéré
    sont incluses mais marquées, à vérifier manuellement avant réservation.
*   Tri par prix total, export CSV/JSON, top 10 en console.

**Contrainte découverte : pas d'exécution possible depuis cette session**
L'environnement d'exécution (Claude Code) où ce module a été écrit n'a
qu'un accès réseau restreint à une liste blanche d'infrastructure de dev
(GitHub, npm, PyPI...) — confirmé bloqué pour tout domaine web général,
y compris via un outil de fetch alternatif (jusqu'à Wikipédia). Le
scraper n'a donc **jamais pu être exécuté ni ses sélecteurs CSS vérifiés**
contre les sites réels — voir les avertissements dans `scraper/README.md`.

**Solution de contournement retenue :** exécution via GitHub Codespaces
(accès internet complet, utilisable depuis un simple navigateur/téléphone
quand aucun poste local n'est disponible), avec itération sur les
sélecteurs au fur et à mesure des erreurs remontées.

**Prochaines étapes :**
*   Lancer `scraper/run.py --debug` dans un Codespace et corriger les
    sélecteurs CSS des deux providers en fonction des erreurs réelles.
*   Une fois validé, envisager d'ajouter d'autres voyagistes tout-inclus
    (hors Sunwing/WestJet) si le besoin se répète.
