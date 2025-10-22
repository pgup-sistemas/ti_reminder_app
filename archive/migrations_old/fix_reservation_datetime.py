"""
Script para corrigir campos start_datetime e end_datetime em reservas existentes
"""
import sys
import os
from datetime import datetime, time

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import EquipmentReservation

def fix_reservation_datetimes():
    """Corrige campos datetime em reservas que estão NULL"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("CORRIGINDO CAMPOS DATETIME EM RESERVAS")
        print("=" * 60)
        
        # Buscar todas as reservas
        reservations = EquipmentReservation.query.all()
        total = len(reservations)
        fixed = 0
        
        print(f"\nTotal de reservas encontradas: {total}")
        
        for reservation in reservations:
            needs_fix = False
            
            # Verificar se start_datetime está NULL
            if reservation.start_datetime is None:
                needs_fix = True
                # Combinar start_date e start_time
                if reservation.start_date and reservation.start_time:
                    reservation.start_datetime = datetime.combine(
                        reservation.start_date,
                        reservation.start_time if isinstance(reservation.start_time, time) else time(9, 0)
                    )
                    print(f"  ✓ Reserva #{reservation.id}: start_datetime corrigido")
                else:
                    print(f"  ✗ Reserva #{reservation.id}: ERRO - start_date ou start_time ausente")
            
            # Verificar se end_datetime está NULL
            if reservation.end_datetime is None:
                needs_fix = True
                # Combinar end_date e end_time
                if reservation.end_date and reservation.end_time:
                    reservation.end_datetime = datetime.combine(
                        reservation.end_date,
                        reservation.end_time if isinstance(reservation.end_time, time) else time(18, 0)
                    )
                    print(f"  ✓ Reserva #{reservation.id}: end_datetime corrigido")
                else:
                    print(f"  ✗ Reserva #{reservation.id}: ERRO - end_date ou end_time ausente")
            
            if needs_fix:
                fixed += 1
        
        # Salvar alterações
        try:
            db.session.commit()
            print(f"\n{'=' * 60}")
            print(f"SUCESSO: {fixed} reservas corrigidas de {total} total")
            print(f"{'=' * 60}")
        except Exception as e:
            db.session.rollback()
            print(f"\n{'=' * 60}")
            print(f"ERRO ao salvar: {str(e)}")
            print(f"{'=' * 60}")
            return False
        
        return True

if __name__ == '__main__':
    success = fix_reservation_datetimes()
    sys.exit(0 if success else 1)
