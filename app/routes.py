import os
from datetime import date, datetime, time, timedelta
import time as time_module
from functools import wraps

from dateutil.relativedelta import relativedelta
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for, send_from_directory)
from app.utils import flash_success, flash_error, flash_warning, flash_info
from werkzeug.utils import secure_filename

import markdown

from .auth_utils import login_required
from . import limiter  # Importar limiter para exceções de rate limit
from .forms import ChamadoAdminForm  # Importados formulários necessários
from .forms import (ChamadoEditForm, ChamadoForm, ComentarioTutorialForm, FeedbackTutorialForm,
                     ReminderForm, TaskForm, TutorialForm, UserEditForm)
from .models import Chamado  # Importados modelos necessários
from .models import ComentarioChamado, ComentarioTutorial, Equipment, EquipmentRequest, FeedbackTutorial, Reminder, Sector, Task, Tutorial, TutorialImage, User, VisualizacaoTutorial, db
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
            flash_error("Acesso restrito ao administrador.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def admin_or_ti_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (session.get("is_admin") or session.get("is_ti")):
            flash_error("Acesso restrito a administradores e equipe de TI.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def admin_or_ti_required_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (session.get("is_admin") or session.get("is_ti")):
            return jsonify({'error': 'Sem permissão'}), 403
        return f(*args, **kwargs)

    return decorated_function


bp = Blueprint("main", __name__)

@bp.route('/favicon.ico')
def favicon():
    """Serve favicon raiz: ICO se existir, caso contrário SVG."""
    import os
    static_dir = current_app.static_folder
    ico_path = os.path.join(static_dir, 'favicon.ico')
    if os.path.exists(ico_path):
        return send_from_directory(static_dir, 'favicon.ico', mimetype='image/x-icon')
    icons_dir = os.path.join(static_dir, 'icons')
    return send_from_directory(icons_dir, 'logo.svg', mimetype='image/svg+xml')


@bp.route("/")
@login_required
def index():
    # Importação local para evitar dependência circular se outros módulos importarem main.py diretamente
    from .models import Chamado, EquipmentReservation

    search = request.args.get("search", "").strip().lower()
    status = request.args.get("status", "").strip().lower()

    # NOTA: Recorrência automática agora é processada pelo ReminderService via scheduler
    # Não é mais necessário processar aqui, evitando problemas de performance e duplicação
    
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
        # Buscar equipamentos (fluxo novo equipment_v2 - reservas globais)
        equipamentos_count = EquipmentReservation.query.count()
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

        # Buscar equipamentos do usuário (fluxo novo equipment_v2)
        if is_ti:
            # TI vê todas as reservas
            equipamentos_count = EquipmentReservation.query.count()
        else:
            # Usuário comum vê apenas suas reservas
            equipamentos_count = EquipmentReservation.query.filter_by(
                user_id=user_id
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
@login_required
def complete_reminder(id):
    from .services.reminder_service import ReminderService
    
    # Verificar permissões
    if session.get("is_admin"):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    
    # Usar o serviço para completar e criar histórico automaticamente
    user_id = session.get("user_id")
    success = ReminderService.complete_reminder(
        reminder_id=id,
        user_id=user_id,
        notes=f"Lembrete marcado como concluído manualmente"
    )
    
    if success:
        flash_success("Lembrete marcado como realizado!")
    else:
        flash_error("Erro ao marcar lembrete como realizado.")
    
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
        flash_error("Lembrete cancelado!")
    elif reminder.status == "ativo":
        reminder.status = "pausado"
        flash_warning("Lembrete pausado!")
    elif reminder.status == "pausado":
        reminder.status = "ativo"
        reminder.pause_until = None
        flash_success("Lembrete reativado!")
    elif reminder.status == "cancelado":
        reminder.status = "ativo"
        flash_success("Lembrete reativado!")

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
        # Calcula o status do lembrete
        if r.completed:
            status = "completed"
        elif r.due_date:
            if r.due_date < date.today():
                status = "expired"
            elif r.due_date == date.today():
                status = "alert"
            elif (r.due_date - date.today()).days <= 7:
                status = "alert"
            else:
                status = "ok"
        else:
            status = "pending"
        
        # Pegar setor de forma segura
        sector_name = "-"
        try:
            if r.sector:
                if hasattr(r.sector, 'name'):
                    sector_name = r.sector.name
                elif isinstance(r.sector, str):
                    sector_name = r.sector
        except Exception as e:
            print(f"Erro ao obter setor do lembrete {r.id}: {e}")
            sector_name = "-"
        
        reminders_data.append(
            {
                "id": r.id,
                "name": r.name or "Sem nome",
                "type": r.type or "-",
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "responsible": r.responsible or "-",
                "frequency": r.frequency or "Nenhuma",
                "sector": sector_name,
                "completed": r.completed if r.completed is not None else False,
                "status_control": r.status or "ativo",
                "pause_until": r.pause_until.isoformat() if r.pause_until else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "priority": r.priority or "media",
                "contract_number": r.contract_number or "",
                "cost": float(r.cost) if r.cost is not None else None,
                "supplier": r.supplier or "",
                "notes": r.notes or "",
                "status": status,
                "category": r.category or "",
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


# ============================
# Exportações Analytics (PDF/Excel)
# ============================
@bp.route("/api/analytics/export/excel")
@login_required
def analytics_export_excel():
    """Exporta os dados atuais do dashboard Analytics em Excel (xlsx)."""
    from app.services.analytics.analytics_service import AnalyticsService
    from io import BytesIO
    import pandas as pd
    
    # Parâmetros de período
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()
    
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # KPIs
        kpis = AnalyticsService.get_dashboard_kpis()
        df_kpis = pd.DataFrame([
            {"Métrica": "Chamados Abertos", "Valor": kpis.get("chamados_abertos", 0)},
            {"Métrica": "Chamados do Mês", "Valor": kpis.get("chamados_mes", 0)},
            {"Métrica": "Taxa de SLA (%)", "Valor": kpis.get("sla_taxa", 0)},
            {"Métrica": "Satisfação Média", "Valor": kpis.get("satisfacao_media", 0)},
            {"Métrica": "Lembretes Ativos", "Valor": kpis.get("lembretes_ativos", 0)},
            {"Métrica": "Lembretes Vencidos", "Valor": kpis.get("lembretes_vencidos", 0)},
            {"Métrica": "Equipamentos em Uso", "Valor": kpis.get("equipamentos_uso", 0)},
            {"Métrica": "Total Tutoriais", "Valor": kpis.get("total_tutoriais", 0)},
            {"Métrica": "Visualizações Tutoriais", "Valor": kpis.get("total_visualizacoes", 0)},
            {"Métrica": "Tarefas Concluídas", "Valor": kpis.get("tasks_concluidas", 0)},
            {"Métrica": "Tarefas Pendentes", "Valor": kpis.get("tasks_pendentes", 0)},
        ])
        df_kpis.to_excel(writer, sheet_name="KPIs", index=False)
        
        # Evolução por período
        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        evolucao = AnalyticsService.get_chamados_por_periodo(start_d, end_d)
        df_evol = pd.DataFrame(evolucao)
        if not df_evol.empty:
            df_evol.to_excel(writer, sheet_name="Evolucao", index=False)
        
        # Prioridade
        prioridade = AnalyticsService.get_chamados_por_prioridade()
        df_pri = pd.DataFrame(prioridade)
        if not df_pri.empty:
            df_pri.to_excel(writer, sheet_name="Prioridade", index=False)
        
        # Performance técnico
        perf = AnalyticsService.get_performance_por_tecnico(start_d, end_d)
        df_perf = pd.DataFrame(perf)
        if not df_perf.empty:
            df_perf.to_excel(writer, sheet_name="Performance", index=False)
        
        # Setor
        setor = AnalyticsService.get_chamados_por_setor()
        df_set = pd.DataFrame(setor)
        if not df_set.empty:
            df_set.to_excel(writer, sheet_name="Setor", index=False)
    
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"analytics_dashboard_{date.today().isoformat()}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/api/analytics/export/pdf")
@login_required
def analytics_export_pdf():
    """Exporta um PDF com KPIs e tabelas resumidas do dashboard Analytics."""
    from app.services.analytics.analytics_service import AnalyticsService
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    # Parâmetros
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    
    # Buscar dados
    kpis = AnalyticsService.get_dashboard_kpis()
    evolucao = AnalyticsService.get_chamados_por_periodo(start_d, end_d)
    prioridade = AnalyticsService.get_chamados_por_prioridade()
    perf = AnalyticsService.get_performance_por_tecnico(start_d, end_d)
    setor = AnalyticsService.get_chamados_por_setor()
    
    # Montar PDF
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    content = []
    
    content.append(Paragraph("Dashboard Analytics - Relatório", styles["Title"]))
    content.append(Paragraph(f"Período: {start} a {end}", styles["Normal"]))
    content.append(Spacer(1, 12))
    
    # KPIs
    kpi_table = [["Métrica", "Valor"],
                 ["Chamados Abertos", kpis.get("chamados_abertos", 0)],
                 ["Chamados do Mês", kpis.get("chamados_mes", 0)],
                 ["Taxa de SLA (%)", kpis.get("sla_taxa", 0)],
                 ["Satisfação Média", kpis.get("satisfacao_media", 0)],
                 ["Lembretes Ativos", kpis.get("lembretes_ativos", 0)],
                 ["Lembretes Vencidos", kpis.get("lembretes_vencidos", 0)],
                 ["Equipamentos em Uso", kpis.get("equipamentos_uso", 0)],
                 ["Total Tutoriais", kpis.get("total_tutoriais", 0)],
                 ["Visualizações Tutoriais", kpis.get("total_visualizacoes", 0)],
                 ["Tarefas Concluídas", kpis.get("tasks_concluidas", 0)],
                 ["Tarefas Pendentes", kpis.get("tasks_pendentes", 0)]]
    t = Table(kpi_table, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    content.append(t)
    content.append(Spacer(1, 14))
    
    def add_table(title, data, headers):
        content.append(Paragraph(title, styles['Heading2']))
        rows = [headers] + [list(d.values()) if isinstance(d, dict) else d for d in data]
        tbl = Table(rows, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        content.append(tbl)
        content.append(Spacer(1, 10))
    
    if evolucao:
        add_table("Evolução de Chamados", evolucao, ["periodo", "total"])
    if prioridade:
        add_table("Chamados por Prioridade", prioridade, ["prioridade", "total"])
    if perf:
        add_table("Performance por Técnico", perf, ["tecnico", "total", "tempo_medio", "sla_taxa"])
    if setor:
        add_table("Chamados por Setor", setor, ["setor", "total"])
    
    doc.build(content)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"analytics_dashboard_{date.today().isoformat()}.pdf",
        mimetype='application/pdf'
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

        # Processar campo de custo (converter string para float)
        cost_value = None
        if form.cost.data:
            try:
                # Remover R$, espaços e converter vírgula para ponto
                cost_str = form.cost.data.replace('R$', '').replace(' ', '').replace(',', '.')
                cost_value = float(cost_str)
            except (ValueError, AttributeError):
                cost_value = None
        
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
            priority=form.priority.data,
            category=form.category.data,
            contract_number=form.contract_number.data,
            cost=cost_value,
            supplier=form.supplier.data,
            notes=form.notes.data,
            created_at=get_current_time_for_db(),
        )
        db.session.add(reminder)
        db.session.commit()
        flash_success("Lembrete cadastrado com sucesso!")
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
        flash_success("Lembrete atualizado!")
        return redirect(url_for("main.reminders"))
    return render_template(
        "reminders.html", reminders=Reminder.query.all(), form=form, edit_id=id
    )


@bp.route("/reminders/delete/<int:id>", methods=["POST"])
@login_required
def delete_reminder(id):
    # Admin pode excluir qualquer lembrete; usuário comum apenas os próprios
    if session.get("is_admin"):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(
            id=id, user_id=session.get("user_id")
        ).first_or_404()
    db.session.delete(reminder)
    db.session.commit()
    flash_success("Lembrete excluído!")
    return redirect(url_for("main.reminders"))


# --- API de Notificações ---
# Rota movida para o final do arquivo para evitar duplicação
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
                flash_error("Este email já está em uso por outro usuário.")
                return redirect(url_for("main.edit_user", id=user.id))

            # Verifica se o nome de usuário já está em uso por outro usuário
            existing_username = User.query.filter(
                User.username == form.username.data, User.id != user.id
            ).first()
            if existing_username:
                logger.warning(
                    f"Tentativa de usar nome de usuário já existente: {form.username.data}"
                )
                flash_error(
    "Este nome de usuário já está em uso por outro usuário."
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
                        flash_error(
                            "Não é possível remover os privilégios de administrador do último administrador ativo."
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
                    flash_error("A senha deve ter pelo menos 6 caracteres.")
                    return redirect(url_for("main.edit_user", id=user.id))
                user.set_password(form.new_password.data)
                logger.info("Senha do usuário atualizada com sucesso")
                flash_success("Senha alterada com sucesso!")

            # Salva as alterações no banco de dados
            db.session.commit()
            logger.info(f"Usuário {user.id} atualizado com sucesso no banco de dados")

            flash_success("Usuário atualizado com sucesso!")
            return redirect(url_for("main.users_admin"))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar usuário: {str(e)}", exc_info=True)
            flash_error(f"Erro ao atualizar usuário: {str(e)}")
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
        flash_error("Você não pode desativar sua própria conta.")
        return redirect(url_for("main.users_admin"))

    # Verifica se está tentando desativar o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash_error(
                "Não é possível desativar o último administrador ativo do sistema."
            )
            return redirect(url_for("main.users_admin"))

    user.ativo = not user.ativo

    try:
        db.session.commit()
        status = "ativado" if user.ativo else "desativado"
        flash_success(f"Usuário {status} com sucesso!")
    except Exception as e:
        db.session.rollback()
        flash_error("Ocorreu um erro ao atualizar o status do usuário.")

    return redirect(url_for("main.users_admin"))


@bp.route("/admin/users/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_user(id):
    from .models import User

    user = User.query.get_or_404(id)

    # Impede que o usuário exclua a si mesmo
    if id == session.get("user_id"):
        flash_error("Você não pode excluir sua própria conta.")
        return redirect(url_for("main.users_admin"))

    # Verifica se está tentando excluir o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash_error(
                "Não é possível excluir o último administrador ativo do sistema."
            )
            return redirect(url_for("main.users_admin"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash_success("Usuário excluído com sucesso!")
    except Exception as e:
        db.session.rollback()
        flash_error(
            "Ocorreu um erro ao excluir o usuário. Por favor, tente novamente."
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
            flash_error("Nome de usuário ou email já está em uso.")
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
            flash_success("Usuário criado com sucesso!")
            return redirect(url_for("main.users_admin"))
        except Exception as e:
            db.session.rollback()
            flash_error(
                "Ocorreu um erro ao criar o usuário. Por favor, tente novamente."
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

    flash_success(
        f"Senha redefinida com sucesso! Nova senha: {password} - Recomenda-se copiar e enviar ao usuário por um canal seguro."
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
            flash_error("Senha atual incorreta.")
            return render_template("user_profile.html", form=form, user=user)

        # Alterar para a nova senha
        user.set_password(form.new_password.data)
        db.session.commit()

        flash_success("Senha alterada com sucesso!")
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
    from datetime import datetime, date

    # Obter permissões do usuário
    permissions = PermissionManager.get_user_permissions()
    is_admin = permissions.get('is_admin', False)
    is_ti = permissions.get('is_ti', False)
    can_view_all = permissions.get('can_view_all', False)

    def apply_permissions(query, model_name):
        """Aplica filtro de permissões conforme o perfil atual."""
        return PermissionManager.filter_query_by_permissions(query, model_name, permissions)

    # Processar filtros da requisição
    filters = {
        'task_status': request.args.get("task_status", ""),
        'reminder_status': request.args.get("reminder_status", ""),
        'chamado_status': request.args.get("chamado_status", ""),
        'start_date': None,
        'end_date': None,
        'sector_id': request.args.get("sector_id", type=int),
        'user_id': request.args.get("user_id", type=int),
        'sla_page': request.args.get("sla_page", 1, type=int),
        'sla_per_page': request.args.get("sla_per_page", 10, type=int),
        # Escopo global: estatísticas de todo o sistema (sem restrições por usuário)
        'global': can_view_all,
    }

    # Converter datas com validação
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")

    if start_date_str:
        try:
            filters['start_date'] = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash_warning("Data inicial inválida.")

    if end_date_str:
        try:
            filters['end_date'] = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash_warning("Data final inválida.")

    # Obter dados filtrados usando o serviço (para gráficos, SLA etc.)
    dashboard_data = DashboardService.get_filtered_data(filters, permissions)

    # ======================================================
    # ESTATÍSTICAS GLOBAIS (SEM FILTRO POR USUÁRIO/SETOR)
    # Usadas pelos cards principais do topo do dashboard
    # ======================================================
    from app.models import Task, Reminder, Chamado

    # Atividades & Projetos (Task)
    tasks_total_global = Task.query.count()
    tasks_done_global = Task.query.filter_by(completed=True).count()
    tasks_pending_global = Task.query.filter(
        Task.completed == False,  # noqa: E712
        Task.date >= date.today()
    ).count()
    tasks_expired_global = Task.query.filter(
        Task.completed == False,  # noqa: E712
        Task.date < date.today()
    ).count()

    # Notificações Programadas (Reminder)
    reminders_total_global = Reminder.query.count()
    reminders_done_global = Reminder.query.filter_by(completed=True).count()
    reminders_pending_global = Reminder.query.filter_by(completed=False).count()

    # Tickets & Suporte (Chamado)
    chamados_total_global = Chamado.query.count()
    chamados_aberto_global = Chamado.query.filter_by(status='Aberto').count()
    chamados_em_andamento_global = Chamado.query.filter_by(status='Em Andamento').count()
    chamados_resolvido_global = Chamado.query.filter_by(status='Resolvido').count()
    chamados_fechado_global = Chamado.query.filter_by(status='Fechado').count()

    # Preparar dados para o template
    if can_view_all:
        inventory_total = Equipment.query.count()
        inventory_disponiveis = Equipment.query.filter_by(status='disponivel').count()
        inventory_emprestados = Equipment.query.filter_by(status='emprestado').count()
        inventory_manutencao = Equipment.query.filter_by(status='manutencao').count()
        inventory_danificados = Equipment.query.filter_by(status='danificado').count()
        inventory_perdidos = Equipment.query.filter_by(status='perdido').count()
    else:
        inventory_total = 0
        inventory_disponiveis = 0
        inventory_emprestados = 0
        inventory_manutencao = 0
        inventory_danificados = 0
        inventory_perdidos = 0

    # Estatísticas de equipamentos para o card "Gestão de Ativos" (fluxo equipment_v2)
    # Sempre globais: somam todas as solicitações/empréstimos do sistema
    from app.models import EquipmentReservation, EquipmentLoan
    equipamentos_total = EquipmentReservation.query.count()
    equipamentos_solicitados = EquipmentReservation.query.filter_by(status='pendente').count()
    equipamentos_negados = EquipmentReservation.query.filter_by(status='rejeitada').count()
    equipamentos_entregues = EquipmentLoan.query.count()

    template_data = {
        # Estatísticas de tarefas (globais para o card de Atividades & Projetos)
        'tasks_total': tasks_total_global,
        'tasks_done': tasks_done_global,
        'tasks_pending': tasks_pending_global,
        'tasks_expired': tasks_expired_global,

        # Estatísticas de lembretes (globais para o card de Notificações Programadas)
        'reminders_total': reminders_total_global,
        'reminders_done': reminders_done_global,
        'reminders_pending': reminders_pending_global,

        # Estatísticas de chamados (globais para o card de Tickets & Suporte)
        'chamados_total': chamados_total_global,
        'chamados_aberto': chamados_aberto_global,
        'chamados_em_andamento': chamados_em_andamento_global,
        'chamados_resolvido': chamados_resolvido_global,
        'chamados_fechado': chamados_fechado_global,

        # Estatísticas de equipamentos (novo fluxo equipment_v2)
        'equipamentos_total': equipamentos_total,
        'equipamentos_solicitados': equipamentos_solicitados,
        'equipamentos_aprovados': dashboard_data['stats']['equipamentos']['aprovados'],
        'equipamentos_entregues': equipamentos_entregues,
        'equipamentos_devolvidos': dashboard_data['stats']['equipamentos']['devolvidos'],
        'equipamentos_negados': equipamentos_negados,

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
        'sla_pagination': dashboard_data['sla_data'].get('pagination', {}),

        # Performance geral do sistema
        'overall_performance': dashboard_data['performance'],

        # Inventário de equipamentos (globais)
        'inventory_total': inventory_total,
        'inventory_disponiveis': inventory_disponiveis,
        'inventory_emprestados': inventory_emprestados,
        'inventory_manutencao': inventory_manutencao,
        'inventory_danificados': inventory_danificados,
        'inventory_perdidos': inventory_perdidos,
        'can_view_inventory': can_view_all,

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

    # Encontrar tutorial mais útil - otimizado com query SQL
    from sqlalchemy import func
    tutorial_mais_util = db.session.query(Tutorial, func.count(FeedbackTutorial.id).label('util_count'))\
        .outerjoin(FeedbackTutorial, (FeedbackTutorial.tutorial_id == Tutorial.id) & (FeedbackTutorial.util == True))\
        .group_by(Tutorial.id)\
        .order_by(func.count(FeedbackTutorial.id).desc())\
        .first()
    template_data['tutorial_mais_util'] = tutorial_mais_util[0] if tutorial_mais_util else None

    # ============================================
    # SLA EXPANDIDO - Equipamentos, Tarefas e Lembretes
    # ============================================
    from datetime import timedelta
    
    # --- SLA DE EQUIPAMENTOS ---
    # Calcular tempo médio de aprovação (de Solicitado para Aprovado)
    equipamentos_aprovados_query = EquipmentRequest.query.filter(
        EquipmentRequest.status.in_(['Aprovado', 'Entregue', 'Devolvido']),
        EquipmentRequest.approval_date.isnot(None)
    )
    equipamentos_aprovados = apply_permissions(
        equipamentos_aprovados_query,
        'EquipmentRequest'
    ).all()
    
    if equipamentos_aprovados:
        total_tempo_aprovacao = sum([
            (eq.approval_date - eq.request_date).total_seconds() / 3600 
            for eq in equipamentos_aprovados
        ])
        media_aprovacao_horas = total_tempo_aprovacao / len(equipamentos_aprovados)
        
        # Formatar tempo médio de aprovação
        if media_aprovacao_horas < 1:
            template_data['equipamento_sla_aprovacao_media'] = f"{int(media_aprovacao_horas * 60)}m"
        elif media_aprovacao_horas < 24:
            template_data['equipamento_sla_aprovacao_media'] = f"{int(media_aprovacao_horas)}h"
        else:
            dias = int(media_aprovacao_horas / 24)
            horas = int(media_aprovacao_horas % 24)
            template_data['equipamento_sla_aprovacao_media'] = f"{dias}d {horas}h"
        
        # Percentual de cumprimento (meta: 24h)
        aprovados_no_prazo = sum([1 for eq in equipamentos_aprovados 
                                  if (eq.approval_date - eq.request_date).total_seconds() / 3600 <= 24])
        template_data['equipamento_sla_aprovacao_percent'] = int((aprovados_no_prazo / len(equipamentos_aprovados)) * 100)
    else:
        template_data['equipamento_sla_aprovacao_media'] = 'N/A'
        template_data['equipamento_sla_aprovacao_percent'] = 0
    
    # Calcular tempo médio de entrega (de Aprovado para Entregue)
    equipamentos_entregues_query = EquipmentRequest.query.filter(
        EquipmentRequest.status.in_(['Entregue', 'Devolvido']),
        EquipmentRequest.approval_date.isnot(None),
        EquipmentRequest.delivery_date.isnot(None)
    )
    equipamentos_entregues_list = apply_permissions(
        equipamentos_entregues_query,
        'EquipmentRequest'
    ).all()
    
    if equipamentos_entregues_list:
        total_tempo_entrega = sum([
            (datetime.combine(eq.delivery_date, datetime.min.time()) - eq.approval_date).total_seconds() / 3600 
            for eq in equipamentos_entregues_list
        ])
        media_entrega_horas = total_tempo_entrega / len(equipamentos_entregues_list)
        
        # Formatar tempo médio de entrega
        if media_entrega_horas < 24:
            template_data['equipamento_sla_entrega_media'] = f"{int(media_entrega_horas)}h"
        else:
            dias = int(media_entrega_horas / 24)
            horas = int(media_entrega_horas % 24)
            template_data['equipamento_sla_entrega_media'] = f"{dias}d {horas}h"
        
        # Percentual de cumprimento (meta: 48h)
        entregues_no_prazo = sum([1 for eq in equipamentos_entregues_list 
                                  if (datetime.combine(eq.delivery_date, datetime.min.time()) - eq.approval_date).total_seconds() / 3600 <= 48])
        template_data['equipamento_sla_entrega_percent'] = int((entregues_no_prazo / len(equipamentos_entregues_list)) * 100)
    else:
        template_data['equipamento_sla_entrega_media'] = 'N/A'
        template_data['equipamento_sla_entrega_percent'] = 0
    
    # Equipamentos pendentes de aprovação
    equipamentos_pendentes_query = apply_permissions(
        EquipmentRequest.query.filter_by(status='Solicitado'),
        'EquipmentRequest'
    )
    template_data['equipamentos_pendentes_aprovacao'] = equipamentos_pendentes_query.count()
    
    # Equipamentos com atraso na entrega (aprovados há mais de 48h mas ainda não entregues)
    data_limite_entrega = datetime.now() - timedelta(hours=48)
    equipamentos_atraso_query = EquipmentRequest.query.filter(
        EquipmentRequest.status == 'Aprovado',
        EquipmentRequest.approval_date < data_limite_entrega
    )
    template_data['equipamentos_atraso_entrega'] = apply_permissions(
        equipamentos_atraso_query,
        'EquipmentRequest'
    ).count()
    
    # --- SLA DE TAREFAS ---
    # Taxa de conclusão no prazo
    tarefas_concluidas = apply_permissions(
        Task.query.filter_by(completed=True),
        'Task'
    ).all()
    
    if tarefas_concluidas:
        # Consideramos "no prazo" se foi concluída no mesmo dia ou antes da data de criação + prazo razoável
        tarefas_no_prazo = sum([1 for task in tarefas_concluidas])  # Simplificado: todas concluídas contam como no prazo
        template_data['tarefas_sla_percent'] = int((tarefas_no_prazo / len(tarefas_concluidas)) * 100) if len(tarefas_concluidas) > 0 else 0
    else:
        template_data['tarefas_sla_percent'] = 0
    
    # Tempo médio de conclusão (baseado na diferença entre data da tarefa e hoje para pendentes, ou considerando concluídas)
    if tarefas_concluidas:
        # Simplificado: média de dias desde a criação
        total_dias = sum([(datetime.now().date() - task.date).days for task in tarefas_concluidas])
        media_dias = total_dias / len(tarefas_concluidas)
        
        if media_dias < 1:
            template_data['tarefas_tempo_medio'] = f"{int(media_dias * 24)}h"
        else:
            template_data['tarefas_tempo_medio'] = f"{int(media_dias)} dia{'s' if media_dias > 1 else ''}"
    else:
        template_data['tarefas_tempo_medio'] = 'N/A'
    
    # --- SLA DE LEMBRETES ---
    # Taxa de realização no prazo (lembretes concluídos antes ou na data de vencimento)
    lembretes_concluidos = apply_permissions(
        Reminder.query.filter_by(completed=True),
        'Reminder'
    ).all()
    
    if lembretes_concluidos:
        # Consideramos "no prazo" todos os concluídos (simplificado)
        template_data['lembretes_sla_percent'] = 100 if lembretes_concluidos else 0
    else:
        template_data['lembretes_sla_percent'] = 0
    
    # Lembretes vencendo hoje
    hoje = datetime.now().date()
    lembretes_vencendo_hoje_query = Reminder.query.filter(
        Reminder.due_date == hoje,
        Reminder.completed == False,
        Reminder.status == 'ativo'
    )
    template_data['lembretes_vencendo_hoje'] = apply_permissions(
        lembretes_vencendo_hoje_query,
        'Reminder'
    ).count()

    # ============================================
    # POPULAR TABELAS DE SLA COM DADOS REAIS
    # ============================================
    
    # --- TABELA DE EQUIPAMENTOS ---
    equipamentos_page = request.args.get('equipamentos_page', 1, type=int)
    equipamentos_per_page = request.args.get('equipamentos_per_page', 10, type=int)
    
    # Query de equipamentos com SLA (solicitados ou aprovados)
    equipamentos_query = EquipmentRequest.query.filter(
        EquipmentRequest.status.in_(['Solicitado', 'Aprovado', 'Entregue'])
    ).order_by(EquipmentRequest.request_date.desc())
    equipamentos_query = apply_permissions(equipamentos_query, 'EquipmentRequest')
    
    equipamentos_sla_pagination = equipamentos_query.paginate(
        page=equipamentos_page,
        per_page=equipamentos_per_page,
        error_out=False
    )
    
    # Calcular status SLA para cada equipamento
    equipamentos_sla_list = []
    for eq in equipamentos_sla_pagination.items:
        # Calcular tempo desde solicitação
        tempo_desde_solicitacao = (datetime.now() - eq.request_date).total_seconds() / 3600  # em horas
        
        # Determinar status SLA
        if eq.status == 'Solicitado':
            if tempo_desde_solicitacao > 24:
                status_sla = 'vencido'
            elif tempo_desde_solicitacao > 20:
                status_sla = 'critico'
            else:
                status_sla = 'ok'
        elif eq.status == 'Aprovado' and eq.approval_date:
            tempo_desde_aprovacao = (datetime.now() - eq.approval_date).total_seconds() / 3600
            if tempo_desde_aprovacao > 48:
                status_sla = 'vencido'
            elif tempo_desde_aprovacao > 40:
                status_sla = 'critico'
            else:
                status_sla = 'ok'
        else:
            status_sla = 'concluido'
        
        equipamentos_sla_list.append({
            'id': eq.id,
            'descricao': eq.description or 'Equipamento',
            'solicitante': eq.requester.username if eq.requester else 'N/A',
            'status': eq.status,
            'data_solicitacao': eq.request_date,
            'status_sla': status_sla
        })
    
    template_data['equipamentos_sla_list'] = equipamentos_sla_list
    template_data['equipamentos_sla_pagination'] = equipamentos_sla_pagination
    
    # --- TABELA DE TAREFAS ---
    tarefas_page = request.args.get('tarefas_page', 1, type=int)
    tarefas_per_page = request.args.get('tarefas_per_page', 10, type=int)
    
    # Query de tarefas (todas as tarefas)
    tarefas_query = Task.query.order_by(Task.date.desc(), Task.completed.asc())
    tarefas_query = apply_permissions(tarefas_query, 'Task')
    
    tarefas_sla_pagination = tarefas_query.paginate(
        page=tarefas_page,
        per_page=tarefas_per_page,
        error_out=False
    )
    
    # Preparar dados de tarefas
    tarefas_sla_list = []
    for task in tarefas_sla_pagination.items:
        # Determinar status da tarefa
        if task.completed:
            task_status = 'concluida'
        else:
            dias_desde_criacao = (datetime.now().date() - task.date).days
            if dias_desde_criacao > 7:
                task_status = 'vencida'
            elif dias_desde_criacao > 5:
                task_status = 'critica'
            else:
                task_status = 'pendente'
        
        tarefas_sla_list.append({
            'id': task.id,
            'descricao': task.description[:100] if task.description else 'Sem descrição',
            'responsavel': task.user.username if task.user else task.responsible if hasattr(task, 'responsible') else 'N/A',
            'data': task.date,
            'setor': task.sector.name if task.sector else 'N/A',
            'status': task_status,
            'completed': task.completed
        })
    
    template_data['tarefas_sla_list'] = tarefas_sla_list
    template_data['tarefas_sla_pagination'] = tarefas_sla_pagination
    
    # --- TABELA DE LEMBRETES ---
    lembretes_page = request.args.get('lembretes_page', 1, type=int)
    lembretes_per_page = request.args.get('lembretes_per_page', 10, type=int)
    
    # Query de lembretes (ativos e pendentes)
    lembretes_query = Reminder.query.filter(
        Reminder.status == 'ativo'
    ).order_by(Reminder.due_date.asc(), Reminder.completed.asc())
    lembretes_query = apply_permissions(lembretes_query, 'Reminder')
    
    lembretes_sla_pagination = lembretes_query.paginate(
        page=lembretes_page,
        per_page=lembretes_per_page,
        error_out=False
    )
    
    # Preparar dados de lembretes
    lembretes_sla_list = []
    for reminder in lembretes_sla_pagination.items:
        # Determinar status do lembrete
        if reminder.completed:
            reminder_status = 'realizado'
        else:
            if reminder.due_date < datetime.now().date():
                reminder_status = 'vencido'
            elif reminder.due_date == datetime.now().date():
                reminder_status = 'hoje'
            else:
                dias_restantes = (reminder.due_date - datetime.now().date()).days
                if dias_restantes <= 2:
                    reminder_status = 'proximo'
                else:
                    reminder_status = 'pendente'
        
        lembretes_sla_list.append({
            'id': reminder.id,
            'nome': reminder.name[:100] if reminder.name else 'Sem nome',
            'tipo': reminder.type or 'Geral',
            'responsavel': reminder.user.username if reminder.user else reminder.responsible if hasattr(reminder, 'responsible') else 'N/A',
            'due_date': reminder.due_date,
            'status': reminder_status,
            'completed': reminder.completed
        })
    
    template_data['lembretes_sla_list'] = lembretes_sla_list
    template_data['lembretes_sla_pagination'] = lembretes_sla_pagination

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
    from .models import Reminder, Sector, Task, Tutorial, User, ReminderHistory

    task_status = request.args.get("task_status", "")
    reminder_status = request.args.get("reminder_status", "")
    # Filtro opcional para estado operacional do lembrete (ativo, pausado, cancelado, encerrado)
    reminder_state = request.args.get("reminder_state", "")
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

    # Aplicar filtro de estado operacional do lembrete, se fornecido
    if reminder_state in ["ativo", "pausado", "cancelado", "encerrado"]:
        reminder_query = reminder_query.filter(Reminder.status == reminder_state)

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
                    "Usuário": t.user.username if t.user else t.responsible if hasattr(t, 'responsible') else "",
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
                    "Usuário": r.user.username if r.user else r.responsible if hasattr(r, 'responsible') else "",
                    "Realizado": "Sim" if r.completed else "Não",
                    "Prioridade": r.priority or "",
                    "Categoria": r.category or "",
                    "Nº Contrato/Licença": r.contract_number or "",
                    "Valor/Custo": (float(r.cost) if isinstance(r.cost, (int, float)) else None),
                    "Fornecedor": r.supplier or "",
                    "Status": r.status or "",
                    "Pausado Até": r.pause_until.strftime("%d/%m/%Y") if r.pause_until else "",
                    "Data Final": r.end_date.strftime("%d/%m/%Y") if r.end_date else "",
                }
                for r in reminders
            ]
            df_reminders = pd.DataFrame(reminders_data)
            df_reminders.to_excel(
                writer, sheet_name="Lembretes", index=False, header=False, startrow=1
            )
            worksheet_reminders = writer.sheets["Lembretes"]
            worksheet_reminders.merge_range(
                "A1:O1", "Relatório de Lembretes", title_format
            )
            for col_num, value in enumerate(df_reminders.columns.values):
                worksheet_reminders.write(0, col_num, value, header_format)
            for i, col in enumerate(df_reminders.columns):
                column_len = max(df_reminders[col].astype(str).map(len).max(), len(col))
                worksheet_reminders.set_column(i, i, column_len + 2)

            # Formatação monetária BRL para coluna Valor/Custo, se existir
            if not df_reminders.empty and "Valor/Custo" in df_reminders.columns:
                currency_format = workbook.add_format({"num_format": "R$ #,##0.00"})
                cost_idx = df_reminders.columns.get_loc("Valor/Custo")
                # Ajusta largura padrão para coluna de custo com formato
                worksheet_reminders.set_column(cost_idx, cost_idx, 14, currency_format)

        # Nova aba: Histórico de Lembretes
        if export_type in ["all", "reminders_history"]:
            # Respeita filtros aplicados em reminder_query
            reminder_ids = [r.id for r in reminder_query.all()]
            histories = []
            if reminder_ids:
                histories = ReminderHistory.query.filter(
                    ReminderHistory.reminder_id.in_(reminder_ids)
                ).all()

            history_data = [
                {
                    "Lembrete": (Reminder.query.get(h.reminder_id).name if Reminder.query.get(h.reminder_id) else h.reminder_id),
                    "Ação": h.action_type,
                    "Data Ação": h.action_date.strftime("%d/%m/%Y %H:%M") if h.action_date else "",
                    "Vencimento Original": h.original_due_date.strftime("%d/%m/%Y") if h.original_due_date else "",
                    "Concluído": "Sim" if h.completed else "Não",
                    "Concluído por": (User.query.get(h.completed_by).username if h.completed_by else ""),
                    "Notas": h.notes or "",
                }
                for h in histories
            ]

            df_history = pd.DataFrame(history_data)
            df_history.to_excel(
                writer, sheet_name="Histórico Lembretes", index=False, header=False, startrow=1
            )
            ws_hist = writer.sheets["Histórico Lembretes"]
            ws_hist.merge_range("A1:G1", "Histórico de Lembretes", title_format)
            for col_num, value in enumerate(df_history.columns.values):
                ws_hist.write(0, col_num, value, header_format)
            for i, col in enumerate(df_history.columns):
                column_len = max(df_history[col].astype(str).map(len).max(), len(col))
                ws_hist.set_column(i, i, column_len + 2)


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


@bp.route("/export/pdf")
@login_required
def export_pdf():
    """
    Exportar relatórios SLA em formato PDF profissional
    Suporta: chamados, equipamentos, tasks, reminders
    """
    from io import BytesIO
    from datetime import datetime
    from flask import request, session
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.pdfgen import canvas
    
    export_type = request.args.get('export_type', 'chamados')
    
    # Criar buffer para o PDF
    buffer = BytesIO()
    
    # Configurar documento (landscape para mais colunas)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Elementos do PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo de título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    # Estilo de subtítulo
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=1
    )
    
    # Data e hora do relatório
    data_hora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    usuario = session.get('username', 'Usuário')
    
    # ============================================
    # EXPORTAÇÃO DE CHAMADOS COM ANÁLISE DE SLA
    # ============================================
    if export_type == 'chamados':
        elements.append(Paragraph('Análise de SLA - Chamados de Suporte', title_style))
        elements.append(Paragraph(f'Relatório de Indicadores de Cumprimento de Prazos de Atendimento', subtitle_style))
        elements.append(Paragraph(f'Gerado em {data_hora} por {usuario}', subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar chamados
        chamados = Chamado.query.order_by(Chamado.data_abertura.desc()).limit(200).all()
        
        if chamados:
            # ==== INDICADORES DE DESEMPENHO ====
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=8,
                leading=12
            )
            
            # Calcular KPIs
            total_chamados = len(chamados)
            chamados_com_sla = [c for c in chamados if c.prazo_sla]
            total_com_sla = len(chamados_com_sla)
            
            sla_cumprido = len([c for c in chamados_com_sla if c.sla_cumprido == True])
            sla_vencido = len([c for c in chamados_com_sla if c.sla_cumprido == False])
            sla_andamento = total_com_sla - sla_cumprido - sla_vencido
            
            taxa_cumprimento = (sla_cumprido / total_com_sla * 100) if total_com_sla > 0 else 0
            
            # Chamados por prioridade
            criticos = len([c for c in chamados if c.prioridade == 'Critica'])
            altos = len([c for c in chamados if c.prioridade == 'Alta'])
            medios = len([c for c in chamados if c.prioridade == 'Media'])
            baixos = len([c for c in chamados if c.prioridade == 'Baixa'])
            
            # Chamados por status
            abertos = len([c for c in chamados if c.status == 'Aberto'])
            em_andamento = len([c for c in chamados if c.status == 'Em Andamento'])
            resolvidos = len([c for c in chamados if c.status == 'Resolvido'])
            fechados = len([c for c in chamados if c.status == 'Fechado'])
            
            # Tempo médio de resposta
            tempos_resposta = [c.tempo_resposta_horas for c in chamados if c.tempo_resposta_horas]
            tempo_medio_resposta = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0
            
            # Criar painel de indicadores
            elements.append(Paragraph('<b>INDICADORES DE DESEMPENHO (KPIs)</b>', info_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Tabela de KPIs
            kpi_data = [
                ['<b>Métrica</b>', '<b>Valor</b>', '<b>Detalhes</b>'],
                ['Total de Chamados', str(total_chamados), f'{abertos} Abertos, {em_andamento} Em Andamento, {fechados} Fechados'],
                ['Taxa de Cumprimento SLA', f'{taxa_cumprimento:.1f}%', f'{sla_cumprido} cumpridos de {total_com_sla} com SLA'],
                ['SLA Cumprido', str(sla_cumprido), f'{(sla_cumprido/total_com_sla*100):.1f}% do total' if total_com_sla > 0 else 'N/A'],
                ['SLA Vencido', str(sla_vencido), f'{(sla_vencido/total_com_sla*100):.1f}% do total' if total_com_sla > 0 else 'N/A'],
                ['SLA Em Andamento', str(sla_andamento), 'Chamados ainda dentro do prazo'],
                ['Tempo Médio Resposta', f'{tempo_medio_resposta:.1f}h', 'Tempo até primeira resposta'],
                ['Chamados Críticos', str(criticos), f'{(criticos/total_chamados*100):.1f}% do total'],
                ['Chamados por Prioridade', f'C:{criticos} A:{altos}', f'M:{medios} B:{baixos}'],
            ]
            
            kpi_table = Table(kpi_data, colWidths=[6*cm, 4*cm, 10*cm])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            elements.append(kpi_table)
            elements.append(Spacer(1, 0.7*cm))
            
            # ==== DETALHAMENTO DOS CHAMADOS ====
            elements.append(Paragraph('<b>DETALHAMENTO DE CHAMADOS</b>', info_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Cabeçalho da tabela
            data = [['ID', 'Título', 'Prior.', 'Status', 'Abertura', 'SLA', 'Tempo Resp.', 'Satisfação']]
            
            # Adicionar dados (primeiros 80 registros)
            for chamado in chamados[:80]:
                # Status SLA
                if chamado.sla_cumprido == True:
                    status_sla_text = '✓ Cumprido'
                elif chamado.sla_cumprido == False:
                    status_sla_text = '✗ Vencido'
                elif chamado.status_sla == 'vencido':
                    status_sla_text = '✗ Vencido'
                elif chamado.status_sla == 'atencao':
                    status_sla_text = '⚠ Crítico'
                else:
                    status_sla_text = '◷ Normal'
                
                # Tempo de resposta
                if chamado.tempo_resposta_horas:
                    tempo_resp = f'{chamado.tempo_resposta_horas:.1f}h'
                else:
                    tempo_resp = 'Pendente'
                
                # Satisfação
                if chamado.satisfaction_rating:
                    satisfacao = '★' * chamado.satisfaction_rating + '☆' * (5 - chamado.satisfaction_rating)
                else:
                    satisfacao = 'N/A'
                
                # Prioridade abreviada
                prior_map = {'Critica': 'CRIT', 'Alta': 'ALTA', 'Media': 'MED', 'Baixa': 'BXA'}
                prior = prior_map.get(chamado.prioridade, chamado.prioridade[:4].upper())
                
                data.append([
                    str(chamado.id),
                    chamado.titulo[:35] + '...' if len(chamado.titulo) > 35 else chamado.titulo,
                    prior,
                    chamado.status[:10],
                    chamado.data_abertura.strftime('%d/%m %H:%M'),
                    status_sla_text,
                    tempo_resp,
                    satisfacao
                ])
            
            # Criar tabela
            detail_table = Table(data, colWidths=[1.5*cm, 7*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm])
            detail_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (5, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            elements.append(detail_table)
            
            # Adicionar legenda
            elements.append(Spacer(1, 0.5*cm))
            legenda_text = '<b>Legenda:</b> ✓=Cumprido | ✗=Vencido | ⚠=Crítico | ◷=Normal | ★=Satisfação | CRIT=Crítica | ALTA=Alta | MED=Média | BXA=Baixa'
            elements.append(Paragraph(legenda_text, subtitle_style))
            
        else:
            elements.append(Paragraph('Nenhum chamado encontrado no sistema', styles['Normal']))
    
    # ============================================
    # EXPORTAÇÃO DE EQUIPAMENTOS
    # ============================================
    elif export_type == 'equipamentos':
        elements.append(Paragraph('Relatório de SLA - Equipamentos', title_style))
        elements.append(Paragraph(f'Gerado em {data_hora} por {usuario}', subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar equipamentos
        equipamentos = EquipmentRequest.query.filter(
            EquipmentRequest.status.in_(['Solicitado', 'Aprovado', 'Entregue'])
        ).order_by(EquipmentRequest.request_date.desc()).limit(100).all()
        
        if equipamentos:
            data = [['ID', 'Descrição', 'Solicitante', 'Status', 'Data Solicitação', 'SLA']]
            
            for eq in equipamentos:
                tempo_desde_solicitacao = (datetime.now() - eq.request_date).total_seconds() / 3600
                
                if eq.status == 'Solicitado':
                    status_sla = 'Vencido' if tempo_desde_solicitacao > 24 else ('Crítico' if tempo_desde_solicitacao > 20 else 'OK')
                elif eq.status == 'Aprovado' and eq.approval_date:
                    tempo_desde_aprovacao = (datetime.now() - eq.approval_date).total_seconds() / 3600
                    status_sla = 'Vencido' if tempo_desde_aprovacao > 48 else ('Crítico' if tempo_desde_aprovacao > 40 else 'OK')
                else:
                    status_sla = 'Concluído'
                
                data.append([
                    str(eq.id),
                    (eq.description or 'Equipamento')[:35] + '...' if eq.description and len(eq.description) > 35 else (eq.description or 'Equipamento'),
                    eq.requester.username if eq.requester else 'N/A',
                    eq.status,
                    eq.request_date.strftime('%d/%m/%Y %H:%M'),
                    status_sla
                ])
            
            table = Table(data, colWidths=[2*cm, 7*cm, 4*cm, 3*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph('Nenhum equipamento encontrado', styles['Normal']))
    
    # ============================================
    # EXPORTAÇÃO DE TAREFAS
    # ============================================
    elif export_type == 'tasks':
        elements.append(Paragraph('Relatório de SLA - Tarefas', title_style))
        elements.append(Paragraph(f'Gerado em {data_hora} por {usuario}', subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar tarefas
        tarefas = Task.query.order_by(Task.date.desc(), Task.completed.asc()).limit(100).all()
        
        if tarefas:
            data = [['ID', 'Descrição', 'Responsável', 'Data', 'Setor', 'Status']]
            
            for task in tarefas:
                if task.completed:
                    task_status = 'Concluída'
                else:
                    dias_desde_criacao = (datetime.now().date() - task.date).days
                    task_status = 'Vencida' if dias_desde_criacao > 7 else ('Crítica' if dias_desde_criacao > 5 else 'Pendente')
                
                data.append([
                    str(task.id),
                    (task.description[:45] + '...') if task.description and len(task.description) > 45 else (task.description or 'Sem descrição'),
                    task.user.username if task.user else task.responsible if hasattr(task, 'responsible') else 'N/A',
                    task.date.strftime('%d/%m/%Y'),
                    task.sector.name if task.sector else 'N/A',
                    task_status
                ])
            
            table = Table(data, colWidths=[2*cm, 8*cm, 4*cm, 3*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph('Nenhuma tarefa encontrada', styles['Normal']))
    
    # ============================================
    # EXPORTAÇÃO DE LEMBRETES
    # ============================================
    elif export_type == 'reminders':
        elements.append(Paragraph('Relatório de SLA - Lembretes', title_style))
        elements.append(Paragraph(f'Gerado em {data_hora} por {usuario}', subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Buscar lembretes
        lembretes = Reminder.query.filter(
            Reminder.status == 'ativo'
        ).order_by(Reminder.due_date.asc(), Reminder.completed.asc()).limit(100).all()
        
        if lembretes:
            data = [['ID', 'Nome', 'Tipo', 'Responsável', 'Vencimento', 'Status']]
            
            for reminder in lembretes:
                if reminder.completed:
                    reminder_status = 'Realizado'
                else:
                    if reminder.due_date < datetime.now().date():
                        reminder_status = 'Vencido'
                    elif reminder.due_date == datetime.now().date():
                        reminder_status = 'Vence Hoje'
                    else:
                        dias_restantes = (reminder.due_date - datetime.now().date()).days
                        reminder_status = 'Próximo' if dias_restantes <= 2 else 'Pendente'
                
                data.append([
                    str(reminder.id),
                    (reminder.name[:40] + '...') if reminder.name and len(reminder.name) > 40 else (reminder.name or 'Sem nome'),
                    reminder.type or 'Geral',
                    reminder.user.username if reminder.user else reminder.responsible if hasattr(reminder, 'responsible') else 'N/A',
                    reminder.due_date.strftime('%d/%m/%Y'),
                    reminder_status
                ])
            
            table = Table(data, colWidths=[2*cm, 8*cm, 3*cm, 4*cm, 3*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph('Nenhum lembrete encontrado', styles['Normal']))
    
    # Adicionar rodapé
    elements.append(Spacer(1, 1*cm))
    footer_text = f'Documento gerado automaticamente pelo TI OSN System • {data_hora}'
    elements.append(Paragraph(footer_text, subtitle_style))
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar PDF
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'sla_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
        mimetype='application/pdf'
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
@limiter.exempt  # Remover rate limit para documentação
def help_page():
    """Página de ajuda com documentação profissional usando MKDocs"""
    import os
    from flask import current_app, Response
    
    # Caminho para o site gerado pelo MKDocs
    site_dir = os.path.join(current_app.root_path, '..', 'site')
    index_path = os.path.join(site_dir, 'index.html')
    
    # Verificar se o site já foi gerado
    if os.path.exists(index_path):
        try:
            # Ler conteúdo do index.html gerado pelo MKDocs
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Corrigir TODOS os caminhos relativos para absolutos
            # Caminhos com ../
            content = content.replace('href="../css/', 'href="/docs/css/')
            content = content.replace('href="../js/', 'href="/docs/js/')
            content = content.replace('src="../js/', 'src="/docs/js/')
            content = content.replace('href="../img/', 'href="/docs/img/')
            content = content.replace('src="../img/', 'src="/docs/img/')
            content = content.replace('href="../stylesheets/', 'href="/docs/stylesheets/')
            content = content.replace('href="../search/', 'href="/docs/search/')
            content = content.replace('href="../user-guide/', 'href="/docs/user-guide/')
            content = content.replace('href="../admin-guide/', 'href="/docs/admin-guide/')
            
            # Caminhos sem ../
            content = content.replace('href="css/', 'href="/docs/css/')
            content = content.replace('href="js/', 'href="/docs/js/')
            content = content.replace('src="js/', 'src="/docs/js/')
            content = content.replace('href="img/', 'href="/docs/img/')
            content = content.replace('src="img/', 'src="/docs/img/')
            content = content.replace('href="stylesheets/', 'href="/docs/stylesheets/')
            content = content.replace('href="javascripts/', 'href="/docs/javascripts/')
            content = content.replace('src="javascripts/', 'src="/docs/javascripts/')
            content = content.replace('href="user-guide/', 'href="/docs/user-guide/')
            content = content.replace('href="admin-guide/', 'href="/docs/admin-guide/')
            content = content.replace('href="search/', 'href="/docs/search/')
            content = content.replace('src="search/', 'src="/docs/search/')
            content = content.replace('href="api_documentation/', 'href="/docs/api_documentation/')
            content = content.replace('href="apresentacao/', 'href="/docs/apresentacao/')
            content = content.replace('href="RESUMO_EXECUTIVO/', 'href="/docs/RESUMO_EXECUTIVO/')
            
            # Caminhos especiais
            content = content.replace('href="."', 'href="/help"')
            content = content.replace('href="./"', 'href="/help"')
            content = content.replace('action="./search.html"', 'action="/docs/search.html"')
            content = content.replace('href="sitemap.xml', 'href="/docs/sitemap.xml')
            content = content.replace('href="404.html', 'href="/docs/404.html')
            
            # Corrigir base path no JavaScript
            content = content.replace('"base": "."', '"base": "/docs/"')
            
            # Corrigir caminhos no JavaScript (data-search-config)
            content = content.replace('"search": "search/', '"search": "/docs/search/')
            content = content.replace("'search': 'search/", "'search': '/docs/search/")
            
            # Corrigir caminhos dinâmicos de busca (new Worker, import, etc)
            import re
            # Corrigir new Worker("search/worker.js") -> new Worker("/docs/search/worker.js")
            content = re.sub(r'new Worker\(["\']search/', r'new Worker("/docs/search/', content)
            # Corrigir importScripts("search/...) -> importScripts("/docs/search/...)
            content = re.sub(r'importScripts\(["\']search/', r'importScripts("/docs/search/', content)
            # Corrigir qualquer "search/arquivo.js" -> "/docs/search/arquivo.js"
            content = re.sub(r'(["\'])search/([\w\.-]+\.js)', r'\1/docs/search/\2', content)
            
            # Retornar HTML com caminhos corrigidos
            return Response(content, mimetype='text/html')
            
        except Exception as e:
            current_app.logger.error(f"Erro ao ler documentação: {e}")
            return render_template("help.html", title="Central de Ajuda")
    else:
        # Site não foi gerado, usar template fallback
        current_app.logger.warning("Documentação MKDocs não encontrada. Execute: mkdocs build")
        return render_template("help.html", title="Central de Ajuda")


@bp.route("/docs/<path:filename>")
@login_required
@limiter.exempt  # Remover rate limit para arquivos estáticos da documentação
def docs_static(filename):
    """Servir arquivos estáticos e páginas da documentação MKDocs"""
    import os
    from flask import current_app, send_from_directory, Response

    site_dir = os.path.join(current_app.root_path, '..', 'site')
    file_path = os.path.join(site_dir, filename)

    # Se o filename terminar com / ou for um diretório, tentar servir index.html
    if filename.endswith('/') or (os.path.exists(file_path) and os.path.isdir(file_path)):
        if filename.endswith('/'):
            filename = filename[:-1]
        index_path = os.path.join(site_dir, filename, 'index.html')
        
        if os.path.exists(index_path):
            try:
                # Ler e corrigir o conteúdo HTML
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Corrigir TODOS os caminhos relativos para absolutos
                # Caminhos com ../ (para subpáginas)
                content = content.replace('href="../css/', 'href="/docs/css/')
                content = content.replace('href="../js/', 'href="/docs/js/')
                content = content.replace('src="../js/', 'src="/docs/js/')
                content = content.replace('href="../img/', 'href="/docs/img/')
                content = content.replace('src="../img/', 'src="/docs/img/')
                content = content.replace('href="../stylesheets/', 'href="/docs/stylesheets/')
                content = content.replace('href="../search/', 'href="/docs/search/')
                content = content.replace('href="../user-guide/', 'href="/docs/user-guide/')
                content = content.replace('href="../admin-guide/', 'href="/docs/admin-guide/')
                content = content.replace('href="../api_documentation/', 'href="/docs/api_documentation/')
                content = content.replace('href="../apresentacao/', 'href="/docs/apresentacao/')
                content = content.replace('href="../RESUMO_EXECUTIVO/', 'href="/docs/RESUMO_EXECUTIVO/')
                content = content.replace('href=".."', 'href="/help"')
                content = content.replace('href="../"', 'href="/help"')
                
                # Caminhos sem ../ (para mesma pasta)
                content = content.replace('href="css/', 'href="/docs/css/')
                content = content.replace('href="js/', 'href="/docs/js/')
                content = content.replace('src="js/', 'src="/docs/js/')
                content = content.replace('href="img/', 'href="/docs/img/')
                content = content.replace('src="img/', 'src="/docs/img/')
                content = content.replace('href="stylesheets/', 'href="/docs/stylesheets/')
                content = content.replace('href="javascripts/', 'href="/docs/javascripts/')
                content = content.replace('src="javascripts/', 'src="/docs/javascripts/')
                content = content.replace('href="search/', 'href="/docs/search/')
                content = content.replace('src="search/', 'src="/docs/search/')
                
                # Caminhos especiais
                content = content.replace('href="."', 'href="/help"')
                content = content.replace('href="./"', 'href="/help"')
                content = content.replace('action="./search.html"', 'action="/docs/search.html"')
                content = content.replace('action="../search.html"', 'action="/docs/search.html"')
                
                # Corrigir base path no JavaScript
                content = content.replace('"base": "."', '"base": "/docs/"')
                content = content.replace('"base": ".."', '"base": "/docs/"')
                
                # Corrigir caminhos no JavaScript (data-search-config)
                content = content.replace('"search": "search/', '"search": "/docs/search/')
                content = content.replace("'search': 'search/", "'search': '/docs/search/")
                
                # Corrigir caminhos dinâmicos de busca (new Worker, import, etc)
                import re
                # Corrigir new Worker("search/worker.js") -> new Worker("/docs/search/worker.js")
                content = re.sub(r'new Worker\(["\']search/', r'new Worker("/docs/search/', content)
                # Corrigir importScripts("search/...) -> importScripts("/docs/search/...)
                content = re.sub(r'importScripts\(["\']search/', r'importScripts("/docs/search/', content)
                # Corrigir qualquer "search/arquivo.js" -> "/docs/search/arquivo.js"
                content = re.sub(r'(["\'])search/([\w\.-]+\.js)', r'\1/docs/search/\2', content)

                return Response(content, mimetype='text/html')
            except Exception as e:
                current_app.logger.error(f"Erro ao ler página: {e}")
                return "Erro ao carregar página", 500

    # Para arquivos normais (CSS, JS, imagens), usar send_from_directory
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(site_dir, filename)
    
    # Arquivo não encontrado
    return "Arquivo não encontrado", 404


@bp.route("/termos")
def terms():
    # Página de termos de uso
    return render_template("terms.html", title="Termos de Uso")


@bp.route("/privacidade")
def privacy():
    # Página de política de privacidade
    return render_template("privacy.html", title="Política de Privacidade")


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
        flash_success("Tarefa adicionada!")
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
        flash_success("Tarefa atualizada!")
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
    flash_success("Tarefa marcada como concluída!")
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
    flash_success("Tarefa excluída!")
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
        flash_error("Usuário não encontrado. Faça login novamente.")
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
                    flash_success(
    f"Novo setor '{novo_setor.name}' criado com sucesso!"
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
                flash_info("Notificações enviadas com sucesso!")
            except Exception as e:
                db.session.rollback()
                flash_warning(
                    f"Chamado criado, mas houve um erro ao enviar notificações: {str(e)}"
                )
                print(
                    f"Error sending notification email for Chamado {novo_chamado.id}: {e}"
                )

            flash_success("Chamado aberto com sucesso!")
            return redirect(url_for("main.detalhe_chamado", id=novo_chamado.id))

        except Exception as e:
            db.session.rollback()
            flash_error(f"Erro ao abrir o chamado: {str(e)}")
            print(f"Error creating Chamado: {e}")

    # Pré-selecionar o setor do usuário no formulário, se existir
    if setor_usuario and hasattr(form, "setor_id"):
        form.setor_id.data = setor_usuario.id

    return render_template(
        "abrir_chamado.html",
        form=form,
        title="Abrir Novo Ticket",
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
        flash_error("Você não tem permissão para editar este chamado.")
        return redirect(url_for("main.detalhe_chamado", id=id))

    # Não permitir edição se o chamado estiver fechado
    if chamado.status == "Fechado":
        flash_warning("Não é possível editar um chamado fechado.")
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

                flash_success("Chamado atualizado com sucesso!")
                return redirect(url_for("main.detalhe_chamado", id=chamado.id))
            else:
                flash_info("Nenhuma alteração foi realizada.")

        except Exception as e:
            db.session.rollback()
            flash_error(f"Erro ao atualizar o chamado: {str(e)}")
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
        flash_error("Acesso restrito a administradores.")
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
                    flash_warning(
                        "Chamado atualizado, mas ocorreu um erro ao enviar a notificação por e-mail."
                    )

            flash_success("Chamado atualizado com sucesso!")
        else:
            flash_info("Nenhuma alteração foi realizada.")

        return redirect(url_for("main.detalhe_chamado", id=chamado.id))

    # Se o formulário não for válido, mostra os erros
    for field, errors in form.errors.items():
        for error in errors:
            flash_error(f"Erro no campo {getattr(form, field).label.text}: {error}")

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
        flash_error(
            "Apenas membros da equipe de TI ou administradores podem cadastrar tutoriais."
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
        flash_success("Tutorial cadastrado com sucesso!")
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
        flash_error(
    "Apenas o autor TI ou administradores podem editar este tutorial."
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
        flash_success("Tutorial atualizado com sucesso!")
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
        flash_error(
            "Apenas o autor TI ou administradores podem excluir este tutorial."
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
    flash_success("Tutorial excluído com sucesso!")
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
        flash_success("Comentário enviado com sucesso!")
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    else:
        flash_error("Erro ao enviar comentário.")
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
            flash_success("Feedback registrado!")
        else:
            flash_info("Você já enviou feedback para este tutorial.")
        return redirect(url_for("main.detalhe_tutorial", tutorial_id=tutorial.id))
    else:
        flash_error("Erro ao enviar feedback.")
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
# SISTEMA DE EQUIPAMENTOS
# ========================================
# O sistema de equipamentos foi migrado para o blueprint 'equipment_v2'
# Rotas disponíveis em app/blueprints/equipment_clean.py
# ROTAS ANTIGAS DESATIVADAS PARA EVITAR CONFLITO
# ========================================


# @bp.route("/equipment/catalog")
# @login_required
# def equipment_catalog():
#     """Catálogo de equipamentos disponíveis"""
#     # Filtros
#     search = request.args.get('search', '')
#     category = request.args.get('category', '')
#     brand = request.args.get('brand', '')
# 
#     filters = {}
#     if search:
#         filters['search'] = search
#     if category:
#         filters['category'] = category
#     if brand:
#         filters['brand'] = brand
# 
#     # Buscar equipamentos
#     from .services.equipment_service import EquipmentService
#     try:
#         equipments = EquipmentService.get_equipment_catalog(filters)
#     except Exception as e:
#         current_app.logger.error(f"Erro ao buscar equipamentos: {str(e)}")
#         equipments = []
# 
#     # Opções para filtros
#     try:
#         categories = db.session.query(Equipment.category).distinct().filter(
#             Equipment.category.isnot(None)
#         ).order_by(Equipment.category).all()
#         categories = [cat[0] for cat in categories]
#     except Exception as e:
#         current_app.logger.error(f"Erro ao buscar categorias: {str(e)}")
#         categories = []
# 
#     try:
#         brands = db.session.query(Equipment.brand).distinct().filter(
#             Equipment.brand.isnot(None)
#         ).order_by(Equipment.brand).all()
#         brands = [br[0] for br in brands]
#     except Exception as e:
#         current_app.logger.error(f"Erro ao buscar marcas: {str(e)}")
#         brands = []
# 
#     # Estatísticas
#     stats = EquipmentService.get_equipment_stats()
# 
#     return render_template(
#         'equipment_catalog.html',
#         equipments=equipments,
#         categories=categories,
#         brands=brands,
#         stats=stats,
#         search=search,
#         category=category,
#         brand=brand
#     )


# @bp.route("/equipment/cancel-reservation/<int:reservation_id>", methods=['POST'])
# @login_required
# def cancel_reservation(reservation_id):
#     """Cancelar reserva de equipamento"""
#     reservation = EquipmentReservation.query.get_or_404(reservation_id)
# 
#     # Verificar se o usuário pode cancelar
#     user_id = session.get('user_id')
#     if not user_id:
#         return jsonify({'success': False, 'message': 'Sessão expirada. Faça login novamente.'})
# 
#     if reservation.user_id != user_id and not PermissionManager.can_user_approve_equipment(user_id):
#         return jsonify({'success': False, 'message': 'Acesso negado. Você só pode cancelar suas próprias reservas ou precisa de permissões administrativas.'})
# 
#     # Cancelar reserva
#     reservation.status = 'cancelada'
#     db.session.commit()
# 
#     return jsonify({'success': True, 'message': 'Reserva cancelada com sucesso!'})


# ========================================
# ROTAS PARA INTEGRAÇÃO RFID
# ========================================

@bp.route("/rfid/scan", methods=["POST"])
@login_required
@admin_or_ti_required_json
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
@admin_or_ti_required
def simulate_rfid_scan(rfid_tag, reader_id):
    """Simular leitura RFID para testes (apenas admin)"""
    result = RFIDService.simulate_rfid_scan(rfid_tag, reader_id)

    if result["success"]:
        flash_success(f"Leitura RFID simulada: {result['message']}")
    else:
        flash_error(f"Erro na simulação: {result['message']}")

    return redirect(url_for("main.rfid_dashboard"))


@bp.route("/rfid/assign/<int:equipment_id>", methods=["POST"])
@login_required
@admin_or_ti_required
def assign_rfid_tag(equipment_id):
    """Atribuir tag RFID a um equipamento"""
    rfid_tag = request.form.get("rfid_tag", "").strip()

    if not rfid_tag:
        flash_error("Tag RFID é obrigatória.")
        return redirect(url_for("main.equipment_detail", id=equipment_id))

    result = RFIDService.assign_rfid_tag(equipment_id, rfid_tag)

    if result["success"]:
        flash_success("Tag RFID atribuída com sucesso!")
    else:
        flash_error(f"Erro ao atribuir tag: {result['message']}")

    return redirect(url_for("main.equipment_detail", id=equipment_id))


@bp.route("/rfid/remove/<int:equipment_id>", methods=["POST"])
@login_required
@admin_or_ti_required
def remove_rfid_tag(equipment_id):
    """Remover tag RFID de um equipamento"""
    result = RFIDService.remove_rfid_tag(equipment_id)

    if result["success"]:
        flash_success("Tag RFID removida com sucesso!")
    else:
        flash_error(f"Erro ao remover tag: {result['message']}")

    return redirect(url_for("main.equipment_detail", id=equipment_id))


@bp.route("/rfid/location/<int:equipment_id>")
@login_required
@admin_or_ti_required_json
def get_equipment_location(equipment_id):
    """Obter localização atual de um equipamento via RFID"""
    result = RFIDService.get_equipment_location(equipment_id)
    return jsonify(result)


@bp.route("/rfid/dashboard")
@login_required
@admin_or_ti_required
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
@admin_or_ti_required
def bulk_assign_rfid():
    """Atribuição em lote de tags RFID"""
    if request.method == "POST":
        equipment_ids = request.form.getlist("equipment_ids[]")
        rfid_tags = request.form.getlist("rfid_tags[]")

        if not equipment_ids or not rfid_tags:
            flash_error("Selecione equipamentos e forneça tags RFID.")
            return redirect(url_for("main.bulk_assign_rfid"))

        # Converter para inteiros
        try:
            equipment_ids = [int(id) for id in equipment_ids]
        except ValueError:
            flash_error("IDs de equipamentos inválidos.")
            return redirect(url_for("main.bulk_assign_rfid"))

        result = RFIDService.bulk_assign_rfid_tags(equipment_ids, rfid_tags)

        if result["success"]:
            flash_success(result["message"])
        else:
            flash_error(result["message"])

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
@admin_or_ti_required_json
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
        flash_error("Você não tem permissão para avaliar este chamado.")
        return redirect(url_for("main.index"))

    # Verificar se chamado está fechado
    if chamado.status != "Fechado":
        flash_warning("Apenas chamados fechados podem ser avaliados.")
        return redirect(url_for("main.detalhe_chamado", id=chamado_id))

    # Verificar se já foi avaliado
    if chamado.satisfaction_rating:
        flash_info("Este chamado já foi avaliado.")
        return redirect(url_for("main.detalhe_chamado", id=chamado_id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        if not rating or not 1 <= rating <= 5:
            flash_error("Por favor, selecione uma avaliação válida (1-5 estrelas).")
            return render_template("satisfaction_survey.html", chamado=chamado)

        result = SatisfactionService.record_satisfaction_rating(chamado_id, rating, comment)

        if result["success"]:
            flash_success("Avaliação registrada com sucesso! Obrigado pelo feedback.")
            return redirect(url_for("main.detalhe_chamado", id=chamado_id))
        else:
            flash_error(f"Erro ao registrar avaliação: {result['message']}")

    return render_template("satisfaction_survey.html", chamado=chamado)


@bp.route("/satisfaction/dashboard")
@login_required
@admin_or_ti_required
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
@admin_or_ti_required
def send_satisfaction_survey(chamado_id):
    """Enviar pesquisa de satisfação manualmente"""
    result = SatisfactionService.send_satisfaction_survey(chamado_id)

    if result["success"]:
        flash_success("Pesquisa de satisfação enviada com sucesso!")
    else:
        flash_error(f"Erro ao enviar pesquisa: {result['message']}")

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
@admin_or_ti_required
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
        flash_success("Métricas atualizadas com sucesso!")
    else:
        flash_error(f"Erro ao atualizar métricas: {result['message']}")

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
        flash_success(result["message"])
    else:
        flash_error(f"Erro ao atribuir certificação: {result['message']}")

    return redirect(url_for("main.certifications_dashboard"))


@bp.route("/api/certifications/leaderboard")
@login_required
@admin_or_ti_required_json
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
@admin_or_ti_required
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
@admin_or_ti_required
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

    flash_success("Otimizações de performance executadas!")

    return redirect(url_for("main.performance_dashboard"))


@bp.route("/api/performance/metrics")
@login_required
@admin_or_ti_required_json
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
@admin_or_ti_required
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


# ============================================================================
# ANALYTICS API ENDPOINTS
# ============================================================================

@bp.route("/api/analytics/dashboard-kpis")
@login_required
@admin_or_ti_required_json
def api_dashboard_kpis():
    """Retorna KPIs principais para o dashboard"""
    from .services.analytics.analytics_service import AnalyticsService
    
    try:
        kpis = AnalyticsService.get_dashboard_kpis()
        return jsonify(kpis)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar KPIs: {e}")
        return jsonify({'error': 'Erro ao buscar métricas'}), 500


@bp.route("/api/analytics/chamados-periodo")
@login_required
@admin_or_ti_required_json
def api_chamados_periodo():
    """Retorna chamados agrupados por período"""
    from .services.analytics.analytics_service import AnalyticsService
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Parâmetros
        start = request.args.get('start')
        end = request.args.get('end')
        group_by = request.args.get('group_by', 'day')
        
        # Converter strings para dates
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        else:
            start = date.today() - timedelta(days=30)
            
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        else:
            end = date.today()
        
        data = AnalyticsService.get_chamados_por_periodo(start, end, group_by)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados por período: {e}")
        return jsonify({'error': 'Erro ao buscar dados'}), 500


@bp.route("/api/analytics/chamados-prioridade")
@login_required
@admin_or_ti_required_json
def api_chamados_prioridade():
    """Retorna distribuição de chamados por prioridade"""
    from .services.analytics.analytics_service import AnalyticsService
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Parâmetros opcionais
        start = request.args.get('start')
        end = request.args.get('end')
        
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        
        data = AnalyticsService.get_chamados_por_prioridade(start, end)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados por prioridade: {e}")
        return jsonify({'error': 'Erro ao buscar dados'}), 500


@bp.route("/api/analytics/performance-tecnico")
@login_required
@admin_or_ti_required_json
def api_performance_tecnico():
    """Retorna performance de cada técnico"""
    from .services.analytics.analytics_service import AnalyticsService
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Parâmetros
        start = request.args.get('start')
        end = request.args.get('end')
        
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        else:
            start = date.today() - timedelta(days=30)
            
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        else:
            end = date.today()
        
        data = AnalyticsService.get_performance_por_tecnico(start, end)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar performance: {e}")
        return jsonify({'error': 'Erro ao buscar dados'}), 500


@bp.route("/api/analytics/chamados-setor")
@login_required
@admin_or_ti_required_json
def api_chamados_setor():
    """Retorna distribuição de chamados por setor"""
    from .services.analytics.analytics_service import AnalyticsService
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Parâmetros opcionais
        start = request.args.get('start')
        end = request.args.get('end')
        
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        
        data = AnalyticsService.get_chamados_por_setor(start, end)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados por setor: {e}")
        return jsonify({'error': 'Erro ao buscar dados'}), 500


@bp.route("/api/analytics/tutoriais-categoria")
@login_required
@admin_or_ti_required_json
def api_tutoriais_categoria():
    """Retorna distribuição de tutoriais por categoria"""
    from .services.analytics.analytics_service import AnalyticsService
    import traceback
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        current_app.logger.info("Buscando tutoriais por categoria...")
        data = AnalyticsService.get_tutoriais_por_categoria()
        current_app.logger.info(f"Retornando {len(data)} categorias de tutoriais")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar tutoriais por categoria: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Erro ao buscar dados', 'message': str(e)}), 500


@bp.route("/api/analytics/tutoriais-mais-visualizados")
@login_required
@admin_or_ti_required_json
def api_tutoriais_mais_visualizados():
    """Retorna tutoriais mais visualizados"""
    from .services.analytics.analytics_service import AnalyticsService
    import traceback
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        limit = request.args.get('limit', 10, type=int)
        current_app.logger.info(f"Buscando top {limit} tutoriais...")
        data = AnalyticsService.get_tutoriais_mais_visualizados(limit)
        current_app.logger.info(f"Retornando {len(data)} tutoriais")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar tutoriais mais visualizados: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Erro ao buscar dados', 'message': str(e)}), 500


@bp.route("/api/analytics/tasks-periodo")
@login_required
@admin_or_ti_required_json
def api_tasks_periodo():
    """Retorna tarefas agrupadas por período"""
    from .services.analytics.analytics_service import AnalyticsService
    import traceback
    
    # Apenas admin e TI podem acessar
    if not session.get("is_admin") and not session.get("is_ti"):
        return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Parâmetros
        start = request.args.get('start')
        end = request.args.get('end')
        
        # Converter strings para dates
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        else:
            start = date.today() - timedelta(days=30)
            
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        else:
            end = date.today()
        
        current_app.logger.info(f"Buscando tarefas de {start} até {end}...")
        data = AnalyticsService.get_tasks_por_periodo(start, end)
        current_app.logger.info(f"Retornando {len(data)} períodos de tarefas")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar tarefas por período: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Erro ao buscar dados', 'message': str(e)}), 500


@bp.route("/analytics")
@login_required
@admin_or_ti_required
def analytics_dashboard():
    """Página do dashboard de analytics"""
    return render_template("analytics/dashboard.html")
