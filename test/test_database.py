import pytest
import sqlite3
import database

@pytest.fixture
def mock_db(monkeypatch):
    """
    Crea un database in memoria pulito per ogni test.
    Usa 'monkeypatch' per cambiare temporaneamente il DB_PATH del tuo modulo.
    """
    # Sovrascriviamo la variabile DB_PATH in database.py
    monkeypatch.setattr(database, "DB_PATH", ":memory:")
    
    # Inizializziamo il db
    database.init_db()
    
    return database

def test_salva_e_check_user(mock_db):
    # Dati di test
    user_id = 12345
    username = "ct_user"
    topics = "meteo, sport"
    comuni = "Catania, Gravina"

    mock_db.salva_preferenze(user_id, username, topics, comuni)
    comuni_res, topics_res = mock_db.check_user(user_id)

    assert comuni_res == ["Catania", "Gravina"]
    assert topics_res == ["meteo", "sport"]

def test_cancella_utente(mock_db):
    

def test_check_news_timestamp(mock_db):
    id_news = "notizia_etna_01"
    
    # Notizia nuova, quindi non è presente nel db, allora la salvo
    assert mock_db.check_news(id_news) is False 
    # Notizia già presente nel db
    assert mock_db.check_news(id_news) is True

def test_user_not_found(mock_db):
    # Utente non esistente
    assert mock_db.check_user(999999) is False
