from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from .utils.timezone_utils import get_current_time_for_db, now_local, format_local_datetime, utc_to_local
from .models import Reminder, Task, Sector, User, db, Tutorial, TutorialImage, VisualizacaoTutorial, FeedbackTutorial, EquipmentRequest, Chamado, ComentarioChamado, ComentarioTutorial # Importados modelos necessários
from .forms import ReminderForm, TaskForm, TutorialForm, ComentarioTutorialForm, FeedbackTutorialForm, ChamadoForm, ChamadoAdminForm, UserEditForm # Importados formulários necessários
from .auth_utils import login_required
from functools import wraps
from flask import current_app
import os
from werkzeug.utils import secure_filename
import markdown

# Função para exigir que o usuário seja administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Acesso restrito ao administrador.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    # Importação local para evitar dependência circular se outros módulos importarem main.py diretamente
    from .models import Chamado, EquipmentRequest

    search = request.args.get('search', '').strip().lower()
    status = request.args.get('status', '').strip().lower()

    # --- Recorrência automática de lembretes ---
    if session.get('is_admin'):
        reminders = Reminder.query.all()
    else:
        reminders = Reminder.query.filter_by(user_id=session.get('user_id')).all()

    # Recorrência automática
    for r in reminders:
        if (r.due_date < date.today() and 
            not r.notified and 
            r.frequency and 
            r.status == 'ativo' and
            (not r.end_date or r.end_date > date.today()) and
            (not r.pause_until or r.pause_until <= date.today())):
            if r.frequency == 'diario':
                next_due = r.due_date + relativedelta(days=1)
            elif r.frequency == 'quinzenal':
                next_due = r.due_date + relativedelta(days=15)
            elif r.frequency == 'mensal':
                next_due = r.due_date + relativedelta(months=1)
            elif r.frequency == 'anual':
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
                end_date=r.end_date
            )
            db.session.add(novo)
            r.notified = True  # marca o lembrete antigo para não duplicar
            db.session.commit()

    # Consulta de lembretes e tarefas
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    is_ti = session.get('is_ti', False)
    
    if is_admin:
        reminders_count = Reminder.query.count()
        reminders_today = Reminder.query.filter(Reminder.due_date <= date.today()).all()
        tasks_today = Task.query.filter(Task.date <= date.today()).all()
        # Buscar chamados abertos (não fechados)
        chamados_abertos = Chamado.query.filter(
            Chamado.status != 'Fechado'
        ).order_by(
            Chamado.data_abertura.desc()
        ).limit(10).all()  # Limita a 10 chamados mais recentes
        # Buscar equipamentos
        equipamentos_count = EquipmentRequest.query.count()
    else:
        reminders_count = Reminder.query.filter_by(user_id=user_id).count()
        reminders_today = Reminder.query.filter(
            Reminder.due_date <= date.today(),
            Reminder.user_id == user_id
        ).all()
        tasks_today = Task.query.filter(
            Task.date <= date.today(),
            Task.user_id == user_id
        ).all()
        # Buscar chamados do usuário ou do setor do usuário
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None

        chamados_abertos = Chamado.query.filter(
            (Chamado.solicitante_id == user_id) |
            (Chamado.setor_id == setor_id_usuario),
            Chamado.status != 'Fechado'
        ).order_by(
            Chamado.data_abertura.desc()
        ).limit(10).all()  # Limita a 10 chamados mais recentes
        
        # Buscar equipamentos do usuário
        if is_ti:
            equipamentos_count = EquipmentRequest.query.count()
        else:
            equipamentos_count = EquipmentRequest.query.filter_by(requester_id=user_id).count()

    # --- FILTRO E BUSCA LEMBRETES ---
    reminders_today_pend = [r for r in reminders_today if not r.completed]
    reminders_today_done = [r for r in reminders_today if r.completed]
    if search:
        reminders_today_pend = [r for r in reminders_today_pend if search in r.name.lower() or search in r.responsible.lower()]
        reminders_today_done = [r for r in reminders_today_done if search in r.name.lower() or search in r.responsible.lower()]
    if status == 'pendente':
        reminders_today_done = []
    elif status == 'realizado':
        reminders_today_pend = []

    # --- FILTRO E BUSCA TAREFAS ---
    tasks_today_pend = [t for t in tasks_today if not t.completed]
    tasks_today_done = [t for t in tasks_today if t.completed]
    if search:
        tasks_today_pend = [t for t in tasks_today_pend if search in t.description.lower() or search in t.responsible.lower()]
        tasks_today_done = [t for t in tasks_today_done if search in t.description.lower() or search in t.responsible.lower()]
    if status == 'pendente':
        tasks_today_done = []
    elif status == 'realizado':
        tasks_today_pend = []
        
    # --- ATIVIDADES RECENTES ---
    # Combinar atividades recentes de diferentes fontes
    atividades_recentes = []
    
    # Adicionar lembretes recentes
    for r in reminders_today[:5]:  # Limitar a 5 lembretes mais recentes
        atividades_recentes.append({
            'tipo': 'lembrete',
            'data': r.due_date,
            'titulo': r.name,
            'status': 'Realizado' if r.completed else 'Pendente',
            'icone': 'bell',
            'cor': 'success' if r.completed else 'warning'
        })
    
    # Adicionar tarefas recentes
    for t in tasks_today[:5]:  # Limitar a 5 tarefas mais recentes
        atividades_recentes.append({
            'tipo': 'tarefa',
            'data': t.date,
            'titulo': t.description,
            'status': 'Concluída' if t.completed else 'Pendente',
            'icone': 'tasks',
            'cor': 'success' if t.completed else 'primary'
        })
    
    # Adicionar chamados recentes
    for c in chamados_abertos[:5]:  # Limitar a 5 chamados mais recentes
        atividades_recentes.append({
            'tipo': 'chamado',
            'data': c.data_abertura,
            'titulo': c.titulo,
            'status': c.status,
            'icone': 'ticket-alt',
            'cor': 'info' if c.status == 'Em Andamento' else 'warning'
        })
    
    # Ordenar atividades por data (mais recentes primeiro)
    # Converter todas as datas para datetime para evitar erro de comparação entre date e datetime
    for atividade in atividades_recentes:
        if isinstance(atividade['data'], date) and not isinstance(atividade['data'], datetime):
            # Converter date para datetime
            atividade['data'] = datetime.combine(atividade['data'], time.min)
    
    atividades_recentes.sort(key=lambda x: x['data'], reverse=True)
    
    # Limitar a 10 atividades no total
    atividades_recentes = atividades_recentes[:10]
    
    # Calcular estatísticas de SLA (apenas para administradores)
    sla_vencidos = 0
    sla_criticos = 0
    sla_ok = 0
    performance_sla = 0
    
    if is_admin:
        # Buscar todos os chamados abertos (não fechados)
        chamados_abertos_sla = Chamado.query.filter(
            Chamado.status != 'Fechado'
        ).all()
        
        # Calcular SLA para chamados que não têm prazo definido
        for chamado in chamados_abertos_sla:
            if not chamado.prazo_sla:
                chamado.calcular_sla()
        
        # Commit das mudanças no SLA
        db.session.commit()
        
        # Agora contar os status de SLA
        for chamado in chamados_abertos_sla:
            status_sla = chamado.status_sla
            if status_sla == 'vencido':
                sla_vencidos += 1
            elif status_sla == 'atencao':
                sla_criticos += 1
            elif status_sla == 'normal':
                sla_ok += 1
        
        # Calcular performance de SLA dos últimos 30 dias
        from datetime import timedelta
        trinta_dias_atras = get_current_time_for_db() - timedelta(days=30)
        
        chamados_fechados_30_dias = Chamado.query.filter(
            Chamado.data_fechamento >= trinta_dias_atras,
            Chamado.data_fechamento.isnot(None)
        ).all()
        
        if chamados_fechados_30_dias:
            # Calcular SLA para chamados fechados que não têm sla_cumprido definido
            for chamado in chamados_fechados_30_dias:
                if chamado.sla_cumprido is None and chamado.prazo_sla:
                    # Se foi fechado dentro do prazo, considera cumprido
                    chamado.sla_cumprido = chamado.data_fechamento <= chamado.prazo_sla
            
            db.session.commit()
            
            sla_cumpridos = len([c for c in chamados_fechados_30_dias if c.sla_cumprido])
            performance_sla = round((sla_cumpridos / len(chamados_fechados_30_dias)) * 100)

    return render_template(
        'index.html',
        lembretes_count=reminders_count,
        tarefas_count=len(tasks_today_pend),
        chamados_count=len(chamados_abertos),
        equipamentos_count=equipamentos_count,
        reminders_today_pend=reminders_today_pend,
        reminders_today_done=reminders_today_done,
        tasks_today_pend=tasks_today_pend,
        tasks_today_done=tasks_today_done,
        chamados_abertos=chamados_abertos,
        atividades_recentes=atividades_recentes,
        ultimo_acesso=format_local_datetime(now_local(), '%d/%m/%Y %H:%M'),
        is_admin=session.get('is_admin', False),
        sla_vencidos=sla_vencidos,
        sla_criticos=sla_criticos,
        sla_ok=sla_ok,
        performance_sla=performance_sla
    )

# --- Lembretes ---
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import send_file, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@bp.route('/reminders/complete/<int:id>', methods=['POST'])
def complete_reminder(id):
    if session.get('is_admin'):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    reminder.completed = True
    db.session.commit()
    flash('Lembrete marcado como realizado!', 'success')
    return redirect(url_for('main.reminders'))

@bp.route('/reminders/toggle_status/<int:id>', methods=['POST'])
@login_required
def toggle_reminder_status(id):
    if session.get('is_admin'):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    
    # Obter o status desejado do formulário, se fornecido
    target_status = request.form.get('target_status')
    
    if target_status == 'cancelado':
        reminder.status = 'cancelado'
        flash('Lembrete cancelado!', 'danger')
    elif reminder.status == 'ativo':
        reminder.status = 'pausado'
        flash('Lembrete pausado!', 'warning')
    elif reminder.status == 'pausado':
        reminder.status = 'ativo'
        reminder.pause_until = None
        flash('Lembrete reativado!', 'success')
    elif reminder.status == 'cancelado':
        reminder.status = 'ativo'
        flash('Lembrete reativado!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.reminders'))

from flask import request

@bp.route('/reminders/json')
@login_required
def reminders_json():
    # Mesma lógica de ordenação e filtro da rota principal
    order_by = request.args.get('order_by', 'id')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if session.get('is_admin'):
        query = Reminder.query
    else:
        query = Reminder.query.filter_by(user_id=session.get('user_id'))

    # Aplica a ordenação
    if order_by == 'due_date':
        query = query.order_by(getattr(Reminder.due_date, order)())
    elif order_by == 'name':
        query = query.order_by(getattr(Reminder.name, order)())
    else:  # id ou padrão
        query = query.order_by(Reminder.id.desc())

    # Aplica a paginação
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reminders = pagination.items

    # Converte para dicionário para serialização JSON
    reminders_data = []
    for r in reminders:
        reminders_data.append({
            'id': r.id,
            'name': r.name,
            'type': r.type,
            'due_date': r.due_date.isoformat(),
            'responsible': r.responsible,
            'frequency': r.frequency,
            'sector': r.sector.name if r.sector else '',
            'completed': r.completed,
            'status_control': r.status,  # Campo de controle de status (ativo, pausado, cancelado)
            'pause_until': r.pause_until.isoformat() if r.pause_until else None,
            'end_date': r.end_date.isoformat() if r.end_date else None,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'status': 'completed' if r.completed else
                     'expired' if r.due_date < date.today() else
                     'ok' if r.due_date == date.today() else
                     'alert' if (r.due_date - date.today()).days <= 7 else
                     'pending'
        })

    return jsonify({
        'reminders': reminders_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@bp.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    form = ReminderForm()

    # Popular o select de setores
    from .models import Sector
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, 'Selecione')] + [(s.id, s.name) for s in sectors]

    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ''
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
            user_id=session.get('user_id'),
            status=form.status.data,
            pause_until=form.pause_until.data,
            end_date=form.end_date.data,
            created_at=get_current_time_for_db()
        )
        db.session.add(reminder)
        db.session.commit()
        flash('Lembrete cadastrado com sucesso!', 'success')
        return redirect(url_for('main.reminders'))

    return render_template('reminders.html', form=form)

@bp.route('/reminders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_reminder(id):
    from .models import Sector
    # Admin pode editar qualquer lembrete, usuário comum só os próprios
    if session.get('is_admin'):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    form = ReminderForm(obj=reminder)
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, 'Selecione')] + [(s.id, s.name) for s in sectors]
    if reminder.sector_id:
        form.sector_id.data = reminder.sector_id
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ''
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
        flash('Lembrete atualizado!', 'success')
        return redirect(url_for('main.reminders'))
    return render_template('reminders.html', reminders=Reminder.query.all(), form=form, edit_id=id)

@bp.route('/reminders/delete/<int:id>', methods=['POST'])
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    flash('Lembrete excluído!', 'success')
    return redirect(url_for('main.reminders'))

# --- API de Notificações ---
# Rota movida para o final do arquivo para evitar duplicação

# Chamados atualizados recentemente (últimas 24 horas)
    yesterday = datetime.now() - timedelta(hours=24)
    
    # Buscar chamados do usuário ou que o usuário é responsável
    chamados_query = Chamado.query.filter(
        Chamado.data_ultima_atualizacao > yesterday
    )
    
    # Se não for TI, filtrar apenas chamados do usuário
    if not is_ti:
        chamados_query = chamados_query.filter(
            Chamado.solicitante_id == user_id
        )
    
    chamados_updated = [{
        'id': c.id,
        'titulo': c.titulo,
        'status': c.status,
        'ultima_atualizacao': c.data_ultima_atualizacao.strftime('%d/%m/%Y %H:%M')
    } for c in chamados_query.all()]
    
    return jsonify({
        'reminders_expiring': reminders_expiring,
        'tasks_overdue': tasks_overdue,
        'chamados_updated': chamados_updated
    })

# --- Administração de Usuários ---
@bp.route('/admin/users')
@login_required
@admin_required
def users_admin():
    from .models import User
    users = User.query.order_by(User.id).all()
    return render_template('users.html', users=users)

@bp.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    from .models import User, Sector
    from .forms import UserEditForm

    user = User.query.get_or_404(id)
    form = UserEditForm(obj=user)

    # Define o setor atual do usuário no formulário
    if user.sector_id:
        form.sector_id.data = user.sector_id

    # Se o usuário for o próprio, não pode remover os privilégios de admin
    if user.id == session.get('user_id'):
        form.is_admin.data = True  # Garante que o admin não remova seus próprios privilégios

    if form.validate_on_submit():
        # Verifica se o email já está em uso por outro usuário
        existing_user = User.query.filter(User.email == form.email.data, User.id != user.id).first()
        if existing_user:
            flash('Este email já está em uso por outro usuário.', 'danger')
            return redirect(url_for('main.edit_user', id=user.id))

        # Verifica se o nome de usuário já está em uso por outro usuário
        existing_username = User.query.filter(User.username == form.username.data, User.id != user.id).first()
        if existing_username:
            flash('Este nome de usuário já está em uso por outro usuário.', 'danger')
            return redirect(url_for('main.edit_user', id=user.id))

        # Atualiza os dados básicos
        user.username = form.username.data
        user.email = form.email.data

        # Atualiza o setor
        user.sector_id = form.sector_id.data if form.sector_id.data != 0 else None

        # Atualiza o status de TI (qualquer usuário pode ser marcado como TI)
        user.is_ti = form.is_ti.data

        # Impede que o próprio administrador remova seus privilégios
        if user.id == session.get('user_id'):
            user.is_admin = True  # Garante que o admin não remova seus próprios privilégios
        else:
            # Verifica se é o último administrador ativo
            if user.is_admin and not form.is_admin.data:
                admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
                if admin_count <= 1:  # Se for o único admin ativo
                    flash('Não é possível remover os privilégios de administrador do último administrador ativo.', 'danger')
                    return redirect(url_for('main.edit_user', id=user.id))

            user.is_admin = form.is_admin.data

        # Atualiza a senha se solicitado
        if form.change_password.data and form.new_password.data:
            if len(form.new_password.data) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
                return redirect(url_for('main.edit_user', id=user.id))

            user.set_password(form.new_password.data)
            flash('Senha alterada com sucesso!', 'success')

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('main.users_admin'))
        except Exception as e:
            db.session.rollback()
            flash('Ocorreu um erro ao atualizar o usuário. Por favor, tente novamente.', 'danger')
            return redirect(url_for('main.edit_user', id=user.id))

    return render_template('edit_user.html', form=form, user=user)

@bp.route('/admin/users/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    from .models import User

    user = User.query.get_or_404(id)

    # Impede que o usuário desative a si mesmo
    if id == session.get('user_id'):
        flash('Você não pode desativar sua própria conta.', 'danger')
        return redirect(url_for('main.users_admin'))

    # Verifica se está tentando desativar o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash('Não é possível desativar o último administrador ativo do sistema.', 'danger')
            return redirect(url_for('main.users_admin'))

    user.ativo = not user.ativo

    try:
        db.session.commit()
        status = 'ativado' if user.ativo else 'desativado'
        flash(f'Usuário {status} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ocorreu um erro ao atualizar o status do usuário.', 'danger')

    return redirect(url_for('main.users_admin'))

@bp.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    from .models import User

    user = User.query.get_or_404(id)

    # Impede que o usuário exclua a si mesmo
    if id == session.get('user_id'):
        flash('Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('main.users_admin'))

    # Verifica se está tentando excluir o último administrador ativo
    if user.is_admin and user.ativo:  # Se for admin e estiver ativo
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:  # Se for o único admin ativo
            flash('Não é possível excluir o último administrador ativo do sistema.', 'danger')
            return redirect(url_for('main.users_admin'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ocorreu um erro ao excluir o usuário. Por favor, tente novamente.', 'danger')

    return redirect(url_for('main.users_admin'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    from .models import User
    from .forms import UserRegisterForm

    form = UserRegisterForm()

    if form.validate_on_submit():
        # Verifica se já existe um usuário com o mesmo nome de usuário ou email
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()

        if existing_user:
            flash('Nome de usuário ou email já está em uso.', 'danger')
            return render_template('register_admin.html', form=form, title='Registrar Novo Usuário')

        # Cria o novo usuário
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data if hasattr(form, 'is_admin') else False,
            is_ti=form.is_ti.data if hasattr(form, 'is_ti') else False,
            ativo=True
        )

        # Define a senha
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('main.users_admin'))
        except Exception as e:
            db.session.rollback()
            flash('Ocorreu um erro ao criar o usuário. Por favor, tente novamente.', 'danger')

    return render_template('register_admin.html', form=form, title='Registrar Novo Usuário')

@bp.route('/admin/users/reset_password/<int:id>', methods=['POST'])
@login_required
@admin_required
def reset_user_password(id):
    from .models import User
    from werkzeug.security import generate_password_hash
    import string
    import secrets

    user = User.query.get_or_404(id)

    # Gerar uma senha aleatória segura
    alphabet = string.ascii_letters + string.digits + '!@#$%&*'
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        # Garantir que a senha tenha pelo menos um caractere especial e um número
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in '!@#$%&*' for c in password)):
            break

    # Definir a nova senha
    user.set_password(password)
    db.session.commit()

    # Aqui você pode adicionar o código para enviar a nova senha por email
    # send_password_reset_email(user.email, password)

    flash(f'Senha redefinida com sucesso! Nova senha: {password} - Recomenda-se copiar e enviar ao usuário por um canal seguro.', 'success')
    return redirect(url_for('main.users_admin'))

# --- Rotas principais ---

@bp.route('/dashboard')
def dashboard():
    from flask import request, session
    from .models import Sector, User, Chamado, Task, Reminder # Adicionado Chamado, Task, Reminder
    from datetime import datetime, date # Adicionado datetime e date

    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    chamado_status = request.args.get('chamado_status', '') # Novo filtro para chamados
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id = request.args.get('user_id', type=int)

    # Conversão de datas
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inicial inválida.', 'warning')
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data final inválida.', 'warning')

    # Listas para filtros
    sectors = Sector.query.order_by(Sector.name).all()
    users = User.query.order_by(User.username).all()

    task_query = Task.query
    reminder_query = Reminder.query
    chamado_query = Chamado.query # Nova query para chamados
    equipment_query = EquipmentRequest.query # Query para equipamentos

    # Filtros
    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    is_ti = session.get('is_ti', False) # Verifica se o usuário é de TI

    if not is_admin and not is_ti: # Se não for admin nem TI, filtra por tarefas do usuário
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == current_user_id)
    elif not is_admin and is_ti: # Se for TI mas não admin, pode ver chamados do setor
        user = User.query.get(current_user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=current_user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None
        chamado_query = chamado_query.filter((Chamado.solicitante_id == current_user_id) | (Chamado.setor_id == setor_id_usuario))
        # TI pode ver todas as solicitações de equipamento
        equipment_query = EquipmentRequest.query

    if task_status == 'done':
        task_query = task_query.filter(Task.completed == True)
    elif task_status == 'pending':
        task_query = task_query.filter(Task.completed == False, Task.date >= date.today()) # Apenas pendentes não vencidas
    elif task_status == 'expired':
        task_query = task_query.filter(Task.completed == False, Task.date < date.today())

    if reminder_status == 'done':
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == 'pending':
        reminder_query = reminder_query.filter(Reminder.completed == False)
        # Adicionar lógica para lembretes vencidos se necessário, similar a tarefas

    if chamado_status: # Filtro de status para chamados
        chamado_query = chamado_query.filter(Chamado.status == chamado_status)

    if start_date:
        task_query = task_query.filter(Task.date >= start_date)
        reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura >= start_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date >= start_date)
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)
        equipment_query = equipment_query.filter(EquipmentRequest.destination_sector.contains(Sector.query.get(sector_id).name if Sector.query.get(sector_id) else '')) # Filtro por setor de destino para equipamentos

    if user_id and (is_admin or is_ti): # Admin ou TI pode filtrar por qualquer usuário
        task_query = task_query.filter(Task.user_id == user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == user_id)

    # Totais
    tasks_all = task_query.all()
    reminders_all = reminder_query.all()
    chamados_all = chamado_query.all()
    equipamentos_all = equipment_query.all() # Obtém as solicitações de equipamento filtradas

    tasks_total = len(tasks_all)
    reminders_total = len(reminders_all)
    chamados_total = len(chamados_all)
    equipamentos_total = len(equipamentos_all) # Total de equipamentos solicitados

    tasks_done = len([t for t in tasks_all if t.completed])
    tasks_pending = len([t for t in tasks_all if not t.completed and t.date >= date.today()])
    tasks_expired = len([t for t in tasks_all if not t.completed and t.date < date.today()])

    reminders_done = len([r for r in reminders_all if r.completed])
    reminders_pending = len([r for r in reminders_all if not r.completed]) # Adicionar lógica de vencidos se houver

    chamados_aberto = len([c for c in chamados_all if c.status == 'Aberto'])
    chamados_em_andamento = len([c for c in chamados_all if c.status == 'Em Andamento'])
    chamados_resolvido = len([c for c in chamados_all if c.status == 'Resolvido']) # Novo
    chamados_fechado = len([c for c in chamados_all if c.status == 'Fechado'])
    # Adicionar outros status de chamado conforme necessário

    # Contagens de status para equipamentos
    equipamentos_solicitados = len([e for e in equipamentos_all if e.status == 'Solicitado'])
    equipamentos_aprovados = len([e for e in equipamentos_all if e.status == 'Aprovado'])
    equipamentos_entregues = len([e for e in equipamentos_all if e.status == 'Entregue'])
    equipamentos_devolvidos = len([e for e in equipamentos_all if e.status == 'Devolvido'])
    equipamentos_negados = len([e for e in equipamentos_all if e.status == 'Negado'])


    # --- Dados para Gráficos de Linha (por mês, últimos 12 meses) ---
    from collections import OrderedDict
    from datetime import date, timedelta # date já estava, timedelta adicionado
    from dateutil.relativedelta import relativedelta # Adicionado relativedelta
    import calendar
    today = date.today()
    meses = []
    for i in range(11, -1, -1):
        m = (today.replace(day=1) - relativedelta(months=i))
        meses.append(m)
    meses_labels = [m.strftime('%b/%Y') for m in meses]
    tarefas_por_mes = [0]*12
    tarefas_concluidas_por_mes = [0]*12
    lembretes_por_mes = [0]*12
    lembretes_realizados_por_mes = [0]*12
    chamados_por_mes = [0]*12 # Para chamados
    equipamentos_por_mes = [0]*12 # Para equipamentos

    for idx, m in enumerate(meses):
        prox = (m + relativedelta(months=1))
        tarefas_mes = [t for t in tasks_all if t.date >= m and t.date < prox]
        tarefas_por_mes[idx] = len(tarefas_mes)
        tarefas_concluidas_por_mes[idx] = len([t for t in tarefas_mes if t.completed])
        lembretes_mes = [r for r in reminders_all if r.due_date >= m and r.due_date < prox]
        lembretes_por_mes[idx] = len(lembretes_mes)
        lembretes_realizados_por_mes[idx] = len([r for r in lembretes_mes if r.completed])
        chamados_mes = [c for c in chamados_all if c.data_abertura.date() >= m and c.data_abertura.date() < prox]
        chamados_por_mes[idx] = len(chamados_mes)
        equipamentos_mes = [e for e in equipamentos_all if e.request_date.date() >= m and e.request_date.date() < prox]
        equipamentos_por_mes[idx] = len(equipamentos_mes)


    # --- Dados para Gráfico de Barra (por setor) ---
    setores_labels = [s.name for s in sectors]
    tarefas_por_setor = [len([t for t in tasks_all if t.sector_id == s.id]) for s in sectors]
    lembretes_por_setor = [len([r for r in reminders_all if r.sector_id == s.id]) for s in sectors]
    chamados_por_setor = [len([c for c in chamados_all if c.setor_id == s.id]) for s in sectors] # Novo
    equipamentos_por_setor = [len([e for e in equipamentos_all if s.name in e.destination_sector]) for s in sectors] # Equipamentos por setor de destino


    # --- Tutoriais: agregação ---
    tutoriais = Tutorial.query.all()
    total_tutoriais = len(tutoriais)
    # Visualizações por tutorial
    visualizacoes_por_tutorial = {t.id: 0 for t in tutoriais}
    for v in VisualizacaoTutorial.query.all():
        if v.tutorial_id in visualizacoes_por_tutorial:
            visualizacoes_por_tutorial[v.tutorial_id] += 1
    # Top 5 mais visualizados
    top_tutoriais_ids = sorted(visualizacoes_por_tutorial, key=visualizacoes_por_tutorial.get, reverse=True)[:5]
    top_tutoriais = [Tutorial.query.get(tid) for tid in top_tutoriais_ids]
    top_tutoriais_labels = [t.titulo for t in top_tutoriais if t]
    top_tutoriais_values = [visualizacoes_por_tutorial[t.id] for t in top_tutoriais if t]
    # Feedbacks agregados
    feedbacks = FeedbackTutorial.query.all()
    feedbacks_util = sum(1 for f in feedbacks if f.util)
    feedbacks_nao_util = sum(1 for f in feedbacks if not f.util)
    # Feedback por tutorial (top 5 mais feedbacks)
    feedbacks_por_tutorial = {t.id: 0 for t in tutoriais}
    for f in feedbacks:
        if f.tutorial_id in feedbacks_por_tutorial:
            feedbacks_por_tutorial[f.tutorial_id] += 1
    top_feedback_ids = sorted(feedbacks_por_tutorial, key=feedbacks_por_tutorial.get, reverse=True)[:5]
    top_feedback_tutoriais = [Tutorial.query.get(tid) for tid in top_feedback_ids]
    top_feedback_labels = [t.titulo for t in top_feedback_tutoriais if t]
    top_feedback_values = [feedbacks_por_tutorial[t.id] for t in top_feedback_tutoriais if t]
    # Tutorial mais visualizado e mais útil
    tutorial_mais_visualizado = Tutorial.query.get(top_tutoriais_ids[0]) if top_tutoriais_ids else None
    tutorial_mais_util = None
    max_util = -1
    for t in tutoriais:
        util = sum(1 for f in t.feedbacks if f.util)
        if util > max_util:
            max_util = util
            tutorial_mais_util = t

    # Filtros para tutoriais
    tutorial_query = Tutorial.query
    if not is_admin and not is_ti: # Usuário comum só vê os seus
        tutorial_query = tutorial_query.filter(Tutorial.autor_id == current_user_id)
    if sector_id:
        tutorial_query = tutorial_query.join(User).filter(User.sector_id == sector_id)
    if user_id and (is_admin or is_ti): # Admin ou TI pode filtrar por autor
        tutorial_query = tutorial_query.filter(Tutorial.autor_id == user_id)
    if start_date:
        tutorial_query = tutorial_query.filter(Tutorial.data_criacao >= start_date)
    if end_date:
        tutorial_query = tutorial_query.filter(Tutorial.data_criacao <= end_date)
    tutoriais = tutorial_query.all()
    
    # Calcular estatísticas de SLA (apenas para administradores)
    sla_vencidos = 0
    sla_criticos = 0
    sla_ok = 0
    performance_sla = 0
    chamados_sla = []
    
    if is_admin:
        # Buscar todos os chamados abertos (não fechados)
        chamados_abertos_dashboard = Chamado.query.filter(
            Chamado.status != 'Fechado'
        ).order_by(Chamado.data_abertura.desc()).limit(20).all()
        
        # Calcular SLA para chamados que não têm prazo definido
        for chamado in chamados_abertos_dashboard:
            if not chamado.prazo_sla:
                chamado.calcular_sla()
        
        # Commit das mudanças no SLA
        db.session.commit()
        
        chamados_sla = chamados_abertos_dashboard
        
        # Contar os status de SLA
        for chamado in chamados_abertos_dashboard:
            status_sla = chamado.status_sla
            if status_sla == 'vencido':
                sla_vencidos += 1
            elif status_sla == 'atencao':
                sla_criticos += 1
            elif status_sla == 'normal':
                sla_ok += 1
        
        # Calcular performance de SLA dos últimos 30 dias
        from datetime import timedelta
        trinta_dias_atras = get_current_time_for_db() - timedelta(days=30)
        
        chamados_fechados_30_dias = Chamado.query.filter(
            Chamado.data_fechamento >= trinta_dias_atras,
            Chamado.data_fechamento.isnot(None)
        ).all()
        
        if chamados_fechados_30_dias:
            # Calcular SLA para chamados fechados que não têm sla_cumprido definido
            for chamado in chamados_fechados_30_dias:
                if chamado.sla_cumprido is None and chamado.prazo_sla:
                    # Se foi fechado dentro do prazo, considera cumprido
                    chamado.sla_cumprido = chamado.data_fechamento <= chamado.prazo_sla
            
            db.session.commit()
            
            sla_cumpridos = len([c for c in chamados_fechados_30_dias if c.sla_cumprido])
            performance_sla = round((sla_cumpridos / len(chamados_fechados_30_dias)) * 100)

    return render_template('dashboard.html',
        tasks_total=tasks_total,
        tasks_done=tasks_done,
        tasks_pending=tasks_pending,
        tasks_expired=tasks_expired,
        reminders_total=reminders_total,
        reminders_done=reminders_done,
        reminders_pending=reminders_pending,
        chamados_total=chamados_total,
        chamados_aberto=chamados_aberto,
        chamados_em_andamento=chamados_em_andamento,
        chamados_resolvido=chamados_resolvido, # Novo
        chamados_fechado=chamados_fechado,
        equipamentos_total=equipamentos_total, # Total de equipamentos
        equipamentos_solicitados=equipamentos_solicitados,
        equipamentos_aprovados=equipamentos_aprovados,
        equipamentos_entregues=equipamentos_entregues,
        equipamentos_devolvidos=equipamentos_devolvidos,
        equipamentos_negados=equipamentos_negados,
        sectors=sectors,
        users=users,
        selected_sector=sector_id,
        selected_user=user_id,
        meses_labels=meses_labels,
        tarefas_por_mes=tarefas_por_mes,
        tarefas_concluidas_por_mes=tarefas_concluidas_por_mes,
        lembretes_por_mes=lembretes_por_mes,
        lembretes_realizados_por_mes=lembretes_realizados_por_mes,
        chamados_por_mes=chamados_por_mes,
        equipamentos_por_mes=equipamentos_por_mes,
        setores_labels=setores_labels,
        tarefas_por_setor=tarefas_por_setor,
        lembretes_por_setor=lembretes_por_setor,
        chamados_por_setor=chamados_por_setor, # Novo
        equipamentos_por_setor=equipamentos_por_setor,
        total_tutoriais=total_tutoriais,
        top_tutoriais_labels=top_tutoriais_labels,
        top_tutoriais_values=top_tutoriais_values,
        feedbacks_util=feedbacks_util,
        feedbacks_nao_util=feedbacks_nao_util,
        top_feedback_labels=top_feedback_labels,
        top_feedback_values=top_feedback_values,
        tutorial_mais_visualizado=tutorial_mais_visualizado,
        tutorial_mais_util=tutorial_mais_util,
        sla_vencidos=sla_vencidos,
        sla_criticos=sla_criticos,
        sla_ok=sla_ok,
        performance_sla=performance_sla,
        chamados_sla=chamados_sla,
    )

@bp.route('/export/excel')
def export_excel():
    from flask import request, session # session já estava importado globalmente, mas garantindo
    from .models import Task, Reminder, Chamado, Sector, User, Tutorial # Adicionado Tutorial
    from datetime import datetime, date # Adicionado datetime, date
    import pandas as pd # pd já estava importado globalmente
    from io import BytesIO # BytesIO já estava importado globalmente

    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    chamado_status = request.args.get('chamado_status', '') # Novo
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id_filter = request.args.get('user_id', type=int) # Renomeado para evitar conflito com user_id da sessão

    # Conversão de datas
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass # Ignorar data inválida para exportação, ou poderia dar flash
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    task_query = Task.query
    reminder_query = Reminder.query
    chamado_query = Chamado.query # Novo
    equipment_query = EquipmentRequest.query # Query para equipamentos

    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    is_ti = session.get('is_ti', False)

    # Filtros de permissão
    if not is_admin and not is_ti:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == current_user_id)
    elif not is_admin and is_ti:
        user = User.query.get(current_user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=current_user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None
        chamado_query = chamado_query.filter((Chamado.solicitante_id == current_user_id) | (Chamado.setor_id == setor_id_usuario))
        equipment_query = EquipmentRequest.query # TI pode ver todas as solicitações de equipamento

    if task_status == 'done':
        task_query = task_query.filter(Task.completed == True)
    elif task_status == 'pending':
        task_query = task_query.filter(Task.completed == False, Task.date >= date.today())
    elif task_status == 'expired':
        task_query = task_query.filter(Task.completed == False, Task.date < date.today())

    if reminder_status == 'done':
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == 'pending':
        reminder_query = reminder_query.filter(Reminder.completed == False)

    if chamado_status:
        chamado_query = chamado_query.filter(Chamado.status == chamado_status)

    if start_date:
        task_query = task_query.filter(Task.date >= start_date)
        reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura >= start_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date >= start_date)
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)
        # Filtro para equipamentos por setor de destino
        setor_nome = Sector.query.get(sector_id).name if Sector.query.get(sector_id) else ''
        equipment_query = equipment_query.filter(EquipmentRequest.destination_sector.contains(setor_nome))


    if user_id_filter and (is_admin or is_ti): # Admin ou TI pode filtrar por qualquer usuário
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == user_id_filter)


    export_type = request.args.get('export_type', 'all')
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})

        if export_type in ['all', 'tasks']:
            tasks = task_query.all()
            tasks_data = [{
                'Descrição': t.description,
                'Data': t.date.strftime('%d/%m/%Y') if t.date else '',
                'Responsável': t.responsible,
                'Setor': t.sector.name if t.sector else '',
                'Usuário': t.usuario.username if t.usuario else '',
                'Concluída': 'Sim' if t.completed else 'Não'
            } for t in tasks]
            df_tasks = pd.DataFrame(tasks_data)
            df_tasks.to_excel(writer, sheet_name='Tarefas', index=False, header=False, startrow=1)
            worksheet_tasks = writer.sheets['Tarefas']
            worksheet_tasks.merge_range('A1:F1', 'Relatório de Tarefas', title_format)
            for col_num, value in enumerate(df_tasks.columns.values):
                worksheet_tasks.write(0, col_num, value, header_format)
            # Auto-ajustar colunas (exemplo)
            for i, col in enumerate(df_tasks.columns):
                column_len = max(df_tasks[col].astype(str).map(len).max(), len(col))
                worksheet_tasks.set_column(i, i, column_len + 2)


        if export_type in ['all', 'reminders']:
            reminders = reminder_query.all()
            reminders_data = [{
                'Nome': r.name,
                'Tipo': r.type,
                'Vencimento': r.due_date.strftime('%d/%m/%Y') if r.due_date else '',
                'Responsável': r.responsible,
                'Setor': r.sector.name if r.sector else '',
                'Usuário': r.usuario.username if r.usuario else '',
                'Realizado': 'Sim' if r.completed else 'Não'
            } for r in reminders]
            df_reminders = pd.DataFrame(reminders_data)
            df_reminders.to_excel(writer, sheet_name='Lembretes', index=False, header=False, startrow=1)
            worksheet_reminders = writer.sheets['Lembretes']
            worksheet_reminders.merge_range('A1:G1', 'Relatório de Lembretes', title_format)
            for col_num, value in enumerate(df_reminders.columns.values):
                worksheet_reminders.write(0, col_num, value, header_format)
            for i, col in enumerate(df_reminders.columns):
                column_len = max(df_reminders[col].astype(str).map(len).max(), len(col))
                worksheet_reminders.set_column(i, i, column_len + 2)

        if export_type in ['all', 'chamados']: # Novo bloco para chamados
            chamados = chamado_query.all()
            chamados_data = [{
                'ID': c.id,
                'Título': c.titulo,
                'Status': c.status,
                'Prioridade': c.prioridade,
                'Abertura': c.data_abertura.strftime('%d/%m/%Y %H:%M') if c.data_abertura else '',
                'Prazo SLA': c.prazo_sla.strftime('%d/%m/%Y %H:%M') if c.prazo_sla else 'N/A',
                'Status SLA': c.status_sla if hasattr(c, 'status_sla') else 'N/A',
                'Solicitante': c.solicitante.username if c.solicitante else '',
                'Setor': c.setor.name if c.setor else '',
                'Responsável TI': c.responsavel_ti.username if c.responsavel_ti else '',
                'Fechamento': c.data_fechamento.strftime('%d/%m/%Y %H:%M') if c.data_fechamento else 'Em Aberto'
            } for c in chamados]
            df_chamados = pd.DataFrame(chamados_data)
            if not df_chamados.empty:
                df_chamados.to_excel(writer, sheet_name='Chamados', index=False, header=False, startrow=2)
                worksheet_chamados = writer.sheets['Chamados']
                worksheet_chamados.merge_range('A1:K1', 'Relatório de Chamados', title_format)
                for col_num, value in enumerate(df_chamados.columns.values):
                    worksheet_chamados.write(1, col_num, value, header_format)
                for i, col in enumerate(df_chamados.columns):
                    column_len = max(df_chamados[col].astype(str).map(len).max(), len(col))
                    worksheet_chamados.set_column(i, i, column_len + 2)
            else:
                # Criar planilha mesmo sem dados
                worksheet_chamados = workbook.add_worksheet('Chamados')
                worksheet_chamados.merge_range('A1:K1', 'Relatório de Chamados', title_format)
                worksheet_chamados.write_row(1, 0, ['ID', 'Título', 'Status', 'Prioridade', 'Abertura', 'Prazo SLA', 'Status SLA', 'Solicitante', 'Setor', 'Responsável TI', 'Fechamento'], header_format)
                worksheet_chamados.write(2, 0, 'Nenhum chamado encontrado com os filtros aplicados')

        if export_type in ['all', 'equipamentos']: # Bloco para equipamentos
            equipamentos = equipment_query.all()
            equipamentos_data = [{
                'ID': e.id,
                'Descrição': e.description,
                'Patrimônio': e.patrimony,
                'Tipo': e.equipment_type,
                'Status': e.status,
                'Solicitante': e.requester.username if e.requester else '',
                'Data Solicitação': e.request_date.strftime('%d/%m/%Y') if e.request_date else ''
            } for e in equipamentos]
            df_equipamentos = pd.DataFrame(equipamentos_data)
            df_equipamentos.to_excel(writer, sheet_name='Equipamentos', index=False, header=False, startrow=1)
            worksheet_equipamentos = writer.sheets['Equipamentos']
            worksheet_equipamentos.merge_range('A1:G1', 'Relatório de Equipamentos', title_format)
            for col_num, value in enumerate(df_equipamentos.columns.values):
                worksheet_equipamentos.write(0, col_num, value, header_format)
            for i, col in enumerate(df_equipamentos.columns):
                column_len = max(df_equipamentos[col].astype(str).map(len).max(), len(col))
                worksheet_equipamentos.set_column(i, i, column_len + 2)

        if export_type in ['all', 'tutoriais']:
            # Consulta para obter os tutoriais
            tutorial_query = Tutorial.query
            
            # Aplicar filtros de data se fornecidos
            if start_date:
                tutorial_query = tutorial_query.filter(Tutorial.data_criacao >= start_date)
            if end_date:
                tutorial_query = tutorial_query.filter(Tutorial.data_criacao <= end_date)
                
            # Aplicar filtro de usuário se fornecido
            if user_id_filter and (is_admin or is_ti):
                tutorial_query = tutorial_query.filter(Tutorial.autor_id == user_id_filter)
                
            # Obter todos os tutoriais filtrados
            tutoriais = tutorial_query.all()
            
            tutoriais_data = [{
                'Título': t.titulo,
                'Categoria': t.categoria or '',
                'Autor': t.autor.username,
                'Data de Criação': t.data_criacao.strftime('%d/%m/%Y %H:%M'),
                'Visualizações': len(t.visualizacoes),
                'Feedback Útil': sum(1 for f in t.feedbacks if f.util),
                'Feedback Não Útil': sum(1 for f in t.feedbacks if not f.util)
            } for t in tutoriais]
            df_tutoriais = pd.DataFrame(tutoriais_data)
            df_tutoriais.to_excel(writer, sheet_name='Tutoriais', index=False, header=False, startrow=1)
            worksheet_tutoriais = writer.sheets['Tutoriais']
            worksheet_tutoriais.merge_range('A1:G1', 'Relatório de Tutoriais', title_format)
            for col_num, value in enumerate(df_tutoriais.columns.values):
                worksheet_tutoriais.write(0, col_num, value, header_format)
            for i, col in enumerate(df_tutoriais.columns):
                column_len = max(df_tutoriais[col].astype(str).map(len).max(), len(col))
                worksheet_tutoriais.set_column(i, i, column_len + 2)

    output.seek(0)
    # Forçar mimetype correto para navegadores modernos
    return send_file(
        output,
        download_name='relatorio_reminder.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/help')
@login_required
def help_page():
    """Página de ajuda com documentação do sistema"""
    return render_template('help.html', title='Central de Ajuda')

@bp.route('/export/pdf')
def export_pdf():
    from flask import request, session, make_response # make_response adicionado
    # Models já importados na export_excel, mas para clareza se esta função for movida:
    # from .models import Task, Reminder, Chamado, Sector, User
    # datetime, date já importados
    # from io import BytesIO # Já importado
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    chamado_status = request.args.get('chamado_status', '') # Novo
    export_type = request.args.get('export_type', 'all')

    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id_filter = request.args.get('user_id', type=int)

    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError: pass
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError: pass

    task_query = Task.query
    reminder_query = Reminder.query
    chamado_query = Chamado.query
    equipment_query = EquipmentRequest.query # Query para equipamentos

    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    is_ti = session.get('is_ti', False)

    # Filtros de permissão
    if not is_admin and not is_ti:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == current_user_id)
    elif not is_admin and is_ti:
        user = User.query.get(current_user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=current_user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None
        chamado_query = chamado_query.filter((Chamado.solicitante_id == current_user_id) | (Chamado.setor_id == setor_id_usuario))
        equipment_query = EquipmentRequest.query

    if task_status == 'done':
        task_query = task_query.filter(Task.completed == True)
    elif task_status == 'pending':
        task_query = task_query.filter(Task.completed == False, Task.date >= date.today())
    elif task_status == 'expired':
        task_query = task_query.filter(Task.completed == False, Task.date < date.today())

    if reminder_status == 'done':
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == 'pending':
        reminder_query = reminder_query.filter(Reminder.completed == False)

    if chamado_status:
        chamado_query = chamado_query.filter(Chamado.status == chamado_status)

    if start_date:
        task_query = task_query.filter(Task.date >= start_date)
        reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura >= start_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date >= start_date)
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)
        equipment_query = equipment_query.filter(EquipmentRequest.request_date <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)
        setor_nome = Sector.query.get(sector_id).name if Sector.query.get(sector_id) else ''
        equipment_query = equipment_query.filter(EquipmentRequest.destination_sector.contains(setor_nome))


    if user_id_filter and (is_admin or is_ti):
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)
        equipment_query = equipment_query.filter(EquipmentRequest.requester_id == user_id_filter)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['h2'] # Usar H2 para subtítulos de seção
    title_style.alignment = 1 # Center
    normal_style = styles['Normal']
    normal_style.fontSize = 8 # Reduzir um pouco para caber mais dados


    # Definindo larguras das colunas (ajustar conforme necessário)
    col_widths_tasks = [2.3*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch]
    col_widths_reminders = [1.8*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch]
    col_widths_chamados = [0.4*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch]
    col_widths_equipamentos = [0.4*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch] # Larguras para equipamentos

    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), # Azul escuro para cabeçalho
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#DCE6F1")), # Azul claro para dados
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ])

    # Título Geral do Documento
    elements.append(Paragraph("Relatório Geral - TI OSN System", styles['h1']))
    elements.append(Spacer(1, 0.3*inch))

    if export_type in ['all', 'tasks']:
        tasks = task_query.all()
        elements.append(Paragraph("Relatório de Tarefas", title_style))
        elements.append(Spacer(1, 0.1*inch))
        if tasks:
            data_tasks = [["Descrição", "Data", "Responsável", "Setor", "Usuário", "Concluída"]]
            for t in tasks:
                data_tasks.append([
                    Paragraph(t.description if t.description else '', normal_style),
                    t.date.strftime('%d/%m/%Y') if t.date else '',
                    Paragraph(t.responsible if t.responsible else '', normal_style),
                    Paragraph(t.sector.name if t.sector else '', normal_style),
                    Paragraph(t.usuario.username if t.usuario else '', normal_style),
                    "Sim" if t.completed else "Não"
                ])
            table = Table(data_tasks, colWidths=col_widths_tasks)
            table.setStyle(table_style)
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhuma tarefa encontrada.", normal_style))
        elements.append(PageBreak() if export_type == 'all' else Spacer(1, 0.3*inch))

    if export_type in ['all', 'reminders']:
        reminders = reminder_query.all()
        elements.append(Paragraph("Relatório de Lembretes", title_style))
        elements.append(Spacer(1, 0.1*inch))
        if reminders:
            data_reminders = [["Nome", "Tipo", "Vencimento", "Responsável", "Setor", "Usuário", "Realizado"]]
            for r in reminders:
                data_reminders.append([
                    Paragraph(r.name if r.name else '', normal_style),
                    Paragraph(r.type if r.type else '', normal_style),
                    r.due_date.strftime('%d/%m/%Y') if r.due_date else '',
                    Paragraph(r.responsible if r.responsible else '', normal_style),
                    Paragraph(r.sector.name if r.sector else '', normal_style),
                    Paragraph(r.usuario.username if r.usuario else '', normal_style),
                    "Sim" if r.completed else "Não"
                ])
            table = Table(data_reminders, colWidths=col_widths_reminders)
            table.setStyle(table_style)
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum lembrete encontrado.", normal_style))
        elements.append(PageBreak() if export_type == 'all' else Spacer(1, 0.3*inch))

    if export_type in ['all', 'chamados']:
        chamados = chamado_query.all()
        elements.append(Paragraph("Relatório de Chamados", title_style))
        elements.append(Spacer(1, 0.1*inch))
        if chamados:
            data_chamados = [["ID", "Título", "Status", "Prioridade", "Abertura", "Solicitante", "Setor", "Resp. TI"]]
            for c in chamados:
                data_chamados.append([
                    str(c.id),
                    Paragraph(c.titulo if c.titulo else '', normal_style),
                    Paragraph(c.status if c.status else '', normal_style),
                    Paragraph(c.prioridade if c.prioridade else '', normal_style),
                    c.data_abertura.strftime('%d/%m/%Y %H:%M') if c.data_abertura else '',
                    Paragraph(c.solicitante.username if c.solicitante else '', normal_style),
                    Paragraph(c.setor.name if c.setor else '', normal_style),
                    Paragraph(c.responsavel_ti.username if c.responsavel_ti else '', normal_style)
                ])
            table = Table(data_chamados, colWidths=col_widths_chamados)
            table.setStyle(table_style)
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum chamado encontrado.", normal_style))
        elements.append(PageBreak() if export_type == 'all' else Spacer(1, 0.3*inch))

    if export_type in ['all', 'equipamentos']:
        equipamentos = equipment_query.all()
        elements.append(Paragraph("Relatório de Equipamentos", title_style))
        elements.append(Spacer(1, 0.1*inch))
        if equipamentos:
            data_equipamentos = [["ID", "Descrição", "Patrimônio", "Tipo", "Status", "Solicitante", "Data Solicitação"]]
            for e in equipamentos:
                data_equipamentos.append([
                    str(e.id),
                    Paragraph(e.description if e.description else '', normal_style),
                    e.patrimony if e.patrimony else '',
                    e.equipment_type if e.equipment_type else '',
                    Paragraph(e.status if e.status else '', normal_style),
                    Paragraph(e.requester.username if e.requester else '', normal_style),
                    e.request_date.strftime('%d/%m/%Y') if e.request_date else ''
                ])
            table = Table(data_equipamentos, colWidths=col_widths_equipamentos)
            table.setStyle(table_style)
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum equipamento encontrado.", normal_style))
        elements.append(PageBreak() if export_type == 'all' else Spacer(1, 0.3*inch))

    if not elements or all(isinstance(el, (Paragraph, Spacer)) and "Nenhum" in el.text for el in elements if isinstance(el, Paragraph)):
         elements.append(Paragraph("Nenhum dado para exportar com os filtros selecionados.", styles['Normal']))

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
    if export_type in ['all', 'tutoriais']:
        elements.append(Paragraph("Relatório de Tutoriais", title_style))
        elements.append(Spacer(1, 0.1*inch))
        if tutoriais:
            data_tutoriais = [["Título", "Categoria", "Autor", "Data de Criação", "Visualizações", "Feedback Útil", "Feedback Não Útil"]]
            for t in tutoriais:
                data_tutoriais.append([
                    Paragraph(t.titulo if t.titulo else '', normal_style),
                    Paragraph(t.categoria if t.categoria else '', normal_style),
                    Paragraph(t.autor.username if t.autor else '', normal_style),
                    t.data_criacao.strftime('%d/%m/%Y %H:%M'),
                    str(len(t.visualizacoes)),
                    str(sum(1 for f in t.feedbacks if f.util)),
                    str(sum(1 for f in t.feedbacks if not f.util))
                ])
            table = Table(data_tutoriais, colWidths=[2*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(table_style)
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum tutorial encontrado.", normal_style))
        elements.append(PageBreak() if export_type == 'all' else Spacer(1, 0.3*inch))

    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_ti_reminder.pdf'
    return response

# --- Tarefas ---
@bp.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    from .models import Sector
    form = TaskForm()
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, 'Selecione')] + [(s.id, s.name) for s in sectors]
    page = request.args.get('page', 1, type=int)
    per_page = 10
    # Filtros e busca
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '')
    query = Task.query
    if status_filter == 'expired':
        query = query.filter(Task.completed == False, Task.date < date.today())
    elif status_filter == 'today':
        query = query.filter(Task.completed == False, Task.date == date.today())
    elif status_filter == 'done':
        query = query.filter(Task.completed == True)
    elif status_filter == 'pending':
        query = query.filter(Task.completed == False, Task.date >= date.today())
    if search:
        query = query.filter(Task.description.ilike(f'%{search}%') | Task.responsible.ilike(f'%{search}%'))
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Task.date == filter_date)
        except:
            pass
    # Admin pode ver todas as tarefas, usuário comum só as próprias
    if not session.get('is_admin'):
        query = query.filter_by(user_id=session.get('user_id'))
    pagination = query.order_by(Task.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items
    # Aplica status visual
    for t in tasks:
        if t.completed:
            t.status = 'done'
        elif t.date < date.today():
            t.status = 'expired'
        elif t.date == date.today():
            t.status = 'today'
        else:
            t.status = 'pending'
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ''
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
            sector_id=sector_id,
            user_id=session.get('user_id')
        )
        db.session.add(task)
        db.session.commit()
        flash('Tarefa adicionada!', 'success')
        return redirect(url_for('main.tasks'))
    return render_template('tasks.html', tasks=tasks, form=form, edit_id=None, pagination=pagination, status_filter=status_filter, search=search, date_filter=date_filter, current_date=date.today())


@bp.route('/tasks/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    if session.get('is_admin'):
        task = Task.query.get_or_404(id)
    else:
        task = Task.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    form = TaskForm(obj=task)
    # Popular o select de setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, 'Selecione')] + [(s.id, s.name) for s in sectors]
    if form.validate_on_submit():
        # Lógica do setor: se novo setor preenchido, criar e usar
        sector_id = form.sector_id.data
        new_sector_name = form.new_sector.data.strip() if form.new_sector.data else ''
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
        flash('Tarefa atualizada!', 'success')
        return redirect(url_for('main.tasks'))
    # Lógica de paginação e filtros igual à função tasks
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '')
    query = Task.query
    if status_filter == 'expired':
        query = query.filter(Task.completed == False, Task.date < date.today())
    elif status_filter == 'today':
        query = query.filter(Task.completed == False, Task.date == date.today())
    elif status_filter == 'done':
        query = query.filter(Task.completed == True)
    elif status_filter == 'pending':
        query = query.filter(Task.completed == False, Task.date >= date.today())
    if search:
        query = query.filter(Task.description.ilike(f'%{search}%') | Task.responsible.ilike(f'%{search}%'))
    if date_filter:
        query = query.filter(Task.date == date_filter)
    pagination = query.order_by(Task.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items
    # Aplica status visual
    for t in tasks:
        if t.completed:
            t.status = 'done'
        elif t.date < date.today():
            t.status = 'expired'
        elif t.date == date.today():
            t.status = 'today'
        else:
            t.status = 'pending'
    return render_template('tasks.html', tasks=tasks, form=form, edit_id=id, pagination=pagination, status_filter=status_filter, search=search, date_filter=date_filter)




@bp.route('/tasks/complete/<int:id>', methods=['POST'])
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.completed = True
    db.session.commit()
    flash('Tarefa marcada como concluída!', 'success')
    return redirect(url_for('main.tasks'))

@bp.route('/tasks/delete/<int:id>', methods=['POST'])
def delete_task(id):
    if session.get('is_admin'):
        task = Task.query.get_or_404(id)
    else:
        task = Task.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Tarefa excluída!', 'success')
    return redirect(url_for('main.tasks'))


from .models import Chamado, User
from .forms import ChamadoForm
from .email_utils import send_chamado_aberto_email

# --- Rotas para Chamados ---

@bp.route('/chamados/abrir', methods=['GET', 'POST'])
@login_required
def abrir_chamado():
    form = ChamadoForm()
    user_id = session.get('user_id')
    user = User.query.get(user_id)

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

    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Verificar se o usuário está criando um novo setor
            if form.new_sector.data and form.new_sector.data.strip():
                # Verificar se o setor já existe
                setor_existente = Sector.query.filter_by(name=form.new_sector.data.strip()).first()
                if setor_existente:
                    setor_id = setor_existente.id
                else:
                    # Criar novo setor
                    novo_setor = Sector(name=form.new_sector.data.strip())
                    db.session.add(novo_setor)
                    db.session.commit()
                    setor_id = novo_setor.id
                    flash(f"Novo setor '{novo_setor.name}' criado com sucesso!", "success")
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
                status='Aberto'  # Status inicial
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
                flash(f"Chamado criado, mas houve um erro ao enviar notificações: {str(e)}", "warning")
                print(f"Error sending notification email for Chamado {novo_chamado.id}: {e}")

            flash("Chamado aberto com sucesso!", "success")
            return redirect(url_for('main.detalhe_chamado', id=novo_chamado.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao abrir o chamado: {str(e)}", "danger")
            print(f"Error creating Chamado: {e}")

    # Pré-selecionar o setor do usuário no formulário, se existir
    if setor_usuario and hasattr(form, 'setor_id'):
        form.setor_id.data = setor_usuario.id
        
    return render_template('abrir_chamado.html',
                         form=form,
                         title='Abrir Novo Chamado',
                         setor_usuario=setor_usuario)

@bp.route('/chamados', methods=['GET'])
@login_required
def listar_chamados():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status_filter = request.args.get('status', '')
    prioridade_filter = request.args.get('prioridade', '')
    setor_filter = request.args.get('sector_id', type=int)

    query = Chamado.query

    # Filtrar por permissão: Admin/TI vê tudo, usuário comum vê os seus e/ou do seu setor
    if not session.get('is_admin'): # Assumindo que 'is_admin' também cobre a equipe de TI por enquanto
        user_id = session.get('user_id')
        # Obter setor do usuário (mesma lógica/problema de 'abrir_chamado')
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None
        # Mostrar chamados do usuário ou do setor do usuário (ajustar conforme regra)
        query = query.filter((Chamado.solicitante_id == user_id) | (Chamado.setor_id == setor_id_usuario))

    # Aplicar filtros adicionais
    if status_filter:
        query = query.filter(Chamado.status == status_filter)
    if prioridade_filter:
        query = query.filter(Chamado.prioridade == prioridade_filter)
    if setor_filter:
        query = query.filter(Chamado.setor_id == setor_filter)

    chamados_paginated = query.order_by(Chamado.data_abertura.desc()).paginate(page=page, per_page=per_page)

    # Para os filtros no template
    setores = Sector.query.order_by(Sector.name).all()
    status_list = db.session.query(Chamado.status).distinct().all()
    prioridade_list = db.session.query(Chamado.prioridade).distinct().all()

    return render_template('listar_chamados.html',
                           chamados=chamados_paginated.items,
                           pagination=chamados_paginated,
                           setores=setores,
                           status_list=[s[0] for s in status_list],
                           prioridade_list=[p[0] for p in prioridade_list],
                           title='Meus Chamados')

@bp.route('/chamados/<int:id>')
@login_required
def detalhe_chamado(id):
    from .forms import ChamadoAdminForm

    query = Chamado.query
    is_admin = session.get('is_admin')
    user_id = session.get('user_id')

    # Aplicar restrição de acesso
    if not is_admin:
        user = User.query.get(user_id)
        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        setor_id_usuario = primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None
        # Permitir ver se for o solicitante ou do mesmo setor
        query = query.filter((Chamado.solicitante_id == user_id) | (Chamado.setor_id == setor_id_usuario))

    chamado = query.filter(Chamado.id == id).first_or_404()

    # Se for administrador, preparar o formulário administrativo
    form = None
    usuarios_ti = []
    if is_admin:
        form = ChamadoAdminForm()
        form.status.choices = [
            ('Aberto', 'Aberto'),
            ('Em Andamento', 'Em Andamento'),
            ('Resolvido', 'Resolvido'),
            ('Fechado', 'Fechado')
        ]
        form.status.data = chamado.status

        # Buscar apenas usuários ativos com perfil de TI
        usuarios_ti = User.query.filter_by(is_ti=True, ativo=True).order_by(User.username).all()

        # Definir o valor atual do responsável TI, se existir
        if chamado.responsavel_ti_id:
            form.responsavel_ti_id.data = str(chamado.responsavel_ti_id)

    return render_template(
        'detalhe_chamado.html',
        chamado=chamado,
        form=form,
        usuarios_ti=usuarios_ti,
        title=f'Chamado #{chamado.id}'
    )

@bp.route('/chamados/<int:id>/admin', methods=['POST'])
@login_required
def gerenciar_chamado(id):
    from .models import Chamado, ComentarioChamado, ComentarioTutorial, db
    from .forms import ChamadoAdminForm
    from .email_utils import send_chamado_atualizado_email

    # Verifica se o usuário é administrador
    if not session.get('is_admin'):
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('main.detalhe_chamado', id=id))

    chamado = Chamado.query.get_or_404(id)
    form = ChamadoAdminForm()

    # Preenche as opções de responsável TI (apenas usuários ativos e marcados como TI)
    usuarios_ti = User.query.filter_by(ativo=True, is_ti=True).order_by(User.username).all()
    form.responsavel_ti_id.choices = [('', 'Nenhum (sem responsável)')] + [(str(u.id), u.username) for u in usuarios_ti]

    if form.validate_on_submit():
        alteracoes = []

        # Atualiza o status se foi alterado
        if form.status.data != chamado.status:
            alteracoes.append(f'Status alterado de "{chamado.status}" para "{form.status.data}"')
            
            # Marcar primeira resposta se mudou de "Aberto" para qualquer outro status
            if chamado.status == 'Aberto' and form.status.data in ['Em Andamento', 'Resolvido', 'Fechado']:
                chamado.marcar_primeira_resposta()
                alteracoes.append('Primeira resposta registrada para cálculo de SLA')
            
            chamado.status = form.status.data

            # Atualiza a data de fechamento se o status for Fechado
            if form.status.data == 'Fechado' and not chamado.data_fechamento:
                chamado.data_fechamento = datetime.utcnow()
                alteracoes.append('Chamado fechado')
            elif form.status.data != 'Fechado' and chamado.data_fechamento:
                chamado.data_fechamento = None
                alteracoes.append('Chamado reaberto')

        # Atualiza o responsável TI se foi alterado
        if form.responsavel_ti_id.data != str(chamado.responsavel_ti_id if chamado.responsavel_ti_id else ''):
            if form.responsavel_ti_id.data:  # Novo responsável selecionado
                novo_responsavel = User.query.get(form.responsavel_ti_id.data)
                if novo_responsavel:
                    alteracoes.append(f'Responsável TI alterado para {novo_responsavel.username}')
                    chamado.responsavel_ti_id = novo_responsavel.id
            else:  # Nenhum responsável selecionado
                if chamado.responsavel_ti:
                    alteracoes.append('Responsável TI removido')
                    chamado.responsavel_ti_id = None

        # Adiciona um comentário se foi preenchido
        if form.comentario.data.strip():
            comentario = ComentarioChamado(
                chamado_id=chamado.id,
                usuario_id=session['user_id'],
                texto=form.comentario.data,
                tipo='comentario'
            )
            db.session.add(comentario)
            alteracoes.append('Comentário adicionado')

        # Se houve alterações, registra como atualização
        if alteracoes:
            # Atualiza a data da última atualização
            chamado.data_ultima_atualizacao = datetime.utcnow()

            # Cria um registro de atualização
            atualizacao = ComentarioChamado(
                chamado_id=chamado.id,
                usuario_id=session['user_id'],
                texto=' | '.join(alteracoes),
                tipo='atualizacao'
            )
            db.session.add(atualizacao)

            db.session.commit()

            # Envia notificação por e-mail se solicitado
            if form.notificar_solicitante.data and chamado.solicitante.email:
                try:
                    send_chamado_atualizado_email(chamado, atualizacao)
                except Exception as e:
                    print(f"Erro ao enviar e-mail: {str(e)}")
                    flash('Chamado atualizado, mas ocorreu um erro ao enviar a notificação por e-mail.', 'warning')

            flash('Chamado atualizado com sucesso!', 'success')
        else:
            flash('Nenhuma alteração foi realizada.', 'info')

        return redirect(url_for('main.detalhe_chamado', id=chamado.id))

    # Se o formulário não for válido, mostra os erros
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.detalhe_chamado', id=chamado.id))

# --- Tutoriais ---
# Apenas usuários com is_ti=True (Equipe de TI) podem cadastrar, editar e excluir tutoriais.

@bp.route('/tutoriais')
@login_required
def listar_tutoriais():
    busca = request.args.get('busca', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 6
    query = Tutorial.query
    if busca:
        query = query.filter((Tutorial.titulo.ilike(f'%{busca}%')) | (Tutorial.conteudo.ilike(f'%{busca}%')) | (Tutorial.categoria.ilike(f'%{busca}%')))
    pagination = query.order_by(Tutorial.data_criacao.desc()).paginate(page=page, per_page=per_page, error_out=False)
    tutoriais = pagination.items
    return render_template('tutoriais.html', tutoriais=tutoriais, busca=busca, pagination=pagination)

@bp.route('/tutoriais/novo', methods=['GET', 'POST'])
@login_required
def novo_tutorial():
    # Apenas membros da equipe de TI ou administradores podem cadastrar tutoriais
    if not (session.get('is_ti') or session.get('is_admin')):
        flash('Apenas membros da equipe de TI ou administradores podem cadastrar tutoriais.', 'danger')
        return redirect(url_for('main.listar_tutoriais'))
    form = TutorialForm()
    if form.validate_on_submit():
        tutorial = Tutorial(
            titulo=form.titulo.data,
            conteudo=form.conteudo.data,
            categoria=form.categoria.data,
            autor_id=session.get('user_id')
        )
        db.session.add(tutorial)
        db.session.commit()
        # Upload de imagens
        if form.imagem.data:
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file = form.imagem.data
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                img = TutorialImage(tutorial_id=tutorial.id, filename=filename)
                db.session.add(img)
            db.session.commit()
        flash('Tutorial cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_tutoriais'))
    return render_template('tutorial_form.html', form=form, title='Novo Tutorial')

@bp.route('/tutoriais/<int:tutorial_id>')
@login_required
def detalhe_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    feedback_form = FeedbackTutorialForm()
    # Registrar visualização (mantém se já estiver)
    visualizacao = VisualizacaoTutorial(tutorial_id=tutorial.id, usuario_id=session.get('user_id'))
    db.session.add(visualizacao)
    db.session.commit()
    # Preparar dados para gráficos (mantém se já estiver)
    visualizacoes = VisualizacaoTutorial.query.filter_by(tutorial_id=tutorial.id).all()
    datas = [v.data.strftime('%d/%m') for v in visualizacoes]
    from collections import Counter
    contagem_datas = Counter(datas)
    datas_ordenadas = sorted(contagem_datas.keys(), key=lambda x: tuple(map(int, x.split('/')[::-1])))
    visualizacoes_labels = datas_ordenadas[-15:]
    visualizacoes_values = [contagem_datas[d] for d in visualizacoes_labels]
    feedbacks = tutorial.feedbacks
    total_util = sum(1 for f in feedbacks if f.util)
    total_nao_util = sum(1 for f in feedbacks if not f.util)
    feedback_data = {
        'labels': ['Útil', 'Não útil'],
        'values': [total_util, total_nao_util]
    }
    import json
    conteudo_markdown = markdown.markdown(tutorial.conteudo, extensions=['extra', 'nl2br'])
    return render_template(
        'tutorial_detalhe.html',
        tutorial=tutorial,
        comentario_form=comentario_form,
        feedback_form=feedback_form,
        visualizacoes_labels=json.dumps(visualizacoes_labels),
        visualizacoes_values=json.dumps(visualizacoes_values),
        feedback_data=json.dumps(feedback_data),
        conteudo_markdown=conteudo_markdown
    )

@bp.route('/tutoriais/<int:tutorial_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    # Apenas membros da equipe de TI ou administradores podem editar tutoriais
    if not (session.get('is_ti') or session.get('is_admin')) or (not session.get('is_admin') and tutorial.autor_id != session.get('user_id')):
        flash('Apenas o autor TI ou administradores podem editar este tutorial.', 'danger')
        return redirect(url_for('main.detalhe_tutorial', tutorial_id=tutorial.id))
    form = TutorialForm(obj=tutorial)
    if form.validate_on_submit():
        tutorial.titulo = form.titulo.data
        tutorial.conteudo = form.conteudo.data
        tutorial.categoria = form.categoria.data
        # Upload de novas imagens
        if form.imagem.data:
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file = form.imagem.data
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                img = TutorialImage(tutorial_id=tutorial.id, filename=filename)
                db.session.add(img)
        db.session.commit()
        flash('Tutorial atualizado com sucesso!', 'success')
        return redirect(url_for('main.detalhe_tutorial', tutorial_id=tutorial.id))
    return render_template('tutorial_form.html', form=form, title='Editar Tutorial')

@bp.route('/tutoriais/<int:tutorial_id>/excluir', methods=['POST'])
@login_required
def excluir_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    # Apenas membros da equipe de TI ou administradores podem excluir tutoriais
    if not (session.get('is_ti') or session.get('is_admin')) or (not session.get('is_admin') and tutorial.autor_id != session.get('user_id')):
        flash('Apenas o autor TI ou administradores podem excluir este tutorial.', 'danger')
        return redirect(url_for('main.detalhe_tutorial', tutorial_id=tutorial.id))
    # Excluir imagens do disco
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    for img in tutorial.imagens:
        img_path = os.path.join(upload_folder, img.filename)
        if os.path.exists(img_path):
            os.remove(img_path)
        db.session.delete(img)
    db.session.delete(tutorial)
    db.session.commit()
    flash('Tutorial excluído com sucesso!', 'success')
    return redirect(url_for('main.listar_tutoriais'))

@bp.route('/tutoriais/<int:tutorial_id>/comentar', methods=['POST'])
@login_required
def comentar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    feedback_form = FeedbackTutorialForm()
    if comentario_form.validate_on_submit():
        comentario = ComentarioTutorial(
            tutorial_id=tutorial.id,
            usuario_id=session.get('user_id'),
            texto=comentario_form.texto.data
        )
        db.session.add(comentario)
        db.session.commit()
        flash('Comentário enviado com sucesso!', 'success')
        return redirect(url_for('main.detalhe_tutorial', tutorial_id=tutorial.id))
    else:
        flash('Erro ao enviar comentário.', 'danger')
        # Renderiza o template com os formulários em caso de erro
        return render_template('tutorial_detalhe.html', tutorial=tutorial, comentario_form=comentario_form, feedback_form=feedback_form)

@bp.route('/tutoriais/<int:tutorial_id>/feedback', methods=['POST'])
@login_required
def feedback_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    comentario_form = ComentarioTutorialForm()
    form = FeedbackTutorialForm()
    if form.validate_on_submit():
        feedback_existente = FeedbackTutorial.query.filter_by(tutorial_id=tutorial.id, usuario_id=session.get('user_id')).first()
        if not feedback_existente:
            feedback = FeedbackTutorial(
                tutorial_id=tutorial.id,
                usuario_id=session.get('user_id'),
                util=form.util.data
            )
            db.session.add(feedback)
            db.session.commit()
            flash('Feedback registrado!', 'success')
        else:
            flash('Você já enviou feedback para este tutorial.', 'info')
        return redirect(url_for('main.detalhe_tutorial', tutorial_id=tutorial.id))
    else:
        flash('Erro ao enviar feedback.', 'danger')
        # Renderiza o template com os formulários em caso de erro
        return render_template('tutorial_detalhe.html', tutorial=tutorial, comentario_form=comentario_form, feedback_form=form)

@bp.route('/tutoriais/<int:tutorial_id>/pdf')
@login_required
def exportar_tutorial_pdf(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, y, tutorial.titulo)
    y -= 30
    p.setFont('Helvetica', 12)
    p.drawString(40, y, f'Categoria: {tutorial.categoria or "Sem categoria"}')
    y -= 20
    p.drawString(40, y, f'Autor: {tutorial.autor.username}')
    y -= 20
    p.drawString(40, y, f'Data: {tutorial.data_criacao.strftime("%d/%m/%Y %H:%M")}')
    y -= 30
    p.setFont('Helvetica', 12)
    conteudo = tutorial.conteudo.replace('\r', '').split('\n')
    for linha in conteudo:
        if y < 60:
            p.showPage()
            y = height - 40
            p.setFont('Helvetica', 12)
        p.drawString(40, y, linha[:110])
        y -= 18
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'tutorial_{tutorial.id}.pdf', mimetype='application/pdf')


# ========================================
# ROTAS PARA CONTROLE DE EQUIPAMENTOS
# ========================================

@bp.route('/equipment/list')
@login_required
def list_equipment():
    """Lista todas as solicitações de equipamentos"""
    # Filtros
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    # Query base
    if session.get('is_admin') or session.get('is_ti'):
        # TI/Admin vê todas as solicitações
        query = EquipmentRequest.query
    else:
        # Usuário comum vê apenas suas solicitações
        query = EquipmentRequest.query.filter_by(requester_id=session.get('user_id'))

    # Aplicar filtros
    if status_filter:
        query = query.filter(EquipmentRequest.status == status_filter)

    if search:
        query = query.filter(
            db.or_(
                EquipmentRequest.description.contains(search),
                EquipmentRequest.patrimony.contains(search),
                EquipmentRequest.equipment_type.contains(search)
            )
        )

    # Ordenar por data de solicitação (mais recente primeiro)
    equipment_requests = query.order_by(EquipmentRequest.request_date.desc()).all()

    return render_template('equipment_list.html',
                         equipment_requests=equipment_requests,
                         status_filter=status_filter,
                         search=search)


@bp.route('/equipment/new', methods=['GET', 'POST'])
@login_required
def new_equipment_request():
    """Nova solicitação de equipamento"""
    if request.method == 'POST':
        # Validar dados
        description = request.form.get('description', '').strip()
        patrimony = request.form.get('patrimony', '').strip()
        equipment_type = request.form.get('equipment_type', '').strip()
        destination_sector = request.form.get('destination_sector', '').strip()
        request_reason = request.form.get('request_reason', '').strip()
        delivery_date_str = request.form.get('delivery_date', '').strip()
        observations = request.form.get('observations', '').strip()

        if not description:
            flash('Descrição é obrigatória.', 'danger')
            return render_template('equipment_form.html')

        if not request_reason:
            flash('Motivo da solicitação é obrigatório.', 'danger')
            return render_template('equipment_form.html')

        if not destination_sector:
            flash('Setor/Destino é obrigatório.', 'danger')
            return render_template('equipment_form.html')

        # Converter data se fornecida
        delivery_date = None
        if delivery_date_str:
            try:
                delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de entrega inválida.', 'danger')
                return render_template('equipment_form.html')

        # Criar solicitação
        equipment_request = EquipmentRequest(
            description=description,
            patrimony=patrimony if patrimony else None,
            equipment_type=equipment_type if equipment_type else None,
            destination_sector=destination_sector if destination_sector else None,
            request_reason=request_reason if request_reason else None,
            delivery_date=delivery_date,
            observations=observations if observations else None,
            requester_id=session.get('user_id'),
            status='Solicitado'
        )

        db.session.add(equipment_request)
        db.session.commit()

        flash('Solicitação de equipamento criada com sucesso!', 'success')
        return redirect(url_for('main.list_equipment'))

    return render_template('equipment_form.html')


@bp.route('/equipment/<int:id>')
@login_required
def equipment_detail(id):
    """Detalhes de uma solicitação de equipamento"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not (session.get('is_admin') or session.get('is_ti') or
            equipment_request.requester_id == session.get('user_id')):
        flash('Você não tem permissão para ver esta solicitação.', 'danger')
        return redirect(url_for('main.list_equipment'))

    return render_template('equipment_detail.html', equipment_request=equipment_request)


@bp.route('/equipment/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_equipment_request(id):
    """Editar solicitação de equipamento"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_edited_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para editar esta solicitação.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if request.method == 'POST':
        # Validar dados
        description = request.form.get('description', '').strip()
        patrimony = request.form.get('patrimony', '').strip()
        equipment_type = request.form.get('equipment_type', '').strip()
        destination_sector = request.form.get('destination_sector', '').strip()
        request_reason = request.form.get('request_reason', '').strip()
        delivery_date_str = request.form.get('delivery_date', '').strip()
        observations = request.form.get('observations', '').strip()

        if not description:
            flash('Descrição é obrigatória.', 'danger')
            return render_template('equipment_form.html', equipment_request=equipment_request)

        if not request_reason:
            flash('Motivo da solicitação é obrigatório.', 'danger')
            return render_template('equipment_form.html', equipment_request=equipment_request)

        if not destination_sector:
            flash('Setor/Destino é obrigatório.', 'danger')
            return render_template('equipment_form.html', equipment_request=equipment_request)

        # Converter data se fornecida
        delivery_date = None
        if delivery_date_str:
            try:
                delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de entrega inválida.', 'danger')
                return render_template('equipment_form.html', equipment_request=equipment_request)

        # Atualizar dados
        equipment_request.description = description
        equipment_request.patrimony = patrimony if patrimony else None
        equipment_request.equipment_type = equipment_type if equipment_type else None
        equipment_request.destination_sector = destination_sector if destination_sector else None
        equipment_request.request_reason = request_reason if request_reason else None
        equipment_request.delivery_date = delivery_date
        equipment_request.observations = observations if observations else None

        db.session.commit()

        flash('Solicitação atualizada com sucesso!', 'success')
        return redirect(url_for('main.equipment_detail', id=id))

    return render_template('equipment_form.html', equipment_request=equipment_request)


@bp.route('/equipment/<int:id>/approve', methods=['POST'])
@login_required
def approve_equipment_request(id):
    """Aprovar solicitação de equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para aprovar solicitações.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if equipment_request.status != 'Solicitado':
        flash('Apenas solicitações pendentes podem ser aprovadas.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    # Aprovar solicitação
    equipment_request.status = 'Aprovado'
    equipment_request.approved_by_id = session.get('user_id')
    equipment_request.approval_date = datetime.utcnow()

    db.session.commit()

    flash('Solicitação aprovada com sucesso!', 'success')
    return redirect(url_for('main.equipment_detail', id=id))


@bp.route('/equipment/<int:id>/reject', methods=['POST'])
@login_required
def reject_equipment_request(id):
    """Recusar solicitação de equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para recusar solicitações.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if equipment_request.status != 'Solicitado':
        flash('Apenas solicitações pendentes podem ser recusadas.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    # Recusar solicitação
    equipment_request.status = 'Negado'
    equipment_request.approved_by_id = session.get('user_id')
    equipment_request.approval_date = datetime.utcnow()

    db.session.commit()

    flash('Solicitação recusada.', 'warning')
    return redirect(url_for('main.equipment_detail', id=id))


@bp.route('/equipment/<int:id>/deliver', methods=['POST'])
@login_required
def deliver_equipment_request(id):
    """Marcar equipamento como entregue (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para marcar como entregue.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if equipment_request.status != 'Aprovado':
        flash('Apenas solicitações aprovadas podem ser marcadas como entregues.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    # Marcar como entregue
    equipment_request.status = 'Entregue'
    equipment_request.received_by_id = session.get('user_id')
    equipment_request.delivery_date = datetime.utcnow().date()

    db.session.commit()

    flash('Equipamento marcado como entregue!', 'success')
    return redirect(url_for('main.equipment_detail', id=id))


@bp.route('/equipment/<int:id>/return', methods=['POST'])
@login_required
def return_equipment_request(id):
    """Marcar equipamento como devolvido (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para marcar como devolvido.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if equipment_request.status != 'Entregue':
        flash('Apenas equipamentos entregues podem ser marcados como devolvidos.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    # Marcar como devolvido
    equipment_request.status = 'Devolvido'
    equipment_request.return_date = datetime.utcnow().date()

    db.session.commit()

    flash('Equipamento marcado como devolvido!', 'success')
    return redirect(url_for('main.equipment_detail', id=id))


@bp.route('/equipment/<int:id>/fill_technical', methods=['GET', 'POST'])
@login_required
def fill_technical_data(id):
    """Preencher dados técnicos do equipamento (TI/Admin)"""
    equipment_request = EquipmentRequest.query.get_or_404(id)

    # Verificar permissão
    if not equipment_request.can_be_approved_by(User.query.get(session.get('user_id'))):
        flash('Você não tem permissão para preencher dados técnicos.', 'danger')
        return redirect(url_for('main.equipment_detail', id=id))

    if request.method == 'POST':
        # Validar dados
        patrimony = request.form.get('patrimony', '').strip()
        equipment_type = request.form.get('equipment_type', '').strip()
        delivery_date_str = request.form.get('delivery_date', '').strip()
        conference_status = request.form.get('conference_status', '').strip()

        # Atualizar dados técnicos
        equipment_request.patrimony = patrimony if patrimony else None
        equipment_request.equipment_type = equipment_type if equipment_type else None
        equipment_request.conference_status = conference_status if conference_status else None

        # Converter data se fornecida
        if delivery_date_str:
            try:
                equipment_request.delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de entrega inválida.', 'danger')
                return render_template('equipment_technical_form.html', equipment_request=equipment_request)

        db.session.commit()

        flash('Dados técnicos atualizados com sucesso!', 'success')
        return redirect(url_for('main.equipment_detail', id=id))

    return render_template('equipment_technical_form.html', equipment_request=equipment_request)




@bp.route('/install-pwa')
def install_pwa():
    """Página de instruções para instalação PWA"""
    return render_template('install_pwa.html')

@bp.route('/offline')
def offline():
    """Página offline"""
    return render_template('offline.html')

@bp.route('/test-notification')
@login_required
def test_notification():
    """Endpoint para testar notificações"""
    return jsonify({
        'reminders_expiring': [{
            'id': 999,
            'name': 'Teste de Notificação',
            'responsible': 'Sistema',
            'days_left': 1
        }],
        'chamados_updated': [],
        'tasks_overdue': []
    })

@bp.route('/api/notifications')
def api_notifications():
    """Endpoint para API de notificações usado pelo notifications.js"""
    # Verificar se o usuário está autenticado
    if 'user_id' not in session:
        return jsonify({
            'error': 'Não autenticado',
            'reminders_expiring': [],
            'chamados_updated': [],
            'tasks_overdue': []
        }), 200  # Retornar código 200 em vez de redirecionar
        
    # Verificar lembretes próximos do vencimento (7 dias)
    user_id = session.get('user_id')
    today = date.today()
    
    # Lembretes vencendo em até 7 dias
    if session.get('is_admin'):
        reminders_expiring = Reminder.query.filter(
            Reminder.due_date >= today,
            Reminder.due_date <= today + timedelta(days=7),
            Reminder.completed == False,
            Reminder.status == 'ativo'
        ).all()
    else:
        reminders_expiring = Reminder.query.filter(
            Reminder.due_date >= today,
            Reminder.due_date <= today + timedelta(days=7),
            Reminder.completed == False,
            Reminder.status == 'ativo',
            Reminder.user_id == user_id
        ).all()
    
    # Tarefas vencidas
    if session.get('is_admin'):
        tasks_overdue = Task.query.filter(
            Task.date < today,
            Task.completed == False
        ).all()
    else:
        tasks_overdue = Task.query.filter(
            Task.date < today,
            Task.completed == False,
            Task.user_id == user_id
        ).all()
    
    # Chamados atualizados recentemente (últimas 24h)
    yesterday = datetime.now() - timedelta(days=1)
    
    if session.get('is_admin') or session.get('is_ti'):
        # Administradores e equipe de TI veem todos os chamados atualizados
        chamados_updated = Chamado.query.filter(
            Chamado.data_ultima_atualizacao >= yesterday,
            Chamado.status != 'Fechado'
        ).all()
    else:
        # Usuários normais veem apenas seus próprios chamados atualizados
        chamados_updated = Chamado.query.filter(
            Chamado.data_ultima_atualizacao >= yesterday,
            Chamado.solicitante_id == user_id,
            Chamado.status != 'Fechado'
        ).all()
    
    return jsonify({
        'reminders_expiring': [{
            'id': r.id,
            'name': r.name,
            'responsible': r.responsible,
            'days_left': (r.due_date - today).days
        } for r in reminders_expiring],
        'chamados_updated': [{
            'id': c.id,
            'titulo': c.titulo,
            'status': c.status,
            'prioridade': c.prioridade,
            'solicitante': c.solicitante.username if c.solicitante else 'Desconhecido'
        } for c in chamados_updated],
        'tasks_overdue': [{
            'id': t.id,
            'name': t.description,
            'days_overdue': (today - t.date).days
        } for t in tasks_overdue]
    })

@bp.route('/demo-components')
@login_required
def demo_components():
    """Página de demonstração dos novos componentes implementados"""
    return render_template('demo_components.html')
