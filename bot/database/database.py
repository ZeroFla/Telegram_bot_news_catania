import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bot.db')

def execute_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall()

def init_db():
    # Tabella Utenti
    execute_query('''
        CREATE TABLE IF NOT EXISTS utenti (
            id_telegram INTEGER PRIMARY KEY,
            username TEXT,
            topics TEXT,
            comuni TEXT
        )''')
    # Tabella News
    execute_query('''
        CREATE TABLE IF NOT EXISTS news_inviate (
            id_news TEXT PRIMARY KEY,
            time_stamp TEXT
        )''')
    print("Inizializzazione DB completata")

def salva_preferenze(user_id, username, topics, comuni):
    # Aggiorna o inserisce le preferenze dell'utente
    query = "INSERT OR REPLACE INTO utenti (id_telegram, username, topics, comuni) VALUES (?, ?, ?, ?)"
    execute_query(query, (user_id, username, topics, comuni))
    print(f"Preferenze aggiornate per {username}")

def cancella_preferenze(user_id):
    #Rimuove l'utente e le sue preferenze dal database.
    query = "DELETE FROM utenti WHERE id_telegram = ?"
    execute_query(query, (user_id,))
    print(f"Preferenze cancellate per {user_id}")

def check_news(id_news):
    # Controlla se la news è già stata inviata, se no la aggiunge con l'ora attuale
    query = "SELECT 1 FROM news_inviate WHERE id_news = ?"
    
    if execute_query(query, (id_news,)):
        return True
    
    # Se non c'è, la aggiungiamo includendo il timestamp attuale
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query("INSERT INTO news_inviate (id_news, time_stamp) VALUES (?, ?)", (id_news, now))
    return False

def clean_db():
    # Elimina notizie più vecchie di 7 giorni
    query = "DELETE FROM news_inviate WHERE time_stamp < datetime('now', '-7 days')"
    execute_query(query)
    print("Pulizia database effettuata")

def check_user(id_telegram):
    # Verifica che un'utente sia già registrato nel DB
    risultato = execute_query("SELECT comuni,topics FROM utenti WHERE id_telegram = ?", (id_telegram,))
        
    if risultato:
        comuni_str, topics_str = risultato[0]
    
        # Trasformo le stringhe in liste eliminando spazi extra
        lista_comuni = [c.strip() for c in comuni_str.split(",")] if comuni_str else []
        lista_topics = [t.strip() for t in topics_str.split(",")] if topics_str else []

        return lista_comuni, lista_topics

    return False
