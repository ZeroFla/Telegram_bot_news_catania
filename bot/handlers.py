import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler

# Ogni volta che succede qualcosa, scrive l'orario esatto (asctime), chi sta parlando (name), quanto è grave (levelname) e il messaggio
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- CONFIGURAZIONE FINTA DEL DATABASE ---
# Questo dizionario simula il database che gestisci col tuo collega.
# In produzione, qui userai SQL o Mongo.
MOCK_DB = {}

def salva_su_db(user_id, dati):
    """Simula il salvataggio finale sul database condiviso"""
    print(f"💾 SALVATAGGIO DB per utente {user_id}: {dati}")
    MOCK_DB[user_id] = dati

# --- DEFINIZIONE DEI DATI ---
# Le opzioni per la provincia di Catania
ZONE_DISPONIBILI = {
    "CT_CENTRO": "Catania Centro",
    "CT_ACIREALE": "Acireale",
    "CT_PATERNO": "Paternò",
    "CT_MISTERBIANCO": "Misterbianco",
    "CT_TUTTA": "Tutta la Provincia"
}

# I topic che mi hai indicato
TOPIC_DISPONIBILI = {
    "TOPIC_SPORT": "⚽ Sport",
    "TOPIC_METEO": "☀️ Meteo",
    "TOPIC_ANNUNCI": "📢 Annunci",
    "TOPIC_CRONACA": "📰 Cronaca"
}

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1. Risponde al comando /start
    2. Mostra la scelta della zona (Città/Provincia)
    """
    user = update.effective_user
    # Inizializziamo una memoria temporanea per questo utente, la condizione ci permette di modificare le scelte gia fatte 
    if 'preferenze' not in context.user_data:
        context.user_data['preferenze'] = { 
            "zona": None,
            "topics": []
        }
    
    await update.message.reply_text(
        f"Ciao {user.first_name}! Benvenuto nel Bot Notizie Catania.\n"
        "Per iniziare, seleziona la tua zona di interesse:"
    )
    
    # Creiamo i bottoni per le città
    keyboard = [
        [InlineKeyboardButton("🌋 Catania Città", callback_data="CT_CENTRO")],
        [InlineKeyboardButton("🍋 Acireale", callback_data="CT_ACIREALE"), 
         InlineKeyboardButton("🏰 Paternò", callback_data="CT_PATERNO")],
        [InlineKeyboardButton("🏗️ Misterbianco", callback_data="CT_MISTERBIANCO")],
        [InlineKeyboardButton("📍 Tutta la Provincia", callback_data="CT_TUTTA")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Scegli una zona:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestisce tutti i click sui bottoni.
    """
    query = update.callback_query
    await query.answer() # Conferma a Telegram che il click è stato ricevuto
    
    dati_click = query.data
    user_data = context.user_data.get('preferenze', {"zona": None, "topics": []})

    # --- FASE 1: GESTIONE SCELTA ZONA ---
    if dati_click in ZONE_DISPONIBILI:
        # Salviamo la zona scelta
        user_data['zona'] = ZONE_DISPONIBILI[dati_click]
        
        #salviamo le modifiche nella memoria a breve termine del bot.
        context.user_data['preferenze'] = user_data 
        
        # Ora mostriamo i topic da scegliere
        await mostra_menu_topics(query, user_data['topics'])

    # --- FASE 2: GESTIONE SCELTA TOPIC (CHECKBOX) ---
    elif dati_click in TOPIC_DISPONIBILI:
        topic_scelto = TOPIC_DISPONIBILI[dati_click]
        
        # Logica Toggle: Se c'è lo tolgo, se non c'è lo aggiungo
        if topic_scelto in user_data['topics']:
            user_data['topics'].remove(topic_scelto)
        else:
            user_data['topics'].append(topic_scelto)
            
        #salviamo le modifiche nella memoria a breve termine del bot.
        context.user_data['preferenze'] = user_data 
        
        # Aggiorno la tastiera visivamente (senza mandare un nuovo messaggio)
        await mostra_menu_topics(query, user_data['topics'])

    # --- FASE 3: SALVATAGGIO FINALE ---
    elif dati_click == "SALVA_TUTTO":
        if not user_data['topics']:
            await query.edit_message_text("⚠️ Devi selezionare almeno un argomento!")
            return

        # Qui chiami la funzione che parla col DB reale
        salva_su_db(update.effective_user.id, user_data)
        
        messaggio_finale = (
            f"✅ **Configurazione Completata!**\n\n"
            f"📍 Zona: {user_data['zona']}\n"
            f"news: {', '.join(user_data['topics'])}\n\n"
            "Riceverai una notifica appena ci sono novità!"
        )
        await query.edit_message_text(text=messaggio_finale, parse_mode='Markdown')


async def mostra_menu_topics(query, topics_selezionati):
    """
    Funzione ausiliaria che disegna i bottoni dei topic.
    Mette una spunta ✅ se il topic è già nella lista dell'utente.
    """
    keyboard = []
    riga = []
    
    for key, label in TOPIC_DISPONIBILI.items():
        # Se l'argomento è selezionato, aggiungi la spunta
        if label in topics_selezionati:
            text_button = f"✅ {label}"
        else:
            text_button = label
            
        #costruisce fisicamente un singolo bottone e lo posiziona sulla riga orizzontale che stai preparando.
        riga.append(InlineKeyboardButton(text_button, callback_data=key))
        
        # Crea righe da 2 bottoni
        if len(riga) == 2:
            keyboard.append(riga)
            riga = []
    
    if riga:
        keyboard.append(riga)
    
    # Aggiungo il bottone CONFERMA in fondo
    keyboard.append([InlineKeyboardButton("💾 SALVA PREFERENZE", callback_data="SALVA_TUTTO")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Modifichiamo il messaggio esistente invece di mandarne uno nuovo
    await query.edit_message_text(
        text=f"Ottimo! Hai scelto: **{query.message.reply_to_message}**.\nOra seleziona gli argomenti (puoi sceglierne più di uno):",
        reply_markup=reply_markup,
        #dice a Telegram: "Non stampare i simboli che ti mando così come sono, ma usali per dare STILE al testo."
        parse_mode='Markdown'
    )

# --- SETUP PER AVVIARE IL BOT (da mettere nel main.py solitamente) ---
if __name__ == '__main__':
    # Inserisci qui il tuo TOKEN preso da BotFather
    TOKEN = "7651978991:AAExi67J3Ettz40xvzi0RDpcpmaYj1kgW_o"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Colleghiamo gli handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot in avvio...")
    app.run_polling()