# bon-plan-vinted

Veille de bonnes affaires : vide-greniers, brocantes et ventes de charité à
Paris intra-muros (volet 1), puis détection d'annonces sous-évaluées sur
Vinted (volet 2, à venir).

## Stack

- Python 3, `requests` uniquement pour le scraping (pas de framework de scraping :
  les sources HTML embarquent du JSON-LD `schema.org/Event`, donc parsing
  regex + `json.loads`, pas besoin de BeautifulSoup/Playwright).

## Sources (volet 1)

- `vide-greniers.org` et `vente-solidaire.org` : même plateforme, même
  structure. Listing paginé via `?offset=YYYY-MM-DD` sur
  `/evenements/Paris-75`. Chaque page contient des blocs
  `<script type="application/ld+json">` de type `Event` avec date, lieu,
  géoloc, description.
- Filtre Paris intra-muros : `location.address.addressLocality == "Paris-75"`
  (les communes limitrophes ont leur propre libellé, ex. `Saint-Mande-94`).
- Arrondissement déduit par regex sur le code postal (75001-75020) ou motif
  "Paris Xe" dans le nom/l'adresse — non fiable à 100% (~50% de couverture),
  amélioration possible via reverse-geocoding des coordonnées lat/lon
  (toujours présentes).
- `robots.txt` des deux sites autorise le crawl de ces pages.

## Commandes

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scraper.py
```

Écrit l'état courant dans `data/events.json` (non versionné) et affiche sur
stdout les événements nouveaux depuis le dernier run (diff par `@id`, qui
inclut la date — un événement récurrent hebdomadaire réapparaît donc comme
"nouveau" à chaque occurrence : limitation connue, pas encore filtrée).

## À venir

- Alertes Telegram sur les nouveaux événements détectés.
- Dashboard (Artifact) pour parcourir les événements à venir.
- Cron GitHub Actions pour l'exécution périodique.
- Volet 2 : scraper Vinted pour détecter des annonces sous-évaluées vs.
  médiane d'articles comparables.
