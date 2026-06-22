#!/usr/bin/env python3
"""
Génère le dashboard HTML du digest quotidien.
Design: kiosque à journaux / revue de presse du matin.
"""

import html
from datetime import datetime
from pathlib import Path

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def format_date_fr(dt: datetime) -> str:
    return f"{JOURS_FR[dt.weekday()]} {dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"


def fmt_short_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return f"{dt.day:02d}/{dt.month:02d}"
    except (ValueError, IndexError):
        return date_str[:10]


def news_item_html(article: dict) -> str:
    titre = html.escape(article.get("titre", ""))
    resume = html.escape(article.get("resume", ""))
    source = html.escape(article.get("source", ""))
    lien = html.escape(article.get("lien", "#"))
    return f"""
    <article class="news-item">
      <span class="news-item__source">{source}</span>
      <h3 class="news-item__title"><a href="{lien}" target="_blank" rel="noopener noreferrer">{titre}</a></h3>
      <p class="news-item__resume">{resume}</p>
    </article>"""


def movie_card_html(film: dict) -> str:
    titre = html.escape(film.get("titre", ""))
    synopsis = html.escape(film.get("synopsis", ""))
    date_sortie = fmt_short_date(film.get("date_sortie", ""))
    note = film.get("note", 0)
    affiche = film.get("affiche")

    img_html = f'<img src="{html.escape(affiche)}" alt="{titre}" class="movie-card__poster">' if affiche else '<div class="movie-card__poster movie-card__poster--placeholder">🎬</div>'

    return f"""
    <article class="movie-card">
      {img_html}
      <div class="movie-card__body">
        <h4 class="movie-card__title">{titre}</h4>
        <p class="movie-card__meta">Sortie le {date_sortie} · ⭐ {note:.1f}/10</p>
        <p class="movie-card__synopsis">{synopsis}</p>
      </div>
    </article>"""


def album_item_html(album: dict) -> str:
    titre = html.escape(album.get("titre", ""))
    artiste = html.escape(album.get("artiste", ""))
    date_sortie = fmt_short_date(album.get("date_sortie", ""))
    return f"""
    <li class="album-item">
      <span class="album-item__icon">💿</span>
      <div>
        <p class="album-item__title">{titre}</p>
        <p class="album-item__artist">{artiste} · {date_sortie}</p>
      </div>
    </li>"""


def event_item_html(event: dict) -> str:
    titre = html.escape(event.get("titre", ""))
    lieu = html.escape(event.get("lieu", ""))
    date_debut = fmt_short_date(event.get("date_debut", ""))
    return f"""
    <li class="event-item">
      <span class="event-item__date">{date_debut}</span>
      <div>
        <p class="event-item__title">{titre}</p>
        <p class="event-item__lieu">{lieu}</p>
      </div>
    </li>"""


def generate_dashboard(history: list[dict], output_path: Path) -> None:
    if not history:
        today = {"date": datetime.now().strftime("%Y-%m-%d"), "news": [], "films": [], "albums": [], "evenements": []}
    else:
        today = history[0]

    try:
        date_dt = datetime.strptime(today["date"], "%Y-%m-%d")
        date_label = format_date_fr(date_dt)
    except (ValueError, KeyError):
        date_label = "Aujourd'hui"

    news = today.get("news", [])
    films = today.get("films", [])
    albums = today.get("albums", [])
    evenements = today.get("evenements", [])

    evenements_angers = [e for e in evenements if e.get("ville") == "Angers"]
    evenements_nantes = [e for e in evenements if e.get("ville") == "Nantes"]

    news_html = "".join(news_item_html(a) for a in news) if news else '<p class="empty-state">Aucun article récupéré aujourd\'hui.</p>'
    films_html = "".join(movie_card_html(f) for f in films) if films else '<p class="empty-state">Aucune sortie cinéma trouvée.</p>'
    albums_html = "".join(album_item_html(a) for a in albums) if albums else '<p class="empty-state">Aucun nouvel album trouvé cette semaine.</p>'
    angers_html = "".join(event_item_html(e) for e in evenements_angers) if evenements_angers else '<p class="empty-state">Rien de programmé pour l\'instant.</p>'
    nantes_html = "".join(event_item_html(e) for e in evenements_nantes) if evenements_nantes else '<p class="empty-state">Rien de programmé pour l\'instant.</p>'

    now_label = datetime.now().strftime("%d/%m/%Y à %Hh%M")

    html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Le digest du jour</title>
<style>
  :root {{
    --paper: #fdfaf3;
    --ink: #1d1b16;
    --ink-soft: #5c5648;
    --rule: #c9bfa5;
    --accent: #9c2b2b;
    --accent-soft: #f4e2e2;
    --serif: 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--paper);
    color: var(--ink);
    font-family: var(--sans);
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }}

  .wrap {{
    max-width: 1040px;
    margin: 0 auto;
    padding: 0 24px 100px;
  }}

  /* ---------- MASTHEAD ---------- */
  header.masthead {{
    text-align: center;
    padding: 48px 0 28px;
    border-bottom: 4px double var(--ink);
    margin-bottom: 36px;
  }}

  .masthead__date {{
    font-family: var(--sans);
    font-size: 12px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }}

  h1.masthead__title {{
    font-family: var(--serif);
    font-size: clamp(38px, 6vw, 60px);
    font-weight: 700;
    letter-spacing: -0.01em;
  }}

  .masthead__sub {{
    font-family: var(--serif);
    font-style: italic;
    font-size: 15px;
    color: var(--ink-soft);
    margin-top: 8px;
  }}

  .masthead__updated {{
    font-size: 11px;
    color: var(--ink-soft);
    margin-top: 14px;
    opacity: 0.75;
  }}

  /* ---------- SECTIONS ---------- */
  section.block {{
    margin-bottom: 48px;
  }}

  .block__header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 8px;
    margin-bottom: 20px;
  }}

  .block__icon {{ font-size: 20px; }}

  h2.block__title {{
    font-family: var(--serif);
    font-size: 24px;
    font-weight: 700;
  }}

  .empty-state {{
    color: var(--ink-soft);
    font-style: italic;
    font-size: 14px;
  }}

  /* ---------- NEWS ---------- */
  .news-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
  }}

  .news-item__source {{
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent);
  }}

  .news-item__title {{
    font-family: var(--serif);
    font-size: 18px;
    margin: 6px 0 8px;
    line-height: 1.3;
  }}

  .news-item__title a {{
    color: var(--ink);
    text-decoration: none;
  }}

  .news-item__title a:hover {{ text-decoration: underline; }}

  .news-item__resume {{
    font-size: 13.5px;
    color: var(--ink-soft);
  }}

  /* ---------- MOVIES ---------- */
  .movies-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
  }}

  .movie-card {{
    display: flex;
    gap: 12px;
    background: #fff;
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 12px;
  }}

  .movie-card__poster {{
    width: 70px;
    height: 100px;
    object-fit: cover;
    border-radius: 4px;
    flex-shrink: 0;
  }}

  .movie-card__poster--placeholder {{
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-soft);
    font-size: 28px;
  }}

  .movie-card__title {{
    font-family: var(--serif);
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 4px;
  }}

  .movie-card__meta {{
    font-size: 11px;
    color: var(--ink-soft);
    margin-bottom: 6px;
  }}

  .movie-card__synopsis {{
    font-size: 12px;
    color: var(--ink-soft);
    line-height: 1.4;
  }}

  /* ---------- ALBUMS ---------- */
  .albums-list, .events-list {{
    list-style: none;
  }}

  .album-item, .event-item {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px dashed var(--rule);
  }}

  .album-item__icon {{ font-size: 18px; }}

  .album-item__title, .event-item__title {{
    font-weight: 600;
    font-size: 14px;
  }}

  .album-item__artist, .event-item__lieu {{
    font-size: 12px;
    color: var(--ink-soft);
  }}

  .event-item__date {{
    font-family: var(--serif);
    font-weight: 700;
    font-size: 13px;
    background: var(--accent-soft);
    color: var(--accent);
    padding: 3px 8px;
    border-radius: 4px;
    white-space: nowrap;
    flex-shrink: 0;
  }}

  /* ---------- EVENTS TWO-COLUMN ---------- */
  .events-cities {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 32px;
  }}

  .events-city__title {{
    font-family: var(--serif);
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 10px;
    color: var(--accent);
  }}

  footer.page-footer {{
    text-align: center;
    color: var(--ink-soft);
    font-size: 11px;
    padding-top: 30px;
    opacity: 0.75;
  }}

  @media (max-width: 600px) {{
    header.masthead {{ padding: 36px 0 22px; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header class="masthead">
      <div class="masthead__date">{date_label}</div>
      <h1 class="masthead__title">Le Digest du Jour</h1>
      <p class="masthead__sub">Actu, cinéma, musique &amp; sorties à Angers et Nantes</p>
      <p class="masthead__updated">Mis à jour le {now_label}</p>
    </header>

    <section class="block">
      <div class="block__header">
        <span class="block__icon">📰</span>
        <h2 class="block__title">À la une</h2>
      </div>
      <div class="news-grid">
        {news_html}
      </div>
    </section>

    <section class="block">
      <div class="block__header">
        <span class="block__icon">🎬</span>
        <h2 class="block__title">Au cinéma</h2>
      </div>
      <div class="movies-grid">
        {films_html}
      </div>
    </section>

    <section class="block">
      <div class="block__header">
        <span class="block__icon">💿</span>
        <h2 class="block__title">Nouveaux albums</h2>
      </div>
      <ul class="albums-list">
        {albums_html}
      </ul>
    </section>

    <section class="block">
      <div class="block__header">
        <span class="block__icon">📍</span>
        <h2 class="block__title">Sorties &amp; expositions</h2>
      </div>
      <div class="events-cities">
        <div>
          <h3 class="events-city__title">Angers</h3>
          <ul class="events-list">{angers_html}</ul>
        </div>
        <div>
          <h3 class="events-city__title">Nantes</h3>
          <ul class="events-list">{nantes_html}</ul>
        </div>
      </div>
    </section>

    <footer class="page-footer">
      Généré automatiquement chaque jour · Sources : RSS France Info &amp; France 24, TMDB, MusicBrainz, Open Data Nantes Métropole &amp; OpenAgenda
    </footer>
  </div>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    sample_history = [{
        "date": datetime.now().strftime("%Y-%m-%d"),
        "news": [
            {"source": "France Info", "titre": "Exemple de titre d'actualité", "resume": "Court résumé de l'article pour donner une idée du contenu affiché.", "lien": "https://example.com"},
        ],
        "films": [
            {"titre": "Film Exemple", "date_sortie": "2026-06-20", "synopsis": "Synopsis du film à titre d'exemple pour le test de rendu.", "note": 7.2, "affiche": None},
        ],
        "albums": [
            {"titre": "Album Exemple", "artiste": "Artiste Test", "date_sortie": "2026-06-19"},
        ],
        "evenements": [
            {"titre": "Exposition Test", "lieu": "Musée des Beaux-Arts", "date_debut": "2026-06-25", "ville": "Angers"},
            {"titre": "Concert Test", "lieu": "Stereolux", "date_debut": "2026-06-27", "ville": "Nantes"},
        ],
    }]
    generate_dashboard(sample_history, Path("docs/index.html"))
    print("OK - test généré dans docs/index.html")
