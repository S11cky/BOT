# M&A Watcher - MVP (Slovak notifications via Telegram)

Tento balík obsahuje hotový MVP program (Python) ktorý sleduje RSS / press release feedy pre veľké firmy
a posiela notifikácie o potenciálnych akvizíciách na Telegram v slovenčine.

**Poznámka:** súbor `acquirers.yaml` obsahuje ukážkový zoznam veľkých US firiem (nie úplných 200). Môžeš ho rozšíriť o top 200 podľa vlastného zoznamu alebo importovať. Skript je pripravený pracovať hneď po nastavení Telegram tokenu a CHAT_ID.

## Súbory
- `main.py` — hlavný skript, ktorý sťahuje feedy, detekuje akvizície a posiela notifikácie.
- `init_db.py` — vytvorí SQLite databázu `mna_watch.db` a potrebné tabuľky.
- `acquirers.yaml` — konfigurácia sledovaných korporácií (príklad, rozšíriť podľa potreby).
- `requirements.txt` — pip dependencies.
- `Dockerfile` — pre jednoduché spustenie v containery.
- `.env.example` — ukážka potrebných environment premenných.
- `run.sh` — jednoduchý spúšťací skript (lokálne testing).
- `README.md` — tento súbor.

## Rýchle spustenie (lokálne)
1. Vytvor virtuálne prostredie a nainštaluj závislosti:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Skopíruj `.env.example` do `.env` a doplň `TG_TOKEN` a `TG_CHAT_ID`:
```bash
cp .env.example .env
# edit .env
```

3. Inicializuj DB:
```bash
python init_db.py
```

4. Spusti skript (pre test):
```bash
python main.py
```

## Docker
```bash
docker build -t mna_watcher:latest .
docker run --env-file .env mna_watcher:latest
```

## Poznámky o citlivých údajoch a rate limits
- Rešpektuj `robots.txt` a rate-limit zdrojov.
- Ak plánuješ masívne scraping, radšej pridaj platené API (Crunchbase, NewsAPI, atď.).

---
Ak chceš, môžem upraviť `acquirers.yaml` a doplniť presný **top 200** amerických firiem — pošli mi potvrdenie a hneď to doplním (môžem to aj automatizovať z verejných zdrojov).