import os
import re
import sys
from typing import Dict, List, Optional

import feedparser  # type: ignore
import requests
from bs4 import BeautifulSoup, Tag  # type: ignore

from bot.config import COMUNI_PROVINCIA, QUARTIERI_CATANIA

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Definiamo i tipi per chiarezza
Notizia = Dict[str, Optional[str]]

tutti_i_luoghi: List[str] = list(QUARTIERI_CATANIA.values()) + list(COMUNI_PROVINCIA.values())

RSS_URL = "https://www.cataniatoday.it/rss"


def analizza_html(url_notizia: str) -> Optional[str]:
    localita_trovata: Optional[str] = None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url_notizia, headers=headers, timeout=3)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        link_loc = soup.find("a", href=re.compile(r"^/notizie/[a-z-]+/$"))
        if link_loc and isinstance(link_loc, Tag):
            localita_trovata = str(link_loc.get_text()).replace("/", "").strip().title()

    except Exception as e:
        print(f"⚠️ Errore: {e}")

    return localita_trovata


# --- RECUPERO LE NOTIZIE ---
def ricerca_notizia(notizie: int = 10) -> List[Notizia]:
    feed = feedparser.parse(RSS_URL)
    news_list: List[Notizia] = []

    for entry in feed.entries[:notizie]:

        link = str(getattr(entry, "link", ""))
        titolo = str(getattr(entry, "title", "Senza titolo"))

        localita = analizza_html(link)
        # --- VERIFICO IL NOME CORRETTO DELLA LOCALITÀ ---
        if localita == "Ultime Notizie":
            trovati = next(
                (v for v in tutti_i_luoghi if v.lower() in titolo.lower()),
                "Catania",
            )
            localita = trovati

        tags = getattr(entry, "tags", [])
        topic = tags[0].term if tags else "Cronaca"

        enclosures = getattr(entry, "enclosures", [])
        immagine = enclosures[0].href if enclosures else None

        articolo: Notizia = {
            "titolo": titolo,
            "link": link,
            "topic": str(topic),
            "immagine": immagine,
            "luogo": localita,
            "riassunto": str(getattr(entry, "description", "")),
        }
        news_list.append(articolo)

    return news_list
