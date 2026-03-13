import pytest 
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import InlineKeyboardButton

from bot.handlers import crea_tastiera_con_spunte, aggiorna_selezione, get_menu_home, get_menu_quartieri, get_menu_topics, start, cancel, button_handler
from telegram.error import BadRequest

# --- TEST della logica di formattazione ---

CASI_DI_TEST_TASTIERA = [
    #CASO 1: dizionario vuoto
    ({},[],3,[]),
    
    #CASO 2: nessuna casella spuntata
    (
        {"Q_UNO": "Borgo", "Q_DUE": "Librino"}, 
        [],
        3,
        [
            [InlineKeyboardButton("Borgo", callback_data="Q_UNO"),
            InlineKeyboardButton("Librino", callback_data="Q_DUE")]
        ]
    ), 

    #CASO 3: almeno una casella spuntata    
    (
        {"Q_UNO": "Borgo", "Q_DUE": "Librino","Q_TRE": "Cibali"}, 
        ["Borgo"],
        3,
        [
            [InlineKeyboardButton("✅ Borgo", callback_data="Q_UNO"),
            InlineKeyboardButton("Librino", callback_data="Q_DUE"),
            InlineKeyboardButton("Cibali", callback_data="Q_TRE")]
        ]
    ), 

     #CASO 4: logica con prefisso "Catania -"
      (
        {"Q_UNO": "Centro", "Q_DUE": "Periferia"}, 
        ["Catania - Centro"],
        3,
        [
            [InlineKeyboardButton("✅ Centro", callback_data="Q_UNO"),
            InlineKeyboardButton("Periferia", callback_data="Q_DUE")]
        ]
    ),  

    # Caso 5: paginazione con 5 elementi impaginati a 2 colonne creano 3 righe
    (
        {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}, 
        [], 
        2, 
        [
            [InlineKeyboardButton("A", callback_data="1"), InlineKeyboardButton("B", callback_data="2")],
            [InlineKeyboardButton("C", callback_data="3"), InlineKeyboardButton("D", callback_data="4")],
            [InlineKeyboardButton("E", callback_data="5")]
        ]
    ),

    # CASO 6: selezione multipla 
    (
        {"Q_UNO": "Centro", "Q_DUE": "Borgo", "Q_TRE": "Librino"}, 
        ["Catania - Centro", "Librino"], 
        3,
        [
            [InlineKeyboardButton("✅ Centro", callback_data="Q_UNO"),
             InlineKeyboardButton("Borgo", callback_data="Q_DUE"),
             InlineKeyboardButton("✅ Librino", callback_data="Q_TRE")]
        ]
    )
]

@pytest.mark.parametrize("dizionario_dati, lista_selezionati, colonne, risultato_atteso", CASI_DI_TEST_TASTIERA)
def test_crea_tastiera_con_spunte(dizionario_dati, lista_selezionati, colonne, risultato_atteso):
    """
    Test per verificare la corretta generazione della tastiera, 
    l'assegnazione delle spunte e l'impaginazione dinamica in base alle colonne.
    """
    tastiera_generata = crea_tastiera_con_spunte(dizionario_dati, lista_selezionati, colonne)
    assert tastiera_generata == risultato_atteso

# Mock di un sottomenù 
DIZ_TOPIC_MOCK = {   
    "TOPIC_CRONACA": "Cronaca",
    "TOPIC_SPORT": "Sport",
    "TOPIC_TUTTI": "Tutti i topics"
}
CHIAVE_TUTTI = "TOPIC_TUTTI"

CASI_DI_TEST_SELEZIONE = [
    # Attivazione o disattivazione singolo elemento
    ([], "TOPIC_CRONACA", "", ["Cronaca"]),
    (["Cronaca", "Sport"], "TOPIC_CRONACA", "", ["Sport"]),
    
    # Attivazione o disattivazione singolo elemento CON prefisso (es. "Provincia -")
    ([], "TOPIC_SPORT", "Provincia: ", ["Provincia: Sport"]),
    (["Provincia: Cronaca", "Provincia: Sport"], "TOPIC_SPORT", "Provincia: ", ["Provincia: Cronaca"]),
    
    # Seleziona/Deseleziona Tutti
    ([], "TOPIC_TUTTI", "", ["Cronaca", "Sport"]),
    (["Cronaca"], "TOPIC_TUTTI", "", ["Cronaca", "Sport"]),
    (["Cronaca", "Sport"], "TOPIC_TUTTI", "", []),
    
    # Attivazione o disattivazione "Tutti" CON prefisso
    ([], "TOPIC_TUTTI", "Catania - ", ["Catania - Cronaca", "Catania - Sport"]),
    (["Catania - Cronaca", "Catania - Sport"], "TOPIC_TUTTI", "Catania - ", []),

    # L'utente ha già selezionato "Meteo", aggiunge "Sport" ma "Meteo" deve restare.
    (["Meteo"], "TOPIC_SPORT", "", ["Meteo", "Sport"]),
    
    # L'utente ha "Meteo", "Cronaca" e "Sport". Clicca "Deseleziona Tutti i Topic".
    # La funzione deve rimuovere Cronaca e Sport, ma SALVARE "Meteo".
    (["Meteo", "Cronaca", "Sport"], "TOPIC_TUTTI", "", ["Meteo"]),    
]

@pytest.mark.parametrize("lista_iniziale, data_key, prefisso, risultato_atteso", CASI_DI_TEST_SELEZIONE)
def test_aggiorna_selezione(lista_iniziale, data_key, prefisso, risultato_atteso):
    """
    Test per verificare la logica di aggiunta/rimozione singola
    e la selezione/deselezione cumulativa.
    """
    lista_target = lista_iniziale.copy()

    risultato = aggiorna_selezione(
        lista_target=lista_target, 
        data_key=data_key, 
        dizionario=DIZ_TOPIC_MOCK, 
        chiave_tutti=CHIAVE_TUTTI, 
        prefisso=prefisso
    )

    assert risultato == risultato_atteso

# ---TEST del telegram handlers ---

@pytest.mark.asyncio
async def test_start_utente_non_in_db(mocker): 
    # mock del database, poniamo check_user = none perciò l'utente non è trovato
    mock_db = mocker.patch("bot.handlers.check_user", return_value = None)

    # mock del menù
    mock_menu = mocker.patch("bot.handlers.get_menu_home", return_value = "FINTO_MENU")

    # finto utente 
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.first_name = "Mario"
    update.message.reply_text = AsyncMock()

    # finto context 
    context = MagicMock()
    # dizionario vuoto
    context.user_data = {}

    # esecuzione della funzione passandogli i finti update e context
    await start(update, context)

    # test 1: verifica della creazione della struttura dati vuota 
    assert context.user_data['preferenze'] == {"zone": [], "topics": []}

    # test 2: controllato dell'ID corretto nel DB
    mock_db.assert_called_once_with(12345) 

    # test 3: controllo della generazione del menu passandogli le zone attuali
    mock_menu.assert_called_once_with([])
    
    # test 4: verifica del invio del messaggio di benvenuto all'utente
    update.message.reply_text.assert_called_once_with(
        "Ciao Mario! Benvenuto.\nSeleziona i Comuni di tuo interesse (puoi sceglierne più di uno):",
        reply_markup="FINTO_MENU"
    )

@pytest.mark.asyncio
async def test_start_utente_gia_registrato(mocker):   
    # check_user trova l'utente nel database
    dati_finti_dal_db = (["Catania"], ["Sport", "Cronaca"])
    mock_db = mocker.patch("bot.handlers.check_user", return_value=dati_finti_dal_db)
    
    # mock del menù
    mock_menu = mocker.patch("bot.handlers.get_menu_home", return_value="FINTO_MENU")
    
    # finto utente
    update = MagicMock()
    update.effective_user.id = 99999
    update.effective_user.first_name = "Luigi"
    update.message.reply_text = AsyncMock()
    
    # finto context 
    context = MagicMock()
    context.user_data = {}
    
    await start(update, context)
    
    # test 1: controllo del caricamento dei dati dal DB nel context.user_data dell'utente
    assert context.user_data['preferenze'] == {"zone": ["Catania"], "topics": ["Sport", "Cronaca"]}
    
    # test 2: controllo della creazione del menu passandogli la zona recuperata dal DB
    mock_menu.assert_called_once_with(["Catania"])

@pytest.mark.asyncio
async def test_start_utente_con_sessione_attiva(mocker):
    """
    Se l'utente ha già 'preferenze' nel context 
    """
    # mock del database
    mock_db = mocker.patch("bot.handlers.check_user") 
    # mock del menù
    mock_menu = mocker.patch("bot.handlers.get_menu_home", return_value="FINTO_MENU")
    
    # finto utente
    update = MagicMock()
    update.effective_user.id = 77777
    update.effective_user.first_name = "Giulia"
    update.message.reply_text = AsyncMock()
    
    # Prepariamo un context che ha già le preferenze salvate
    context = MagicMock()
    context.user_data = {
        'preferenze': {
            'zone': ["Borgo"], 
            'topics': ["Meteo"]
        }
    }

    await start(update, context)
    
    # test 1: Il database non deve essere stato chiamato
    mock_db.assert_not_called()
    
    # test 2. Il menu deve essere stato generato con le zone già in memoria 
    mock_menu.assert_called_once_with(["Borgo"])

@pytest.mark.asyncio
async def test_cancel(mocker): 
    # mock dela funzione del database che elimina l'utente
    mock_db_cancella = mocker.patch("bot.handlers.cancella_utente")
    
    # finto "update" simulando un utente
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    
    # finto context 
    context = MagicMock()
    context.user_data = {
        'preferenze': {
            'zone': ['Catania', 'Acireale'], 
            'topics': ['Sport']
        }
    }
    
    await cancel(update, context)
    
    # test 1: controllo della chiamata alla funzione del DB passandogli l'ID giusto
    mock_db_cancella.assert_called_once_with(12345)
    
    # test 2: verifica che la lista si stata svuotata nel context
    assert context.user_data['preferenze'] == {"zone": [], "topics": []}
    
    # test 3: controllo nel invio del messaggio all'utente
    update.message.reply_text.assert_called_once_with(
        "🗑️ Il tuo account è stato eliminato con successo!\n\n"
        "Se desideri ricominciare la configurazione, clicca su /start."
    )

# TEST DEL BUTTON_HANDLER 

@pytest.mark.asyncio
async def test_button_handler_errore_nessuna_zona(mocker):
    """
    Simulazione del click su "VAI_AI_TOPIC" quando la lista 'zone' è ancora vuota.
    """
    # finti oggetti 
    update = MagicMock()
    query = AsyncMock()
    update.callback_query = query
    query.data = "VAI_AI_TOPIC"
    
    context = MagicMock()
    # zone e topic vuoti
    context.user_data = {'preferenze': {"zone": [], "topics": []}} 
    
    # eseguiamo l'handler
    await button_handler(update, context)
    
    # test della verifica
    query.answer.assert_called_once_with("⚠️ Seleziona almeno una zona prima di proseguire!", show_alert=True)
    # messaggio non modificato
    query.edit_message_text.assert_not_called()


@pytest.mark.asyncio
async def test_button_handler_navigazione_quartieri(mocker):
    """
    Simulazione del click su "MENU_CATANIA".
    """
    mock_get_quartieri = mocker.patch("bot.handlers.get_menu_quartieri", return_value="TASTIERA_QUARTIERI")
    
    # finti oggetti 
    update = MagicMock()
    query = AsyncMock()
    update.callback_query = query
    query.data = "MENU_CATANIA"
    
    context = MagicMock()
    # zone e topic vuoti
    context.user_data = {'preferenze': {"zone": [], "topics": []}}
    
    await button_handler(update, context)
    
    # test: ricezione del click senza errori
    query.answer.assert_called_once_with()
    # cambio del testo e della tastiera
    query.edit_message_text.assert_called_once_with(
        "Seleziona i Quartieri di Catania:",
        reply_markup="TASTIERA_QUARTIERI"
    )


@pytest.mark.asyncio
async def test_button_handler_click_singolo_comune(mocker):
    """
    Simulazione del click su un comune
    """
    #aggiumgiamo "Acireale"
    mock_aggiorna = mocker.patch("bot.handlers.aggiorna_selezione", return_value=["Acireale"])
    mock_get_home = mocker.patch("bot.handlers.get_menu_home", return_value="TASTIERA_HOME")
    
    # finti oggetti 
    update = MagicMock()
    query = AsyncMock()
    update.callback_query = query
    query.data = "COM_ACIREALE"
    
    context = MagicMock()
    # zone e topic vuoti
    context.user_data = {'preferenze': {"zone": [], "topics": []}}
    
    await button_handler(update, context)
    
    # test 1: controllo del utilizzo della funzione aggiorna_selezione per calcolare le nuove liste
    mock_aggiorna.assert_called_once()
    
    # test 2: verifica l'aggiornato della nuova lista di preferenze dell'utente 
    assert context.user_data['preferenze']['zone'] == ["Acireale"]
    
    # test 3: controllo dell'interfaccia con la nuova lista di preferenze selezionate
    query.edit_message_text.assert_called_once_with(
        "Seleziona i Comuni:", 
        reply_markup="TASTIERA_HOME"
    )


@pytest.mark.asyncio
async def test_button_handler_salvataggio_finale(mocker):
    """
    Simulazione del click su "SALVA_TUTTO" con dati validi
    """
    # Mock della funzione del Database
    mock_salva_db = mocker.patch("bot.handlers.salva_preferenze")
    
    # finto utente
    update = MagicMock()
    update.effective_user.id = 999
    update.effective_user.first_name = "Anna"
    
    # finti oggetti
    query = AsyncMock()
    update.callback_query = query
    query.data = "SALVA_TUTTO"
    
    # aggiornamento del database
    context = MagicMock()
    context.user_data = {
        'preferenze': {
            "zone": ["Acireale", "Catania - Borgo"], 
            "topics": ["Sport", "Meteo"]
        }
    }
    
    await button_handler(update, context)
    
    # test 1: veriica della trasformazione delle liste in stringhe separate da virgole e del salvataggio sul DB
    mock_salva_db.assert_called_once_with(
        999, 
        "Anna", 
        "Sport, Meteo", 
        "Acireale, Catania - Borgo"
    )
    
    # test 2: verifica del invio del messaggio finale con il testo modificato
    mock_edit = query.edit_message_text
    mock_edit.assert_called_once()
    args, kwargs = mock_edit.call_args
    messaggio_inviato = args[0]
    assert "✅ **Configurazione Salvata!**" in messaggio_inviato
    assert "Acireale, Catania - Borgo" in messaggio_inviato


@pytest.mark.asyncio
async def test_button_handler_bad_request_ignorata(mocker):
    """
    Simulazione di un doppio tap veloce dell'utente.
    """
    # finti oggetti 
    update = MagicMock()
    query = AsyncMock()
    update.callback_query = query
    query.data = "MENU_CATANIA"
    
    context = MagicMock()
    context.user_data = {'preferenze': {"zone": [], "topics": []}}
    
    # lancio di un errore simulato
    query.edit_message_text.side_effect = BadRequest("Message is not modified")
    
    await button_handler(update, context)