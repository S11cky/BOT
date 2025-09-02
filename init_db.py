import sqlite3

def init_sent_alerts_db():
    """Vytvorí tabuľku v databáze pre ukladanie odoslaných alertov"""
    conn = sqlite3.connect('mna_watch.db')  # Pripojíme sa k databáze
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS sent_alerts (
      ticker TEXT PRIMARY KEY
    );
    ''')  # Vytvoríme tabuľku, ak ešte neexistuje
    conn.commit()  # Uložíme zmeny
    conn.close()

# Zavolaj túto funkciu raz pri nastavení databázy:
init_sent_alerts_db()
