import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# --- IMPORTAZIONE DEI TUOI FILE ---
from bot.handlers import start, button_handler  # Importa le funzioni dell'interfaccia
from bot.database.database import init_db, execute_query, check_news
from scraper.catania_news import ricerca_notizia
import os
from dotenv import load_dotenv

# Configurazione logging
logging.basicConfig(level=logging.INFO)

# Carico il TOKEN da .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- LOGICA DEL MONITORAGGIO (L'unico pezzo che unisce scraper e bot) ---
async def monitor_news_job(context):
    print("🔎 Controllo news...")
    ultime_news = ricerca_notizia()
    nuove_da_inviare = [n for n in ultime_news if not check_news(n['link'])]

    if nuove_da_inviare:
        utenti = execute_query("SELECT id_telegram, topics, comuni FROM utenti")
        for u_id, u_topics, u_comuni in utenti:
            for news in nuove_da_inviare:
                # Confronto (Matching)
                if news['topic'].lower() in u_topics.lower() or news['luogo'].lower() in u_comuni.lower():
                    try:
                        testo = f"📍 *{news['luogo']}*\n📰 *{news['titolo']}*\n\n{news['link']}"
                        await context.bot.send_message(chat_id=u_id, text=testo, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Errore invio: {e}")

# --- AVVIO ---
if __name__ == '__main__':
    init_db()
   

    app = ApplicationBuilder().token(TOKEN).build()

    # REGISTRAZIONE FUNZIONI IMPORTATE
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # TIMER
    if app.job_queue:
        app.job_queue.run_repeating(monitor_news_job, interval=300, first=10)

    print("🚀 Bot avviato con successo usando i moduli esterni!")
    app.run_polling()
