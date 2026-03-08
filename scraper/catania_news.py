import sys, os
import feedparser
import requests
from bs4 import BeautifulSoup
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.config import QUARTIERI_CATANIA, COMUNI_PROVINCIA
tutti_i_luoghi = list(QUARTIERI_CATANIA.values()) + list(COMUNI_PROVINCIA.values())

RSS_URL = "https://www.cataniatoday.it/rss"

def analizza_html(url_notizia):
    localita_trovata = None
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_notizia, headers=headers, timeout=3)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, 'html.parser')

        link_loc = soup.find('a', href=re.compile(r'^/notizie/[a-z-]+/$'))
        if link_loc:
            localita_trovata = link_loc.get_text().replace("/", "").strip().title()
            
    except Exception as e:
        print(f"⚠️ Errore: {e}")

    return localita_trovata
# --- RECUPERO LE NOTIZIE ---
def ricerca_notizia():
    feed = feedparser.parse(RSS_URL)
    news_list=[]

    for entry in feed.entries[:30]:
        localita = analizza_html(entry.link)
        # --- VERIFICO IL NOME CORRETTO DELLA LOCALITÀ ---
        if localita == "Ultime Notizie":
            trovati = next((v for v in tutti_i_luoghi if v.lower() in str(entry.title).lower()), "Catania")
            localita = trovati

        articolo = {
            "titolo": entry.title,
            "link": entry.link,
            "topic": entry.tags[0].term,
           "immagine": entry.enclosures[0].href,
            "luogo": localita,
            "riassunto": entry.description
            }
        news_list.append(articolo)

    return news_list

