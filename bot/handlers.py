import logging
from typing import Any, Dict, List, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.config import COMUNI_PROVINCIA, QUARTIERI_CATANIA, TOPIC_DISPONIBILI
from bot.database.database import cancella_utente, check_user, salva_preferenze

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def crea_tastiera_con_spunte(
    dizionario_dati: Dict[str, str], lista_selezionati: List[str], colonne: int = 3
) -> List[List[InlineKeyboardButton]]:
    keyboard = []
    riga = []

    for chiave, nome_chiaro in dizionario_dati.items():
        is_selected = False

        if nome_chiaro in lista_selezionati:
            is_selected = True
        elif f"Catania - {nome_chiaro}" in lista_selezionati:
            is_selected = True

        testo = f"✅ {nome_chiaro}" if is_selected else nome_chiaro
        riga.append(InlineKeyboardButton(testo, callback_data=chiave))

        if len(riga) == colonne:
            keyboard.append(riga)
            riga = []

    if riga:
        keyboard.append(riga)
    return keyboard


def aggiorna_selezione(
    lista_target: List[str],
    data_key: str,
    dizionario: Dict[str, str],
    chiave_tutti: str,
    prefisso: str = "",
) -> List[str]:
    if data_key == chiave_tutti:
        tutti_i_valori = []
        for k, v in dizionario.items():
            if k == chiave_tutti:
                continue
            valore_db = f"{prefisso}{v}" if prefisso else v
            tutti_i_valori.append(valore_db)

        elementi_gia_presenti = [x for x in tutti_i_valori if x in lista_target]

        if len(elementi_gia_presenti) == len(tutti_i_valori):
            for item in tutti_i_valori:
                if item in lista_target:
                    lista_target.remove(item)
        else:
            for item in tutti_i_valori:
                if item not in lista_target:
                    lista_target.append(item)
        return lista_target
    else:
        valore = f"{prefisso}{dizionario[data_key]}" if prefisso else dizionario[data_key]
        if valore in lista_target:
            lista_target.remove(valore)
        else:
            lista_target.append(valore)
        return lista_target


def get_menu_home(zone_selezionate: List[str]) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("🌋 CATANIA CENTRO (Quartieri) 🏙️", callback_data="MENU_CATANIA")]]
    keyboard.extend(crea_tastiera_con_spunte(COMUNI_PROVINCIA, zone_selezionate, colonne=3))
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)


def get_menu_quartieri(zone_selezionate: List[str]) -> InlineKeyboardMarkup:
    keyboard = crea_tastiera_con_spunte(QUARTIERI_CATANIA, zone_selezionate, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)


def get_menu_topics(topics_selezionati: List[str]) -> InlineKeyboardMarkup:
    keyboard = crea_tastiera_con_spunte(TOPIC_DISPONIBILI, topics_selezionati, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("💾 SALVA E CONCLUDI", callback_data="SALVA_TUTTO")])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if not user or not message:
        return

    if "preferenze" not in context.user_data:  # type: ignore
        context.user_data["preferenze"] = {"zone": [], "topics": []}  # type: ignore
        data_db = check_user(user.id)
        if data_db:
            zone_salvate, topics_salvati = data_db
            context.user_data["preferenze"]["zone"] = zone_salvate  # type: ignore
            context.user_data["preferenze"]["topics"] = topics_salvati  # type: ignore

    user_prefs = context.user_data["preferenze"]  # type: ignore
    zone_attuali = cast(List[str], user_prefs["zone"])

    await message.reply_text(
        f"Ciao {user.first_name}! Benvenuto.\nSeleziona i Comuni di tuo interesse:",
        reply_markup=get_menu_home(zone_attuali),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if not user or not message:
        return

    cancella_utente(user.id)
    context.user_data["preferenze"] = {"zone": [], "topics": []}  # type: ignore

    await message.reply_text("🗑️ Il tuo account è stato eliminato con successo!\n\n" "Clicca su /start per ricominciare.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    user = update.effective_user
    if not user:
        return

    if "preferenze" not in context.user_data:  # type: ignore
        context.user_data["preferenze"] = {"zone": [], "topics": []}  # type: ignore

    user_data = cast(Dict[str, List[str]], context.user_data["preferenze"])  # type: ignore

    # Spostiamo i controlli di validazione in una funzione dedicata
    if not await _is_valid_action(query, query.data, user_data):
        return

    await query.answer()

    try:
        await _router_navigazione(query, query.data, user, user_data)
    except BadRequest:
        pass


async def _is_valid_action(query: Any, data: str, user_data: Dict[str, List[str]]) -> bool:
    if data == "VAI_AI_TOPIC" and not user_data["zone"]:
        await query.answer("⚠️ Seleziona almeno una zona!", show_alert=True)
        return False
    if data == "SALVA_TUTTO" and not user_data["topics"]:
        await query.answer("⚠️ Seleziona almeno un argomento!", show_alert=True)
        return False
    return True


async def _router_navigazione(query: Any, data: str, user: Any, user_data: Dict[str, List[str]]) -> None:
    if data in ["MENU_CATANIA", "INDIETRO_COMUNI"]:
        await _gestisci_menu_principale(query, data, user_data)
    elif data == "VAI_AI_TOPIC" or data in TOPIC_DISPONIBILI:
        await _gestisci_selezione_topics(query, data, user_data)
    elif data == "SALVA_TUTTO":
        await _esegui_salvataggio(query, user, user_data)
    else:
        await _gestisci_selezione_zone(query, data, user_data)


async def _gestisci_menu_principale(query: Any, data: str, user_data: Dict[str, List[str]]) -> None:
    if data == "MENU_CATANIA":
        await query.edit_message_text(
            "Seleziona i Quartieri di Catania:",
            reply_markup=get_menu_quartieri(user_data["zone"]),
        )
    elif data == "INDIETRO_COMUNI":
        await query.edit_message_text("Seleziona i Comuni:", reply_markup=get_menu_home(user_data["zone"]))


async def _gestisci_selezione_topics(query: Any, data: str, user_data: Dict[str, List[str]]) -> None:
    if data in TOPIC_DISPONIBILI:
        user_data["topics"] = aggiorna_selezione(user_data["topics"], data, TOPIC_DISPONIBILI, "TOPIC_TUTTI")

    testo_zone = ", ".join(user_data["zone"])
    if len(testo_zone) > 100:
        testo_zone = testo_zone[:100] + "..."

    await query.edit_message_text(
        text=f"📍 Zone selezionate: `{testo_zone}`\n\nSeleziona gli argomenti:",
        reply_markup=get_menu_topics(user_data["topics"]),
        parse_mode="Markdown",
    )


async def _gestisci_selezione_zone(query: Any, data: str, user_data: Dict[str, List[str]]) -> None:
    if data.startswith("Q_"):
        user_data["zone"] = aggiorna_selezione(user_data["zone"], data, QUARTIERI_CATANIA, "Q_TUTTA_CT", "Catania - ")
        await query.edit_message_text(
            "Seleziona i Quartieri di Catania:",
            reply_markup=get_menu_quartieri(user_data["zone"]),
        )
    elif data.startswith("COM_"):
        user_data["zone"] = aggiorna_selezione(user_data["zone"], data, COMUNI_PROVINCIA, "COM_TUTTI")
        await query.edit_message_text("Seleziona i Comuni:", reply_markup=get_menu_home(user_data["zone"]))


async def _esegui_salvataggio(query: Any, user: Any, user_data: Dict[str, List[str]]) -> None:
    stringa_topics = ", ".join(user_data["topics"])
    stringa_zone = ", ".join(user_data["zone"])
    salva_preferenze(user.id, user.first_name, stringa_topics, stringa_zone)

    messaggio = (
        f"✅ **Configurazione Salvata!**\n\n"
        f"📍 **Zone:** {stringa_zone}\n"
        f"🗞️ **News:** {stringa_topics}\n\n"
        "Riceverai una notifica appena ci sono novità!"
    )
    await query.edit_message_text(messaggio, parse_mode="Markdown")
