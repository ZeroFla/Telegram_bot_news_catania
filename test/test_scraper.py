from unittest.mock import Mock

import feedparser
import pytest
import requests

from scraper.catania_news import analizza_html, ricerca_notizia


# Parametrizzo i possibili html da analizzare
@pytest.mark.parametrize(
    "html_possibili, status_finto, localita_risultati",
    [
        (
            '<a class="u-nav-03 o-link-inverse" href="/notizie/tutte/" rel="nofollow">Roma</a>',
            200,
            "Roma",
        ),
        ("<html><body>Niente link qui</body></html>", 200, None),
        ("Errore", 404, None),
    ],
)
def test_analizza_html_successo(
    monkeypatch, html_possibili, status_finto, localita_risultati
):
    mock = Mock()
    mock.status_code = status_finto
    mock.text = html_possibili

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock)
    risultato = analizza_html("https://link-finto.com")
    assert risultato == localita_risultati


def test_analizza_html_eccezione(monkeypatch):
    # Testo l'exeption
    mock_crash = Mock()
    mock_crash.side_effect = requests.exceptions.ConnectionError(
        "Errore di rete simulato"
    )

    monkeypatch.setattr("requests.get", mock_crash)
    risultato = analizza_html("https://link-finto.com")

    assert risultato is None

    # Parametrizzo il feed rss


@pytest.mark.parametrize(
    "feed_possibili, html_possibili , localita_possibili",
    [
        (
            """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
        <channel>
            <item>
                <title>Referendum giustizia, Schifani plaude Marina Berlusconi</title>
                <link>https://www.cataniatoday.it/politica/referendum.html</link>
                <category>Politica</category>
                <enclosure url="https://immagine-test.jpg" length="1" type="image/jpeg"/>
                <description>Le dichiarazioni del governatore sulla riforma.</description>
            </item>
        </channel>
        </rss>
        """,
            '<a class="u-nav-03 o-link-inverse" href="/notizie/tutte/" rel="nofollow">Roma</a>',
            "Roma",
        ),
        (
            """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
        <channel>
            <item>
                <title>Referendum giustizia, Schifani plaude Marina Berlusconi</title>
                <link>https://www.cataniatoday.it/politica/referendum.html</link>
                <category>Politica</category>
                <enclosure url="https://immagine-test.jpg" length="1" type="image/jpeg"/>
                <description>Le dichiarazioni del governatore sulla riforma.</description>
            </item>
        </channel>
        </rss>
        """,
            '<a class="u-nav-03 o-link-inverse" href="/notizie/tutte/" rel="nofollow">Ultime Notizie</a>',
            "Catania",
        ),
        (
            """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
        <channel>
            <item>
                <title>Fermati 4 contrabbandieri a Paternò</title>
                <link>https://www.cataniatoday.it/politica/referendum.html</link>
                <category>Politica</category>
                <enclosure url="https://immagine-test.jpg" length="1" type="image/jpeg"/>
                <description>Le dichiarazioni del governatore sulla riforma.</description>
            </item>
        </channel>
        </rss>
        """,
            '<a class="u-nav-03 o-link-inverse" href="/notizie/tutte/" rel="nofollow">Ultime Notizie</a>',
            "Paternò",
        ),
    ],
)
def test_ricerca_successo(
    monkeypatch, feed_possibili, html_possibili, localita_possibili
):
    # Testo il caso in cui tutto sia corretto
    mock = Mock()
    mock.status_code = 200
    mock.text = html_possibili
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock)

    feed_finto = feedparser.parse(feed_possibili)
    monkeypatch.setattr("feedparser.parse", lambda *args, **kwargs: feed_finto)

    notizia = ricerca_notizia()
    assert notizia[0]["luogo"] == localita_possibili


def test_ricerca_notizia_feed_vuoto(monkeypatch):
    # Testo un caso in cui il feed sia vuoto
    mock_feed = Mock()
    mock_feed.entries = []
    monkeypatch.setattr(
        "scraper.catania_news.feedparser.parse", lambda *args, **kwargs: mock_feed
    )

    risultato = ricerca_notizia()

    assert risultato == []
    assert len(risultato) == 0
