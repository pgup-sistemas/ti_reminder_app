from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .models import Reminder, Task, Sector, db
from .forms import ReminderForm, TaskForm
from .auth_utils import login_required
from . import db
from datetime import date
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
    if session.get('is_admin'):
        reminders_count = Reminder.query.count()
        reminders_today = Reminder.query.filter(Reminder.due_date <= date.today()).all()
        tasks_today = Task.query.filter(Task.date <= date.today()).all()
    else:
        reminders_count = Reminder.query.filter_by(user_id=session.get('user_id')).count()
        reminders_today = Reminder.query.filter(Reminder.due_date <= date.today(), Reminder.user_id == session.get('user_id')).all()
        tasks_today = Task.query.filter(Task.date <= date.today(), Task.user_id == session.get('user_id')).all()
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
        tasks_today_done=tasks_today_done
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

@bp.route('/reminders/json')
def reminders_json():
    reminders = Reminder.query.all()
    reminders_list = []
    for r in reminders:
        # status logic replicada do template
        if r.completed:
            status = 'completed'
        elif r.due_date < date.today():
            status = 'expired'
        elif r.due_date == date.today():
            status = 'ok'
        else:
            status = 'alert'
        reminders_list.append({
            'id': r.id,
            'name': r.name,
            'type': r.type,
            'due_date': r.due_date.strftime('%Y-%m-%d'),
            'responsible': r.responsible,
            'frequency': r.frequency,
            'completed': r.completed,
            'status': status,
            'sector': r.sector.name if r.sector else ''
        })
    return {'reminders': reminders_list}

from flask import request

@bp.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    # Admin pode ver todos os lembretes, usuários comuns só os próprios
    if session.get('is_admin'):
        query = Reminder.query
    else:
        query = Reminder.query.filter_by(user_id=session.get('user_id'))
    reminders_paginated = query.order_by(Reminder.due_date.desc()).paginate(page=page, per_page=per_page)
    reminders = reminders_paginated.items
    # Recorrência automática: cria novo lembrete se vencido e for mensal/anual
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
                next_due = None
            if next_due:
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
    # Status por cor
    for r in reminders:
        if r.due_date < date.today():
            r.status = 'expired'
        elif (r.due_date - date.today()).days <= 3:
            r.status = 'alert'
        else:
            r.status = 'ok'
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
    return render_template('reminders.html', reminders=reminders, form=form, pagination=reminders_paginated)

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
    from .models import User
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = bool(request.form.get('is_admin'))
        user.username = username
        user.email = email
        user.is_admin = is_admin
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('main.users_admin'))
    return render_template('edit_user.html', user=user)

@bp.route('/admin/users/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    from .models import User
    user = User.query.get_or_404(id)
    user.ativo = not user.ativo
    db.session.commit()
    flash('Status do usuário atualizado!', 'success')
    return redirect(url_for('main.users_admin'))

@bp.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    from .models import User
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('main.users_admin'))

# --- Rotas principais ---

@bp.route('/dashboard')
def dashboard():
    from flask import request
    from .models import Sector, User
    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id = request.args.get('user_id', type=int)
    # Listas para filtros
    sectors = Sector.query.order_by(Sector.name).all()
    users = User.query.order_by(User.username).all()
    task_query = Task.query
    reminder_query = Reminder.query
    # Filtros
    if not session.get('is_admin'):
        task_query = task_query.filter(Task.user_id == session.get('user_id'))
        reminder_query = reminder_query.filter(Reminder.user_id == session.get('user_id'))
    if task_status == 'done':
        task_query = task_query.filter(Task.completed == True)
    elif task_status == 'pending':
        task_query = task_query.filter(Task.completed == False)
    if reminder_status == 'done':
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == 'pending':
        reminder_query = reminder_query.filter(Reminder.completed == False)
    if start_date:
        try:
            task_query = task_query.filter(Task.date >= start_date)
            reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        except:
            pass
    if end_date:
        try:
            task_query = task_query.filter(Task.date <= end_date)
            reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        except:
            pass
    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
    if user_id:
        task_query = task_query.filter(Task.user_id == user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id)
    # Totais
    tasks_total = task_query.count()
    reminders_total = reminder_query.count()
    tasks = task_query.all()
    reminders = reminder_query.all()
    tasks_done = len([t for t in tasks if t.completed])
    tasks_pending = len([t for t in tasks if not t.completed])
    tasks_expired = len([t for t in tasks if not t.completed and t.date < date.today()])
    reminders_done = len([r for r in reminders if r.completed])
    reminders_pending = len([r for r in reminders if not r.completed])

    # --- Dados para Gráficos de Linha (por mês, últimos 12 meses) ---
    from collections import OrderedDict
    from datetime import timedelta
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
        tarefas_mes = [t for t in tasks if t.date >= m and t.date < prox]
        tarefas_por_mes[idx] = len(tarefas_mes)
        tarefas_concluidas_por_mes[idx] = len([t for t in tarefas_mes if t.completed])
        lembretes_mes = [r for r in reminders if r.due_date >= m and r.due_date < prox]
        lembretes_por_mes[idx] = len(lembretes_mes)
        lembretes_realizados_por_mes[idx] = len([r for r in lembretes_mes if r.completed])

    # --- Dados para Gráfico de Barra (por setor) ---
    setores_labels = [s.name for s in sectors]
    tarefas_por_setor = [len([t for t in tasks if t.sector_id == s.id]) for s in sectors]
    lembretes_por_setor = [len([r for r in reminders if r.sector_id == s.id]) for s in sectors]

    return render_template('dashboard.html',
        tasks_total=tasks_total,
        tasks_done=tasks_done,
        tasks_pending=tasks_pending,
        tasks_expired=tasks_expired,
        reminders_total=reminders_total,
        reminders_done=reminders_done,
        reminders_pending=reminders_pending,
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
        lembretes_por_setor=lembretes_por_setor
    )

@bp.route('/export/excel')
def export_excel():
    from flask import request
    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id = request.args.get('user_id', type=int)
    task_query = Task.query
    reminder_query = Reminder.query
    # Filtros iguais ao dashboard
    if not session.get('is_admin'):
        task_query = task_query.filter(Task.user_id == session.get('user_id'))
        reminder_query = reminder_query.filter(Reminder.user_id == session.get('user_id'))
    if task_status == 'done':
        task_query = task_query.filter(Task.completed == True)
    elif task_status == 'pending':
        task_query = task_query.filter(Task.completed == False)
    if reminder_status == 'done':
        reminder_query = reminder_query.filter(Reminder.completed == True)
    elif reminder_status == 'pending':
        reminder_query = reminder_query.filter(Reminder.completed == False)
    if start_date:
        try:
            task_query = task_query.filter(Task.date >= start_date)
            reminder_query = reminder_query.filter(Reminder.due_date >= start_date)
        except:
            pass
    if end_date:
        try:
            task_query = task_query.filter(Task.date <= end_date)
            reminder_query = reminder_query.filter(Reminder.due_date <= end_date)
        except:
            pass
    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
    if user_id:
        task_query = task_query.filter(Task.user_id == user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id)
    tasks = task_query.all()
    reminders = reminder_query.all()
    export_type = request.args.get('export_type', 'all')
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        # Adiciona título na primeira planilha
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        # Tarefas
        if export_type in ['all', 'tasks']:
            tasks_data = [{
                'Descrição': t.description,
                'Data': t.date.strftime('%Y-%m-%d'),
                'Responsável': t.responsible,
                'Setor': t.sector.name if t.sector else '',
                'Usuário': t.user.username if t.user else '',
                'Concluída': 'Sim' if t.completed else 'Não'
            } for t in tasks]
            df_tasks = pd.DataFrame(tasks_data)
            df_tasks.to_excel(writer, sheet_name='Tarefas', index=False, startrow=2)
            worksheet = writer.sheets['Tarefas']
            worksheet.merge_range('A1:F1', 'Relatório de Tarefas e Lembretes', title_format)
        # Lembretes
        if export_type in ['all', 'reminders']:
            reminders_data = [{
                'Nome': r.name,
                'Tipo': r.type,
                'Data': r.due_date.strftime('%Y-%m-%d'),
                'Responsável': r.responsible,
                'Setor': r.sector.name if r.sector else '',
                'Usuário': r.user.username if r.user else '',
                'Realizado': 'Sim' if r.completed else 'Não'
            } for r in reminders]
            df_reminders = pd.DataFrame(reminders_data)
            df_reminders.to_excel(writer, sheet_name='Lembretes', index=False, startrow=2)
            worksheet = writer.sheets['Lembretes']
            worksheet.merge_range('A1:G1', 'Relatório de Tarefas e Lembretes', title_format)
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
    from flask import request, session
    task_status = request.args.get('task_status', '')
    reminder_status = request.args.get('reminder_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sector_id = request.args.get('sector_id', type=int)
    user_id = request.args.get('user_id', type=int)
    task_query = Task.query
    reminder_query = Reminder.query
    # Permissão: usuários comuns só exportam seus próprios dados
    if not session.get('is_admin'):
        task_query = task_query.filter(Task.user_id == session.get('user_id'))
        reminder_query = reminder_query.filter(Reminder.user_id == session.get('user_id'))
    # Admin pode filtrar por setor ou usuário
    if sector_id:
        task_query = task_query.filter(Task.sector_id == sector_id)
        reminder_query = reminder_query.filter(Reminder.sector_id == sector_id)
    if user_id:
        task_query = task_query.filter(Task.user_id == user_id)
        reminder_query = reminder_query.filter(Reminder.user_id == user_id)
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
    if start_date:
        try:
            sd = date.fromisoformat(start_date)
            task_query = task_query.filter(Task.date >= sd)
            reminder_query = reminder_query.filter(Reminder.due_date >= sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = date.fromisoformat(end_date)
            task_query = task_query.filter(Task.date <= ed)
            reminder_query = reminder_query.filter(Reminder.due_date <= ed)
        except Exception:
            pass
    tasks = task_query.all()
    reminders = reminder_query.all()
    export_type = request.args.get('export_type', 'all')
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    # Título geral
    p.setFont('Helvetica-Bold', 18)
    p.drawString(40, y, 'Relatório de Tarefas e Lembretes')
    y -= 35
    if export_type in ['all', 'tasks']:
        p.setFont('Helvetica-Bold', 14)
        p.drawString(40, y, 'Relatório de Tarefas')
        y -= 25
        p.setFont('Helvetica', 10)
        for t in tasks:
            p.drawString(40, y, f"{t.description} | {t.date.strftime('%Y-%m-%d')} | {t.responsible} | {'Concluída' if t.completed else 'Pendente'}")
            y -= 15
            if y < 60:
                p.showPage()
                y = height - 40
                p.setFont('Helvetica-Bold', 18)
                p.drawString(40, y, 'Relatório de Tarefas e Lembretes')
                y -= 35
                p.setFont('Helvetica-Bold', 14)
                p.drawString(40, y, 'Relatório de Tarefas')
                y -= 25
                p.setFont('Helvetica', 10)
        y -= 20
    if export_type in ['all', 'reminders']:
        p.setFont('Helvetica-Bold', 14)
        p.drawString(40, y, 'Relatório de Lembretes')
        y -= 25
        p.setFont('Helvetica', 10)
        for r in reminders:
            p.drawString(40, y, f"{r.name} | {r.due_date.strftime('%Y-%m-%d')} | {r.responsible} | {'Realizado' if r.completed else 'Pendente'}")
            y -= 15
            if y < 60:
                p.showPage()
                y = height - 40
    p.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='relatorio_reminder.pdf',
        mimetype='application/pdf'
    )

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
