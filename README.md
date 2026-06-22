# 📰 Le Digest du Jour

Ce projet récupère **chaque matin automatiquement** : l'actualité du jour
(France + international), les sorties cinéma, les nouveaux albums musicaux,
et les événements culturels à venir à Angers et Nantes — puis publie le tout
sur une page web facile à consulter.

---

## Comment ça marche

```
Chaque jour à 7h30 (heure de Paris)
        │
        ▼
GitHub Actions réveille le script
        │
        ▼
Le script interroge 5 sources en parallèle :
  • RSS France Info & France 24 (actu)
  • TMDB (sorties cinéma)
  • MusicBrainz (nouveaux albums)
  • Open Data Nantes Métropole (événements Nantes)
  • OpenAgenda (événements Angers)
        │
        ▼
Génération d'une page HTML de synthèse
        │
        ▼
Publication automatique sur GitHub Pages
```

---

## Installation (10 minutes, une seule fois)

Tu connais déjà cette mécanique grâce aux deux projets précédents. Une seule
clé API à configurer ici (TMDB, gratuite).

### Étape 1 — Récupère une clé API TMDB (gratuite)

1. Va sur **https://www.themoviedb.org/** et crée un compte
2. Va dans **Paramètres** → **API**
3. Demande une clé API (usage non-commercial / développeur)
4. **Copie ta clé API** (v3 auth) une fois approuvée

> Cette clé est gratuite et sans limite de paiement caché — TMDB est financé
> par la communauté et les dons, pas par la vente de données.

### Étape 2 — Crée le dépôt GitHub

```bash
cd chemin/vers/le/dossier/daily-digest
git init
git add .
git commit -m "Premier import du digest quotidien"
git branch -M main
git remote add origin https://github.com/TON-PSEUDO/daily-digest.git
git push -u origin main
```

### Étape 3 — Configure le secret GitHub

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**
- Nom : `TMDB_API_KEY` → Valeur : ta clé TMDB

### Étape 4 — Active GitHub Pages

**Settings** → **Pages** → Source : **"GitHub Actions"**

### Étape 5 — Premier test

Onglet **Actions** → workflow **"Digest quotidien"** → **"Run workflow"**

### Étape 6 — Ton lien

`https://ton-pseudo.github.io/daily-digest/`

---

## Personnaliser

Tout se règle dans **`config/preferences.json`** :

```json
{
  "news": {
    "flux_rss": [
      { "nom": "France Info - À la Une", "url": "https://www.franceinfo.fr/titres.rss" }
    ]
  },
  "evenements_locaux": {
    "villes": [
      { "nom": "Angers", "source": "openagenda_public" },
      { "nom": "Nantes", "source": "nantes_metropole" }
    ]
  }
}
```

- **Ajouter un flux RSS** : ajoute un objet `{ "nom": "...", "url": "..." }`
  dans `flux_rss`. Beaucoup de sites de presse proposent un flux RSS (souvent
  visible en bas de page ou dans "À propos").
- **Ajuster le nombre d'éléments affichés** : modifie les champs
  `nombre_articles_max`, `nombre_films_max`, etc.

---

## Sources utilisées et limites à connaître

| Source | Fiabilité | Limite |
|---|---|---|
| RSS France Info / France 24 | Bonne | Certains sites de presse bloquent occasionnellement les requêtes automatisées (protection anti-robot). Si une source ne répond pas un jour, elle est simplement ignorée ce jour-là — pas d'erreur bloquante. |
| TMDB (cinéma) | Très bonne | Nécessite la clé API configurée à l'étape 1. |
| MusicBrainz (albums) | Bonne | Base communautaire : certains albums très récents ou très niche peuvent manquer s'ils n'ont pas encore été ajoutés par la communauté. |
| Open Data Nantes Métropole | Bonne | Dataset municipal, structure stable mais peut évoluer sans préavis. |
| OpenAgenda (Angers) | Moyenne | Dépend des organisateurs qui publient leurs événements sur cette plateforme — couverture partielle, pas un agenda municipal officiel exhaustif. |

**Si une section apparaît vide un jour donné** (par exemple "aucun film"),
c'est normal — certains jours n'ont simplement pas de nouvelle sortie dans
une catégorie donnée, ou la source a été temporairement indisponible. Le
système réessaiera automatiquement le lendemain.

## Pour aller plus loin (non inclus, à la demande)

- Ajout d'autres flux RSS thématiques (sport, tech, etc.)
- Filtrage des événements par type (concerts seulement, expos seulement...)
- Élargir les sources de musique (ex: croiser avec Discogs)
- Notification push ou email en plus de la page web

Dis-moi si tu veux qu'on ajoute l'une de ces briques.
