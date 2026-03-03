import sqlite3

def create_db():
        conn = sqlite3.connect('new.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utenti (
            it_telegram INTEGER PRIMARY KEY,
            username TEXT,
            quartieri TEXT,
            comuni TEXT,
            topic TEXT
        )
        ''')
        conn.commit()
        conn.close()
        print("Data base creato")

if __name__ == "__main__":
    create_db()
