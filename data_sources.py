# pôvodné:
lockup_end = ipo_date + timedelta(days=LOCKUP_DAYS_DEFAULT)
today = date.today()
days_to_lockup = (lockup_end - today).days

# nahraď týmto:
lockup_end = ipo_date + timedelta(days=LOCKUP_DAYS_DEFAULT)
today = date.today()
days_to_lockup = (lockup_end - today).days
# ak je po lock-upe (alebo IPO staršie než 180 dní), nehlás nič
if days_to_lockup < 0 or (today - ipo_date).days > LOCKUP_DAYS_DEFAULT:
    days_to_lockup = None
