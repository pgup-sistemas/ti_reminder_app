from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .models import Reminder, Task, Sector, User, db
from .forms import ReminderForm, TaskForm
from .auth_utils import login_required
from functools import wraps

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
    from .models import Chamado
    
    search = request.args.get('search', '').strip().lower()
    status = request.args.get('status', '').strip().lower()
    
    # --- Recorrência automática de lembretes ---
    if session.get('is_admin'):
        reminders = Reminder.query.all()
    else:
        reminders = Reminder.query.filter_by(user_id=session.get('user_id')).all()
    
    # Recorrência automática
    for r in reminders:
        if r.due_date < date.today() and not r.notified:
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
                user_id=r.user_id
            )
            db.session.add(novo)
            r.notified = True  # marca o lembrete antigo para não duplicar
            db.session.commit()
    
    # Consulta de lembretes e tarefas
    if session.get('is_admin'):
        reminders_count = Reminder.query.count()
        reminders_today = Reminder.query.filter(Reminder.due_date <= date.today()).all()
        tasks_today = Task.query.filter(Task.date <= date.today()).all()
        # Buscar chamados abertos (não fechados)
        chamados_abertos = Chamado.query.filter(
            Chamado.status != 'Fechado'
        ).order_by(
            Chamado.data_abertura.desc()
        ).limit(10).all()  # Limita a 10 chamados mais recentes
    else:
        user_id = session.get('user_id')
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
    
    return render_template(
        'index.html',
        reminders_count=reminders_count,
        reminders_today_pend=reminders_today_pend,
        reminders_today_done=reminders_today_done,
        tasks_today_pend=tasks_today_pend,
        tasks_today_done=tasks_today_done,
        chamados_abertos=chamados_abertos,
        is_admin=session.get('is_admin', False)
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
            user_id=session.get('user_id')
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
    from datetime import datetime # Adicionado datetime

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

    # Filtros
    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)

    if not is_admin:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
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
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)

    if user_id and is_admin: # Admin pode filtrar por qualquer usuário
        task_query = task_query.filter(Task.user_id == user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id)

    # Totais
    tasks_all = task_query.all()
    reminders_all = reminder_query.all()
    chamados_all = chamado_query.all()

    tasks_total = len(tasks_all)
    reminders_total = len(reminders_all)
    chamados_total = len(chamados_all)

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
    for idx, m in enumerate(meses):
        prox = (m + relativedelta(months=1))
        tarefas_mes = [t for t in tasks_all if t.date >= m and t.date < prox]
        tarefas_por_mes[idx] = len(tarefas_mes)
        tarefas_concluidas_por_mes[idx] = len([t for t in tarefas_mes if t.completed])
        lembretes_mes = [r for r in reminders_all if r.due_date >= m and r.due_date < prox]
        lembretes_por_mes[idx] = len(lembretes_mes)
        lembretes_realizados_por_mes[idx] = len([r for r in lembretes_mes if r.completed])
        # Adicionar lógica para chamados por mês se necessário

    # --- Dados para Gráfico de Barra (por setor) ---
    setores_labels = [s.name for s in sectors]
    tarefas_por_setor = [len([t for t in tasks_all if t.sector_id == s.id]) for s in sectors]
    lembretes_por_setor = [len([r for r in reminders_all if r.sector_id == s.id]) for s in sectors]
    chamados_por_setor = [len([c for c in chamados_all if c.setor_id == s.id]) for s in sectors] # Novo

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
        sectors=sectors,
        users=users,
        selected_sector=sector_id,
        selected_user=user_id,
        meses_labels=meses_labels,
        tarefas_por_mes=tarefas_por_mes,
        tarefas_concluidas_por_mes=tarefas_concluidas_por_mes,
        lembretes_por_mes=lembretes_por_mes,
        lembretes_realizados_por_mes=lembretes_realizados_por_mes,
        setores_labels=setores_labels,
        tarefas_por_setor=tarefas_por_setor,
        lembretes_por_setor=lembretes_por_setor,
        chamados_por_setor=chamados_por_setor # Novo
    )

@bp.route('/export/excel')
def export_excel():
    from flask import request, session # session já estava importado globalmente, mas garantindo
    from .models import Task, Reminder, Chamado, Sector, User # Adicionado Chamado, Sector, User
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

    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)

    # Filtros
    if not is_admin:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)
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
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)

    if user_id_filter and is_admin: # Admin pode filtrar por qualquer usuário
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)

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
                'Usuário': t.user.username if t.user else '',
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
                'Usuário': r.user.username if r.user else '',
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
                'Solicitante': c.solicitante.username if c.solicitante else '',
                'Setor': c.setor.name if c.setor else '',
                'Responsável TI': c.responsavel_ti.username if c.responsavel_ti else ''
            } for c in chamados]
            df_chamados = pd.DataFrame(chamados_data)
            df_chamados.to_excel(writer, sheet_name='Chamados', index=False, header=False, startrow=1)
            worksheet_chamados = writer.sheets['Chamados']
            worksheet_chamados.merge_range('A1:H1', 'Relatório de Chamados', title_format)
            for col_num, value in enumerate(df_chamados.columns.values):
                worksheet_chamados.write(0, col_num, value, header_format)
            for i, col in enumerate(df_chamados.columns):
                column_len = max(df_chamados[col].astype(str).map(len).max(), len(col))
                worksheet_chamados.set_column(i, i, column_len + 2)

    output.seek(0)
    # Forçar mimetype correto para navegadores modernos
    return send_file(
        output,
        download_name='relatorio_reminder.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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

    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)

    if not is_admin:
        task_query = task_query.filter(Task.user_id == current_user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == current_user_id)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == current_user_id)

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
    if end_date:
        task_query = task_query.filter(Task.date <= end_date)
        reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        chamado_query = chamado_query.filter(Chamado.data_abertura <= end_date)

    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
        chamado_query = chamado_query.filter(Chamado.setor_id == sector_id)

    if user_id_filter and is_admin:
        task_query = task_query.filter(Task.user_id == user_id_filter)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id_filter)
        chamado_query = chamado_query.filter(Chamado.solicitante_id == user_id_filter)

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
    elements.append(Paragraph("Relatório Geral - TI Reminder", styles['h1']))
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
                    Paragraph(t.user.username if t.user else '', normal_style),
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
                    Paragraph(r.user.username if r.user else '', normal_style),
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
        elements.append(Spacer(1, 0.3*inch))

    if not elements or all(isinstance(el, (Paragraph, Spacer)) and "Nenhum" in el.text for el in elements if isinstance(el, Paragraph)):
         elements.append(Paragraph("Nenhum dado para exportar com os filtros selecionados.", styles['Normal']))

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
    if search:
        query = query.filter(Task.description.ilike(f'%{search}%'))
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
    
    # 1. Verifica se o usuário tem um setor atribuído diretamente (se o modelo permitir)
    if hasattr(user, 'setor') and user.setor:
        setor_usuario = user.setor
    # 2. Verifica em lembretes do usuário
    elif hasattr(user, 'lembretes') and user.lembretes:
        for lembrete in user.lembretes:
            if hasattr(lembrete, 'setor') and lembrete.setor:
                setor_usuario = lembrete.setor
                break
    # 3. Verifica em tarefas do usuário
    elif hasattr(user, 'tarefas') and user.tarefas:
        for tarefa in user.tarefas:
            if hasattr(tarefa, 'setor') and tarefa.setor:
                setor_usuario = tarefa.setor
                break
    
    if request.method == 'POST' and form.validate_on_submit():
        if not setor_usuario:
            flash('Não foi possível determinar o setor do usuário. Contate o administrador.', 'danger')
            return render_template('abrir_chamado.html', form=form, title='Abrir Novo Chamado', setor_usuario=setor_usuario)
        
        try:
            novo_chamado = Chamado(
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                prioridade=form.prioridade.data,
                solicitante_id=user_id,
                setor_id=setor_usuario.id,
                status='Aberto'  # Status inicial
            )
            
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
    setor_filter = request.args.get('setor_id', type=int)

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
    from .models import Chamado, ComentarioChamado, db
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



