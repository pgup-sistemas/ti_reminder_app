"""
Testes unitários para os utilitários do TI Reminder App
"""
import pytest
from datetime import datetime, timezone
from app.utils.timezone_utils import get_current_time_for_db, now_local


@pytest.mark.unit
class TestTimezoneUtils:
    """Testes para utilitários de timezone"""
    
    def test_get_current_time_for_db(self):
        """Testa obtenção do tempo atual para banco de dados"""
        time_db = get_current_time_for_db()
        
        assert isinstance(time_db, datetime)
        # Deve estar próximo do tempo atual (diferença menor que 5 segundos)
        now = datetime.utcnow()
        diff = abs((time_db - now).total_seconds())
        assert diff < 5
    
    def test_now_local(self):
        """Testa obtenção do tempo local"""
        time_local = now_local()
        
        assert isinstance(time_local, datetime)
        # Deve ter timezone info
        assert time_local.tzinfo is not None
    
    def test_timezone_consistency(self):
        """Testa consistência entre funções de timezone"""
        db_time = get_current_time_for_db()
        local_time = now_local()
        
        # Converter local_time para UTC para comparação
        local_utc = local_time.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Diferença deve ser pequena (menos de 5 segundos)
        diff = abs((db_time - local_utc).total_seconds())
        assert diff < 5
