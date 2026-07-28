# Scraper "brute force" tout-inclus (module expérimental)

Ce module est **séparé du backend officiel** (`backend/`, API Amadeus). Il ne
respecte pas les principes listés dans `AI_BRIEFING.md` ("API only, no
scraping") — c'est un choix assumé, demandé explicitement pour un besoin
ponctuel : trouver un séjour tout-inclus au départ de YUL, dans les 2
prochains jours, chez des voyagistes qui ne vendent pas leurs forfaits via
API publique.

## ⚠️ Important — non testé en conditions réelles

Ce code a été écrit **sans accès réseau** (l'environnement où il a été rédigé
n'a pas d'accès internet général). Les sélecteurs CSS/XPath dans
`providers/transat.py` et `providers/air_canada_vacations.py` sont donc des
**meilleures suppositions**, pas des valeurs vérifiées contre le DOM réel.
Au premier lancement, il est très probable qu'il faille les ajuster.

Pour faciliter le débogage :
- Chaque étape de scraping est isolée avec try/except explicite.
- En cas d'échec de sélecteur, une capture d'écran + le HTML de la page sont
  sauvegardés dans `scraper/output/debug/` pour inspection.
- Lance avec `--debug` pour un navigateur non-headless (visible) et des logs
  verbeux.

## Portée

- **Origine** : YUL (Montréal-Trudeau)
- **Fenêtre de départ** : aujourd'hui + les 2 prochains jours (configurable
  dans `config.py`)
- **Durée du séjour** : 10 à 14 nuits
- **Budget max** : 12 000 $ CAD pour le voyage (2 passagers par défaut —
  ajuste `PAX` dans `config.py` si besoin)
- **Voyagistes ciblés** : Air Transat (Vacances Transat), Vacances Air
  Canada. **Sunwing et WestJet Vacances sont explicitement exclus.**
- **Destinations** : liste de destinations soleil tout-inclus classiques au
  départ de YUL, **en excluant par défaut les destinations à fort risque de
  sargasses** (Cancún/Riviera Maya, Punta Cana) — voir `config.py`
  `SARGASSUM_RISK`. Les destinations à risque "modéré" sont incluses mais
  marquées — vérifie les prévisions de sargasses (ex. via les bulletins de
  l'université USF/Optical Oceanography Lab ou les rapports des voyagistes)
  avant de réserver, ces données varient semaine par semaine et ne sont pas
  disponibles via ce script.

## Installation

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
```

## Utilisation

```bash
python run.py                  # recherche complète, résultats triés par prix
python run.py --debug          # navigateur visible + logs verbeux + dumps HTML en cas d'erreur
python run.py --provider transat   # limiter à un seul voyagiste
python run.py --max-price 8000     # filtrer un budget différent
```

Les résultats sont écrits dans `scraper/output/offers_<timestamp>.csv` et
`.json`, triés par prix total croissant, et les 10 meilleures offres sont
affichées dans la console.

## Éthique / CGU

Ce script fait un nombre limité de requêtes (usage personnel, une recherche
ponctuelle, pas de volume industriel), avec des délais entre chaque requête
pour rester raisonnable. Il n'utilise aucune technique d'évasion anti-bot
(pas de spoofing d'empreinte, pas de résolution de CAPTCHA, pas de rotation
de proxies). Si un site bloque la requête ou affiche un CAPTCHA, le script
le signale et passe à la suite plutôt que d'insister. L'utilisation de ce
script reste à la discrétion et sous la responsabilité de l'utilisateur au
regard des conditions d'utilisation de chaque site.
