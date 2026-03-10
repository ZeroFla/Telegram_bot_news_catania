import pytest
import sqlite3
import bot.database.database
from datetime import datetime, timedelta
import os

@pytest.fixture
def mock_db(monkeypatch):
    # Creo un db di test
    test_db = "test_db"
    monkeypatch.setattr(bot.database.database, "DB_PATH", test_db)
    
    # Inizializziamo il db
    bot.database.database.init_db()
    # A ogni funzione di test verrà creato un test_db, verrà usato e poi eliminato grazie a yield
    yield bot.database.database

    if os.path.exists(test_db):
        os.remove(test_db)

def test_salva_check_cancella_user(mock_db):
    # Dati di test
    user_id = 12345
    username = "ct_user"
    topics = "meteo, sport"
    comuni = "Catania, Gravina"

    mock_db.salva_preferenze(user_id, username, topics, comuni)
    pref = mock_db.check_user(user_id)
    # Test salva e check utenti
    assert pref is not False 
    comuni_ris, topics_ris = pref
    assert mock_db.check_user(2345) == False # Test utente non in DB
    assert comuni_ris == ["Catania", "Gravina"]
    assert topics_ris == ["meteo", "sport"]

    # Test cancella utente
    mock_db.cancella_utente(user_id)
    assert mock_db.check_user(user_id) == False

def test_check_news(mock_db):
    # Test check news
    id_news = "id_generico" 
    
    # Notizia nuova, quindi non è presente nel db, allora la salvo
    assert mock_db.check_news(id_news) is False 
    # Notizia già presente nel db
    assert mock_db.check_news(id_news) is True

def test_clean_db(mock_db):
    id_da_eliminare = 98767
    data_finta = datetime.now() - timedelta(days=8)
    # Inietto manualmente una news con timestamp alterato
    mock_db.execute_query("INSERT INTO news_inviate (id_news,time_stamp) VALUES (?,?)", (id_da_eliminare, data_finta.strftime("%Y-%m-%d %H:%M:%S")))
    # Inserisco una seconda news con timestamp regolare
    mock_db.check_news(76384)
    # Pulisco il DB
    mock_db.clean_db()
    # Test notizia più vecchia di 7 giorni 
    assert len(mock_db.execute_query("SELECT 1 FROM news_inviate WHERE id_news = ?", (id_da_eliminare,))) == 0
    # Testo notizia nuova
    assert len(mock_db.execute_query("SELECT 1 FROM news_inviate WHERE id_news = ?", (76384,))) == 1

def test_execute_query(mock_db):
    
    # Creo una tabella di test
    mock_db.execute_query("CREATE TABLE test (id INTEGER, nome TEXT)")
    # Inserisco dei dati
    mock_db.execute_query("INSERT INTO test (id,nome) VALUES (?,?)",(1,"Saro"))
    # Recupero i dati precedentemente inseriti
    test = mock_db.execute_query("SELECT nome FROM test WHERE id = ?", (1,))

    # Verifico la lughezza della lista
    assert len(test) == 1
    # Verifico che il nome sia corretto
    assert test[0][0] == "Saro"
