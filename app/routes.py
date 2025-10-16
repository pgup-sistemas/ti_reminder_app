import os
from datetime import date, datetime, time, timedelta
import time as time_module
from functools import wraps

from dateutil.relativedelta import relativedelta
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.utils import secure_filename

import markdown

from .auth_utils import login_required
from .forms import ChamadoAdminForm  # Importados formulários necessários
from .forms import (ChamadoEditForm, ChamadoForm, ComentarioTutorialForm, FeedbackTutorialForm,
                     ReminderForm, TaskForm, TutorialForm, UserEditForm)
from .models import Chamado  # Importados modelos necessários
from .models import (ComentarioChamado, ComentarioTutorial, EquipmentRequest,
                      FeedbackTutorial, Reminder, Sector, Task, Tutorial,
                      TutorialImage, User, VisualizacaoTutorial, db)
from .services.dashboard_service import DashboardService
from .services.permission_manager import PermissionManager
from .services.rfid_service import RFIDService
from .services.satisfaction_service import SatisfactionService
from .services.certification_service import CertificationService
from .services.performance_service import PerformanceService
from .utils.timezone_utils import (format_local_datetime,
                                    get_current_time_for_db, now_local,
                                    utc_to_local)


# Função para exigir que o usuário seja administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Acesso restrito ao administrador.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    # Importação local para evitar dependência circular se outros módulos importarem main.py diretamente
    from .models import Chamado, EquipmentRequest

    search = request.args.get("search", "").strip().lower()
    status = request.args.get("status", "").strip().lower()

    # --- Recorrência automática de lembretes ---
    if session.get("is_admin"):
        reminders = Reminder.query.all()
    else:
        reminders = Reminder.query.filter_by(user_id=session.get("user_id")).all()

    # Recorrência automática
    for r in reminders:
        if (
            r.due_date < date.today()
            and not r.notified
            and r.frequency
            and r.status == "ativo"
            and (not r.end_date or r.end_date > date.today())
            and (not r.pause_until or r.pause_until <= date.today())
        ):
            if r.frequency == "diario":
                next_due = r.due_date + relativedelta(days=1)
            elif r.frequency == "quinzenal":
                next_due = r.due_date + relativedelta(days=15)
            elif r.frequency == "mensal":
                next_due = r.due_date + relativedelta(months=1)
            elif r.frequency == "anual":
                next_due = r.due_date + relativedelta(years=1)
            else:
                continue
            novo = Reminder(
                name=r.name,
                type=r.type,
                due_date=next_due,
                responsible=r.responsible,
                frequency=r.frequency,
                sector_id=r.sector_id,
                user_id=r.user_id,
                status=r.status,
                pause_until=r.pause_until,
                end_date=r.end_date,
            )
            db.session.add(novo)
            r.notified = True  # marca o lembrete antigo para não duplicar
            db.session.commit()

    # Consulta de lembretes e tarefas
    user_id = session.get("user_id")
    is_admin = session.get("is_admin")
    is_ti = session.get("is_ti", False)

    if is_admin:
        reminders_count = Reminder.query.count()
        reminders_today = Reminder.query.filter(Reminder.due_date <= date.today()).all()
        tasks_today = Task.query.filter(Task.date <= date.today()).all()
        # Buscar chamados abertos (não fechados) - apenas campos existentes no banco
        chamados_abertos = (
            Chamado.query.filter(Chamado.status != "Fechado")
            .options(db.load_only(
                Chamado.id, Chamado.titulo, Chamado.descricao, Chamado.status,
                Chamado.prioridade, Chamado.data_abertura, Chamado.data_ultima_atualizacao,
                Chamado.data_fechamento, Chamado.solicitante_id, Chamado.setor_id,
                Chamado.responsavel_ti_id, Chamado.prazo_sla, Chamado.data_primeira_resposta,
                Chamado.sla_cumprido, Chamado.tempo_resposta_horas
            ))
            .order_by(Chamado.data_abertura.desc())
            .limit(10)
            .all()
        )  # Limita a 10 chamados mais recentes
        # Buscar equipamentos
        equipamentos_count = EquipmentRequest.query.count()
    else:
        reminders_count = Reminder.query.filter_by(user_id=user_id).count()
        reminders_today = Reminder.query.filter(
            Reminder.due_date <= date.today(), Reminder.user_id == user_id
        ).all()
        tasks_today = Task.query.filter(
            Task.date <= date.today(), Task.user_id == user_id
        ).all()
        # Buscar chamados do usuário ou do setor do usuário
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = (
            primeiro_lembrete.sector_id
            if primeiro_lembrete and primeiro_lembrete.sector_id
            else None
        )

        chamados_abertos = (
            Chamado.query.filter(
                (Chamado.solicitante_id == user_id)
                | (Chamado.setor_id == setor_id_usuario),
                Chamado.status != "Fechado",
            )
            .options(db.load_only(
                Chamado.id, Chamado.titulo, Chamado.descricao, Chamado.status,
                Chamado.prioridade, Chamado.data_abertura, Chamado.data_ultima_atualizacao,
                Chamado.data_fechamento, Chamado.solicitante_id, Chamado.setor_id,
                Chamado.responsavel_ti_id, Chamado.prazo_sla, Chamado.data_primeira_resposta,
                Chamado.sla_cumprido, Chamado.tempo_resposta_horas
            ))
            .order_by(Chamado.data_abertura.desc())
            .limit(10)
            .all()
        )  # Limita a 10 chamados mais recentes

        # Buscar equipamentos do usuário - apenas campos existentes no banco
        if is_ti:
            equipamentos_count = EquipmentRequest.query.count()
        else:
            equipamentos_count = EquipmentRequest.query.filter_by(
                requester_id=user_id
            ).count()

    # --- FILTRO E BUSCA LEMBRETES ---
    reminders_today_pend = [r for r in reminders_today if not r.completed]
    reminders_today_done = [r for r in reminders_today if r.completed]

    # --- DADOS DO SISTEMA ---
    import os
    import shutil
    from datetime import datetime

    # Contar usuários ativos (logados nas últimas 24h)
    usuarios_ativos = User.query.filter(User.ativo == True).count()

    # Último acesso do usuário atual
    current_user = User.query.get(user_id)
    ultimo_acesso = (
        datetime.now().strftime("%d/%m/%Y %H:%M") if current_user else "Nunca acessado"
    )

    # Informações de armazenamento (simulado)
    try:
        total, used, free = shutil.disk_usage("/")
        storage_used_gb = used / (1024**3)
        storage_total_gb = total / (1024**3)
        storage_percent = int((used / total) * 100)
    except:
        # Fallback para Windows ou erro
        storage_used_gb = 1.2
        storage_total_gb = 2.0
        storage_percent = 75
    if search:
        reminders_today_pend = [
            r
            for r in reminders_today_pend
            if search in r.name.lower() or search in r.responsible.lower()
        ]
        reminders_today_done = [
            r
            for r in reminders_today_done
            if search in r.name.lower() or search in r.responsible.lower()
        ]
    if status == "pendente":
        reminders_today_done = []
    elif status == "realizado":
        reminders_today_pend = []

    # --- FILTRO E BUSCA TAREFAS ---
    tasks_today_pend = [t for t in tasks_today if not t.completed]
    tasks_today_done = [t for t in tasks_today if t.completed]
    if search:
        tasks_today_pend = [
            t
            for t in tasks_today_pend
            if search in t.description.lower() or search in t.responsible.lower()
        ]
        tasks_today_done = [
            t
            for t in tasks_today_done
            if search in t.description.lower() or search in t.responsible.lower()
        ]
    if status == "pendente":
        tasks_today_done = []
    elif status == "realizado":
        tasks_today_pend = []

    # --- ATIVIDADES RECENTES ---
    # Combinar atividades recentes de diferentes fontes
    atividades_recentes = []

    # Adicionar lembretes recentes
    for r in reminders_today[:5]:  # Limitar a 5 lembretes mais recentes
        atividades_recentes.append(
            {
                "tipo": "lembrete",
                "data": r.due_date,
                "titulo": r.name,
                "status": "Realizado" if r.completed else "Pendente",
                "icone": "bell",
                "cor": "success" if r.completed else "warning",
            }
        )

    # Adicionar tarefas recentes
    for t in tasks_today[:5]:  # Limitar a 5 tarefas mais recentes
        atividades_recentes.append(
            {
                "tipo": "tarefa",
                "data": t.date,
                "titulo": t.description,
                "status": "Concluída" if t.completed else "Pendente",
                "icone": "tasks",
                "cor": "success" if t.completed else "primary",
            }
        )

    # Adicionar chamados recentes
    for c in chamados_abertos[:5]:  # Limitar a 5 chamados mais recentes
        atividades_recentes.append(
            {
                "tipo": "chamado",
                "data": c.data_abertura,
                "titulo": c.titulo,
                "status": c.status,
                "icone": "ticket-alt",
                "cor": "info" if c.status == "Em Andamento" else "warning",
            }
        )

    # Ordenar atividades por data (mais recentes primeiro)
    # Converter todas as datas para datetime para evitar erro de comparação entre date e datetime
    for atividade in atividades_recentes:
        if isinstance(atividade["data"], date) and not isinstance(
            atividade["data"], datetime
        ):
            # Converter date para datetime
            atividade["data"] = datetime.combine(atividade["data"], time.min)

    atividades_recentes.sort(key=lambda x: x["data"], reverse=True)

    # Limitar a 10 atividades no total
    atividades_recentes = atividades_recentes[:10]

    # Calcular estatísticas de SLA (apenas para administradores)
    sla_vencidos = 0
    sla_criticos = 0
    sla_ok = 0
    performance_sla = 0

    if is_admin:
        # Buscar todos os chamados abertos (não fechados) - apenas campos existentes
        chamados_abertos_sla = Chamado.query.filter(Chamado.status != "Fechado").options(db.load_only(
            Chamado.id, Chamado.titulo, Chamado.descricao, Chamado.status,
            Chamado.prioridade, Chamado.data_abertura, Chamado.data_ultima_atualizacao,
            Chamado.data_fechamento, Chamado.solicitante_id, Chamado.setor_id,
            Chamado.responsavel_ti_id, Chamado.prazo_sla, Chamado.data_primeira_resposta,
            Chamado.sla_cumprido, Chamado.tempo_resposta_horas
        )).all()

        # Calcular SLA para chamados que não têm prazo definido
        for chamado in chamados_abertos_sla:
            if not chamado.prazo_sla:
                chamado.calcular_sla()

        # Commit das mudanças no SLA
        db.session.commit()

        # Agora contar os status de SLA
        for chamado in chamados_abertos_sla:
            status_sla = chamado.status_sla
            if status_sla == "vencido":
                sla_vencidos += 1
            elif status_sla == "atencao":
                sla_criticos += 1
            elif status_sla == "normal":
                sla_ok += 1

        # Calcular performance de SLA dos últimos 30 dias
        from datetime import timedelta

        trinta_dias_atras = get_current_time_for_db() - timedelta(days=30)

        chamados_fechados_30_dias = Chamado.query.filter(
            Chamado.data_fechamento >= trinta_dias_atras,
            Chamado.data_fechamento.isnot(None),
        ).options(db.load_only(
            Chamado.id, Chamado.titulo, Chamado.descricao, Chamado.status,
            Chamado.prioridade, Chamado.data_abertura, Chamado.data_ultima_atualizacao,
            Chamado.data_fechamento, Chamado.solicitante_id, Chamado.setor_id,
            Chamado.responsavel_ti_id, Chamado.prazo_sla, Chamado.data_primeira_resposta,
            Chamado.sla_cumprido, Chamado.tempo_resposta_horas
        )).all()

        if chamados_fechados_30_dias:
            # Calcular SLA para chamados fechados que não têm sla_cumprido definido
            for chamado in chamados_fechados_30_dias:
                if chamado.sla_cumprido is None and chamado.prazo_sla:
                    # Se foi fechado dentro do prazo, considera cumprido
                    chamado.sla_cumprido = chamado.data_fechamento <= chamado.prazo_sla

            db.session.commit()

            sla_cumpridos = len(
                [c for c in chamados_fechados_30_dias if c.sla_cumprido]
            )
            performance_sla = (
                round((sla_cumpridos / len(chamados_fechados_30_dias)) * 100)
                if chamados_fechados_30_dias
                else 100
            )

    return render_template(
        "index.html",
        reminders_count=reminders_count,
        lembretes_count=len(reminders_today_pend),
        tasks_count=len(tasks_today),
        chamados_count=len(chamados_abertos),
        equipamentos_count=equipamentos_count,
        reminders_today=reminders_today_pend,
        tasks_today=tasks_today,
        chamados_abertos=chamados_abertos,
        atividades_recentes=atividades_recentes,
        usuarios_ativos=usuarios_ativos,
        ultimo_acesso=ultimo_acesso,
        storage_used_gb=storage_used_gb,
        storage_total_gb=storage_total_gb,
        storage_percent=storage_percent,
        is_admin=session.get("is_admin", False),
        sla_vencidos=sla_vencidos,
        sla_criticos=sla_criticos,
        sla_ok=sla_ok,
        performance_sla=performance_sla,
    )


from io import BytesIO

import pandas as pd
# --- Lembretes ---
from dateutil.relativedelta import relativedelta
from flask import make_response, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


@bp.route("/reminders/complete/<int:id>", methods=["POST"])
def complete_reminder(id):
    if session.get("is_admin"):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    reminder.completed = True
    db.session.commit()
    flash("Lembrete marcado como realizado!", "success")
    return redirect(url_for("main.reminders"))


@bp.route("/reminders/toggle_status/<int:id>", methods=["POST"])
@login_required
def toggle_reminder_status(id):
    if session.get("is_admin"):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()

    # Obter o status desejado do formulário, se fornecido
    target_status = request.form.get("target_status")

    if target_status == "cancelado":
        reminder.status = "cancelado"
        flash("Lembrete cancelado!", "danger")
    elif reminder.status == "ativo":
        reminder.status = "pausado"
        flash("Lembrete pausado!", "warning")
    elif reminder.status == "pausado":
        reminder.status = "ativo"
        reminder.pause_until = None
        flash("Lembrete reativado!", "success")
    elif reminder.status == "cancelado":
        reminder.status = "ativo"
        flash("Lembrete reativado!", "success")

    db.session.commit()
    return redirect(url_for("main.reminders"))


from flask import request


@bp.route("/reminders/json")
@login_required
def reminders_json():
    # Mesma lógica de ordenação e filtro da rota principal
    order_by = request.args.get("order_by", "id")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    if session.get("is_admin"):
        query = Reminder.query
    else:
        query = Reminder.query.filter_by(user_id=session.get("user_id"))

    # Aplica a ordenação
    if order_by == "due_date":
        query = query.order_by(getattr(Reminder.due_date, order)())
    elif order_by == "name":
        query = query.order_by(getattr(Reminder.name, order)())
    else:  # id ou padrão
        query = query.order_by(Reminder.id.desc())

    # Aplica a paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reminders = pagination.items

    # Converte para dicionário para serialização JSON
    reminders_data = []
    for r in reminders:
        reminders_data.append(
            {
                "id": r.id,
                "name": r.name,
                "type": r.type,
                "due_date": r.due_date.isoformat(),
                "responsible": r.responsible,
                "frequency": r.frequency,
                "sector": r.sector.name if r.sector else "",
                "completed": r.completed,
                "status_control": r.status,  # Campo de controle de status (ativo, pausado, cancelado)
                "pause_until": r.pause_until.isoformat() if r.pause_until else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "status": "completed"
                if r.completed
                else "expired"
                if r.due_date < date.today()
                else "ok"
                if r.due_date == date.today()
                else "alert"
                if (r.due_date - date.today()).days <= 7
                else "pending",
            }
        )

    return jsonify(
        {
            "reminders": reminders_data,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    )


@bp.route("/reminders", methods=["GET", "POST"])
@login_required
def reminders():
    form = ReminderForm()

    # Popular o select de setores
    from .models import Sector

    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione")] + [(s.id, s.name) for s in sectors]

    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ""
        if new_sector_name:
            existing = Sector.query.filter_by(name=new_sector_name).first()
            if existing:
                sector = existing
            else:
                sector = Sector(name=new_sector_name)
                db.session.add(sector)
                db.session.commit()
            sector_id = sector.id
        elif sector_id == 0:
            sector_id = None

        reminder = Reminder(
            name=form.name.data,
            type=form.type.data,
            due_date=form.due_date.data,
            responsible=form.responsible.data,
            frequency=form.frequency.data,
            sector_id=sector_id,
            user_id=session.get("user_id"),
            status=form.status.data,
            pause_until=form.pause_until.data,
            end_date=form.end_date.data,
            created_at=get_current_time_for_db(),
        )
        db.session.add(reminder)
        db.session.commit()
        flash("Lembrete cadastrado com sucesso!", "success")
        return redirect(url_for("main.reminders"))

    return render_template("reminders.html", form=form)


@bp.route("/reminders/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_reminder(id):
    from .models import Sector

    # Admin pode editar qualquer lembrete, usuário comum só os próprios
    if session.get("is_admin"):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    form = ReminderForm(obj=reminder)
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione")] + [(s.id, s.name) for s in sectors]
    if reminder.sector_id:
        form.sector_id.data = reminder.sector_id
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ""
        if new_sector_name:
            existing = Sector.query.filter_by(name=new_sector_name).first()
            if existing:
                sector = existing
            else:
                sector = Sector(name=new_sector_name)
                db.session.add(sector)
                db.session.commit()
            sector_id = sector.id
        elif sector_id == 0:
            sector_id = None
        form.populate_obj(reminder)
        reminder.sector_id = sector_id
        db.session.commit()
        flash("Lembrete atualizado!", "success")
        return redirect(url_for("main.reminders"))
    return render_template(
        "reminders.html", reminders=Reminder.query.all(), form=form, edit_id=id
    )


@bp.route("/reminders/delete/<int:id>", methods=["POST"])
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    flash("Lembrete excluído!", "success")
    return redirect(url_for("main.reminders"))

    # --- API de Notificações ---
    # Rota movida para o final do arquivo para evitar duplicação

    # Chamados atualizados recentemente (últimas 24 horas)
    yesterday = datetime.now() - timedelta(hours=24)

    # Buscar chamados do usuário ou que o usuário é responsável
    chamados_query = Chamado.query.filter(Chamado.data_ultima_atualizacao > yesterday)

    # Se não for TI, filtrar apenas chamados do usuário
    if not is_ti:
        chamados_query = chamados_query.filter(Chamado.solicitante_id == user_id)

    chamados_updated = [
        {
            "id": c.id,
            "titulo": c.titulo,
            "status": c.status,
            "ultima_atualizacao": c.data_ultima_atualizacao.strftime("%d/%m/%Y %H:%M"),
        }
        for c in chamados_query.all()
    ]

    return jsonify(
        {
            "reminders_expiring": reminders_expiring,
            "tasks_overdue": tasks_overdue,
            "chamados_updated": chamados_updated,
        }
    )


# --- Administração de Usuários ---
@bp.route("/admin/users")
@login_required
@admin_required
def users_admin():
    from .models import User

    users = User.query.order_by(User.id).all()
    return render_template("users.html", users=users)


@bp.route("/admin/users/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):
    import logging

    from .forms import UserEditForm
    from .models import Sector, User

    # Configura o logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    user = User.query.get_or_404(id)
    logger.debug(
        f"Usuário carregado: {user.username}, Email: {user.email}, Setor: {user.sector_id}, Admin: {user.is_admin}, TI: {user.is_ti}"
    )

    form = UserEditForm(obj=user)
    logger.debug(
        f"Formulário carregado com dados do usuário. Dados do formulário: {form.data}"
    )

    # Define o setor atual do usuário no formulário
    if user.sector_id:
        form.sector_id.data = user.sector_id

    # Se o usuário for o próprio, não pode remover os privilégios de admin
    if user.id == session.get("user_id"):
        form.is_admin.data = (
            True  # Garante que o admin não remova seus próprios privilégios
        )

    if form.validate_on_submit():
        try:
            logger.debug(f"Formulário validado. Dados do formulário: {form.data}")

            # Verifica se o email já está em uso por outro usuário
            existing_user = User.query.filter(
                User.email == form.email.data, User.id != user.id
            ).first()
            if existing_user:
                logger.warning(
                    f"Tentativa de usar email já existente: {form.email.data}"
                )
                flash("Este email já está em uso por outro usuário.", "danger")
                return redirect(url_for("main.edit_user", id=user.id))

            # Verifica se o nome de usuário já está em uso por outro usuário
            existing_username = User.query.filter(
                User.username == form.username.data, User.id != user.id
            ).first()
            if existing_username:
                logger.warning(
                    f"Tentativa de usar nome de usuário já existente: {form.username.data}"
                )
                flash(
                    "Este nome de usuário já está em uso por outro usuário.", "danger"
                )
                return redirect(url_for("main.edit_user", id=user.id))

            # Log dos dados atuais do usuário antes da atualização
            logger.debug(
                f"Dados atuais do usuário - Username: {user.username}, Email: {user.email}, Setor: {user.sector_id}, Admin: {user.is_admin}, TI: {user.is_ti}"
            )

            # Atualiza os dados básicos
            user.username = form.username.data
            user.email = form.email.data
            logger.debug(
                f"Novos dados do usuário - Username: {user.username}, Email: {user.email}"
            )

            # Atualiza o setor
            user.sector_id = form.sector_id.data if form.sector_id.data != 0 else None
            logger.debug(f"Novo setor do usuário: {user.sector_id}")

            # Atualiza o status de TI (qualquer usuário pode ser marcado como TI)
            user.is_ti = form.is_ti.data
            logger.debug(f"Status de TI atualizado para: {user.is_ti}")

            # Impede que o próprio administrador remova seus privilégios
            if user.id == session.get("user_id"):
                user.is_admin = (
                    True  # Garante que o admin não remova seus próprios privilégios
                )
                logger.debug(
                    "Usuário é o próprio administrador, mantendo privilégios de admin"
                )
            else:
                # Verifica se é o último administrador ativo
                if user.is_admin and not form.is_admin.data:
                    admin_count = User.query.filter_by(
                        is_admin=True, ativo=True
                    ).count()
                    if admin_count <= 1:  # Se for o único admin ativo
                        logger.warning(
                            "Tentativa de remover o último administrador ativo"
                        )
                        flash(
                            "Não é possível remover os privilégios de administrador do último administrador ativo.",
                            "danger",
                        )
                        return redirect(url_for("main.edit_user", id=user.id))
                user.is_admin = form.is_admin.data
                logger.debug(f"Status de admin atualizado para: {user.is_admin}")

            # Atualiza a senha se solicitado
            if form.change_password.data and form.new_password.data:
                if len(form.new_password.data) < 6:
                    logger.warning(
                        "Tentativa de definir senha com menos de 6 caracteres"
                    )
                    flash("A senha deve ter pelo menos 6 caracteres.", "danger")
                    return redirect(url_for("main.edit_user", id=user.id))
                user.set_password(form.new_password.data)
                logger.info("Senha do usuário atualizada com sucesso")
                flash("Senha alterada com sucesso!", "success")

            # Salva as alterações no banco de dados
            db.session.commit()
            logger.info(f"Usuário {user.id} atualizado com sucesso no banco de dados")

            flash("Usuário atualizado com sucesso!", "success")
            return redirect(url_for("main.users_admin"))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar usuário: {str(e)}", exc_info=True)
            flash(f"Erro ao atualizar usuário: {str(e)}", "danger")
            return redirect(url_for("main.edit_user", id=user.id))

    return render_template("edit_user.html", form=form, user=user)


@bp.route("/admin/users/toggle/<int:id>", methods=["POST"])
@login_required
@admin_required
def toggle_user(id):
    from .models import User

    user = User.query.get_or_404(id)

    # Impede que o usuário desative a si mesmo
    if id == session.get("user_id"):
        flash("Você não pode desativar sua própria conta.", "danger")
        return redirect(url_for("main.users_admin"))

    # Verifica se está tentando desativar o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash(
                "Não é possível desativar o último administrador ativo do sistema.",
                "danger",
            )
            return redirect(url_for("main.users_admin"))

    user.ativo = not user.ativo

    try:
        db.session.commit()
        status = "ativado" if user.ativo else "desativado"
        flash(f"Usuário {status} com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Ocorreu um erro ao atualizar o status do usuário.", "danger")

    return redirect(url_for("main.users_admin"))


@bp.route("/admin/users/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_user(id):
    from .models import User

    user = User.query.get_or_404(id)

    # Impede que o usuário exclua a si mesmo
    if id == session.get("user_id"):
        flash("Você não pode excluir sua própria conta.", "danger")
        return redirect(url_for("main.users_admin"))

    # Verifica se está tentando excluir o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash(
                "Não é possível excluir o último administrador ativo do sistema.",
                "danger",
            )
            return redirect(url_for("main.users_admin"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash("Usuário excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(
            "Ocorreu um erro ao excluir o usuário. Por favor, tente novamente.",
            "danger",
        )

    return redirect(url_for("main.users_admin"))


@bp.route("/register", methods=["GET", "POST"])
@login_required
@admin_required
def register():
    from .forms import UserRegisterForm
    from .models import User

    form = UserRegisterForm()

    if form.validate_on_submit():
        # Verifica se já existe um usuário com o mesmo nome de usuário ou email
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash("Nome de usuário ou email já está em uso.", "danger")
            return render_template(
                "register_admin.html", form=form, title="Registrar Novo Usuário"
            )

        # Cria o novo usuário
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data if hasattr(form, "is_admin") else False,
            is_ti=form.is_ti.data if hasattr(form, "is_ti") else False,
            ativo=True,
        )

        # Define a senha
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash("Usuário criado com sucesso!", "success")
            return redirect(url_for("main.users_admin"))
        except Exception as e:
            db.session.rollback()
            flash(
                "Ocorreu um erro ao criar o usuário. Por favor, tente novamente.",
                "danger",
            )

    return render_template(
        "register_admin.html", form=form, title="Registrar Novo Usuário"
    )


@bp.route("/admin/users/reset_password/<int:id>", methods=["POST"])
@login_required
@admin_required
def reset_user_password(id):
    import secrets
    import string

    from werkzeug.security import generate_password_hash

    from .models import User

    user = User.query.get_or_404(id)

    # Gerar uma senha aleatória segura
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(12))
        # Garantir que a senha tenha pelo menos um caractere especial e um número
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%&*" for c in password)
        ):
            break

    # Definir a nova senha
    user.set_password(password)
    db.session.commit()

    # Aqui você pode adicionar o código para enviar a nova senha por email
    # send_password_reset_email(user.email, password)

    flash(
        f"Senha redefinida com sucesso! Nova senha: {password} - Recomenda-se copiar e enviar ao usuário por um canal seguro.",
        "success",
    )
    return redirect(url_for("main.users_admin"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def user_profile():
    """Página de perfil do usuário para alterar senha"""
    from .forms import ChangePasswordForm
    from .models import User

    user_id = session.get("user_id")
    user = User.query.get_or_404(user_id)
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verificar se a senha atual está correta
        if not user.check_password(form.current_password.data):
            flash("Senha atual incorreta.", "danger")
            return render_template("user_profile.html", form=form, user=user)

        # Alterar para a nova senha
        user.set_password(form.new_password.data)
        db.session.commit()

        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for("main.user_profile"))

    return render_template("user_profile.html", form=form, user=user)


# --- Rotas principais ---


@bp.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard principal do sistema - versão refatorada usando serviços
    """
    from flask import request, flash
    from datetime import datetime

    # Obter permissões do usuário
    permissions = PermissionManager.get_user_permissions()

    # Processar filtros da requisição
    filters = {
        'task_status': request.args.get("task_status", ""),
        'reminder_status': request.args.get("reminder_status", ""),
        'chamado_status': request.args.get("chamado_status", ""),
        'start_date': None,
        'end_date': None,
        'sector_id': request.args.get("sector_id", type=int),
        'user_id': request.args.get("user_id", type=int),
    }

    # Converter datas com validação
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")

    if start_date_str:
        try:
            filters['start_date'] = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data inicial inválida.", "warning")

    if end_date_str:
        try:
            filters['end_date'] = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data final inválida.", "warning")

    # Obter dados filtrados usando o serviço
    dashboard_data = DashboardService.get_filtered_data(filters, permissions)

    # Preparar dados para o template
    template_data = {
        # Estatísticas de tarefas
        'tasks_total': dashboard_data['stats']['tasks']['total'],
        'tasks_done': dashboard_data['stats']['tasks']['done'],
        'tasks_pending': dashboard_data['stats']['tasks']['pending'],
        'tasks_expired': dashboard_data['stats']['tasks']['expired'],

        # Estatísticas de lembretes
        'reminders_total': dashboard_data['stats']['reminders']['total'],
        'reminders_done': dashboard_data['stats']['reminders']['done'],
        'reminders_pending': dashboard_data['stats']['reminders']['pending'],

        # Estatísticas de chamados
        'chamados_total': dashboard_data['stats']['chamados']['total'],
        'chamados_aberto': dashboard_data['stats']['chamados']['aberto'],
        'chamados_em_andamento': dashboard_data['stats']['chamados']['em_andamento'],
        'chamados_resolvido': dashboard_data['stats']['chamados']['resolvido'],
        'chamados_fechado': dashboard_data['stats']['chamados']['fechado'],

        # Estatísticas de equipamentos
        'equipamentos_total': dashboard_data['stats']['equipamentos']['total'],
        'equipamentos_solicitados': dashboard_data['stats']['equipamentos']['solicitados'],
        'equipamentos_aprovados': dashboard_data['stats']['equipamentos']['aprovados'],
        'equipamentos_entregues': dashboard_data['stats']['equipamentos']['entregues'],
        'equipamentos_devolvidos': dashboard_data['stats']['equipamentos']['devolvidos'],
        'equipamentos_negados': dashboard_data['stats']['equipamentos']['negados'],

        # Dados para gráficos de evolução
        'meses_labels': dashboard_data['chart_data']['evolution']['labels'],
        'tarefas_por_mes': dashboard_data['chart_data']['evolution']['tarefas'],
        'tarefas_concluidas_por_mes': dashboard_data['chart_data']['evolution']['tarefas'],  # Mantém compatibilidade
        'lembretes_por_mes': dashboard_data['chart_data']['evolution']['lembretes'],
        'lembretes_realizados_por_mes': dashboard_data['chart_data']['evolution']['lembretes'],  # Mantém compatibilidade
        'chamados_por_mes': dashboard_data['chart_data']['evolution']['chamados'],
        'equipamentos_por_mes': dashboard_data['chart_data']['evolution']['equipamentos'],

        # Dados para gráficos de setores
        'setores_labels': dashboard_data['chart_data']['sectors']['labels'],
        'tarefas_por_setor': dashboard_data['chart_data']['sectors']['tarefas'],
        'lembretes_por_setor': dashboard_data['chart_data']['sectors']['lembretes'],
        'chamados_por_setor': dashboard_data['chart_data']['sectors']['chamados'],
        'equipamentos_por_setor': dashboard_data['chart_data']['sectors']['equipamentos'],

        # Dados de tutoriais
        'total_tutoriais': dashboard_data['chart_data']['tutorials']['total'],
        'top_tutoriais_labels': dashboard_data['chart_data']['tutorials']['top_labels'],
        'top_tutoriais_values': dashboard_data['chart_data']['tutorials']['top_values'],
        'feedbacks_util': dashboard_data['chart_data']['tutorials']['feedbacks_util'],
        'feedbacks_nao_util': dashboard_data['chart_data']['tutorials']['feedbacks_nao_util'],
        'top_feedback_labels': dashboard_data['chart_data']['tutorials']['top_labels'],  # Reutiliza
        'top_feedback_values': dashboard_data['chart_data']['tutorials']['top_values'],  # Reutiliza

        # Dados SLA (apenas para admin)
        'sla_vencidos': dashboard_data['sla_data'].get('vencidos', 0),
        'sla_criticos': dashboard_data['sla_data'].get('criticos', 0),
        'sla_ok': dashboard_data['sla_data'].get('ok', 0),
        'performance_sla': dashboard_data['sla_data'].get('performance', 0),
        'chamados_sla': dashboard_data['sla_data'].get('chamados_sla', []),

        # Performance geral do sistema
        'overall_performance': dashboard_data['performance'],

        # Dados para filtros
        'sectors': Sector.query.order_by(Sector.name).all(),
        'users': User.query.order_by(User.username).all(),
        'selected_sector': filters['sector_id'],
        'selected_user': filters['user_id'],
    }

    # Adicionar tutoriais mais visualizados/utilizados (compatibilidade com template antigo)
    if dashboard_data['chart_data']['tutorials']['top_labels']:
        template_data['tutorial_mais_visualizado'] = Tutorial.query.filter_by(
            titulo=dashboard_data['chart_data']['tutorials']['top_labels'][0]
        ).first()

    # Encontrar tutorial mais útil
    tutorial_mais_util = None
    max_util = -1
    for tutorial in Tutorial.query.all():
        util = sum(1 for f in tutorial.feedbacks if f.util)
        if util > max_util:
            max_util = util
            tutorial_mais_util = tutorial
    template_data['tutorial_mais_util'] = tutorial_mais_util

    return render_template("dashboard.html", **template_data)


@bp.route("/export/excel")
def export_excel():
    from datetime import date  # Adicionado datetime, date
    from datetime import datetime
    from io import BytesIO  # BytesIO já estava importado globalmente

    import pandas as pd  # pd já estava importado globalmente
    from flask import \
        request  # session já estava importado globalmente, mas garantindo
    from flask import session

    from .models import Chamado  # Adicionado Tutorial
    from .models import Reminder, Sector, Task, Tutorial, User

    task_status = request.args.get("task_status", "")
    reminder_status = request.args.get("reminder_status", "")
    chamado_status = request.args.get("chamado_status", "")  # Novo
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    sector_id = request.args.get("sector_id", type=int)
    user_id_filter = request.args.get(
        "user_id", type=int
    )  # Renomeado para evitar conflito com user_id da sessão

    # Conversão de datas
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass  # Ignorar data inválida para exportação, ou poderia dar flash
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    task_query = Task.query
    reminder_query = Reminder.query
    chamado_query = Chamado.query  # Novo
    equipment_query = EquipmentRequest.query  # Query para equipamentos

    current_user_id = session.get("user_id")
    is_admin = session.get("is_admin", False)
    is_ti = session.get("is_ti", False)

    # Filtros de permissão
    if not is_admin and not is_ti:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
        equipment_query = equipment_query.filter(
            EquipmentRequest.requester_id == current_user_id
        )
    elif not is_admin and is_ti:
        user = User.query.get(current_user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=current_user_id).first()
        setor_id_usuario = (
            primeiro_lembrete.sector_id
            if primeiro_lembrete and primeiro_lembrete.sector_id
            else None
        )
        chamado_query = chamado_query.filter(
            (Chamado.solicitante_id == current_user_id)
            | (Chamado.setor_id == setor_id_usuario)
        )
        equipment_query = (
            EquipmentRequest.query
        )  # TI pode ver todas as solicitações de equipamento

    if task_status == "done":
        task_query = task_query.filter(Task.completed == True)
    elif task_status == "pending":
        task_query = task_query.filter(
            Task.completed == False, Task.date >= date.today()
        )
    elif task_status == "expired":
        task_query = task_query.filter(
            Task.completed == False, Task.date < date.today()
        )

    if reminder_status == "done":
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == "pending":
        reminder_query = reminder_query.filter(Reminder.completed == False)

    if chamado_status:
        chamado_query = chamado_query.filter(Chamado.status == chamado_status)

    if start_date:
        task_query = task_query.filter(Task.date >= start_date)
        reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura >= start_date)
        equipment_query = equipment_query.filter(
            EquipmentRequest.request_date >= start_date
        )
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)
        equipment_query = equipment_query.filter(
            EquipmentRequest.request_date <= end_date
        )

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)
        # Filtro para equipamentos por setor de destino
        setor_nome = (
            Sector.query.get(sector_id).name if Sector.query.get(sector_id) else ""
        )
        equipment_query = equipment_query.filter(
            EquipmentRequest.destination_sector.contains(setor_nome)
        )

    if user_id_filter and (
        is_admin or is_ti
    ):  # Admin ou TI pode filtrar por qualquer usuário
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)
        equipment_query = equipment_query.filter(
            EquipmentRequest.requester_id == user_id_filter
        )

    export_type = request.args.get("export_type", "all")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        title_format = workbook.add_format(
            {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
        )
        header_format = workbook.add_format(
            {
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#D7E4BC",
                "border": 1,
            }
        )

        if export_type in ["all", "tasks"]:
            tasks = task_query.all()
            tasks_data = [
                {
                    "Descrição": t.description,
                    "Data": t.date.strftime("%d/%m/%Y") if t.date else "",
                    "Responsável": t.responsible,
                    "Setor": t.sector.name if t.sector else "",
                    "Usuário": t.usuario.username if t.usuario else "",
                    "Concluída": "Sim" if t.completed else "Não",
                }
                for t in tasks
            ]
            df_tasks = pd.DataFrame(tasks_data)
            df_tasks.to_excel(
                writer, sheet_name="Tarefas", index=False, header=False, startrow=1
            )
            worksheet_tasks = writer.sheets["Tarefas"]
            worksheet_tasks.merge_range("A1:F1", "Relatório de Tarefas", title_format)
            for col_num, value in enumerate(df_tasks.columns.values):
                worksheet_tasks.write(0, col_num, value, header_format)
            # Auto-ajustar colunas (exemplo)
            for i, col in enumerate(df_tasks.columns):
                column_len = max(df_tasks[col].astype(str).map(len).max(), len(col))
                worksheet_tasks.set_column(i, i, column_len + 2)

        if export_type in ["all", "reminders"]:
            reminders = reminder_query.all()
            reminders_data = [
                {
                    "Nome": r.name,
                    "Tipo": r.type,
                    "Vencimento": r.due_date.strftime("%d/%m/%Y") if r.due_date else "",
                    "Responsável": r.responsible,
                    "Setor": r.sector.name if r.sector else "",
                    "Usuário": r.usuario.username if r.usuario else "",
                    "Realizado": "Sim" if r.completed else "Não",
                }
                for r in reminders
            ]
            df_reminders = pd.DataFrame(reminders_data)
            df_reminders.to_excel(
                writer, sheet_name="Lembretes", index=False, header=False, startrow=1
            )
            worksheet_reminders = writer.sheets["Lembretes"]
            worksheet_reminders.merge_range(
                "A1:G1", "Relatório de Lembretes", title_format
            )
            for col_num, value in enumerate(df_reminders.columns.values):
                worksheet_reminders.write(0, col_num, value, header_format)
            for i, col in enumerate(df_reminders.columns):
                column_len = max(df_reminders[col].astype(str).map(len).max(), len(col))
                worksheet_reminders.set_column(i, i, column_len + 2)

        if export_type in ["all", "chamados"]:  # Novo bloco para chamados
            chamados = chamado_query.all()
            chamados_data = [
                {
                    "ID": c.id,
                    "Título": c.titulo,
                    "Status": c.status,
                    "Prioridade": c.prioridade,
                    "Abertura": c.data_abertura.strftime("%d/%m/%Y %H:%M")
                    if c.data_abertura
                    else "",
                    "Prazo SLA": c.prazo_sla.strftime("%d/%m/%Y %H:%M")
                    if c.prazo_sla
                    else "N/A",
                    "Status SLA": c.status_sla if hasattr(c, "status_sla") else "N/A",
                    "Solicitante": c.solicitante.username if c.solicitante else "",
                    "Setor": c.setor.name if c.setor else "",
                    "Responsável TI": c.responsavel_ti.username
                    if c.responsavel_ti
                    else "",
                    "Fechamento": c.data_fechamento.strftime("%d/%m/%Y %H:%M")
                    if c.data_fechamento
                    else "Em Aberto",
                }
                for c in chamados
            ]
            df_chamados = pd.DataFrame(chamados_data)
            if not df_chamados.empty:
                df_chamados.to_excel(
                    writer, sheet_name="Chamados", index=False, header=False, startrow=2
                )
                worksheet_chamados = writer.sheets["Chamados"]
                worksheet_chamados.merge_range(
                    "A1:K1", "Relatório de Chamados", title_format
                )
                for col_num, value in enumerate(df_chamados.columns.values):
                    worksheet_chamados.write(1, col_num, value, header_format)
                for i, col in enumerate(df_chamados.columns):
                    column_len = max(
                        df_chamados[col].astype(str).map(len).max(), len(col)
                    )
                    worksheet_chamados.set_column(i, i, column_len + 2)
            else:
                # Criar planilha mesmo sem dados
                worksheet_chamados = workbook.add_worksheet("Chamados")
                worksheet_chamados.merge_range(
                    "A1:K1", "Relatório de Chamados", title_format
                )
                worksheet_chamados.write_row(
                    1,
                    0,
                    [
                        "ID",
                        "Título",
                        "Status",
                        "Prioridade",
                        "Abertura",
                        "Prazo SLA",
                        "Status SLA",
                        "Solicitante",
                        "Setor",
                        "Responsável TI",
                        "Fechamento",
                    ],
                    header_format,
                )
                worksheet_chamados.write(
                    2, 0, "Nenhum chamado encontrado com os filtros aplicados"
                )

        if export_type in ["all", "equipamentos"]:  # Bloco para equipamentos
            equipamentos = equipment_query.all()
            equipamentos_data = [
                {
                    "ID": e.id,
                    "Descrição": e.description,
                    "Patrimônio": e.patrimony,
                    "Tipo": e.equipment_type,
                    "Status": e.status,
                    "Solicitante": e.requester.username if e.requester else "",
                    "Data Solicitação": e.request_date.strftime("%d/%m/%Y")
                    if e.request_date
                    else "",
                }
                for e in equipamentos
            ]
            df_equipamentos = pd.DataFrame(equipamentos_data)
            df_equipamentos.to_excel(
                writer, sheet_name="Equipamentos", index=False, header=False, startrow=1
            )
            worksheet_equipamentos = writer.sheets["Equipamentos"]
            worksheet_equipamentos.merge_range(
                "A1:G1", "Relatório de Equipamentos", title_format
            )
            for col_num, value in enumerate(df_equipamentos.columns.values):
                worksheet_equipamentos.write(0, col_num, value, header_format)
            for i, col in enumerate(df_equipamentos.columns):
                column_len = max(
                    df_equipamentos[col].astype(str).map(len).max(), len(col)
                )
                worksheet_equipamentos.set_column(i, i, column_len + 2)

        if export_type in ["all", "tutoriais"]:
            # Consulta para obter os tutoriais
            tutorial_query = Tutorial.query

            # Aplicar filtros de data se fornecidos
            if start_date:
                tutorial_query = tutorial_query.filter(
                    Tutorial.data_criacao >= start_date
                )
            if end_date:
                tutorial_query = tutorial_query.filter(
                    Tutorial.data_criacao <= end_date
                )

            # Aplicar filtro de usuário se fornecido
            if user_id_filter and (is_admin or is_ti):
                tutorial_query = tutorial_query.filter(
                    Tutorial.autor_id == user_id_filter
                )

            # Obter todos os tutoriais filtrados
            tutoriais = tutorial_query.all()

            tutoriais_data = [
                {
                    "Título": t.titulo,
                    "Categoria": t.categoria or "",
                    "Autor": t.autor.username,
                    "Data de Criação": t.data_criacao.strftime("%d/%m/%Y %H:%M"),
                    "Visualizações": len(t.visualizacoes),
                    "Feedback Útil": sum(1 for f in t.feedbacks if f.util),
                    "Feedback Não Útil": sum(1 for f in t.feedbacks if not f.util),
                }
                for t in tutoriais
            ]
            df_tutoriais = pd.DataFrame(tutoriais_data)
            df_tutoriais.to_excel(
                writer, sheet_name="Tutoriais", index=False, header=False, startrow=1
            )
            worksheet_tutoriais = writer.sheets["Tutoriais"]
            worksheet_tutoriais.merge_range(
                "A1:G1", "Relatório de Tutoriais", title_format
            )
            for col_num, value in enumerate(df_tutoriais.columns.values):
                worksheet_tutoriais.write(0, col_num, value, header_format)
            for i, col in enumerate(df_tutoriais.columns):
                column_len = max(df_tutoriais[col].astype(str).map(len).max(), len(col))
                worksheet_tutoriais.set_column(i, i, column_len + 2)

    output.seek(0)
    # Forçar mimetype correto para navegadores modernos
    return send_file(
        output,
        download_name="relatorio_reminder.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/docs")
@login_required
def docs_redirect():
    """Redirecionamento de /docs para /help para compatibilidade"""
    return redirect(url_for("main.help_page"))

@bp.route("/docs/")
@login_required
def docs_redirect_slash():
    """Redirecionamento de /docs/ para /help para compatibilidade"""
    return redirect(url_for("main.help_page"))

@bp.route("/help")
@login_required
def help_page():
    """Página de ajuda com documentação profissional usando MKDocs"""
    import subprocess
    import os
    import re
    from flask import current_app, url_for

    try:
        # Verificar se MKDocs está instalado
        import mkdocs

        # Construir documentação se necessário
        docs_dir = os.path.join(current_app.root_path, '..', 'docs')
        site_dir = os.path.join(current_app.root_path, '..', 'site')

        if os.path.exists(docs_dir):
            # Construir documentação MKDocs
            try:
                subprocess.run([
                    'mkdocs', 'build',
                    '--config-file', os.path.join(current_app.root_path, '..', 'mkdocs.yml'),
                    '--site-dir', site_dir,
                    '--clean'
                ], check=True, capture_output=True)

                # Verificar se index.html foi gerado
                index_path = os.path.join(site_dir, 'index.html')
                if os.path.exists(index_path):
                    # Ler conteúdo do index.html gerado pelo MKDocs
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Corrigir caminhos relativos para caminhos absolutos do Flask
                    # Substituir caminhos relativos por caminhos absolutos para /docs/
                    content = content.replace('href="assets/', 'href="/docs/assets/')
                    content = content.replace('src="assets/', 'src="/docs/assets/')
                    content = content.replace('href="javascripts/', 'href="/docs/javascripts/')
                    content = content.replace('src="javascripts/', 'src="/docs/javascripts/')
                    content = content.replace('href="stylesheets/', 'href="/docs/stylesheets/')
                    content = content.replace('href="user-guide/', 'href="/docs/user-guide/')
                    content = content.replace('href="admin-guide/', 'href="/docs/admin-guide/')
                    content = content.replace('href="dev-guide/', 'href="/docs/dev-guide/')
                    content = content.replace('href="references/', 'href="/docs/references/')
                    content = content.replace('href="search/', 'href="/docs/search/')
                    content = content.replace('href="."', 'href="/docs/"')
                    content = content.replace('href="./"', 'href="/docs/"')
                    content = content.replace('href="./', 'href="/docs/')
                    content = content.replace('href="sitemap.xml', 'href="/docs/sitemap.xml')
                    content = content.replace('href="404.html', 'href="/docs/404.html')
                    # Corrigir caminhos no JavaScript de configuração
                    content = content.replace('"search": "assets/javascripts/workers/', '"search": "/docs/assets/javascripts/workers/')
                    content = content.replace('"search": "search/', '"search": "/docs/search/')
                    # Corrigir o base path para funcionar com /docs/
                    content = content.replace('"base": "."', '"base": "/docs/"')

                    # Retornar conteúdo HTML corrigido
                    from flask import Response
                    return Response(content, mimetype='text/html')

            except subprocess.CalledProcessError as e:
                # Em caso de erro no MKDocs, fallback para template original
                current_app.logger.error(f"Erro ao construir documentação MKDocs: {e}")
            except FileNotFoundError:
                # MKDocs não encontrado, fallback para template original
                current_app.logger.warning("MKDocs não encontrado, usando template padrão")

        # Fallback para template HTML original
        return render_template("help.html", title="Central de Ajuda")

    except ImportError:
        # MKDocs não instalado, usar template original
        return render_template("help.html", title="Central de Ajuda")


@bp.route("/docs/<path:filename>")
@login_required
def docs_static(filename):
    """Servir arquivos estáticos e páginas da documentação MKDocs"""
    import os
    from flask import current_app, send_from_directory, Response

    site_dir = os.path.join(current_app.root_path, '..', 'site')

    # Se o filename terminar com / ou for um diretório, tentar servir index.html
    if filename.endswith('/') or os.path.isdir(os.path.join(site_dir, filename)):
        if filename.endswith('/'):
            filename = filename[:-1]
        index_path = os.path.join(site_dir, filename, 'index.html')
        if os.path.exists(index_path):
            # Ler e corrigir o conteúdo HTML
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Corrigir caminhos relativos
            content = content.replace('href="assets/', 'href="/docs/assets/')
            content = content.replace('src="assets/', 'src="/docs/assets/')
            content = content.replace('href="javascripts/', 'href="/docs/javascripts/')
            content = content.replace('src="javascripts/', 'src="/docs/javascripts/')
            content = content.replace('href="stylesheets/', 'href="/docs/stylesheets/')
            content = content.replace('href="user-guide/', 'href="/docs/user-guide/')
            content = content.replace('href="admin-guide/', 'href="/docs/admin-guide/')
            content = content.replace('href="dev-guide/', 'href="/docs/dev-guide/')
            content = content.replace('href="references/', 'href="/docs/references/')
            content = content.replace('href="."', 'href="/docs/index.html"')
            content = content.replace('href="./"', 'href="/docs/index.html"')

            return Response(content, mimetype='text/html')

    # Para arquivos normais, usar send_from_directory
    return send_from_directory(site_dir, filename)


@bp.route("/termos")
def terms():
    # Página de termos de uso
    return render_template("terms.html", title="Termos de Uso")


@bp.route("/privacidade")
def privacy():
    # Página de política de privacidade
    return render_template("privacy.html", title="Política de Privacidade")


@bp.route("/export/pdf")
def export_pdf():
    from flask import make_response  # make_response adicionado
    from flask import request, session
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle, Image, Frame,
                                    PageTemplate, BaseDocTemplate)
    from reportlab.lib.colors import HexColor

    task_status = request.args.get("task_status", "")
    reminder_status = request.args.get("reminder_status", "")
    chamado_status = request.args.get("chamado_status", "")  # Novo
    export_type = request.args.get("export_type", "all")

    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    sector_id = request.args.get("sector_id", type=int)
    user_id_filter = request.args.get("user_id", type=int)

    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    task_query = Task.query
    reminder_query = Reminder.query
    chamado_query = Chamado.query
    equipment_query = EquipmentRequest.query  # Query para equipamentos

    current_user_id = session.get("user_id")
    is_admin = session.get("is_admin", False)
    is_ti = session.get("is_ti", False)

    # Filtros de permissão
    if not is_admin and not is_ti:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
        equipment_query = equipment_query.filter(
            EquipmentRequest.requester_id == current_user_id
        )
    elif not is_admin and is_ti:
        user = User.query.get(current_user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=current_user_id).first()
        setor_id_usuario = (
            primeiro_lembrete.sector_id
            if primeiro_lembrete and primeiro_lembrete.sector_id
            else None
        )
        chamado_query = chamado_query.filter(
            (Chamado.solicitante_id == current_user_id)
            | (Chamado.setor_id == setor_id_usuario)
        )
        equipment_query = EquipmentRequest.query

    if task_status == "done":
        task_query = task_query.filter(Task.completed == True)
    elif task_status == "pending":
        task_query = task_query.filter(
            Task.completed == False, Task.date >= date.today()
        )
    elif task_status == "expired":
        task_query = task_query.filter(
            Task.completed == False, Task.date < date.today()
        )

    if reminder_status == "done":
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == "pending":
        reminder_query = reminder_query.filter(Reminder.completed == False)

    if chamado_status:
        chamado_query = chamado_query.filter(Chamado.status == chamado_status)

    if start_date:
        task_query = task_query.filter(Task.date >= start_date)
        reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura >= start_date)
        equipment_query = equipment_query.filter(
            EquipmentRequest.request_date >= start_date
        )
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)
        equipment_query = equipment_query.filter(
            EquipmentRequest.request_date <= end_date
        )

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)
        setor_nome = (
            Sector.query.get(sector_id).name if Sector.query.get(sector_id) else ""
        )
        equipment_query = equipment_query.filter(
            EquipmentRequest.destination_sector.contains(setor_nome)
        )

    if user_id_filter and (is_admin or is_ti):
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)
        equipment_query = equipment_query.filter(
            EquipmentRequest.requester_id == user_id_filter
        )

    # Criar PDF profissional em formato LANDSCAPE
    buffer = BytesIO()

    # Configurar estilos profissionais
    styles = getSampleStyleSheet()

    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=HexColor('#2C3E50')
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=HexColor('#34495E')
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=15,
        textColor=HexColor('#2C3E50'),
        borderWidth=1,
        borderColor=HexColor('#BDC3C7'),
        borderPadding=5,
        backgroundColor=HexColor('#ECF0F1')
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        textColor=HexColor('#2C3E50')
    )

    # Função para criar cabeçalho e rodapé em LANDSCAPE
    def header_footer(canvas, doc):
        canvas.saveState()

        # Cabeçalho - ajustado para landscape
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(HexColor('#2C3E50'))
        canvas.drawString(1.5*cm, 19*cm, "TI OSN System - Relatório Executivo")

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#7F8C8D'))
        canvas.drawString(1.5*cm, 18.3*cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Linha separadora - ajustada para landscape
        canvas.setStrokeColor(HexColor('#BDC3C7'))
        canvas.line(1.5*cm, 17.8*cm, 27*cm, 17.8*cm)

        # Rodapé - ajustado para landscape
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#7F8C8D'))
        canvas.drawString(1.5*cm, 1*cm, f"Página {doc.page}")

        # Logo/branding (simples) - ajustado para landscape
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(HexColor('#3498DB'))
        canvas.drawString(23*cm, 1*cm, "OSN Technologies")

        canvas.restoreState()

    # Criar template de página LANDSCAPE
    # A4 landscape: 29.7cm x 21cm, mas usaremos landscape(A4) que é 11.69" x 8.27"
    from reportlab.lib.pagesizes import landscape
    frame = Frame(1.5*cm, 2*cm, 26.5*cm, 16*cm, id='normal')  # Ajustado para landscape
    template = PageTemplate(id='main', frames=frame, onPage=header_footer)
    doc = BaseDocTemplate(buffer, pageTemplates=[template], pagesize=landscape(A4))

    elements = []

    # Página de capa - ajustada para landscape
    elements.append(Spacer(1, 6*cm))
    elements.append(Paragraph("RELATÓRIO EXECUTIVO", title_style))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("Sistema de Gestão TI OSN", subtitle_style))
    elements.append(Spacer(1, 2*cm))

    # Informações do relatório
    report_info = [
        ["Data de Geração:", datetime.now().strftime("%d/%m/%Y %H:%M")],
        ["Período Analisado:", f"{start_date.strftime('%d/%m/%Y') if start_date else 'Todo período'} - {end_date.strftime('%d/%m/%Y') if end_date else 'Atual'}"],
        ["Usuário:", User.query.get(session.get('user_id')).username if session.get('user_id') else 'Sistema'],
        ["Tipo de Relatório:", export_type.title()],
    ]

    info_table = Table(report_info, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # Sumário Executivo
    elements.append(Paragraph("SUMÁRIO EXECUTIVO", section_title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Calcular estatísticas gerais
    total_tasks = len(tasks) if 'tasks' in locals() else 0
    completed_tasks = sum(1 for t in tasks if t.completed) if 'tasks' in locals() else 0
    total_reminders = len(reminders) if 'reminders' in locals() else 0
    completed_reminders = sum(1 for r in reminders if r.completed) if 'reminders' in locals() else 0
    total_chamados = len(chamados) if 'chamados' in locals() else 0
    closed_chamados = sum(1 for c in chamados if c.status == 'Fechado') if 'chamados' in locals() else 0

    executive_summary = f"""
    Este relatório apresenta uma análise abrangente do Sistema de Gestão TI OSN, abrangendo o período de {start_date.strftime('%d/%m/%Y') if start_date else 'todo o histórico'} até {end_date.strftime('%d/%m/%Y') if end_date else 'data atual'}.

    <b>Métricas Principais:</b><br/>
    • Total de Tarefas: {total_tasks} ({completed_tasks} concluídas - {round(completed_tasks/total_tasks*100, 1) if total_tasks > 0 else 0}% de conclusão)<br/>
    • Total de Lembretes: {total_reminders} ({completed_reminders} realizados - {round(completed_reminders/total_reminders*100, 1) if total_reminders > 0 else 0}% de realização)<br/>
    • Total de Chamados: {total_chamados} ({closed_chamados} fechados - {round(closed_chamados/total_chamados*100, 1) if total_chamados > 0 else 0}% de resolução)<br/>
    • Eficiência Geral: {round((completed_tasks + completed_reminders + closed_chamados) / (total_tasks + total_reminders + total_chamados) * 100, 1) if (total_tasks + total_reminders + total_chamados) > 0 else 0}%<br/>

    O relatório inclui análises detalhadas, gráficos de performance e recomendações para otimização dos processos.
    """

    elements.append(Paragraph(executive_summary, normal_style))
    elements.append(PageBreak())

    # Índice
    elements.append(Paragraph("ÍNDICE", section_title_style))
    elements.append(Spacer(1, 0.5*cm))

    toc_content = """
    1. Sumário Executivo ........................... 1<br/>
    2. Índice ....................................... 2<br/>
    3. Visão Geral do Sistema ........................ 3<br/>
    4. Análise de Tarefas ........................... 4<br/>
    5. Análise de Lembretes ......................... 5<br/>
    6. Análise de Chamados .......................... 6<br/>
    7. Controle de Equipamentos ..................... 7<br/>
    8. Base de Conhecimento ........................ 8<br/>
    9. Indicadores de Performance ................... 9<br/>
    10. Recomendações ............................. 10<br/>
    """

    elements.append(Paragraph(toc_content, normal_style))
    elements.append(PageBreak())

    # Visão Geral do Sistema
    elements.append(Paragraph("VISÃO GERAL DO SISTEMA", section_title_style))
    elements.append(Spacer(1, 0.5*cm))

    system_overview = f"""
    <b>Visão Geral do Sistema TI OSN</b><br/><br/>

    O Sistema de Gestão TI OSN é uma plataforma abrangente para gerenciamento de atividades, chamados de suporte, lembretes e controle de equipamentos. Esta análise apresenta dados consolidados de todas as operações do sistema.

    <b>Período de Análise:</b> {start_date.strftime('%d/%m/%Y') if start_date else 'Todo o histórico'} - {end_date.strftime('%d/%m/%Y') if end_date else 'Data atual'}<br/>
    <b>Filtros Aplicados:</b> {', '.join([f'{k}: {v}' for k, v in request.args.items() if v and k != 'export_type']) or 'Nenhum filtro adicional'}<br/>
    <b>Usuário Responsável:</b> {User.query.get(session.get('user_id')).username if session.get('user_id') else 'Sistema'}<br/>

    <b>Status Geral do Sistema:</b><br/>
    • Sistema operacional e funcional<br/>
    • Base de dados atualizada<br/>
    • Relatório gerado automaticamente<br/>
    """

    elements.append(Paragraph(system_overview, normal_style))
    elements.append(PageBreak())

    # Análise de Tarefas
    if export_type in ["all", "tasks"]:
        elements.append(Paragraph("ANÁLISE DE TAREFAS", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        tasks = task_query.all()

        # Estatísticas das tarefas
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.completed)
        pending_tasks = total_tasks - completed_tasks
        overdue_tasks = sum(1 for t in tasks if not t.completed and t.date and t.date < date.today())

        task_stats = f"""
        <b>Estatísticas de Tarefas:</b><br/>
        • Total de Tarefas: {total_tasks}<br/>
        • Tarefas Concluídas: {completed_tasks} ({round(completed_tasks/total_tasks*100, 1) if total_tasks > 0 else 0}%)<br/>
        • Tarefas Pendentes: {pending_tasks} ({round(pending_tasks/total_tasks*100, 1) if total_tasks > 0 else 0}%)<br/>
        • Tarefas Vencidas: {overdue_tasks}<br/>
        • Taxa de Conclusão: {round(completed_tasks/total_tasks*100, 1) if total_tasks > 0 else 0}%<br/>
        """

        elements.append(Paragraph(task_stats, normal_style))
        elements.append(Spacer(1, 0.5*cm))

        if tasks:
            # Tabela de tarefas
            data_tasks = [["ID", "Descrição", "Data", "Responsável", "Setor", "Status"]]

            for t in tasks:
                status = "Concluída" if t.completed else ("Vencida" if t.date and t.date < date.today() else "Pendente")
                status_color = "green" if t.completed else ("red" if t.date and t.date < date.today() else "orange")

                data_tasks.append([
                    str(t.id),
                    Paragraph(t.description[:50] + "..." if t.description and len(t.description) > 50 else t.description or "", normal_style),
                    t.date.strftime("%d/%m/%Y") if t.date else "N/A",
                    t.responsible or "N/A",
                    t.sector.name if t.sector else "N/A",
                    status
                ])

            col_widths_tasks = [1.2*cm, 8*cm, 3*cm, 3.5*cm, 3.5*cm, 3*cm]
            table_tasks = Table(data_tasks, colWidths=col_widths_tasks, repeatRows=1)

            table_style_tasks = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ECF0F1')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

            table_tasks.setStyle(table_style_tasks)
            elements.append(table_tasks)
        else:
            elements.append(Paragraph("Nenhuma tarefa encontrada com os filtros aplicados.", normal_style))

        elements.append(PageBreak() if export_type == "all" else Spacer(1, 0.3 * inch))

    # Análise de Lembretes
    if export_type in ["all", "reminders"]:
        elements.append(Paragraph("ANÁLISE DE LEMBRETES", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        reminders = reminder_query.all()

        # Estatísticas dos lembretes
        total_reminders = len(reminders)
        completed_reminders = sum(1 for r in reminders if r.completed)
        pending_reminders = total_reminders - completed_reminders
        expired_reminders = sum(1 for r in reminders if not r.completed and r.due_date and r.due_date < date.today())

        reminder_stats = f"""
        <b>Estatísticas de Lembretes:</b><br/>
        • Total de Lembretes: {total_reminders}<br/>
        • Lembretes Realizados: {completed_reminders} ({round(completed_reminders/total_reminders*100, 1) if total_reminders > 0 else 0}%)<br/>
        • Lembretes Pendentes: {pending_reminders} ({round(pending_reminders/total_reminders*100, 1) if total_reminders > 0 else 0}%)<br/>
        • Lembretes Vencidos: {expired_reminders}<br/>
        • Taxa de Realização: {round(completed_reminders/total_reminders*100, 1) if total_reminders > 0 else 0}%<br/>
        """

        elements.append(Paragraph(reminder_stats, normal_style))
        elements.append(Spacer(1, 0.5*cm))

        if reminders:
            # Tabela de lembretes
            data_reminders = [["ID", "Nome", "Tipo", "Vencimento", "Responsável", "Setor", "Status"]]

            for r in reminders:
                status = "Realizado" if r.completed else ("Vencido" if r.due_date and r.due_date < date.today() else "Pendente")

                data_reminders.append([
                    str(r.id),
                    Paragraph(r.name[:40] + "..." if r.name and len(r.name) > 40 else r.name or "", normal_style),
                    r.type or "N/A",
                    r.due_date.strftime("%d/%m/%Y") if r.due_date else "N/A",
                    r.responsible or "N/A",
                    r.sector.name if r.sector else "N/A",
                    status
                ])

            col_widths_reminders = [1.2*cm, 7*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm, 3*cm]
            table_reminders = Table(data_reminders, colWidths=col_widths_reminders, repeatRows=1)

            table_style_reminders = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E74C3C')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FADBD8')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E74C3C')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

            table_reminders.setStyle(table_style_reminders)
            elements.append(table_reminders)
        else:
            elements.append(Paragraph("Nenhum lembrete encontrado com os filtros aplicados.", normal_style))

        elements.append(PageBreak() if export_type == "all" else Spacer(1, 0.3 * inch))

    # Análise de Chamados
    if export_type in ["all", "chamados"]:
        elements.append(Paragraph("ANÁLISE DE CHAMADOS", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        chamados = chamado_query.all()

        # Estatísticas dos chamados
        total_chamados = len(chamados)
        abertos = sum(1 for c in chamados if c.status == 'Aberto')
        andamento = sum(1 for c in chamados if c.status == 'Em Andamento')
        resolvidos = sum(1 for c in chamados if c.status == 'Resolvido')
        fechados = sum(1 for c in chamados if c.status == 'Fechado')

        # SLA Analysis
        chamados_com_sla = [c for c in chamados if c.prazo_sla]
        sla_cumpridos = sum(1 for c in chamados_com_sla if c.sla_cumprido)
        taxa_sla = round(sla_cumpridos / len(chamados_com_sla) * 100, 1) if chamados_com_sla else 0

        chamados_stats = f"""
        <b>Estatísticas de Chamados:</b><br/>
        • Total de Chamados: {total_chamados}<br/>
        • Status: {abertos} Abertos, {andamento} Em Andamento, {resolvidos} Resolvidos, {fechados} Fechados<br/>
        • Taxa de Resolução: {round(fechados/total_chamados*100, 1) if total_chamados > 0 else 0}%<br/>
        • Chamados com SLA: {len(chamados_com_sla)}<br/>
        • Performance SLA: {taxa_sla}% ({sla_cumpridos}/{len(chamados_com_sla)} cumpridos)<br/>
        """

        elements.append(Paragraph(chamados_stats, normal_style))
        elements.append(Spacer(1, 0.5*cm))

        if chamados:
            # Tabela de chamados
            data_chamados = [["ID", "Título", "Status", "Prioridade", "Abertura", "Solicitante", "Setor", "SLA"]]

            for c in chamados:
                sla_status = "OK" if c.sla_cumprido else "Vencido" if c.prazo_sla and c.data_fechamento and c.data_fechamento > c.prazo_sla else "Em Prazo"

                data_chamados.append([
                    str(c.id),
                    Paragraph(c.titulo[:40] + "..." if c.titulo and len(c.titulo) > 40 else c.titulo or "", normal_style),
                    c.status,
                    c.prioridade,
                    c.data_abertura.strftime("%d/%m/%Y") if c.data_abertura else "N/A",
                    c.solicitante.username if c.solicitante else "N/A",
                    c.setor.name if c.setor else "N/A",
                    sla_status
                ])

            col_widths_chamados = [1.2*cm, 7*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm, 3*cm, 2.5*cm]
            table_chamados = Table(data_chamados, colWidths=col_widths_chamados, repeatRows=1)

            table_style_chamados = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#27AE60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#D5F4E6')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#27AE60')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

            table_chamados.setStyle(table_style_chamados)
            elements.append(table_chamados)
        else:
            elements.append(Paragraph("Nenhum chamado encontrado com os filtros aplicados.", normal_style))

        elements.append(PageBreak() if export_type == "all" else Spacer(1, 0.3 * inch))

    # Controle de Equipamentos
    if export_type in ["all", "equipamentos"]:
        elements.append(Paragraph("CONTROLE DE EQUIPAMENTOS", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        equipamentos = equipment_query.all()

        # Estatísticas dos equipamentos
        total_equipamentos = len(equipamentos)
        solicitados = sum(1 for e in equipamentos if e.status == 'Solicitado')
        aprovados = sum(1 for e in equipamentos if e.status == 'Aprovado')
        entregues = sum(1 for e in equipamentos if e.status == 'Entregue')
        devolvidos = sum(1 for e in equipamentos if e.status == 'Devolvido')
        negados = sum(1 for e in equipamentos if e.status == 'Negado')

        equipamentos_stats = f"""
        <b>Estatísticas de Equipamentos:</b><br/>
        • Total de Solicitações: {total_equipamentos}<br/>
        • Status: {solicitados} Solicitados, {aprovados} Aprovados, {entregues} Entregues, {devolvidos} Devolvidos, {negados} Negados<br/>
        • Taxa de Aprovação: {round(aprovados/total_equipamentos*100, 1) if total_equipamentos > 0 else 0}%<br/>
        • Taxa de Entrega: {round(entregues/total_equipamentos*100, 1) if total_equipamentos > 0 else 0}%<br/>
        • Taxa de Devolução: {round(devolvidos/total_equipamentos*100, 1) if total_equipamentos > 0 else 0}%<br/>
        """

        elements.append(Paragraph(equipamentos_stats, normal_style))
        elements.append(Spacer(1, 0.5*cm))

        if equipamentos:
            # Tabela de equipamentos
            data_equipamentos = [["ID", "Descrição", "Patrimônio", "Tipo", "Status", "Solicitante", "Data"]]

            for e in equipamentos:
                data_equipamentos.append([
                    str(e.id),
                    Paragraph(e.description[:40] + "..." if e.description and len(e.description) > 40 else e.description or "", normal_style),
                    e.patrimony or "N/A",
                    e.equipment_type or "N/A",
                    e.status,
                    e.requester.username if e.requester else "N/A",
                    e.request_date.strftime("%d/%m/%Y") if e.request_date else "N/A"
                ])

            col_widths_equipamentos = [1.2*cm, 7*cm, 3*cm, 3*cm, 3*cm, 3.5*cm, 3*cm]
            table_equipamentos = Table(data_equipamentos, colWidths=col_widths_equipamentos, repeatRows=1)

            table_style_equipamentos = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#9B59B6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#E8DAEF')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#9B59B6')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

            table_equipamentos.setStyle(table_style_equipamentos)
            elements.append(table_equipamentos)
        else:
            elements.append(Paragraph("Nenhum equipamento encontrado com os filtros aplicados.", normal_style))

        elements.append(PageBreak() if export_type == "all" else Spacer(1, 0.3 * inch))

    if not elements or all(
        isinstance(el, (Paragraph, Spacer)) and "Nenhum" in el.text
        for el in elements
        if isinstance(el, Paragraph)
    ):
        elements.append(
            Paragraph(
                "Nenhum dado para exportar com os filtros selecionados.",
                styles["Normal"],
            )
        )

    # Base de Conhecimento (Tutoriais)
    tutorial_query = Tutorial.query
    if not is_admin and not is_ti:
        tutorial_query = tutorial_query.filter(Tutorial.autor_id == current_user_id)
    if sector_id:
        tutorial_query = tutorial_query.join(User).filter(User.sector_id == sector_id)
    if user_id_filter and (is_admin or is_ti):
        tutorial_query = tutorial_query.filter(Tutorial.autor_id == user_id_filter)
    if start_date:
        tutorial_query = tutorial_query.filter(Tutorial.data_criacao >= start_date)
    if end_date:
        tutorial_query = tutorial_query.filter(Tutorial.data_criacao <= end_date)
    tutoriais = tutorial_query.all()

    if export_type in ["all", "tutoriais"]:
        elements.append(Paragraph("BASE DE CONHECIMENTO", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Estatísticas dos tutoriais
        total_tutoriais = len(tutoriais)
        total_visualizacoes = sum(len(t.visualizacoes) for t in tutoriais)
        total_feedbacks = sum(len(t.feedbacks) for t in tutoriais)
        feedbacks_uteis = sum(sum(1 for f in t.feedbacks if f.util) for t in tutoriais)
        media_visualizacoes = round(total_visualizacoes / total_tutoriais, 1) if total_tutoriais > 0 else 0
        taxa_satisfacao = round(feedbacks_uteis / total_feedbacks * 100, 1) if total_feedbacks > 0 else 0

        tutoriais_stats = f"""
        <b>Estatísticas da Base de Conhecimento:</b><br/>
        • Total de Tutoriais: {total_tutoriais}<br/>
        • Total de Visualizações: {total_visualizacoes}<br/>
        • Média de Visualizações por Tutorial: {media_visualizacoes}<br/>
        • Total de Feedbacks: {total_feedbacks}<br/>
        • Feedbacks Úteis: {feedbacks_uteis} ({taxa_satisfacao}%)<br/>
        • Taxa de Satisfação: {taxa_satisfacao}%<br/>
        """

        elements.append(Paragraph(tutoriais_stats, normal_style))
        elements.append(Spacer(1, 0.5*cm))

        if tutoriais:
            # Tabela de tutoriais
            data_tutoriais = [["Título", "Categoria", "Autor", "Visualizações", "Feedbacks", "Avaliação"]]

            for t in tutoriais:
                feedbacks_positivos = sum(1 for f in t.feedbacks if f.util)
                total_feedbacks_t = len(t.feedbacks)
                avaliacao = f"{feedbacks_positivos}/{total_feedbacks_t}" if total_feedbacks_t > 0 else "N/A"

                data_tutoriais.append([
                    Paragraph(t.titulo[:35] + "..." if t.titulo and len(t.titulo) > 35 else t.titulo or "", normal_style),
                    t.categoria or "N/A",
                    t.autor.username if t.autor else "N/A",
                    str(len(t.visualizacoes)),
                    str(total_feedbacks_t),
                    avaliacao
                ])

            col_widths_tutoriais = [6*cm, 3*cm, 3.5*cm, 2*cm, 2*cm, 2.5*cm]
            table_tutoriais = Table(data_tutoriais, colWidths=col_widths_tutoriais, repeatRows=1)

            table_style_tutoriais = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#F39C12')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FDEAA7')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#F39C12')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

            table_tutoriais.setStyle(table_style_tutoriais)
            elements.append(table_tutoriais)
        else:
            elements.append(Paragraph("Nenhum tutorial encontrado com os filtros aplicados.", normal_style))

        elements.append(PageBreak() if export_type == "all" else Spacer(1, 0.3 * inch))

    # Indicadores de Performance
    if export_type == "all":
        elements.append(Paragraph("INDICADORES DE PERFORMANCE", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        # KPIs principais
        kpis_data = [
            ["Indicador", "Valor", "Meta", "Status"],
            ["Taxa de Conclusão de Tarefas", f"{round(completed_tasks/total_tasks*100, 1) if total_tasks > 0 else 0}%", "80%", "✓" if (completed_tasks/total_tasks*100 if total_tasks > 0 else 0) >= 80 else "✗"],
            ["Taxa de Realização de Lembretes", f"{round(completed_reminders/total_reminders*100, 1) if total_reminders > 0 else 0}%", "85%", "✓" if (completed_reminders/total_reminders*100 if total_reminders > 0 else 0) >= 85 else "✗"],
            ["Taxa de Resolução de Chamados", f"{round(fechados/total_chamados*100, 1) if total_chamados > 0 else 0}%", "90%", "✓" if (fechados/total_chamados*100 if total_chamados > 0 else 0) >= 90 else "✗"],
            ["Performance SLA", f"{taxa_sla}%", "95%", "✓" if taxa_sla >= 95 else "✗"],
            ["Taxa de Satisfação Tutoriais", f"{taxa_satisfacao}%", "75%", "✓" if taxa_satisfacao >= 75 else "✗"],
        ]

        kpis_table = Table(kpis_data, colWidths=[7*cm, 3*cm, 3*cm, 3*cm])
        kpis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ECF0F1')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(kpis_table)
        elements.append(PageBreak())

        # Recomendações
        elements.append(Paragraph("RECOMENDAÇÕES", section_title_style))
        elements.append(Spacer(1, 0.5*cm))

        recomendacoes = """
        <b>Recomendações para Melhoria:</b><br/><br/>

        <b>1. Gestão de Tarefas:</b><br/>
        • Implementar sistema de notificações automáticas para tarefas próximas do vencimento<br/>
        • Criar categorias de prioridade para melhor organização<br/>
        • Estabelecer SLA interno para conclusão de tarefas<br/><br/>

        <b>2. Gestão de Lembretes:</b><br/>
        • Automatizar recorrência de lembretes de manutenção preventiva<br/>
        • Implementar sistema de escalação para lembretes não realizados<br/>
        • Criar templates padronizados para diferentes tipos de lembretes<br/><br/>

        <b>3. Atendimento de Chamados:</b><br/>
        • Melhorar tempo de primeira resposta através de chatbots<br/>
        • Implementar sistema de conhecimento automático<br/>
        • Criar métricas de satisfação do usuário<br/><br/>

        <b>4. Controle de Equipamentos:</b><br/>
        • Implementar RFID para rastreamento automático<br/>
        • Criar alertas para equipamentos com devolução pendente<br/>
        • Estabelecer política de manutenção preventiva<br/><br/>

        <b>5. Base de Conhecimento:</b><br/>
        • Incentivar criação de tutoriais pelos usuários<br/>
        • Implementar sistema de avaliação e comentários<br/>
        • Criar certificações para contribuidores ativos<br/><br/>

        <b>Conclusão:</b><br/>
        O sistema TI OSN apresenta boa performance geral, com oportunidades de melhoria identificadas.
        A implementação das recomendações acima contribuirá para aumento da eficiência operacional
        e melhoria na satisfação dos usuários.
        """

        elements.append(Paragraph(recomendacoes, normal_style))

    # Verificar se há dados para exportar
    if not elements or len(elements) <= 5:  # Apenas capa, sumário, índice
        elements.append(Paragraph("Nenhum dado encontrado para os filtros aplicados.", normal_style))

    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)

    # Retornar resposta
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=relatorio_executivo_ti_osn_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return response


# --- Tarefas ---
@bp.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    from .models import Sector

    form = TaskForm()
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione")] + [(s.id, s.name) for s in sectors]
    page = request.args.get("page", 1, type=int)
    per_page = 10
    # Filtros e busca
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "").strip()
    date_filter = request.args.get("date", "")
    query = Task.query
    if status_filter == "expired":
        query = query.filter(Task.completed == False, Task.date < date.today())
    elif status_filter == "today":
        query = query.filter(Task.completed == False, Task.date == date.today())
    elif status_filter == "done":
        query = query.filter(Task.completed == True)
    elif status_filter == "pending":
        query = query.filter(Task.completed == False, Task.date >= date.today())
    if search:
        query = query.filter(
            Task.description.ilike(f"%{search}%")
            | Task.responsible.ilike(f"%{search}%")
        )
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(Task.date == filter_date)
        except:
            pass
    # Admin pode ver todas as tarefas, usuário comum só as próprias
    if not session.get("is_admin"):
        query = query.filter_by(user_id=session.get("user_id"))
    pagination = query.order_by(Task.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tasks = pagination.items
    # Aplica status visual
    for t in tasks:
        if t.completed:
            t.status = "done"
        elif t.date < date.today():
            t.status = "expired"
        elif t.date == date.today():
            t.status = "today"
        else:
            t.status = "pending"
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ""
        if new_sector_name:
            existing = Sector.query.filter_by(name=new_sector_name).first()
            if existing:
                sector = existing
            else:
                sector = Sector(name=new_sector_name)
                db.session.add(sector)
                db.session.commit()
            sector_id = sector.id
        elif sector_id == 0:
            sector_id = None
        task = Task(
            description=form.description.data,
            date=form.date.data,
            responsible=form.responsible.data,
            completed=form.completed.data,
            priority=form.priority.data,
            sector_id=sector_id,
            user_id=session.get("user_id"),
        )
        db.session.add(task)
        db.session.commit()
        flash("Tarefa adicionada!", "success")
        return redirect(url_for("main.tasks"))
    return render_template(
        "tasks.html",
        tasks=tasks,
        form=form,
        edit_id=None,
        pagination=pagination,
        status_filter=status_filter,
        search=search,
        date_filter=date_filter,
        current_date=date.today(),
    )


@bp.route("/tasks/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):
    if session.get("is_admin"):
        task = Task.query.get_or_404(id)
    else:
        task = Task.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    form = TaskForm(obj=task)
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione")] + [(s.id, s.name) for s in sectors]
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ""
        if new_sector_name:
            existing = Sector.query.filter_by(name=new_sector_name).first()
            if existing:
                sector = existing
            else:
                sector = Sector(name=new_sector_name)
                db.session.add(sector)
                db.session.commit()
            sector_id = sector.id
        elif sector_id == 0:
            sector_id = None
        form.populate_obj(task)
        task.sector_id = sector_id
        db.session.commit()
        flash("Tarefa atualizada!", "success")
        return redirect(url_for("main.tasks"))
    # Lógica de paginação e filtros igual à função tasks
    page = request.args.get("page", 1, type=int)
    per_page = 10
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "").strip()
    date_filter = request.args.get("date", "")
    query = Task.query
    if status_filter == "expired":
        query = query.filter(Task.completed == False, Task.date < date.today())
    elif status_filter == "today":
        query = query.filter(Task.completed == False, Task.date == date.today())
    elif status_filter == "done":
        query = query.filter(Task.completed == True)
    elif status_filter == "pending":
        query = query.filter(Task.completed == False, Task.date >= date.today())
    if search:
        query = query.filter(
            Task.description.ilike(f"%{search}%")
            | Task.responsible.ilike(f"%{search}%")
        )
    if date_filter:
        query = query.filter(Task.date == date_filter)
    pagination = query.order_by(Task.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tasks = pagination.items
    # Aplica status visual
    for t in tasks:
        if t.completed:
            t.status = "done"
        elif t.date < date.today():
            t.status = "expired"
        elif t.date == date.today():
            t.status = "today"
        else:
            t.status = "pending"
    return render_template(
        "tasks.html",
        tasks=tasks,
        form=form,
        edit_id=id,
        pagination=pagination,
        status_filter=status_filter,
        search=search,
        date_filter=date_filter,
    )


@bp.route("/tasks/complete/<int:id>", methods=["POST"])
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.completed = True
    db.session.commit()
    flash("Tarefa marcada como concluída!", "success")
    return redirect(url_for("main.tasks"))


@bp.route("/tasks/delete/<int:id>", methods=["POST"])
def delete_task(id):
    if session.get("is_admin"):
        task = Task.query.get_or_404(id)
    else:
        task = Task.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Tarefa excluída!", "success")
    return redirect(url_for("main.tasks"))


from .email_utils import send_chamado_aberto_email
from .forms import ChamadoForm
from .models import Chamado, User

# --- Rotas para Chamados ---


@bp.route("/chamados/abrir", methods=["GET", "POST"])
@login_required
def abrir_chamado():
    form = ChamadoForm()
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    # Verificar se o usuário existe
    if not user:
        flash("Usuário não encontrado. Faça login novamente.", "danger")
        return redirect(url_for("auth.login"))

    # Tenta obter o setor do usuário de diferentes fontes
    setor_usuario = None

    # 1. Verifica se o usuário tem um setor atribuído diretamente
    if user.sector:
        setor_usuario = user.sector
    # 2. Verifica em lembretes do usuário
    elif user.reminders:
        for lembrete in user.reminders:
            if lembrete.sector:
                setor_usuario = lembrete.sector
                break
    # 3. Verifica em tarefas do usuário
    elif user.tasks:
        for tarefa in user.tasks:
            if tarefa.sector:
                setor_usuario = tarefa.sector
                break

    if request.method == "POST" and form.validate_on_submit():
        try:
            # Verificar se o usuário está criando um novo setor
            if form.new_sector.data and form.new_sector.data.strip():
                # Verificar se o setor já existe
                setor_existente = Sector.query.filter_by(
                    name=form.new_sector.data.strip()
                ).first()
                if setor_existente:
                    setor_id = setor_existente.id
                else:
                    # Criar novo setor
                    novo_setor = Sector(name=form.new_sector.data.strip())
                    db.session.add(novo_setor)
                    db.session.commit()
                    setor_id = novo_setor.id
                    flash(
                        f"Novo setor '{novo_setor.name}' criado com sucesso!", "success"
                    )
            else:
                # Usar o setor selecionado pelo usuário no formulário
                setor_id = form.setor_id.data

                # Se o usuário não selecionou um setor (valor 0), usar o setor do usuário ou criar um genérico
                if setor_id == 0:
                    setor_id = setor_usuario.id if setor_usuario else 1

                    # Verificar se o setor existe, se não, criar um setor genérico
                    if not Sector.query.get(setor_id):
                        setor_generico = Sector(id=1, name="Geral")
                        db.session.add(setor_generico)
                        db.session.commit()
                        setor_id = 1

            novo_chamado = Chamado(
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                prioridade=form.prioridade.data,
                solicitante_id=user_id,
                setor_id=setor_id,
                status="Aberto",  # Status inicial
            )

            # Calcular e definir o prazo de SLA automaticamente
            novo_chamado.calcular_sla()

            db.session.add(novo_chamado)
            db.session.commit()

            # Enviar email de notificação
            try:
                send_chamado_aberto_email(novo_chamado)
                flash("Notificações enviadas com sucesso!", "info")
            except Exception as e:
                db.session.rollback()
                flash(
                    f"Chamado criado, mas houve um erro ao enviar notificações: {str(e)}",
                    "warning",
                )
                print(
                    f"Error sending notification email for Chamado {novo_chamado.id}: {e}"
                )

            flash("Chamado aberto com sucesso!", "success")
            return redirect(url_for("main.detalhe_chamado", id=novo_chamado.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao abrir o chamado: {str(e)}", "danger")
            print(f"Error creating Chamado: {e}")

    # Pré-selecionar o setor do usuário no formulário, se existir
    if setor_usuario and hasattr(form, "setor_id"):
        form.setor_id.data = setor_usuario.id

    return render_template(
        "abrir_chamado.html",
        form=form,
        title="Abrir Novo Chamado",
        setor_usuario=setor_usuario,
    )


@bp.route("/chamados/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_chamado(id):
    """Editar chamado por usuários comuns (apenas título, descrição e setor)"""
    # Verificar permissão: apenas o solicitante pode editar
    chamado = Chamado.query.get_or_404(id)
    user_id = session.get("user_id")

    if chamado.solicitante_id != user_id:
        flash("Você não tem permissão para editar este chamado.", "danger")
        return redirect(url_for("main.detalhe_chamado", id=id))

    # Não permitir edição se o chamado estiver fechado
    if chamado.status == "Fechado":
        flash("Não é possível editar um chamado fechado.", "warning")
        return redirect(url_for("main.detalhe_chamado", id=id))

    form = ChamadoEditForm(obj=chamado)

    if form.validate_on_submit():
        try:
            alteracoes = []

            # Verificar se houve mudanças
            if form.titulo.data != chamado.titulo:
                alteracoes.append(f'Título alterado de "{chamado.titulo}" para "{form.titulo.data}"')
                chamado.titulo = form.titulo.data

            if form.descricao.data != chamado.descricao:
                alteracoes.append("Descrição alterada")
                chamado.descricao = form.descricao.data

            # Lógica do setor: se novo setor preenchido, criar e usar
            setor_id = form.setor_id.data
            new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ""
            if new_sector_name:
                existing = Sector.query.filter_by(name=new_sector_name).first()
                if existing:
                    setor = existing
                else:
                    setor = Sector(name=new_sector_name)
                    db.session.add(setor)
                    db.session.commit()
                if setor_id != setor.id:
                    alteracoes.append(f'Setor alterado para "{setor.name}"')
                    setor_id = setor.id
            elif setor_id == 0:
                setor_id = None

            if setor_id != chamado.setor_id:
                setor_antigo = chamado.setor.name if chamado.setor else "Nenhum"
                setor_novo = Sector.query.get(setor_id).name if setor_id and Sector.query.get(setor_id) else "Nenhum"
                alteracoes.append(f'Setor alterado de "{setor_antigo}" para "{setor_novo}"')
                chamado.setor_id = setor_id

            # Se houve alterações, registrar no histórico
            if alteracoes:
                # Atualiza a data da última atualização
                chamado.data_ultima_atualizacao = datetime.utcnow()

                # Cria um registro de atualização
                atualizacao = ComentarioChamado(
                    chamado_id=chamado.id,
                    usuario_id=user_id,
                    texto=" | ".join(alteracoes),
                    tipo="atualizacao",
                )
                db.session.add(atualizacao)

                db.session.commit()

                flash("Chamado atualizado com sucesso!", "success")
                return redirect(url_for("main.detalhe_chamado", id=chamado.id))
            else:
                flash("Nenhuma alteração foi realizada.", "info")

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar o chamado: {str(e)}", "danger")
            print(f"Error updating Chamado {id}: {e}")

    # Pré-selecionar o setor atual no formulário
    if chamado.setor_id:
        form.setor_id.data = chamado.setor_id

    return render_template(
        "editar_chamado.html",
        form=form,
        chamado=chamado,
        title=f"Editar Chamado #{chamado.id}",
    )


@bp.route("/chamados", methods=["GET"])
@login_required
def listar_chamados():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    status_filter = request.args.get("status", "")
    prioridade_filter = request.args.get("prioridade", "")
    setor_filter = request.args.get("sector_id", type=int)

    query = Chamado.query

    # Filtrar por permissão: Admin/TI vê tudo, usuário comum vê os seus e/ou do seu setor
    if not session.get(
        "is_admin"
    ):  # Assumindo que 'is_admin' também cobre a equipe de TI por enquanto
        user_id = session.get("user_id")
        # Obter setor do usuário (mesma lógica/problema de 'abrir_chamado')
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = (
            primeiro_lembrete.sector_id
            if primeiro_lembrete and primeiro_lembrete.sector_id
            else None
        )
        # Mostrar chamados do usuário ou do setor do usuário (ajustar conforme regra)
        query = query.filter(
            (Chamado.solicitante_id == user_id) | (Chamado.setor_id == setor_id_usuario)
        )

    # Aplicar filtros adicionais
    if status_filter:
        query = query.filter(Chamado.status == status_filter)
    if prioridade_filter:
        query = query.filter(Chamado.prioridade == prioridade_filter)
    if setor_filter:
        query = query.filter(Chamado.setor_id == setor_filter)

    chamados_paginated = query.order_by(Chamado.data_abertura.desc()).paginate(
        page=page, per_page=per_page
    )

    # Para os filtros no template
    setores = Sector.query.order_by(Sector.name).all()
    status_list = db.session.query(Chamado.status).distinct().all()
    prioridade_list = db.session.query(Chamado.prioridade).distinct().all()

    return render_template(
        "listar_chamados.html",
        chamados=chamados_paginated.items,
        pagination=chamados_paginated,
        setores=setores,
        status_list=[s[0] for s in status_list],
        prioridade_list=[p[0] for p in prioridade_list],
        title="Meus Chamados",
    )


@bp.route("/chamados/<int:id>")
@login_required
def detalhe_chamado(id):
    from .forms import ChamadoAdminForm

    query = Chamado.query
    is_admin = session.get("is_admin")
    user_id = session.get("user_id")

    # Aplicar restrição de acesso
    if not is_admin:
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = (
            primeiro_lembrete.sector_id
            if primeiro_lembrete and primeiro_lembrete.sector_id
            else None
        )
        # Permitir ver se for o solicitante ou do mesmo setor
        query = query.filter(
            (Chamado.solicitante_id == user_id) | (Chamado.setor_id == setor_id_usuario)
        )

    chamado = query.filter(Chamado.id == id).first_or_404()

    # Se for administrador, preparar o formulário administrativo
    form = None
    usuarios_ti = []
    if is_admin:
        form = ChamadoAdminForm()
        form.status.choices = [
            ("Aberto", "Aberto"),
            ("Em Andamento", "Em Andamento"),
            ("Resolvido", "Resolvido"),
            ("Fechado", "Fechado"),
        ]
        form.status.data = chamado.status

        # Buscar apenas usuários ativos com perfil de TI
        usuarios_ti = (
            User.query.filter_by(is_ti=True, ativo=True).order_by(User.username).all()
        )

        # Definir o valor atual do responsável TI, se existir
        if chamado.responsavel_ti_id:
            form.responsavel_ti_id.data = str(chamado.responsavel_ti_id)

    return render_template(
        "detalhe_chamado.html",
        chamado=chamado,
        form=form,
        usuarios_ti=usuarios_ti,
        title=f"Chamado #{chamado.id}",
    )


@bp.route("/chamados/<int:id>/admin", methods=["POST"])
@login_required
def gerenciar_chamado(id):
    from .email_utils import send_chamado_atualizado_email
    from .forms import ChamadoAdminForm
    from .models import Chamado, ComentarioChamado, ComentarioTutorial, db

    # Verifica se o usuário é administrador
    if not session.get("is_admin"):
        flash("Acesso restrito a administradores.", "danger")
        return redirect(url_for("main.detalhe_chamado", id=id))

    chamado = Chamado.query.get_or_404(id)
    form = ChamadoAdminForm()

    # Preenche as opções de responsável TI (apenas usuários ativos e marcados como TI)
    usuarios_ti = (
        User.query.filter_by(ativo=True, is_ti=True).order_by(User.username).all()
    )
    form.responsavel_ti_id.choices = [("", "Nenhum (sem responsável)")] + [
        (str(u.id), u.username) for u in usuarios_ti
    ]

    if form.validate_on_submit():
        alteracoes = []

        # Atualiza o status se foi alterado
        if form.status.data != chamado.status:
            alteracoes.append(
                f'Status alterado de "{chamado.status}" para "{form.status.data}"'
            )

            # Marcar primeira resposta se mudou de "Aberto" para qualquer outro status
            if chamado.status == "Aberto" and form.status.data in [
                "Em Andamento",
                "Resolvido",
                "Fechado",
            ]:
                chamado.marcar_primeira_resposta()
                alteracoes.append("Primeira resposta registrada para cálculo de SLA")

            chamado.status = form.status.data

            # Atualiza a data de fechamento se o status for Fechado
            if form.status.data == "Fechado" and not chamado.data_fechamento:
                chamado.data_fechamento = datetime.utcnow()
                alteracoes.append("Chamado fechado")
            elif form.status.data != "Fechado" and chamado.data_fechamento:
                chamado.data_fechamento = None
                alteracoes.append("Chamado reaberto")

        # Atualiza o responsável TI se foi alterado
        if form.responsavel_ti_id.data != str(
            chamado.responsavel_ti_id if chamado.responsavel_ti_id else ""
        ):
            if form.responsavel_ti_id.data:  # Novo responsável selecionado
                novo_responsavel = User.query.get(form.responsavel_ti_id.data)
                if novo_responsavel:
                    alteracoes.append(
                        f"Responsável TI alterado para {novo_responsavel.username}"
                    )
                    chamado.responsavel_ti_id = novo_responsavel.id
            else:  # Nenhum responsável selecionado
                if chamado.responsavel_ti:
                    alteracoes.append("Responsável TI removido")
                    chamado.responsavel_ti_id = None

        # Adiciona um comentário se foi preenchido
        if form.comentario.data.strip():
            comentario = ComentarioChamado(
                chamado_id=chamado.id,
                usuario_id=session["user_id"],
                texto=form.comentario.data,
                tipo="comentario",
            )
            db.session.add(comentario)
            alteracoes.append("Comentário adicionado")

        # Se houve alterações, registra como atualização
        if alteracoes:
            # Atualiza a data da última atualização
            chamado.data_ultima_atualizacao = datetime.utcnow()

            # Cria um registro de atualização
            atualizacao = ComentarioChamado(
                chamado_id=chamado.id,
                usuario_id=session["user_id"],
                texto=" | ".join(alteracoes),
                tipo="atualizacao",
            )
            db.session.add(atualizacao)

            db.session.commit()

            # Envia notificação por e-mail se solicitado
            if form.notificar_solicitante.data and chamado.solicitante.email:
                try:
                    send_chamado_atualizado_email(chamado, atualizacao)
                except Exception as e:
                    print(f"Erro ao enviar e-mail: {str(e)}")
                    flash(
                        "Chamado atualizado, mas ocorreu um erro ao enviar a notificação por e-mail.",
                        "warning",
                    )

            flash("Chamado atualizado com sucesso!", "success")
        else:
            flash("Nenhuma alteração foi realizada.", "info")

        return redirect(url_for("main.detalhe_chamado", id=chamado.id))

    # Se o formulário não for válido, mostra os erros
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erro no campo {getattr(form, field).label.text}: {error}", "danger")

    return redirect(url_for("main.detalhe_chamado", id=chamado.id))


# --- Tutoriais ---
# Apenas usuários com is_ti=True (Equipe de TI) podem cadastrar, editar e excluir tutoriais.


@bp.route("/tutoriais")
@login_required
def listar_tutoriais():
    busca = request.args.get("busca", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 6
    query = Tutorial.query
    if busca:
        query = query.filter(
            (Tutorial.titulo.ilike(f"%{busca}%"))
            | (Tutorial.conteudo.ilike(f"%{busca}%"))
            | (Tutorial.categoria.ilike(f"%{busca}%"))
        )
    pagination = query.order_by(Tutorial.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tutoriais = pagination.items
    return render_template(
        "tutoriais.html", tutoriais=tutoriais, busca=busca, pagination=pagination
    )


@bp.route("/tutoriais/novo", methods=["GET", "POST"])
@login_required
def novo_tutorial():
    # Apenas membros da equipe de TI ou administradores podem cadastrar tutoriais
    if not (session.get("is_ti") or session.get("is_admin")):
        flash(
            "Apenas membros da equipe de TI ou administradores podem cadastrar tutoriais.",
            "danger",
        )
        return redirect(url_for("main.listar_tutoriais"))
    form = TutorialForm()
    if form.validate_on_submit():
        tutorial = Tutorial(
            titulo=form.titulo.data,
            conteudo=form.conteudo.data,
            categoria=form.categoria.data,
            autor_id=session.get("user_id"),
        )
        db.session.add(tutorial)
        db.session.commit()
        # Upload de imagens
        if form.imagem.data:
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file = form.imagem.data
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                img = TutorialImage(tutorial_id=tutorial.id, filename=filename)
                db.session.add(img)
            db.session.commit()
        flash("Tutorial cadastrado com sucesso!", "success")
        return redirect(url_for("main.listar_tutoriais"))
    return render_template("tutorial_form.html", form=form, title="Novo Tutorial")


@bp.route("/tutoriais/<int:tutorial_id>")
@login_required
def detalhe_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    feedback_form = FeedbackTutorialForm()
    # Registrar visualização (mantém se já estiver)
    visualizacao = VisualizacaoTutorial(
        tutorial_id=tutorial.id, usuario_id=session.get("user_id")
    )
    db.session.add(visualizacao)
    db.session.commit()
    # Preparar dados para gráficos (mantém se já estiver)
    visualizacoes = VisualizacaoTutorial.query.filter_by(tutorial_id=tutorial.id).all()
    datas = [v.data.strftime("%d/%m") for v in visualizacoes]
    from collections import Counter

    contagem_datas = Counter(datas)
    datas_ordenadas = sorted(
        contagem_datas.keys(), key=lambda x: tuple(map(int, x.split("/")[::-1]))
    )
    visualizacoes_labels = datas_ordenadas[-15:]
    visualizacoes_values = [contagem_datas[d] for d in visualizacoes_labels]
    feedbacks = tutorial.feedbacks
    total_util = sum(1 for f in feedbacks if f.util)
    total_nao_util = sum(1 for f in feedbacks if not f.util)
    feedback_data = {
        "labels": ["Útil", "Não útil"],
        "values": [total_util, total_nao_util],
    }
    import json

    conteudo_markdown = markdown.markdown(
        tutorial.conteudo, extensions=["extra", "nl2br"]
    )
    return render_template(
        "tutorial_detalhe.html",
        tutorial=tutorial,
        comentario_form=comentario_form,
        feedback_form=feedback_form,
        visualizacoes_labels=json.dumps(visualizacoes_labels),
        visualizacoes_values=json.dumps(visualizacoes_values),
        feedback_data=json.dumps(feedback_data),
        conteudo_markdown=conteudo_markdown,
    )


@bp.route("/tutoriais/<int:tutorial_id>/editar", methods=["GET", "POST"])
@login_required
def editar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    # Apenas membros da equipe de TI ou administradores podem editar tutoriais
    if not (session.get("is_ti") or session.get("is_admin")) or (
        not session.get("is_admin") and tutorial.autor_id != session.get("user_id")
    ):
        flash(
            "Apenas o autor TI ou administradores podem editar este tutorial.", "danger"
        )
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    form = TutorialForm(obj=tutorial)
    if form.validate_on_submit():
        tutorial.titulo = form.titulo.data
        tutorial.conteudo = form.conteudo.data
        tutorial.categoria = form.categoria.data
        # Upload de novas imagens
        if form.imagem.data:
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file = form.imagem.data
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                img = TutorialImage(tutorial_id=tutorial.id, filename=filename)
                db.session.add(img)
        db.session.commit()
        flash("Tutorial atualizado com sucesso!", "success")
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    return render_template("tutorial_form.html", form=form, title="Editar Tutorial")


@bp.route("/tutoriais/<int:tutorial_id>/excluir", methods=["POST"])
@login_required
def excluir_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    # Apenas membros da equipe de TI ou administradores podem excluir tutoriais
    if not (session.get("is_ti") or session.get("is_admin")) or (
        not session.get("is_admin") and tutorial.autor_id != session.get("user_id")
    ):
        flash(
            "Apenas o autor TI ou administradores podem excluir este tutorial.",
            "danger",
        )
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    # Excluir imagens do disco
    upload_folder = os.path.join(current_app.root_path, "static", "uploads")
    for img in tutorial.imagens:
        img_path = os.path.join(upload_folder, img.filename)
        if os.path.exists(img_path):
            os.remove(img_path)
        db.session.delete(img)
    db.session.delete(tutorial)
    db.session.commit()
    flash("Tutorial excluído com sucesso!", "success")
    return redirect(url_for("main.listar_tutoriais"))


@bp.route("/tutoriais/<int:tutorial_id>/comentar", methods=["POST"])
@login_required
def comentar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    feedback_form = FeedbackTutorialForm()
    if comentario_form.validate_on_submit():
        comentario = ComentarioTutorial(
            tutorial_id=tutorial.id,
            usuario_id=session.get("user_id"),
            texto=comentario_form.texto.data,
        )
        db.session.add(comentario)
        db.session.commit()
        flash("Comentário enviado com sucesso!", "success")
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    else:
        flash("Erro ao enviar comentário.", "danger")
        # Renderiza o template com os formulários em caso de erro
        return render_template(
            "tutorial_detalhe.html",
            tutorial=tutorial,
            comentario_form=comentario_form,
            feedback_form=feedback_form,
        )


@bp.route("/tutoriais/<int:tutorial_id>/feedback", methods=["POST"])
@login_required
def feedback_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    form = FeedbackTutorialForm()
    if form.validate_on_submit():
        feedback_existente = FeedbackTutorial.query.filter_by(
            tutorial_id=tutorial.id, usuario_id=session.get("user_id")
        ).first()
        if not feedback_existente:
            feedback = FeedbackTutorial(
                tutorial_id=tutorial.id,
                usuario_id=session.get("user_id"),
                util=form.util.data,
            )
            db.session.add(feedback)
            db.session.commit()
            flash("Feedback registrado!", "success")
        else:
            flash("Você já enviou feedback para este tutorial.", "info")
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    else:
        flash("Erro ao enviar feedback.", "danger")
        # Renderiza o template com os formulários em caso de erro
        return render_template(
            "tutorial_detalhe.html",
            tutorial=tutorial,
            comentario_form=comentario_form,
            feedback_form=form,
        )


@bp.route("/tutoriais/<int:tutorial_id>/pdf")
@login_required
def exportar_tutorial_pdf(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, tutorial.titulo)
    y -= 30
    p.setFont("Helvetica", 12)
    p.drawString(40, y, f'Categoria: {tutorial.categoria or "Sem categoria"}')
    y -= 20
    p.drawString(40, y, f"Autor: {tutorial.autor.username}")
    y -= 20
    p.drawString(40, y, f'Data: {tutorial.data_criacao.strftime("%d/%m/%Y %H:%M")}')
    y -= 30
    p.setFont("Helvetica", 12)
    conteudo = tutorial.conteudo.replace("\r", "").split("\n")
    for linha in conteudo:
        if y < 60:
            p.showPage()
            y = height - 40
            p.setFont("Helvetica", 12)
        p.drawString(40, y, linha[:110])
        y -= 18
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"tutorial_{tutorial.id}.pdf",
        mimetype="application/pdf",
    )


# ========================================
# ROTAS PARA CONTROLE DE EQUIPAMENTOS
# ========================================


@bp.route("/equipment/list")
@login_required
def list_equipment():
    """Lista todas as solicitações de equipamentos"""
    # Filtros
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "").strip()

    # Query base
    if session.get("is_admin") or session.get("is_ti"):
        # TI/Admin vê todas as solicitações
        query = EquipmentRequest.query
    else:
        # Usuário comum vê apenas suas solicitações
        query = EquipmentRequest.query.filter_by(requester_id=session.get("user_id"))

    # Aplicar filtros
    if status_filter:
        query = query.filter(EquipmentRequest.status == status_filter)

    if search:
        query = query.filter(
            db.or_(
                EquipmentRequest.description.contains(search),
                EquipmentRequest.patrimony.contains(search),
                EquipmentRequest.equipment_type.contains(search),
            )
        )

    # Ordenar por data de solicitação (mais recente primeiro)
    equipment_requests = query.order_by(EquipmentRequest.request_date.desc()).all()

    return render_template(
        "equipment_list.html",
        equipment_requests=equipment_requests,
        status_filter=status_filter,
        search=search,
    )


@bp.route("/equipment/new", methods=["GET", "POST"])
@login_required
def new_equipment_request():
    """Nova solicitação de equipamento"""
    if request.method == "POST":
        # Validar dados
        description = request.form.get("description", "").strip()
        patrimony = request.form.get("patrimony", "").strip()
        equipment_type = request.form.get("equipment_type", "").strip()
        destination_sector = request.form.get("destination_sector", "").strip()
        request_reason = request.form.get("request_reason", "").strip()
        delivery_date_str = request.form.get("delivery_date", "").strip()
        observations = request.form.get("observations", "").strip()

        if not description:
            flash("Descrição é obrigatória.", "danger")
            return render_template("equipment_form.html")

        if not request_reason:
            flash("Motivo da solicitação é obrigatório.", "danger")
            return render_template("equipment_form.html")

        if not destination_sector:
            flash("Setor/Destino é obrigatório.", "danger")
            return render_template("equipment_form.html")

        # Converter data se fornecida
        delivery_date = None
        if delivery_date_str:
            try:
                delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Data de entrega inválida.", "danger")
                return render_template("equipment_form.html")

        # Criar solicitação
        equipment_request = EquipmentRequest(
            description=description,
            patrimony=patrimony if patrimony else None,
            equipment_type=equipment_type if equipment_type else None,
            destination_sector=destination_sector if destination_sector else None,
            request_reason=request_reason if request_reason else None,
            delivery_date=delivery_date,
            observations=observations if observations else None,
            requester_id=session.get("user_id"),
            status="Solicitado",
        )

        db.session.add(equipment_request)
        db.session.commit()

        flash("Solicitação de equipamento criada com sucesso!", "success")
        return redirect(url_for("main.list_equipment"))

    return render_template("equipment_form.html")


@bp.route("/equipment/<int:id>")
@login_required
def equipment_detail(id):
    """Detalhes de uma solicitação de equipamento"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not (
        session.get("is_admin")
        or session.get("is_ti")
        or equipment_request.requester_id == session.get("user_id")
    ):
        flash("Você não tem permissão para ver esta solicitação.", "danger")
        return redirect(url_for("main.list_equipment"))

    return render_template("equipment_detail.html", equipment_request=equipment_request)


@bp.route("/equipment/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_equipment_request(id):
    """Editar solicitação de equipamento"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_edited_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para editar esta solicitação.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if request.method == "POST":
        # Validar dados
        description = request.form.get("description", "").strip()
        patrimony = request.form.get("patrimony", "").strip()
        equipment_type = request.form.get("equipment_type", "").strip()
        destination_sector = request.form.get("destination_sector", "").strip()
        request_reason = request.form.get("request_reason", "").strip()
        delivery_date_str = request.form.get("delivery_date", "").strip()
        observations = request.form.get("observations", "").strip()

        if not description:
            flash("Descrição é obrigatória.", "danger")
            return render_template(
                "equipment_form.html", equipment_request=equipment_request
            )

        if not request_reason:
            flash("Motivo da solicitação é obrigatório.", "danger")
            return render_template(
                "equipment_form.html", equipment_request=equipment_request
            )

        if not destination_sector:
            flash("Setor/Destino é obrigatório.", "danger")
            return render_template(
                "equipment_form.html", equipment_request=equipment_request
            )

        # Converter data se fornecida
        delivery_date = None
        if delivery_date_str:
            try:
                delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Data de entrega inválida.", "danger")
                return render_template(
                    "equipment_form.html", equipment_request=equipment_request
                )

        # Atualizar dados
        equipment_request.description = description
        equipment_request.patrimony = patrimony if patrimony else None
        equipment_request.equipment_type = equipment_type if equipment_type else None
        equipment_request.destination_sector = (
            destination_sector if destination_sector else None
        )
        equipment_request.request_reason = request_reason if request_reason else None
        equipment_request.delivery_date = delivery_date
        equipment_request.observations = observations if observations else None

        db.session.commit()

        flash("Solicitação atualizada com sucesso!", "success")
        return redirect(url_for("main.equipment_detail", id=id))

    return render_template("equipment_form.html", equipment_request=equipment_request)


@bp.route("/equipment/<int:id>/approve", methods=["POST"])
@login_required
def approve_equipment_request(id):
    """Aprovar solicitação de equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para aprovar solicitações.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if equipment_request.status != "Solicitado":
        flash("Apenas solicitações pendentes podem ser aprovadas.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    # Aprovar solicitação
    equipment_request.status = "Aprovado"
    equipment_request.approved_by_id = session.get("user_id")
    equipment_request.approval_date = datetime.utcnow()

    db.session.commit()

    flash("Solicitação aprovada com sucesso!", "success")
    return redirect(url_for("main.equipment_detail", id=id))


@bp.route("/equipment/<int:id>/reject", methods=["POST"])
@login_required
def reject_equipment_request(id):
    """Recusar solicitação de equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para recusar solicitações.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if equipment_request.status != "Solicitado":
        flash("Apenas solicitações pendentes podem ser recusadas.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    # Recusar solicitação
    equipment_request.status = "Negado"
    equipment_request.approved_by_id = session.get("user_id")
    equipment_request.approval_date = datetime.utcnow()

    db.session.commit()

    flash("Solicitação recusada.", "warning")
    return redirect(url_for("main.equipment_detail", id=id))


@bp.route("/equipment/<int:id>/deliver", methods=["POST"])
@login_required
def deliver_equipment_request(id):
    """Marcar equipamento como entregue (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para marcar como entregue.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if equipment_request.status != "Aprovado":
        flash(
            "Apenas solicitações aprovadas podem ser marcadas como entregues.", "danger"
        )
        return redirect(url_for("main.equipment_detail", id=id))

    # Marcar como entregue
    equipment_request.status = "Entregue"
    equipment_request.received_by_id = session.get("user_id")
    equipment_request.delivery_date = datetime.utcnow().date()

    db.session.commit()

    flash("Equipamento marcado como entregue!", "success")
    return redirect(url_for("main.equipment_detail", id=id))


@bp.route("/equipment/<int:id>/return", methods=["POST"])
@login_required
def return_equipment_request(id):
    """Marcar equipamento como devolvido (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para marcar como devolvido.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if equipment_request.status != "Entregue":
        flash(
            "Apenas equipamentos entregues podem ser marcados como devolvidos.",
            "danger",
        )
        return redirect(url_for("main.equipment_detail", id=id))

    # Marcar como devolvido
    equipment_request.status = "Devolvido"
    equipment_request.return_date = datetime.utcnow().date()

    db.session.commit()

    flash("Equipamento marcado como devolvido!", "success")
    return redirect(url_for("main.equipment_detail", id=id))


@bp.route("/equipment/<int:id>/fill_technical", methods=["GET", "POST"])
@login_required
def fill_technical_data(id):
    """Preencher dados técnicos do equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get("user_id"))):
        flash("Você não tem permissão para preencher dados técnicos.", "danger")
        return redirect(url_for("main.equipment_detail", id=id))

    if request.method == "POST":
        # Validar dados
        patrimony = request.form.get("patrimony", "").strip()
        equipment_type = request.form.get("equipment_type", "").strip()
        delivery_date_str = request.form.get("delivery_date", "").strip()
        conference_status = request.form.get("conference_status", "").strip()

        # Atualizar dados técnicos
        equipment_request.patrimony = patrimony if patrimony else None
        equipment_request.equipment_type = equipment_type if equipment_type else None
        equipment_request.conference_status = (
            conference_status if conference_status else None
        )

        # Converter data se fornecida
        if delivery_date_str:
            try:
                equipment_request.delivery_date = datetime.strptime(
                    delivery_date_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Data de entrega inválida.", "danger")
                return render_template(
                    "equipment_technical_form.html", equipment_request=equipment_request
                )

        db.session.commit()

        flash("Dados técnicos atualizados com sucesso!", "success")
        return redirect(url_for("main.equipment_detail", id=id))

    return render_template(
        "equipment_technical_form.html", equipment_request=equipment_request
    )


# ========================================
# ROTAS PARA INTEGRAÇÃO RFID
# ========================================

@bp.route("/rfid/scan", methods=["POST"])
@login_required
def rfid_scan():
    """Endpoint para leitura RFID - chamado pelos leitores"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Dados não fornecidos"}), 400

    rfid_tag = data.get("rfid_tag")
    reader_id = data.get("reader_id")

    if not rfid_tag or not reader_id:
        return jsonify({"success": False, "message": "Tag RFID e reader_id são obrigatórios"}), 400

    # Processar leitura RFID
    result = RFIDService.scan_equipment(rfid_tag, reader_id)

    # Log da operação
    if result["success"]:
        current_app.logger.info(f"RFID Scan - Tag: {rfid_tag}, Reader: {reader_id}, Location: {result.get('new_location', 'Unknown')}")
    else:
        current_app.logger.warning(f"RFID Scan Failed - Tag: {rfid_tag}, Reader: {reader_id}, Error: {result['message']}")

    return jsonify(result)


@bp.route("/rfid/simulate/<rfid_tag>/<reader_id>", methods=["POST"])
@login_required
@admin_required
def simulate_rfid_scan(rfid_tag, reader_id):
    """Simular leitura RFID para testes (apenas admin)"""
    result = RFIDService.simulate_rfid_scan(rfid_tag, reader_id)

    if result["success"]:
        flash(f"Leitura RFID simulada: {result['message']}", "success")
    else:
        flash(f"Erro na simulação: {result['message']}", "danger")

    return redirect(url_for("main.rfid_dashboard"))


@bp.route("/rfid/assign/<int:equipment_id>", methods=["POST"])
@login_required
@admin_required
def assign_rfid_tag(equipment_id):
    """Atribuir tag RFID a um equipamento"""
    rfid_tag = request.form.get("rfid_tag", "").strip()

    if not rfid_tag:
        flash("Tag RFID é obrigatória.", "danger")
        return redirect(url_for("main.equipment_detail", id=equipment_id))

    result = RFIDService.assign_rfid_tag(equipment_id, rfid_tag)

    if result["success"]:
        flash("Tag RFID atribuída com sucesso!", "success")
    else:
        flash(f"Erro ao atribuir tag: {result['message']}", "danger")

    return redirect(url_for("main.equipment_detail", id=equipment_id))


@bp.route("/rfid/remove/<int:equipment_id>", methods=["POST"])
@login_required
@admin_required
def remove_rfid_tag(equipment_id):
    """Remover tag RFID de um equipamento"""
    result = RFIDService.remove_rfid_tag(equipment_id)

    if result["success"]:
        flash("Tag RFID removida com sucesso!", "success")
    else:
        flash(f"Erro ao remover tag: {result['message']}", "danger")

    return redirect(url_for("main.equipment_detail", id=equipment_id))


@bp.route("/rfid/location/<int:equipment_id>")
@login_required
def get_equipment_location(equipment_id):
    """Obter localização atual de um equipamento via RFID"""
    result = RFIDService.get_equipment_location(equipment_id)
    return jsonify(result)


@bp.route("/rfid/dashboard")
@login_required
@admin_required
def rfid_dashboard():
    """Dashboard de monitoramento RFID"""
    # Obter equipamentos com RFID ativo
    rfid_equipment = EquipmentRequest.query.filter(
        EquipmentRequest.rfid_tag.isnot(None)
    ).order_by(EquipmentRequest.updated_at.desc()).all()

    # Obter equipamentos perdidos
    lost_equipment = RFIDService.get_lost_equipment()

    # Status dos leitores
    reader_status = RFIDService.get_reader_status()

    # Estatísticas RFID
    total_rfid_equipment = len(rfid_equipment)
    active_rfid_equipment = sum(1 for eq in rfid_equipment if eq.rfid_status == "ativo")
    lost_count = len(lost_equipment)

    return render_template(
        "rfid_dashboard.html",
        rfid_equipment=rfid_equipment,
        lost_equipment=lost_equipment,
        reader_status=reader_status,
        total_rfid_equipment=total_rfid_equipment,
        active_rfid_equipment=active_rfid_equipment,
        lost_count=lost_count,
    )


@bp.route("/rfid/bulk-assign", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_assign_rfid():
    """Atribuição em lote de tags RFID"""
    if request.method == "POST":
        equipment_ids = request.form.getlist("equipment_ids[]")
        rfid_tags = request.form.getlist("rfid_tags[]")

        if not equipment_ids or not rfid_tags:
            flash("Selecione equipamentos e forneça tags RFID.", "danger")
            return redirect(url_for("main.bulk_assign_rfid"))

        # Converter para inteiros
        try:
            equipment_ids = [int(id) for id in equipment_ids]
        except ValueError:
            flash("IDs de equipamentos inválidos.", "danger")
            return redirect(url_for("main.bulk_assign_rfid"))

        result = RFIDService.bulk_assign_rfid_tags(equipment_ids, rfid_tags)

        if result["success"]:
            flash(result["message"], "success")
        else:
            flash(result["message"], "danger")

        return redirect(url_for("main.rfid_dashboard"))

    # GET: mostrar formulário
    # Equipamentos sem RFID atribuído
    available_equipment = EquipmentRequest.query.filter(
        EquipmentRequest.rfid_tag.is_(None),
        EquipmentRequest.status.in_(["Aprovado", "Entregue"])
    ).order_by(EquipmentRequest.id).all()

    return render_template("rfid_bulk_assign.html", available_equipment=available_equipment)


@bp.route("/api/rfid/status")
@login_required
def rfid_status_api():
    """API para status RFID em tempo real"""
    reader_status = RFIDService.get_reader_status()
    lost_equipment = RFIDService.get_lost_equipment()

    return jsonify({
        "readers": reader_status,
        "lost_equipment_count": len(lost_equipment),
        "lost_equipment": [
            {
                "id": eq.id,
                "description": eq.description,
                "last_scan": eq.rfid_last_scan.isoformat() if eq.rfid_last_scan else None
            }
            for eq in lost_equipment[:5]  # Limitar a 5 para performance
        ],
        "timestamp": get_current_time_for_db().isoformat()
    })


# ========================================
# ROTAS PARA MÉTRICAS DE SATISFAÇÃO
# ========================================

@bp.route("/satisfaction/survey/<int:chamado_id>", methods=["GET", "POST"])
@login_required
def satisfaction_survey(chamado_id):
    """Página de pesquisa de satisfação para chamados"""
    chamado = Chamado.query.get_or_404(chamado_id)

    # Verificar se usuário pode avaliar este chamado
    if chamado.solicitante_id != session.get("user_id") and not session.get("is_admin"):
        flash("Você não tem permissão para avaliar este chamado.", "danger")
        return redirect(url_for("main.index"))

    # Verificar se chamado está fechado
    if chamado.status != "Fechado":
        flash("Apenas chamados fechados podem ser avaliados.", "warning")
        return redirect(url_for("main.detalhe_chamado", id=chamado_id))

    # Verificar se já foi avaliado
    if chamado.satisfaction_rating:
        flash("Este chamado já foi avaliado.", "info")
        return redirect(url_for("main.detalhe_chamado", id=chamado_id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        if not rating or not 1 <= rating <= 5:
            flash("Por favor, selecione uma avaliação válida (1-5 estrelas).", "danger")
            return render_template("satisfaction_survey.html", chamado=chamado)

        result = SatisfactionService.record_satisfaction_rating(chamado_id, rating, comment)

        if result["success"]:
            flash("Avaliação registrada com sucesso! Obrigado pelo feedback.", "success")
            return redirect(url_for("main.detalhe_chamado", id=chamado_id))
        else:
            flash(f"Erro ao registrar avaliação: {result['message']}", "danger")

    return render_template("satisfaction_survey.html", chamado=chamado)


@bp.route("/satisfaction/dashboard")
@login_required
@admin_required
def satisfaction_dashboard():
    """Dashboard de métricas de satisfação"""
    # Estatísticas gerais
    stats_30_days = SatisfactionService.get_satisfaction_stats(30)
    stats_90_days = SatisfactionService.get_satisfaction_stats(90)

    # Tendências
    trends = SatisfactionService.get_satisfaction_trends(6)

    # Feedback detalhado recente
    recent_feedback = SatisfactionService.get_detailed_feedback(30)

    # Chamados pendentes de avaliação
    pending_surveys = SatisfactionService.get_pending_surveys()

    return render_template(
        "satisfaction_dashboard.html",
        stats_30_days=stats_30_days,
        stats_90_days=stats_90_days,
        trends=trends,
        recent_feedback=recent_feedback[:10],  # Limitar a 10 mais recentes
        pending_surveys=pending_surveys[:10]   # Limitar a 10 pendentes
    )


@bp.route("/satisfaction/send-survey/<int:chamado_id>", methods=["POST"])
@login_required
@admin_required
def send_satisfaction_survey(chamado_id):
    """Enviar pesquisa de satisfação manualmente"""
    result = SatisfactionService.send_satisfaction_survey(chamado_id)

    if result["success"]:
        flash("Pesquisa de satisfação enviada com sucesso!", "success")
    else:
        flash(f"Erro ao enviar pesquisa: {result['message']}", "danger")

    return redirect(url_for("main.detalhe_chamado", id=chamado_id))


@bp.route("/api/satisfaction/stats")
@login_required
def satisfaction_stats_api():
    """API para estatísticas de satisfação em tempo real"""
    stats = SatisfactionService.get_satisfaction_stats(30)

    return jsonify({
        "average_rating": stats["average_rating"],
        "total_surveys": stats["total_surveys"],
        "response_rate": stats["response_rate"],
        "rating_distribution": stats["rating_distribution"],
        "timestamp": get_current_time_for_db().isoformat()
    })


# ========================================
# ROTAS PARA CERTIFICAÇÕES
# ========================================

@bp.route("/certifications/dashboard")
@login_required
def certifications_dashboard():
    """Dashboard de certificações e leaderboard"""
    # Obter dados para o template com tratamento de erro
    try:
        leaderboard = CertificationService.get_leaderboard(20)
    except Exception as e:
        current_app.logger.error(f"Erro ao obter leaderboard: {e}")
        leaderboard = []

    try:
        cert_stats = CertificationService.get_certification_stats()
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {e}")
        cert_stats = {"total_users": 0, "total_certifications": 0, "active_certifications": 0}

    try:
        user_certs = CertificationService.get_user_certifications(session.get("user_id"))
    except Exception as e:
        current_app.logger.error(f"Erro ao obter certificações do usuário: {e}")
        user_certs = []

    # Métricas do usuário atual com verificação segura
    user_metrics = None
    try:
        current_user = User.query.get(session.get("user_id"))
        if current_user:
            # Verificar se contribution_metrics existe e tem dados
            if hasattr(current_user, 'contribution_metrics') and current_user.contribution_metrics:
                user_metrics = current_user.contribution_metrics[0] if len(current_user.contribution_metrics) > 0 else None
    except Exception as e:
        current_app.logger.error(f"Erro ao obter métricas do usuário: {e}")
        user_metrics = None

    return render_template(
        "certifications_dashboard.html",
        leaderboard=leaderboard,
        cert_stats=cert_stats,
        user_certs=user_certs,
        user_metrics=user_metrics
    )


@bp.route("/certifications/update-metrics/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def update_user_metrics(user_id):
    """Atualizar métricas de um usuário (admin)"""
    result = CertificationService.update_user_metrics(user_id)

    if result["success"]:
        flash("Métricas atualizadas com sucesso!", "success")
    else:
        flash(f"Erro ao atualizar métricas: {result['message']}", "danger")

    return redirect(url_for("main.certifications_dashboard"))


@bp.route("/certifications/award/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def award_certification(user_id):
    """Atribuir certificação a um usuário"""
    cert_type = request.form.get("certification_type")
    level = request.form.get("level", type=int)

    result = CertificationService.award_certification(user_id, cert_type, level)

    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(f"Erro ao atribuir certificação: {result['message']}", "danger")

    return redirect(url_for("main.certifications_dashboard"))


@bp.route("/api/certifications/leaderboard")
@login_required
def certifications_leaderboard_api():
    """API para leaderboard em tempo real"""
    leaderboard = CertificationService.get_leaderboard(10)

    return jsonify({
        "leaderboard": leaderboard,
        "timestamp": get_current_time_for_db().isoformat()
    })


# ========================================
# ROTAS DE MONITORAMENTO DE PERFORMANCE
# ========================================

@bp.route("/performance/dashboard")
@login_required
@admin_required
def performance_dashboard():
    """Dashboard de monitoramento de performance"""
    # Métricas do sistema
    system_metrics = PerformanceService.get_performance_metrics()

    # Estatísticas do banco de dados
    db_stats = PerformanceService.get_database_performance_stats()

    # Relatório completo
    performance_report = PerformanceService.generate_performance_report()

    return render_template(
        "performance_dashboard.html",
        system_metrics=system_metrics,
        db_stats=db_stats,
        performance_report=performance_report
    )


@bp.route("/performance/optimize")
@login_required
@admin_required
def optimize_performance():
    """Executa otimizações de performance"""
    results = {}

    # Criar índices
    index_result = PerformanceService.create_database_indexes()
    results["indexes"] = index_result

    # Otimizar queries
    PerformanceService.optimize_query_performance()
    results["query_optimization"] = {"success": True, "message": "Otimizações aplicadas"}

    # Limpeza de dados antigos
    cleanup_result = PerformanceService.cleanup_old_data()
    results["cleanup"] = cleanup_result

    flash("Otimizações de performance executadas!", "success")

    return redirect(url_for("main.performance_dashboard"))


@bp.route("/api/performance/metrics")
@login_required
@admin_required
def performance_metrics_api():
    """API para métricas de performance em tempo real"""
    metrics = PerformanceService.get_performance_metrics()
    db_stats = PerformanceService.get_database_performance_stats()

    return jsonify({
        "system": metrics,
        "database": db_stats,
        "timestamp": time_module.time()
    })


@bp.route("/performance/report")
@login_required
@admin_required
def performance_report():
    """Gera relatório de performance em PDF"""
    from flask import make_response
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from io import BytesIO

    # Coletar dados
    report_data = PerformanceService.generate_performance_report()

    # Criar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )

    elements.append(Paragraph("RELATÓRIO DE PERFORMANCE - TI OSN", title_style))
    elements.append(Spacer(1, 12))

    # Métricas do sistema
    elements.append(Paragraph("MÉTRICAS DO SISTEMA", styles['Heading2']))
    elements.append(Spacer(1, 12))

    system_data = report_data.get("system_performance", {})
    system_table_data = [
        ["Métrica", "Valor"],
        ["CPU (%)", f"{system_data.get('cpu_percent', 0)}%"],
        ["Memória (%)", f"{system_data.get('memory_percent', 0)}%"],
        ["Memória Usada (GB)", f"{system_data.get('memory_used_gb', 0):.2f}"],
        ["Disco (%)", f"{system_data.get('disk_percent', 0)}%"],
        ["Disco Usado (GB)", f"{system_data.get('disk_used_gb', 0):.2f}"],
        ["Memória App (MB)", f"{system_data.get('app_memory_mb', 0):.2f}"],
        ["CPU App (%)", f"{system_data.get('app_cpu_percent', 0)}%"],
    ]

    system_table = Table(system_table_data, colWidths=[3*inch, 2*inch])
    system_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(system_table)
    elements.append(Spacer(1, 20))

    # Métricas do banco
    elements.append(Paragraph("MÉTRICAS DO BANCO DE DADOS", styles['Heading2']))
    elements.append(Spacer(1, 12))

    db_data = report_data.get("database_performance", {})
    db_table_data = [
        ["Métrica", "Valor"],
        ["Conexões Ativas", db_data.get("active_connections", 0)],
        ["Cache Hit Ratio (%)", f"{db_data.get('cache_hit_ratio', 0)}%"],
    ]

    db_table = Table(db_table_data, colWidths=[3*inch, 2*inch])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(db_table)
    elements.append(Spacer(1, 20))

    # Recomendações
    recommendations = report_data.get("recommendations", [])
    if recommendations:
        elements.append(Paragraph("RECOMENDAÇÕES", styles['Heading2']))
        elements.append(Spacer(1, 12))

        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", styles['Normal']))
            elements.append(Spacer(1, 6))

    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=performance_report_{int(time.time())}.pdf'

    return response


@bp.route("/install-pwa")
def install_pwa():
    """Página de instruções para instalação PWA"""
    return render_template("install_pwa.html")


@bp.route("/offline")
def offline():
    """Página offline"""
    return render_template("offline.html")


@bp.route("/test-notification")
@login_required
def test_notification():
    """Endpoint para testar notificações"""
    return jsonify(
        {
            "reminders_expiring": [
                {
                    "id": 999,
                    "name": "Teste de Notificação",
                    "responsible": "Sistema",
                    "days_left": 1,
                }
            ],
            "chamados_updated": [],
            "tasks_overdue": [],
        }
    )


@bp.route("/api/notifications")
def api_notifications():
    """Endpoint para API de notificações usado pelo notifications.js"""
    # Verificar se o usuário está autenticado
    if "user_id" not in session:
        return (
            jsonify(
                {
                    "error": "Não autenticado",
                    "reminders_expiring": [],
                    "chamados_updated": [],
                    "tasks_overdue": [],
                }
            ),
            200,
        )  # Retornar código 200 em vez de redirecionar

    # Verificar lembretes próximos do vencimento (7 dias)
    user_id = session.get("user_id")
    today = date.today()

    # Lembretes vencendo em até 7 dias
    if session.get("is_admin"):
        reminders_expiring = Reminder.query.filter(
            Reminder.due_date >= today,
            Reminder.due_date <= today + timedelta(days=7),
            Reminder.completed == False,
            Reminder.status == "ativo",
        ).all()
    else:
        reminders_expiring = Reminder.query.filter(
            Reminder.due_date >= today,
            Reminder.due_date <= today + timedelta(days=7),
            Reminder.completed == False,
            Reminder.status == "ativo",
            Reminder.user_id == user_id,
        ).all()

    # Tarefas vencidas
    if session.get("is_admin"):
        tasks_overdue = Task.query.filter(
            Task.date < today, Task.completed == False
        ).all()
    else:
        tasks_overdue = Task.query.filter(
            Task.date < today, Task.completed == False, Task.user_id == user_id
        ).all()

    # Chamados atualizados recentemente (últimas 24h)
    yesterday = datetime.now() - timedelta(days=1)

    if session.get("is_admin") or session.get("is_ti"):
        # Administradores e equipe de TI veem todos os chamados atualizados
        chamados_updated = Chamado.query.filter(
            Chamado.data_ultima_atualizacao >= yesterday, Chamado.status != "Fechado"
        ).all()
    else:
        # Usuários normais veem apenas seus próprios chamados atualizados
        chamados_updated = Chamado.query.filter(
            Chamado.data_ultima_atualizacao >= yesterday,
            Chamado.solicitante_id == user_id,
            Chamado.status != "Fechado",
        ).all()

    return jsonify(
        {
            "reminders_expiring": [
                {
                    "id": r.id,
                    "name": r.name,
                    "responsible": r.responsible,
                    "days_left": (r.due_date - today).days,
                }
                for r in reminders_expiring
            ],
            "chamados_updated": [
                {
                    "id": c.id,
                    "titulo": c.titulo,
                    "status": c.status,
                    "prioridade": c.prioridade,
                    "solicitante": c.solicitante.username
                    if c.solicitante
                    else "Desconhecido",
                }
                for c in chamados_updated
            ],
            "tasks_overdue": [
                {
                    "id": t.id,
                    "name": t.description,
                    "days_overdue": (today - t.date).days,
                }
                for t in tasks_overdue
            ],
        }
    )
