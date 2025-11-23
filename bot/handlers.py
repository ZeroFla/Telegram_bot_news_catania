import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler

#--- CONFIGURAZIONE --- 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- CONFIGURAZIONE DEL DATABASE ---
# simulazione database da sostituire con SQL
MOCK_DB = {}
def salva_su_db(user_id, dati):
    """Simula il salvataggio finale sul database condiviso"""
    print(f"💾 SALVATAGGIO DB per utente {user_id}: {dati}")
    MOCK_DB[user_id] = dati

# --- DEFINIZIONE DEI DATI ---
QUARTIERI_CATANIA = {
    "Q_BARRIERA": "Barriera", 
    "Q_BICOCCA": "Bicocca", 
    "Q_BORGO": "Borgo",
    "Q_CANALICCHIO": "Canalicchio", 
    "Q_CAPPUCCINI": "Cappuccini", 
    "Q_CIBALI": "Cibali",
    "Q_CIVITA": "Civita", 
    "Q_CORSO_ITALIA": "Corso Italia", 
    "Q_FORTINO": "Fortino",
    "Q_LIBRINO": "Librino", 
    "Q_MONTE_PO": "Monte Po'", 
    "Q_NESIMA": "Nesima",
    "Q_OGNINA": "Ognina", 
    "Q_PIAZZA_DANTE": "Piazza Dante", 
    "Q_PICANELLO": "Picanello",
    "Q_PLAYA": "Playa", 
    "Q_SAN_CRISTOFORO": "San Cristoforo", 
    "Q_SAN_GIORGIO": "San Giorgio",
    "Q_SAN_LEONE": "San Leone", 
    "Q_SAN_NULLO": "San Nullo", 
    "Q_VIA_UMBERTO": "Via Umberto",
    "Q_AEROPORTO": "Zona Aeroporto", 
    "Q_TUTTA_CT": "Tutta Catania Centro"
}

COMUNI_PROVINCIA = {
    "COM_ACI_BONACCORSI": "Aci Bonaccorsi", 
    "COM_ACI_CASTELLO": "Aci Castello",
    "COM_ACI_CATENA": "Aci Catena", 
    "COM_ACI_SANT_ANTONIO": "Aci Sant'Antonio",
    "COM_ACIREALE": "Acireale", 
    "COM_ADRANO": "Adrano", 
    "COM_BELPASSO": "Belpasso",
    "COM_BIANCAVILLA": "Biancavilla", 
    "COM_BRONTE": "Bronte", 
    "COM_CALTAGIRONE": "Caltagirone",
    "COM_CAMPOROTONDO": "Camporotondo Etneo", 
    "COM_CASTEL_IUDICA": "Castel di Iudica",
    "COM_CASTIGLIONE": "Castiglione di Sicilia", 
    "COM_FIUMEFREDDO": "Fiumefreddo",
    "COM_GIARRE": "Giarre", 
    "COM_GRAMMICHELE": "Grammichele", 
    "COM_GRAVINA": "Gravina di Catania",
    "COM_LICODIA": "Licodia Eubea", 
    "COM_LINGUAGLOSSA": "Linguaglossa", 
    "COM_MALETTO": "Maletto",
    "COM_MANIACE": "Maniace", 
    "COM_MASCALI": "Mascali", 
    "COM_MASCALUCIA": "Mascalucia",
    "COM_MAZZARRONE": "Mazzarrone", 
    "COM_MILO": "Milo", 
    "COM_MINEO": "Mineo",
    "COM_MIRABELLA": "Mirabella Imbaccari", 
    "COM_MISTERBIANCO": "Misterbianco",
    "COM_MOTTA": "Motta Sant'Anastasia", 
    "COM_NICOLOSI": "Nicolosi", 
    "COM_PALAGONIA": "Palagonia",
    "COM_PATERNO": "Paternò", 
    "COM_PEDARA": "Pedara", 
    "COM_PIEDIMONTE": "Piedimonte Etneo",
    "COM_RAGALNA": "Ragalna", 
    "COM_RAMACCA": "Ramacca", 
    "COM_RANDAZZO": "Randazzo",
    "COM_RIPOSTO": "Riposto", 
    "COM_SAN_CONO": "San Cono", 
    "COM_SAN_GIOVANNI": "San Giovanni la Punta",
    "COM_SAN_GREGORIO": "San Gregorio", 
    "COM_SAN_MICHELE": "San Michele di Ganzaria",
    "COM_SAN_PIETRO": "San Pietro Clarenza", 
    "COM_SANT_AGATA": "Sant'Agata Li Battiati",
    "COM_SANT_ALFIO": "Sant'Alfio", 
    "COM_SANTA_MARIA": "Santa Maria di Licodia",
    "COM_SANTA_VENERINA": "Santa Venerina", 
    "COM_SCORDIA": "Scordia", 
    "COM_TRECASTAGNI": "Trecastagni",
    "COM_TREMESTIERI": "Tremestieri Etneo", 
    "COM_VALVERDE": "Valverde", 
    "COM_VIAGRANDE": "Viagrande",
    "COM_VIZZINI": "Vizzini", 
    "COM_ZAFFERANA": "Zafferana Etnea",
    "COM_TUTTI": "Tutti i comuni"
}

TOPIC_DISPONIBILI = {   
    "TOPIC_DOSSIER": "Dossier",
    "TOPIC_CRONACA": "Cronaca",
    "TOPIC_POILITICA": "Politica",
    "TOPIC_ATTUALITA": "Attualità",
    "TOPIC_SPORT": "Sport",
    "TOPIC_ECONOMIA" : "Economia e Lavoro",
    "TOPIC_ANNUNCI": "Annunci Lavoro",
    "TOPIC_METEO": "Meteo",
    "TOPIC_AMBIENTE": "Ambiente",
    "TOPIC_SALUTE": "Salute",
    "TOPIC_CASA": "Casa",
    "TOPIC_FORMAZIONE": "Formazione",
    "TOPIC_MOTORI": "Motori",
    "TOPIC_GUIDE": "Guide Catania",
    "TOPIC_TUTTI": "Tutti i topics"
}

# --- HELPER---
def crea_tastiera_con_spunte(dizionario_dati, lista_selezionati, colonne = 3):
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
            
    if riga: keyboard.append(riga)
    return keyboard

def aggiorna_selezione(lista_target, data_key, dizionario, chiave_tutti, prefisso=""):
    if data_key == chiave_tutti:
        tutti_i_valori = []
        for k, v in dizionario.items():
            if k == chiave_tutti: continue

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
    
def get_menu_home(zone_selezionate):
    keyboard = [[InlineKeyboardButton("🌋 CATANIA CENTRO (Quartieri) 🏙️", callback_data="MENU_CATANIA")]]
    keyboard.extend(crea_tastiera_con_spunte(COMUNI_PROVINCIA, zone_selezionate, colonne=3))
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)

def get_menu_quartieri(zone_selezionate):
    keyboard = crea_tastiera_con_spunte(QUARTIERI_CATANIA, zone_selezionate, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("➡️ VAI AI TOPIC", callback_data="VAI_AI_TOPIC")])
    return InlineKeyboardMarkup(keyboard)

def get_menu_topics(topics_selezionati):
    keyboard = crea_tastiera_con_spunte(TOPIC_DISPONIBILI, topics_selezionati, colonne=2)
    keyboard.append([InlineKeyboardButton("🔙 Indietro ai Comuni", callback_data="INDIETRO_COMUNI")])
    keyboard.append([InlineKeyboardButton("💾 SALVA E CONCLUDI", callback_data="SALVA_TUTTO")])
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if 'preferenze' not in context.user_data:
        context.user_data['preferenze'] = {
            "zone": [], 
            "topics": []
        }
    
    zone_attuali = context.user_data['preferenze']['zone']

    await update.message.reply_text(
        f"Ciao {user.first_name}! Benvenuto.\nSeleziona i Comuni di tuo interesse (puoi sceglierne più di uno):"
    )
    await update.message.reply_text(
            "Seleziona i Comuni:", reply_markup = get_menu_home(zone_attuali)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    data = query.data
    
    user_data = context.user_data.get('preferenze', {"zone": [], "topics": []})

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
        if not user_data['zone']:
            await query.answer("⚠️ Seleziona almeno una zona prima di proseguire!", show_alert=True)
            return
        
        testo_zone = ", ".join(user_data['zone'])
        if len(testo_zone) > 100: testo_zone = testo_zone[:100] + "..." 
        await query.edit_message_text(
            text=f"📍 Zone attuali: `{testo_zone}`\n\nSeleziona gli argomenti:", 
            reply_markup=get_menu_topics(user_data['topics']),
            parse_mode='Markdown'
        )
        return
    
    elif data == "SALVA_TUTTO":
        if not user_data['topics']:
            await query.answer("⚠️ Seleziona almeno un argomento!", show_alert=True)
            return

        salva_su_db(update.effective_user.id, user_data)

        messaggio = (
            f"✅ **Configurazione Salvata!**\n\n"
            f"📍 **Zone:**\n"
            f"{', '.join(user_data['zone'])}\n\n"
            f"🗞️ **News:**\n"
            f"{', '.join(user_data['topics'])}\n\n"
            "Riceverai una notifica appena ci sono novità!"
        )
        await query.edit_message_text(messaggio, parse_mode='Markdown')

    # --- LOGICA DI SELEZIONE ---
    # --- CLIK QUARTIERE ---
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

# --- SETUP PER AVVIARE IL BOT (da mettere nel main.py) ---
if __name__ == '__main__':
    # Inserisci qui il tuo TOKEN preso da BotFather
    TOKEN = "7651978991:AAExi67J3Ettz40xvzi0RDpcpmaYj1kgW_o"
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot in avvio...")
    app.run_polling()