from datetime import datetime, timezone, timedelta
from flask import current_app

# Timezone para Porto Velho, Rondônia (UTC-4)
PORTO_VELHO_TZ = timezone(timedelta(hours=-4))

def get_local_timezone():
    """Retorna o timezone configurado para a aplicação"""
    return PORTO_VELHO_TZ

def now_local():
    """Retorna o datetime atual no timezone local (Porto Velho)"""
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    local_tz = get_local_timezone()
    return utc_now.astimezone(local_tz)

def utc_to_local(utc_dt):
    """Converte datetime UTC para timezone local"""
    if utc_dt is None:
        return None
    
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    local_tz = get_local_timezone()
    return utc_dt.astimezone(local_tz)

def local_to_utc(local_dt):
    """Converte datetime local para UTC"""
    if local_dt is None:
        return None
    
    local_tz = get_local_timezone()
    
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=local_tz)
    
    return local_dt.astimezone(timezone.utc)

def format_local_datetime(dt, format_str='%d/%m/%Y %H:%M'):
    """Formata datetime para exibição no timezone local"""
    if dt is None:
        return 'N/A'
    
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

def get_current_time_for_db():
    """Retorna o tempo atual em UTC para salvar no banco de dados"""
    return datetime.utcnow()

def parse_local_datetime(date_str, format_str='%Y-%m-%d %H:%M'):
    """Converte string de data local para datetime UTC para o banco"""
    try:
        local_dt = datetime.strptime(date_str, format_str)
        return local_to_utc(local_dt)
    except ValueError:
        return None
