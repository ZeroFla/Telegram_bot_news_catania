from news_bot import monitor_news_job
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_monitor_news_job_invio_corretto(capsys):
    # Creo un mock per la funzione asyncrona send_message
    mock_context = MagicMock()
    mock_context.bot.send_message = AsyncMock()

    # Definisco dei dati finti 
    news_finta = [{'link': 'https://www.youtube.com/watch?v=xvFZjo5PgG0', 'topic': 'Meteo', 'luogo': 'Napoli', 'titolo': 'Scuole chiuse a Napoli'}]
    utente_finto = [(12345, 'meteo', 'napoli')]

    # Definisco i valori di ritorno per i vari moduli già testati
    with patch('news_bot.ricerca_notizia', return_value=news_finta), \
         patch('news_bot.check_news', return_value=False), \
         patch('news_bot.clean_db') as mock_clean, \
         patch('news_bot.execute_query', return_value=utente_finto):

        # Eseguiamo la funzione
        await monitor_news_job(mock_context)
        
        # Verifichiamo che il database sia stato pulito
        mock_clean.assert_called_once()
        
        # Verifichiamo che il bot abbia inviato il messaggio
        mock_context.bot.send_message.assert_called()
        
        # Verifichiamo il contenuto del messaggio inviato
        args, kwargs = mock_context.bot.send_message.call_args
        assert kwargs['chat_id'] == 12345
        assert "Napoli" in kwargs['text']
        
        # Testo l'Exception
        mock_context.bot.send_message = AsyncMock(side_effect=Exception("Simulated Error"))
        await monitor_news_job(mock_context)
        
        # Verifichiamo che l'errore sia stato stampato
        captured = capsys.readouterr()
        assert "Errore invio: Simulated Error" in captured.out
