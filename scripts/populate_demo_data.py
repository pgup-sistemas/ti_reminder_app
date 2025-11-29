import random
from datetime import datetime, timedelta, date, time

from app import create_app, db
from app.models import (
    User,
    Sector,
    Task,
    Reminder,
    Chamado,
    Equipment,
    EquipmentReservation,
    EquipmentLoan,
)


def get_or_create_sector(name: str) -> Sector:
    sector = Sector.query.filter_by(name=name).first()
    if not sector:
        sector = Sector(name=name)
        db.session.add(sector)
        db.session.commit()
    return sector


def get_or_create_user(username: str, email: str, is_admin=False, is_ti=False, sector: Sector | None = None) -> User:
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            is_ti=is_ti,
            ativo=True,
            sector=sector,
        )
        # senha simples apenas para ambiente de teste
        user.set_password("demo1234")
        db.session.add(user)
        db.session.commit()
    return user


def seed_tasks(demo_user: User, demo_sector: Sector) -> None:
    """Cria tarefas de demonstração para alimentar o card de Atividades & Projetos."""
    if Task.query.filter(Task.description.ilike("DEMO - %")).count() > 0:
        return

    today = date.today()
    samples = [
        ("DEMO - Revisar documentação do sistema", today - timedelta(days=1), False),
        ("DEMO - Reunião de alinhamento com o time", today, False),
        ("DEMO - Fechar demandas pendentes", today - timedelta(days=5), True),
        ("DEMO - Planejamento de sprint", today + timedelta(days=2), False),
    ]

    for desc, d, done in samples:
        task = Task(
            description=desc,
            date=d,
            responsible=demo_user.username,
            completed=done,
            sector_id=demo_sector.id,
            user_id=demo_user.id,
        )
        db.session.add(task)

    db.session.commit()


def seed_reminders(demo_user: User, demo_sector: Sector) -> None:
    """Cria lembretes de demonstração para o card de Notificações Programadas."""
    if Reminder.query.filter(Reminder.name.ilike("DEMO - %")).count() > 0:
        return

    today = date.today()
    samples = [
        ("DEMO - Renovar licença antivírus", today + timedelta(days=7), False),
        ("DEMO - Verificar backups", today, False),
        ("DEMO - Revisar contratos de suporte", today - timedelta(days=3), True),
    ]

    for name, due, done in samples:
        reminder = Reminder(
            name=name,
            type="demo",
            due_date=due,
            responsible=demo_user.username,
            completed=done,
            sector_id=demo_sector.id,
            user_id=demo_user.id,
            status="ativo",
        )
        db.session.add(reminder)

    db.session.commit()


def seed_tickets(demo_user: User, demo_sector: Sector, ti_user: User) -> None:
    """Cria chamados de demonstração para o card de Tickets & Suporte."""
    if Chamado.query.filter(Chamado.titulo.ilike("DEMO - %")).count() > 0:
        return

    now = datetime.utcnow()
    samples = [
        ("DEMO - Problema no Wi-Fi", "Conexão instável", "Aberto"),
        ("DEMO - Solicitação de acesso ao sistema", "Usuário novo no setor", "Em Andamento"),
        ("DEMO - Impressora travada", "Erro de papel atolado", "Fechado"),
    ]

    for titulo, desc, status in samples:
        chamado = Chamado(
            titulo=titulo,
            descricao=desc,
            status=status,
            prioridade="Media",
            data_abertura=now - timedelta(hours=random.randint(1, 72)),
            solicitante_id=demo_user.id,
            setor_id=demo_sector.id,
            responsavel_ti_id=ti_user.id,
        )
        chamado.calcular_sla()
        db.session.add(chamado)

    db.session.commit()


def seed_equipments() -> list[Equipment]:
    """Cria alguns equipamentos de inventário se não existirem (marcados como DEMO)."""
    demo_equipments = []
    base = [
        ("DEMO - Notebook Dell Vostro", "Notebook", "Dell", "Vostro 14", "000DEM1"),
        ("DEMO - Notebook Lenovo ThinkPad", "Notebook", "Lenovo", "ThinkPad", "000DEM2"),
        ("DEMO - Projetor Epson X", "Projetor", "Epson", "X1200", "000DEM3"),
    ]

    for name, category, brand, model, patrimony in base:
        eq = Equipment.query.filter_by(patrimony=patrimony).first()
        if not eq:
            eq = Equipment(
                name=name,
                category=category,
                brand=brand,
                model=model,
                patrimony=patrimony,
                status="disponivel",
                condition="bom",
            )
            db.session.add(eq)
        demo_equipments.append(eq)

    db.session.commit()
    return demo_equipments


def seed_equipment_flow(demo_user: User, ti_user: User, equipments: list[Equipment]) -> None:
    """Cria reservas e empréstimos de demonstração para alimentar cards e telas de equipamentos."""
    if EquipmentReservation.query.filter(EquipmentReservation.purpose.ilike("DEMO - %")).count() > 0:
        return

    today = date.today()

    # Reserva pendente
    if equipments:
        eq1 = equipments[0]
        res1 = EquipmentReservation(
            equipment_id=eq1.id,
            user_id=demo_user.id,
            start_date=today + timedelta(days=1),
            start_time=time(9, 0),
            end_date=today + timedelta(days=1),
            end_time=time(18, 0),
            expected_return_date=today + timedelta(days=1),
            expected_return_time=time(18, 0),
            status="pendente",
            purpose="DEMO - Reserva pendente",
        )
        db.session.add(res1)

    # Reserva confirmada com empréstimo ativo
    if len(equipments) > 1:
        eq2 = equipments[1]
        res2 = EquipmentReservation(
            equipment_id=eq2.id,
            user_id=demo_user.id,
            start_date=today - timedelta(days=1),
            start_time=time(14, 0),
            end_date=today + timedelta(days=1),
            end_time=time(18, 0),
            expected_return_date=today + timedelta(days=1),
            expected_return_time=time(18, 0),
            status="confirmada",
            purpose="DEMO - Empréstimo ativo",
            approved_by_id=ti_user.id,
            approval_date=datetime.utcnow() - timedelta(hours=4),
        )
        db.session.add(res2)
        db.session.flush()  # garante res2.id

        loan = EquipmentLoan(
            equipment_id=eq2.id,
            user_id=demo_user.id,
            loan_date=datetime.utcnow() - timedelta(hours=3),
            loan_time=(datetime.utcnow() - timedelta(hours=3)).time(),
            expected_return_date=today + timedelta(days=1),
            expected_return_time=time(18, 0),
            status="ativo",
            delivered_by_id=ti_user.id,
            reservation_id=res2.id,
        )
        db.session.add(loan)

    # Reserva rejeitada
    if len(equipments) > 2:
        eq3 = equipments[2]
        res3 = EquipmentReservation(
            equipment_id=eq3.id,
            user_id=demo_user.id,
            start_date=today,
            start_time=time(10, 0),
            end_date=today,
            end_time=time(16, 0),
            expected_return_date=today,
            expected_return_time=time(16, 0),
            status="rejeitada",
            purpose="DEMO - Reserva rejeitada",
            approved_by_id=ti_user.id,
            approval_date=datetime.utcnow() - timedelta(hours=1),
            approval_notes="DEMO - conflito de agenda",
        )
        db.session.add(res3)

    db.session.commit()


def main() -> None:
    app = create_app()
    with app.app_context():
        print("[SEED] Iniciando população de dados de demonstração...")

        # Setor e usuários base de demo
        demo_sector = get_or_create_sector("DEMO - TI")
        demo_user = get_or_create_user(
            username="demo_user",
            email="demo_user@example.com",
            is_admin=False,
            is_ti=False,
            sector=demo_sector,
        )
        ti_user = get_or_create_user(
            username="demo_ti",
            email="demo_ti@example.com",
            is_admin=True,
            is_ti=True,
            sector=demo_sector,
        )

        seed_tasks(demo_user, demo_sector)
        seed_reminders(demo_user, demo_sector)
        seed_tickets(demo_user, demo_sector, ti_user)

        equipments = seed_equipments()
        seed_equipment_flow(demo_user, ti_user, equipments)

        print("[SEED] População de dados de demonstração concluída.")


if __name__ == "__main__":
    main()
