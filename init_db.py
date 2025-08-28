import sqlite3
conn = sqlite3.connect('mna_watch.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dt TEXT,
  source TEXT,
  acquirer TEXT,
  target TEXT,
  url TEXT UNIQUE,
  snippet TEXT,
  amount REAL,
  currency TEXT,
  confidence REAL
);
''')
c.execute('CREATE INDEX IF NOT EXISTS ix_events_dt ON events(dt);')
conn.commit()
conn.close()
print("DB initialized: mna_watch.db")
