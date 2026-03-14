from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import InlineKeyboardButton, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.handlers import (
    aggiorna_selezione,
    button_handler,
    cancel,
    crea_tastiera_con_spunte,
    start,
)

# --- TEST della logica di formattazione ---

CASI_DI_TEST_TASTIERA = [
    ({}, [], 3, []),
    (
        {"Q_UNO": "Borgo", "Q_DUE": "Librino"},
        [],
        3,
        [
            [
                InlineKeyboardButton("Borgo", callback_data="Q_UNO"),
                InlineKeyboardButton("Librino", callback_data="Q_DUE"),
            ]
        ],
    ),
    (
        {"Q_UNO": "Borgo", "Q_DUE": "Librino", "Q_TRE": "Cibali"},
        ["Borgo"],
        3,
        [
            [
                InlineKeyboardButton("✅ Borgo", callback_data="Q_UNO"),
                InlineKeyboardButton("Librino", callback_data="Q_DUE"),
                InlineKeyboardButton("Cibali", callback_data="Q_TRE"),
            ]
        ],
    ),
    (
        {"Q_UNO": "Centro", "Q_DUE": "Periferia"},
        ["Catania - Centro"],
        3,
        [
            [
                InlineKeyboardButton("✅ Centro", callback_data="Q_UNO"),
                InlineKeyboardButton("Periferia", callback_data="Q_DUE"),
            ]
        ],
    ),
    (
        {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"},
        [],
        2,
        [
            [
                InlineKeyboardButton("A", callback_data="1"),
                InlineKeyboardButton("B", callback_data="2"),
            ],
            [
                InlineKeyboardButton("C", callback_data="3"),
                InlineKeyboardButton("D", callback_data="4"),
            ],
            [InlineKeyboardButton("E", callback_data="5")],
        ],
    ),
]


@pytest.mark.parametrize(
    "dizionario_dati, lista_selezionati, colonne, risultato_atteso",
    CASI_DI_TEST_TASTIERA,
)
def test_crea_tastiera_con_spunte(
    dizionario_dati, lista_selezionati, colonne, risultato_atteso
):
    tastiera_generata = crea_tastiera_con_spunte(
        dizionario_dati, lista_selezionati, colonne
    )
    assert tastiera_generata == risultato_atteso


# Mock di un sottomenù
DIZ_TOPIC_MOCK = {
    "TOPIC_CRONACA": "Cronaca",
    "TOPIC_SPORT": "Sport",
    "TOPIC_TUTTI": "Tutti i topics",
}
CHIAVE_TUTTI = "TOPIC_TUTTI"

CASI_DI_TEST_SELEZIONE = [
    ([], "TOPIC_CRONACA", "", ["Cronaca"]),
    (["Cronaca", "Sport"], "TOPIC_CRONACA", "", ["Sport"]),
    ([], "TOPIC_TUTTI", "", ["Cronaca", "Sport"]),
    (["Meteo", "Cronaca", "Sport"], "TOPIC_TUTTI", "", ["Meteo"]),
]


@pytest.mark.parametrize(
    "lista_iniziale, data_key, prefisso, risultato_atteso", CASI_DI_TEST_SELEZIONE
)
def test_aggiorna_selezione(lista_iniziale, data_key, prefisso, risultato_atteso):
    lista_target = lista_iniziale.copy()
    risultato = aggiorna_selezione(
        lista_target, data_key, DIZ_TOPIC_MOCK, CHIAVE_TUTTI, prefisso
    )
    assert risultato == risultato_atteso


# --- TEST del telegram handlers ---


@pytest.mark.asyncio
async def test_start_utente_non_in_db(mocker):
    mock_db = mocker.patch("bot.handlers.check_user", return_value=None)
    mocker.patch("bot.handlers.get_menu_home", return_value="FINTO_MENU")

    update = MagicMock(spec=Update)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Mario"
    update.message.reply_text = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}

    await start(update, context)

    assert context.user_data["preferenze"] == {"zone": [], "topics": []}
    mock_db.assert_called_once_with(12345)
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_cancel(mocker):
    mock_db_cancella = mocker.patch("bot.handlers.cancella_utente")

    update = MagicMock(spec=Update)
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {"preferenze": {"zone": ["Catania"], "topics": ["Sport"]}}

    await cancel(update, context)

    mock_db_cancella.assert_called_once_with(12345)
    assert context.user_data["preferenze"] == {"zone": [], "topics": []}


@pytest.mark.asyncio
async def test_button_handler_errore_nessuna_zona(mocker):
    update = MagicMock(spec=Update)
    query = AsyncMock()
    update.callback_query = query
    query.data = "VAI_AI_TOPIC"

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {"preferenze": {"zone": [], "topics": []}}

    await button_handler(update, context)

    query.answer.assert_called_once_with(
        "⚠️ Seleziona almeno una zona!", show_alert=True
    )


@pytest.mark.asyncio
async def test_button_handler_navigazione_quartieri(mocker):
    mocker.patch("bot.handlers.get_menu_quartieri", return_value="TASTIERA_QUARTIERI")

    update = MagicMock(spec=Update)
    query = AsyncMock()
    update.callback_query = query
    query.data = "MENU_CATANIA"
    update.effective_user.id = 123

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {"preferenze": {"zone": [], "topics": []}}

    await button_handler(update, context)

    query.edit_message_text.assert_called_once_with(
        "Seleziona i Quartieri di Catania:", reply_markup="TASTIERA_QUARTIERI"
    )


@pytest.mark.asyncio
async def test_button_handler_salvataggio_finale(mocker):
    mock_salva_db = mocker.patch("bot.handlers.salva_preferenze")

    update = MagicMock(spec=Update)
    update.effective_user.id = 999
    update.effective_user.first_name = "Anna"
    query = AsyncMock()
    update.callback_query = query
    query.data = "SALVA_TUTTO"

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {"preferenze": {"zone": ["Acireale"], "topics": ["Sport"]}}

    await button_handler(update, context)

    mock_salva_db.assert_called_once_with(999, "Anna", "Sport", "Acireale")
    assert query.edit_message_text.called


@pytest.mark.asyncio
async def test_button_handler_bad_request_ignorata(mocker):
    update = MagicMock(spec=Update)
    query = AsyncMock()
    update.callback_query = query
    query.data = "MENU_CATANIA"
    update.effective_user.id = 123

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {"preferenze": {"zone": [], "topics": []}}

    query.edit_message_text.side_effect = BadRequest("Message is not modified")

    # Non deve sollevare eccezioni
    await button_handler(update, context)


@pytest.mark.asyncio
async def test_button_handler_topic_selection(mocker):
    """Test specifico per la nuova funzione di gestione topic"""
    mocker.patch("bot.handlers.get_menu_topics", return_value="MENU_TOPIC")

    update = MagicMock(spec=Update)
    query = AsyncMock()
    update.callback_query = query
    query.data = "TOPIC_CRONACA"  # Simuliamo un topic valido
    update.effective_user.id = 123

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    # Mock dei dati necessari
    context.user_data = {"preferenze": {"zone": ["Catania"], "topics": []}}

    await button_handler(update, context)

    # Verifica che il messaggio sia stato aggiornato
    assert query.edit_message_text.called

    # Recuperiamo gli argomenti della chiamata in modo sicuro
    args, kwargs = query.edit_message_text.call_args

    # Cerchiamo il testo: potrebbe essere il primo argomento posizionale o nel kwarg 'text'
    testo_inviato = kwargs.get("text") if "text" in kwargs else args[0]

    assert "Seleziona gli argomenti:" in testo_inviato
>>>>>>> 894099c (test: fix test failures, remove unused imports and update coverage for new handlers)
