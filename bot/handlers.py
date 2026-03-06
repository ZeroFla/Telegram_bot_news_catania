import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import QUARTIERI_CATANIA, COMUNI_PROVINCIA, TOPIC_DISPONIBILI
from database.database import salva_preferenze

# Configurazione base del logging per tracciare lo stato di esecuzione e gli errori a terminale
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Logica di formattazione ---
def crea_tastiera_con_spunte(dizionario_dati, lista_selezionati, colonne = 3):
    """
    Genera dinamicamente una matrice di InlineKeyboardButton.
    Aggiunge un indicatore visivo (✅) per gli elementi già presenti nello stato dell'utente.
    """
    keyboard = []
    riga = []
    
    for chiave, nome_chiaro in dizionario_dati.items():
        is_selected = False
        
        # Verifica se l'elemento corrente o la sua variante con prefisso è già stato selezionato
        if nome_chiaro in lista_selezionati: 
            is_selected = True
        elif f"Catania - {nome_chiaro}" in lista_selezionati:
            is_selected = True
            
        testo = f"✅ {nome_chiaro}" if is_selected else nome_chiaro
        
        riga.append(InlineKeyboardButton(testo, callback_data=chiave))
        
        # Paginazione della riga in base al parametro 'colonne'
        if len(riga) == colonne:
            keyboard.append(riga)
            riga = []
            
    if riga: keyboard.append(riga)
    return keyboard

def aggiorna_selezione(lista_target, data_key, dizionario, chiave_tutti, prefisso=""):
    """
    Gestisce il toggle (selezione/deselezione) degli elementi.
    Implementa la logica "Seleziona Tutti" verificando l'intersezione degli insiemi.
    """
    if data_key == chiave_tutti:
        tutti_i_valori = []
        for k, v in dizionario.items():
            if k == chiave_tutti: continue

            valore_db = f"{prefisso}{v}" if prefisso else v
            tutti_i_valori.append(valore_db)

        # Calcola quanti elementi sono già presenti nella selezione dell'utente
        elementi_gia_presenti = [x for x in tutti_i_valori if x in lista_target]
        
        # Se tutti gli elementi sono già selezionati, li rimuove. 
        if len(elementi_gia_presenti) == len(tutti_i_valori):
            for item in tutti_i_valori:
                if item in lista_target:
                    lista_target.remove(item)
        # Altrimenti li aggiunge.
        else:
            for item in tutti_i_valori:
                if item not in lista_target:
                    lista_target.append(item)
        
        return lista_target
    else:
        # Toggle per un singolo elemento
        valore = f"{prefisso}{dizionario[data_key]}" if prefisso else dizionario[data_key]
        if valore in lista_target:
            lista_target.remove(valore)
        else:
            lista_target.append(valore)
        return lista_target

# --- Creazione interfacce ---
 
def get_menu_home(zone_selezionate):
    """
    Restituisce la struttura della tastiera per il menu principale (Comuni).
    """
    keyboard = [[InlineKeyboardButton("🌋 CATANIA CENTRO (Quartieri) 🏙️", callback_data="MENU_CATANIA")]]
    keyboard.extend(crea_tastiera_con_spunte(COMUNI_PROVINCIA, zone_selezionate, colonne=3))
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)

def get_menu_quartieri(zone_selezionate):
    """
    Restituisce la struttura della tastiera per il menu di dettaglio (Quartieri di Catania).
    """
    keyboard = crea_tastiera_con_spunte(QUARTIERI_CATANIA, zone_selezionate, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)

def get_menu_topics(topics_selezionati):
    """
    Restituisce la struttura della tastiera per il menu finale (Selezione Argomenti).
    """
    keyboard = crea_tastiera_con_spunte(TOPIC_DISPONIBILI, topics_selezionati, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("💾 SALVA E CONCLUDI", callback_data="SALVA_TUTTO")])
    return InlineKeyboardMarkup(keyboard)

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Funzione di avvio attivata dal comando /start. 
    Prepara la memoria temporanea per salvare le scelte dell'utente e mostra il menu principale dei Comuni.
    """
    user = update.effective_user
    
    # Inizializza la struttura dati temporanea per le preferenze dell'utente
    if 'preferenze' not in context.user_data:
        context.user_data['preferenze'] = {
            "zone": [], 
            "topics": []
        }
    
    zone_attuali = context.user_data['preferenze']['zone']

    await update.message.reply_text(
        f"Ciao {user.first_name}! Benvenuto.\nSeleziona i Comuni di tuo interesse (puoi sceglierne più di uno):", reply_markup = get_menu_home(zone_attuali)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestisce i click sui pulsanti della tastiera. 
    Aggiorna le scelte dell'utente in memoria e cambia il menu visualizzato in base al pulsante premuto.
    """
    query = update.callback_query 
    data = query.data
    user_data = context.user_data.get('preferenze', {"zone": [], "topics": []})

    # --- CONTROLLI DI ERRORE CON POP-UP ---
    if data == "VAI_AI_TOPIC" and not user_data['zone']:
            await query.answer("⚠️ Seleziona almeno una zona prima di proseguire!", show_alert=True)
            return 

    if data == "SALVA_TUTTO" and not user_data['topics']:
            await query.answer("⚠️ Seleziona almeno un argomento!", show_alert=True)
            return

    # Se non ci sono stati errori, conferma la ricezione
    await query.answer()
    
    try:
        # --- LOGICA DI NAVIGAZIONE ---
        if data == "MENU_CATANIA":
            await query.edit_message_text(
                f"Seleziona i Quartieri di Catania:",
                reply_markup = get_menu_quartieri(user_data['zone'])
            )

        elif data == "INDIETRO_COMUNI":
            await query.edit_message_text(
                f"Seleziona i Comuni:", 
                reply_markup = get_menu_home(user_data['zone'])
            )

        elif data == "VAI_AI_TOPIC":        
            testo_zone = ", ".join(user_data['zone'])
            if len(testo_zone) > 100: testo_zone = testo_zone[:100] + "..." 
            await query.edit_message_text(
                text=f"📍 Zone selezionate: `{testo_zone}`\n\nSeleziona gli argomenti:", 
                reply_markup=get_menu_topics(user_data['topics']),
                parse_mode='Markdown'
            )
            return
        
        elif data == "SALVA_TUTTO":
            user = update.effective_user
            # Serializzazione delle liste per il salvataggio su DB relazionale
            stringa_topics = ", ".join(user_data['topics']) 
            stringa_zone = ", ".join(user_data['zone'])

            salva_preferenze(user.id, user.first_name, stringa_topics, stringa_zone)

            messaggio = (
                f"✅ **Configurazione Salvata!**\n\n"
                f"📍 **Zone:**\n"
                f"{', '.join(user_data['zone'])}\n\n"
                f"🗞️ **News:**\n"
                f"{', '.join(user_data['topics'])}\n\n"
                "Riceverai una notifica appena ci sono novità!"
            )
            await query.edit_message_text(messaggio, parse_mode='Markdown')

        # --- CLICCA QUARTIERE ---
        elif data.startswith("Q_"):
            user_data['zone'] = aggiorna_selezione(
                user_data['zone'], data, QUARTIERI_CATANIA, "Q_TUTTA_CT", prefisso="Catania - "
            )
            await query.edit_message_text(
                f"Seleziona i Quartieri di Catania:",
                reply_markup = get_menu_quartieri(user_data['zone'])
            )

        # --- CLICCA COMUNE ---
        elif data.startswith("COM_"):
            user_data['zone'] = aggiorna_selezione(
                user_data['zone'], data, COMUNI_PROVINCIA, "COM_TUTTI"
            )
            await query.edit_message_text(
                f"Seleziona i Comuni:", 
                reply_markup =  get_menu_home(user_data['zone'])
            )
            
        # --- CLICCA TOPIC ---
        elif data in TOPIC_DISPONIBILI:
            user_data['topics'] = aggiorna_selezione(
                user_data['topics'], data, TOPIC_DISPONIBILI, "TOPIC_TUTTI"
            )
            
            testo_zone = ", ".join(user_data['zone'])
            if len(testo_zone) > 100: testo_zone = testo_zone[:100] + "..."
            await query.edit_message_text(
                text=f"📍 Zone attuali: `{testo_zone}`\n\nSeleziona gli argomenti:", 
                reply_markup=get_menu_topics(user_data['topics']), 
                parse_mode='Markdown'
            )

    except BadRequest:
        """
        Evita che il bot si blocchi se l'utente clicca due volte lo stesso bottone molto velocemente
        """
        pass