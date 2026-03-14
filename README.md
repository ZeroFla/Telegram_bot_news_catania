# Telegram_bot_news_catania

Un bot Telegram interattivo per ricevere aggiornamenti e notizie personalizzate sui Comuni della provincia di Catania e i vari Quartieri della città, filtrati per argomento (Cronaca, Sport, Meteo, ecc.).

---

## Di cosa tratta
Questo progetto nasce per offrire un servizio di news. L'utente può navigare in un menù a bottoni, selezionare una o più zone di interesse e scegliere quali argomenti seguire. I dati e le preferenze vengono salvati in un database per l'invio automatico delle notizie pertinenti.

**Esempio notifica:**

<img src="assets/Notifica.jpg" width="30%">

---

## Funzionalità Principali
* **Selezione Geografica Multipla:** Scelta tra i comuni della provincia e i quartieri di Catania centro.

**Menù Comuni**

<img src="assets/Comuni.png" width="30%">

**Menù Quartieri**

<img src="assets/Quartieri.png" width="30%">

* **Filtro per Topic:** Selezione degli argomenti di interesse (es. Cronaca, Sport).

**Menù Topics**

<img src="assets/Topics.png" width="30%">

---

## Requisiti di Sistema
Per eseguire questo bot in locale, è necessario disporre di:
* **Python 3.10+**
* Un token bot valido fornito da [@BotFather](https://t.me/botfather) su Telegram.
---

## Installazione
Prima di avviare il bot, è necessario configurare l'ambiente di sviluppo:

1.Clonare il repository e accedere alla cartella del progetto:
```bash
git clone https://github.com/kodex154/Telegram_bot_news_catania.git
cd Telegram_bot_news_catania
```

2.Creare un ambiente virtule per python ed attivarlo:
```bash
python -m venv .venv
source .venv/bin/active
```

3.Installare le dipendenze:
```bash
pip install -r requirements.txt
```
4.Creare un file .env nella directory principale e inserire il token del bot:
```text
BOT_TOKEN= inserire_qui_il_token
```
---

## Utilizzo
Per avviare il bot, eseguire il file principale dal terminale:
```bash
python news_bot.py
```
* Aprire Telegram e avviare la chat con il bot.
* Digitare il comando `/start` per avviare la procedura di configurazione.
* Utilizzare i bottoni dell'interfaccia per navigare e salvare le preferenze.
* Digitare il comando `/cancel` per rimuovere il proprio profilo e i relativi dati dal database.
