#!/usr/bin/env python3
"""
Daily Digest
Récupère chaque jour : l'actualité du jour (RSS), les sorties cinéma (TMDB),
les sorties d'albums (MusicBrainz), et les événements culturels à Angers et
Nantes (open data), puis génère une page HTML de synthèse.

Usage:
    python3 fetch_digest.py

Variables d'environnement requises (secrets GitHub Actions ou .env local):
    TMDB_API_KEY - Clé API The Movie Database (https://www.themoviedb.org/settings/api)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import feedparser

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "preferences.json"
DATA_DIR = ROOT_DIR / "data"
HISTORY_PATH = DATA_DIR / "historique.json"
DOCS_DIR = ROOT_DIR / "docs"
HTML_OUTPUT_PATH = DOCS_DIR / "index.html"

TMDB_API_BASE = "https://api.themoviedb.org/3"
MUSICBRAINZ_API_BASE = "https://musicbrainz.org/ws/2"
MUSICBRAINZ_USER_AGENT = "DailyDigestPerso/1.0 (usage personnel non-commercial)"

NANTES_API_BASE = "https://data.nantesmetropole.fr/api/v2/catalog/datasets/244400404_agenda-evenements-nantes-metropole_v2/records"
OPENAGENDA_PUBLIC_DATASET = "https://public.opendatasoft.com/api/v2/catalog/datasets/evenements-publics-openagenda/records"

REQUEST_TIMEOUT = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("daily-digest")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch_news(config: dict) -> list[dict]:
    articles = []
    flux_list = config["news"]["flux_rss"]
    max_articles = config["news"].get("nombre_articles_max", 8)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DailyDigestPerso/1.0; +usage personnel)"
    }

    for flux in flux_list:
        try:
            resp = requests.get(flux["url"], headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                log.warning("Flux RSS '%s' a répondu %s, ignoré.", flux["nom"], resp.status_code)
                continue
            parsed = feedparser.parse(resp.content)
            for entry in parsed.entries[:5]:
                articles.append({
                    "source": flux["nom"],
                    "titre": entry.get("title", "Sans titre"),
                    "resume": entry.get("summary", "")[:200],
                    "lien": entry.get("link", ""),
                    "date": entry.get("published", ""),
                })
        except Exception as e:
            log.warning("Echec lecture flux RSS '%s': %s", flux["nom"], e)

    return articles[:max_articles]


def fetch_movies(config: dict) -> list[dict]:
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        log.warning("TMDB_API_KEY manquant, sorties cinéma ignorées.")
        return []

    cine_cfg = config["cinema"]
    params = {
        "api_key": api_key,
        "region": cine_cfg.get("region", "FR"),
        "language": cine_cfg.get("langue", "fr-FR"),
        "page": 1,
    }

    try:
        resp = requests.get(f"{TMDB_API_BASE}/movie/now_playing", params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log.warning("Echec TMDB now_playing: %s - %s", resp.status_code, resp.text[:300])
            return []
        data = resp.json()
    except requests.RequestException as e:
        log.warning("Erreur réseau TMDB: %s", e)
        return []

    max_films = cine_cfg.get("nombre_films_max", 6)
    films = []
    for m in data.get("results", [])[:max_films]:
        films.append({
            "titre": m.get("title", "Titre inconnu"),
            "date_sortie": m.get("release_date", ""),
            "synopsis": (m.get("overview") or "")[:220],
            "note": m.get("vote_average", 0),
            "affiche": f"https://image.tmdb.org/t/p/w300{m['poster_path']}" if m.get("poster_path") else None,
        })

    return films


def fetch_albums(config: dict) -> list[dict]:
    musique_cfg = config["musique"]
    max_albums = musique_cfg.get("nombre_albums_max", 6)

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    headers = {"User-Agent": MUSICBRAINZ_USER_AGENT}
    params = {
        "query": f'firstreleasedate:[{week_ago.isoformat()} TO {today.isoformat()}] AND primarytype:album AND status:official',
        "fmt": "json",
        "limit": max_albums,
    }

    try:
        resp = requests.get(f"{MUSICBRAINZ_API_BASE}/release-group", headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log.warning("Echec MusicBrainz: %s - %s", resp.status_code, resp.text[:300])
            return []
        data = resp.json()
    except requests.RequestException as e:
        log.warning("Erreur réseau MusicBrainz: %s", e)
        return []

    albums = []
    for rg in data.get("release-groups", [])[:max_albums]:
        artist_credit = rg.get("artist-credit", [])
        artiste = artist_credit[0]["name"] if artist_credit else "Artiste inconnu"
        albums.append({
            "titre": rg.get("title", "Titre inconnu"),
            "artiste": artiste,
            "date_sortie": rg.get("first-release-date", ""),
        })

    return albums


def fetch_events_nantes(max_events: int, fenetre_jours: int) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=fenetre_jours)

    params = {
        "where": f"date >= '{today.isoformat()}' AND date <= '{end_date.isoformat()}'",
        "order_by": "date",
        "limit": max_events,
    }

    try:
        resp = requests.get(NANTES_API_BASE, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log.warning("Echec API Nantes Métropole: %s - %s", resp.status_code, resp.text[:300])
            return []
        data = resp.json()
    except requests.RequestException as e:
        log.warning("Erreur réseau API Nantes: %s", e)
        return []

    events = []
    for rec in data.get("records", [])[:max_events]:
        f = rec.get("record", {}).get("fields", {})
        events.append({
            "titre": f.get("nom", "Événement"),
            "date_debut": f.get("date", ""),
            "lieu": f.get("lieu") or f.get("ville", "Nantes"),
            "ville": "Nantes",
        })

    return events


def fetch_events_angers(max_events: int, fenetre_jours: int) -> list[dict]:
    today = datetime.now(timezone.utc)
    end_date = today + timedelta(days=fenetre_jours)
    today_str = today.strftime("%Y-%m-%dT00:00:00+00:00")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59+00:00")

    params = {
        "where": (
            f"location_city = 'Angers' AND "
            f"firstdate_begin >= '{today_str}' AND firstdate_begin <= '{end_str}'"
        ),
        "order_by": "firstdate_begin",
        "limit": max_events,
    }

    try:
        resp = requests.get(OPENAGENDA_PUBLIC_DATASET, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            log.warning("Echec API OpenAgenda (Angers): %s - %s", resp.status_code, resp.text[:300])
            return []
        data = resp.json()
    except requests.RequestException as e:
        log.warning("Erreur réseau API OpenAgenda: %s", e)
        return []

    events = []
    for rec in data.get("records", [])[:max_events]:
        f = rec.get("record", {}).get("fields", {})
        events.append({
            "titre": f.get("title_fr", "Événement"),
            "date_debut": f.get("firstdate_begin", ""),
            "lieu": f.get("location_name", "Angers"),
            "ville": "Angers",
        })

    return events


def fetch_events(config: dict) -> list[dict]:
    evt_cfg = config["evenements_locaux"]
    max_par_ville = evt_cfg.get("nombre_evenements_max_par_ville", 5)
    fenetre = evt_cfg.get("fenetre_jours", 14)

    all_events = []
    for ville_cfg in evt_cfg["villes"]:
        if ville_cfg["source"] == "nantes_metropole":
            all_events.extend(fetch_events_nantes(max_par_ville, fenetre))
        elif ville_cfg["source"] == "openagenda_public":
            all_events.extend(fetch_events_angers(max_par_ville, fenetre))
        time.sleep(0.3)

    return all_events


def save_today_digest(digest: dict) -> None:
    history = []
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)

    history.insert(0, digest)
    history = history[:14]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def main() -> None:
    log.info("=== Génération du digest quotidien ===")
    config = load_config()

    log.info("Récupération des news...")
    news = fetch_news(config)
    log.info("%d articles récupérés.", len(news))

    log.info("Récupération des sorties cinéma...")
    movies = fetch_movies(config)
    log.info("%d films récupérés.", len(movies))

    log.info("Récupération des sorties d'albums...")
    albums = fetch_albums(config)
    log.info("%d albums récupérés.", len(albums))

    log.info("Récupération des événements locaux...")
    events = fetch_events(config)
    log.info("%d événements récupérés.", len(events))

    digest = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "news": news,
        "films": movies,
        "albums": albums,
        "evenements": events,
    }
    save_today_digest(digest)

    history = []
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)

    from generate_html import generate_dashboard
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    generate_dashboard(history, HTML_OUTPUT_PATH)
    log.info("Dashboard généré: %s", HTML_OUTPUT_PATH)

    log.info("=== Fin ===")


if __name__ == "__main__":
    main()