#!/usr/bin/env python3
# main.py - M&A Watcher MVP (Slovak notifications via Telegram)
import re, time, os, sys, math
import feedparser, requests, bs4, datetime as dt, yaml
from rapidfuzz import fuzz
from dotenv import load_dotenv
from tqdm import tqdm
import sqlite3

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')
MIN_AMOUNT_USD = float(os.getenv('MIN_AMOUNT_USD') or 1000000)  # default 50M
FUZZ_THRESHOLD = int(os.getenv('FUZZ_THRESHOLD') or 90)

if not TG_TOKEN or not CHAT_ID:
    print("[WARN] TG_TOKEN or CHAT_ID not set. Notifications will be skipped.")


# -- load acquirers config
with open('acquirers.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
ACQUIRERS = cfg.get('acquirers', [])

def get_alias_list():
    lst = []
    for a in ACQUIRERS:
        names = [a.get('name')]+a.get('aliases', [])
        for n in names:
            if n: lst.append({'canonical': a.get('name'), 'alias': n})
    return lst

ALIAS_LIST = get_alias_list()

# -- simple RSS feeds to monitor (BusinessWire + PR Newswire as baseline)
FEEDS = [
    'https://www.businesswire.com/portal/site/home/rss/',
    'https://www.prnewswire.com/rss/news-releases-list.rss'
]

# DB helpers
def db_conn():
    return sqlite3.connect('mna_watch.db')

def already_seen(url):
    c = db_conn().cursor()
    c.execute('SELECT 1 FROM events WHERE url = ?', (url,))
    r = c.fetchone()
    c.connection.close()
    return bool(r)

def save_event(ev):
    conn = db_conn()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO events(dt, source, acquirer, target, url, snippet, amount, currency, confidence)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ''', (ev.get('dt'), ev.get('source'), ev.get('acquirer'), ev.get('target'),
                        ev.get('url'), ev.get('snippet'), ev.get('amount'), ev.get('currency'), ev.get('confidence')))
        conn.commit()
    except Exception as e:
        # ignore duplicates etc.
        pass
    finally:
        conn.close()

# detection patterns (EN + SK)
ACQ_PATTERNS = [
    r"\b(acquires?|acquisition|merger|buys?|purchase|to acquire)\b",
    r"\b(kupuje|akvíruje|akvizíci[ae]|fúzi[ae])\b"
]
AMOUNT_PAT = re.compile(r"(\$|USD|EUR|€|GBP|£)\s?([0-9\.,]+)\s?(million|milliard|billion|m|bn|milión|miliónov|miliard|miliárd)?", re.I)

def is_acquisition(text):
    t = text.lower()
    return any(re.search(p, t) for p in ACQ_PATTERNS)

def match_acquirer(text):
    best = None
    for a in ALIAS_LIST:
        score = fuzz.partial_ratio(a['alias'].lower(), text.lower())
        if score >= FUZZ_THRESHOLD:
            # prefer higher score and shorter alias (heuristika)
            if not best or score > best[1]:
                best = (a['canonical'], score)
    return best[0] if best else None

def extract_amount(text):
    m = AMOUNT_PAT.search(text)
    if not m: return None, None
    sym, num, scale = m.group(1), m.group(2), (m.group(3) or '').lower()
    num = float(num.replace(',', '').replace(' ', ''))
    # scale normalization (very rough)
    if 'b' in scale or 'miliard' in scale or 'bn' in scale:
        num = num * 1_000_000_000 if 'b' in scale or 'bn' in scale or 'miliard' in scale else num
    elif 'm' in scale or 'mil' in scale or 'milión' in scale:
        num = num * 1_000_000
    # currency guess
    cur = 'USD' if sym in ('$','USD') else ('EUR' if sym in ('€','EUR') else sym)
    return num, cur

def fetch_article_text(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent':'mna-watcher/1.0'})
        r.raise_for_status()
        s = bs4.BeautifulSoup(r.text, 'html.parser')
        ps = " ".join(p.get_text(" ", strip=True) for p in s.find_all('p'))
        return ps
    except Exception as e:
        return ''

def send_telegram(msg):
    if not TG_TOKEN or not CHAT_ID:
        print('[INFO] Skipping Telegram (missing credentials). Message would be:\n', msg)
        return
    try:
        resp = requests.get(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage', params={
            'chat_id': CHAT_ID, 'text': msg, 'disable_web_page_preview': True
        }, timeout=10)
        return resp.json()
    except Exception as e:
        print('[ERROR] Telegram send failed:', e)

def process_entry(item, feed_url):
    title = item.get('title','')
    summary = item.get('summary','') or item.get('description','')
    blob = (title + ' ' + summary).strip()
    if not is_acquisition(blob):
        # try to fetch article full text
        blob = blob + ' ' + fetch_article_text(item.get('link','') or '')
        if not is_acquisition(blob):
            return None
    acquirer = match_acquirer(blob)
    if not acquirer:
        return None
    # try extract target (heuristic from title)
    m = re.search(r"(acquires?|kupuje|acquired|bought|to acquire)\s+([A-Z][\w&.\- ]{2,140})", title, re.I)
    target = m.group(2).strip() if m else None
    amount, currency = extract_amount(blob)
    # filter by amount threshold if we have amount in USD (best-effort)
    if amount and currency == 'USD' and amount < MIN_AMOUNT_USD:
        # below threshold -> skip
        return None
    confidence = 0.5 + (0.4 if amount else 0) + (0.1 if target else 0)
    ev = {
        'dt': item.get('published') or dt.datetime.utcnow().isoformat(),
        'source': feed_url,
        'acquirer': acquirer,
        'target': target,
        'url': item.get('link'),
        'snippet': title[:280],
        'amount': amount,
        'currency': currency,
        'confidence': confidence
    }
    return ev

def process_feed(feed_url):
    print('[INFO] Fetching feed:', feed_url)
    d = feedparser.parse(feed_url)
    for item in d.entries:
        link = item.get('link')
        if not link: continue
        if already_seen(link): continue
        ev = process_entry(item, feed_url)
        if ev:
            save_event(ev)
            # prepare Slovak message
            amount_str = f" za {int(ev['amount']):,} {ev['currency']}" if ev['amount'] else ''
            msg = f"🔔 Akvizícia: {ev['acquirer']} kupuje {ev['target'] or 'neznámu firmu'}{amount_str}\nZdroj: {ev['url']}\nDôvera: {ev['confidence']:.2f}"
            send_telegram(msg)
            print('[ALERT]', msg)

def run_once():
    for f in FEEDS:
        try:
            process_feed(f)
        except Exception as e:
            print('[ERROR] processing feed', f, e)

if __name__ == '__main__':
    # simple loop for local testing (runs once)
    run_once()
    print('Done.')
