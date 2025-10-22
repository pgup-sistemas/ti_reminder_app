#!/usr/bin/env python
"""Script para verificar reservas no banco de dados"""
from app import create_app
from app.models import EquipmentReservation
from sqlalchemy import or_

app = create_app()
with app.app_context():
    reservas = EquipmentReservation.query.all()
    print(f"\n{'='*60}")
    print(f"Total de reservas no banco: {len(reservas)}")
    print(f"{'='*60}\n")
    
    if reservas:
        for r in reservas:
            print(f"ID: {r.id}")
            print(f"  Status: '{r.status}'")
            print(f"  Usuário ID: {r.user_id} ({r.user.username if r.user else 'N/A'})")
            print(f"  Equipamento ID: {r.equipment_id} ({r.equipment.name if r.equipment else 'N/A'})")
            print(f"  Data: {r.start_date} até {r.end_date}")
            print(f"  Horário: {r.start_time} até {r.end_time}")
            print(f"  Criado em: {r.created_at}")
            print("-" * 60)
    else:
        print("❌ NENHUMA RESERVA ENCONTRADA NO BANCO DE DADOS!")
        print("   As reservas podem não estar sendo criadas corretamente.\n")
    
    # Verificar pendentes especificamente
    pendentes = EquipmentReservation.query.filter_by(status='pendente').all()
    print(f"\n{'='*60}")
    print(f"Reservas com status='pendente': {len(pendentes)}")
    print(f"{'='*60}\n")
    
    if pendentes:
        for r in pendentes:
            print(f"  - ID {r.id}: {r.equipment.name if r.equipment else 'N/A'} para {r.user.username if r.user else 'N/A'}")
    
    # Verificar pending também
    pending = EquipmentReservation.query.filter_by(status='pending').all()
    print(f"\nReservas com status='pending': {len(pending)}")
    
    # Verificar confirmadas
    confirmadas = EquipmentReservation.query.filter_by(status='confirmada').all()
    print(f"Reservas com status='confirmada': {len(confirmadas)}")
    
    # Verificar convertidas
    convertidas = EquipmentReservation.query.filter_by(status='convertida').all()
    print(f"Reservas com status='convertida': {len(convertidas)}")
    
    # Verificar reservas com start_datetime NULL
    null_datetime = EquipmentReservation.query.filter(
        or_(
            EquipmentReservation.status == 'pendente',
            EquipmentReservation.status == 'pending'
        ),
        EquipmentReservation.start_datetime.is_(None)
    ).all()
    
    print(f"\n⚠ Reservas pendentes com start_datetime NULL: {len(null_datetime)}")
    
    if null_datetime:
        print("\n" + "-" * 80)
        print("RESERVAS COM PROBLEMA (start_datetime NULL):")
        print("-" * 80)
        for reservation in null_datetime:
            print(f"  - ID: {reservation.id} | Equipamento: {reservation.equipment.name if reservation.equipment else 'N/A'}")
            print(f"    Created At: {reservation.created_at}")
    
    print("\n" + "=" * 80)
