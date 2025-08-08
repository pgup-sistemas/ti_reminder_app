# 📋 Plano de Ação - Implementação de Melhorias

## 🎯 Visão Geral
Este documento define o plano de implementação das funcionalidades restantes do sistema TI OSN System, organizadas por prioridade e dependências.

---

## 🚀 FASE 1: CONTROLE DE LEMBRETES (Prioridade ALTA)

### **Objetivo**: Completar a funcionalidade de controle de lembretes recorrentes

#### **1.1 Atualizar Lógica de Recorrência**
**Arquivo**: `app/routes.py` - Função `index()`
**Tempo Estimado**: 2 horas

```python
# ATUAL (linhas 40-65)
for r in reminders:
    if r.due_date < date.today() and not r.notified:
        # ... lógica existente ...

# NOVO
for r in reminders:
    if (r.due_date < date.today() and 
        not r.notified and 
        r.frequency and 
        r.status == 'ativo' and
        (not r.end_date or r.end_date > date.today()) and
        (not r.pause_until or r.pause_until <= date.today())):
        # ... lógica de criação ...
        novo = Reminder(
            # ... campos existentes ...
            status=r.status,
            pause_until=r.pause_until,
            end_date=r.end_date,
        )
```

#### **1.2 Adicionar Rota de Controle de Status**
**Arquivo**: `app/routes.py`
**Tempo Estimado**: 1 hora

```python
@bp.route('/reminders/toggle_status/<int:id>', methods=['POST'])
@login_required
def toggle_reminder_status(id):
    if session.get('is_admin'):
        reminder = Reminder.query.get_or_404(id)
    else:
        reminder = Reminder.query.filter_by(id=id, user_id=session.get('user_id')).first_or_404()
    
    if reminder.status == 'ativo':
        reminder.status = 'pausado'
        flash('Lembrete pausado!', 'warning')
    elif reminder.status == 'pausado':
        reminder.status = 'ativo'
        reminder.pause_until = None
        flash('Lembrete reativado!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.reminders'))
```

#### **1.3 Atualizar Formulário de Lembretes**
**Arquivo**: `app/forms.py`
**Tempo Estimado**: 30 minutos

```python
class ReminderForm(FlaskForm):
    # ... campos existentes ...
    status = SelectField('Status', choices=[
        ('ativo','Ativo'),
        ('pausado','Pausado'),
        ('cancelado','Cancelado')
    ], default='ativo')
    pause_until = DateField('Pausar até', validators=[Optional()])
    end_date = DateField('Data de fim', validators=[Optional()])
```

#### **1.4 Atualizar Template de Lembretes**
**Arquivo**: `app/templates/reminders.html`
**Tempo Estimado**: 1 hora

```html
<!-- Adicionar botões de controle -->
<td>
    <form method="POST" action="/reminders/toggle_status/{{ reminder.id }}" class="d-inline">
        <button type="submit" class="btn btn-sm btn-{{ 'success' if reminder.status == 'pausado' else 'warning' }}"
                title="{{ 'Reativar' if reminder.status == 'pausado' else 'Pausar' }}">
            <i class="fas fa-{{ 'play' if reminder.status == 'pausado' else 'pause' }}"></i>
        </button>
    </form>
</td>
```

**📅 Cronograma Fase 1**: 1 dia
**🎯 Entregável**: Controle completo de lembretes recorrentes

---

## 🔒 FASE 2: SEGURANÇA AVANÇADA (Prioridade ALTA)

### **Objetivo**: Implementar autenticação de dois fatores e logs de auditoria

#### **2.1 Instalar Dependências**
**Comando**: 
```bash
pip install pyotp flask-limiter
```

#### **2.2 Criar Modelo de Logs de Auditoria**
**Arquivo**: `app/models.py`
**Tempo Estimado**: 1 hora

```python
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
```

#### **2.3 Adicionar Campos 2FA ao Usuário**
**Arquivo**: `app/models.py` - Classe User
**Tempo Estimado**: 30 minutos

```python
class User(db.Model):
    # ... campos existentes ...
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
```

#### **2.4 Criar Utilitário de Auditoria**
**Arquivo**: `app/audit_utils.py`
**Tempo Estimado**: 2 horas

```python
from flask import request, session
from .models import AuditLog, db

def log_activity(action, resource, resource_id=None, details=None):
    """Registra atividade no log de auditoria"""
    try:
        user_id = session.get('user_id') if session else None
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def audit_required(action, resource):
    """Decorator para registrar ações automaticamente"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            log_activity(action, resource)
            return result
        return decorated_function
    return decorator
```

#### **2.5 Implementar 2FA**
**Arquivo**: `app/auth_2fa.py`
**Tempo Estimado**: 3 horas

```python
import pyotp
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User, db

bp_2fa = Blueprint('2fa', __name__)

@bp_2fa.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        code = request.form.get('code')
        if pyotp.TOTP(user.two_factor_secret).verify(code):
            user.two_factor_enabled = True
            db.session.commit()
            flash('2FA ativado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Código inválido!', 'danger')
    
    # Gerar QR Code para primeiro setup
    if not user.two_factor_secret:
        user.two_factor_secret = pyotp.random_base32()
        db.session.commit()
    
    totp = pyotp.TOTP(user.two_factor_secret)
    qr_code_url = totp.provisioning_uri(
        user.email, 
        issuer_name="TI OSN System"
    )
    
    return render_template('setup_2fa.html', qr_code_url=qr_code_url)
```

#### **2.6 Criar Migration para Novos Campos**
**Comando**: 
```bash
flask db migrate -m "Add 2FA and audit fields"
flask db upgrade
```

**📅 Cronograma Fase 2**: 2 dias
**🎯 Entregável**: Sistema de segurança com 2FA e logs de auditoria

---

## 🔌 FASE 3: API REST (Prioridade MÉDIA)

### **Objetivo**: Criar API REST para integração externa

#### **3.1 Instalar Dependências**
**Comando**: 
```bash
pip install flask-restful flask-cors
```

#### **3.2 Configurar API**
**Arquivo**: `app/api/__init__.py`
**Tempo Estimado**: 1 hora

```python
from flask_restful import Api
from flask_cors import CORS

api = Api(prefix='/api/v1')
cors = CORS()

def init_api(app):
    cors.init_app(app)
    api.init_app(app)
    
    # Registrar recursos
    from .resources import (
        ReminderResource, ReminderListResource,
        TaskResource, TaskListResource,
        ChamadoResource, ChamadoListResource
    )
    
    api.add_resource(ReminderListResource, '/reminders')
    api.add_resource(ReminderResource, '/reminders/<int:reminder_id>')
    api.add_resource(TaskListResource, '/tasks')
    api.add_resource(TaskResource, '/tasks/<int:task_id>')
    api.add_resource(ChamadoListResource, '/chamados')
    api.add_resource(ChamadoResource, '/chamados/<int:chamado_id>')
```

#### **3.3 Criar Recursos da API**
**Arquivo**: `app/api/resources.py`
**Tempo Estimado**: 4 horas

```python
from flask_restful import Resource, reqparse
from flask import request, jsonify
from ..models import Reminder, Task, Chamado, db
from ..auth_utils import login_required

class ReminderListResource(Resource):
    @login_required
    def get(self):
        reminders = Reminder.query.filter_by(user_id=session.get('user_id')).all()
        return {
            'reminders': [reminder.to_dict() for reminder in reminders]
        }
    
    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('type', required=True)
        parser.add_argument('due_date', required=True)
        parser.add_argument('responsible', required=True)
        
        args = parser.parse_args()
        
        reminder = Reminder(
            name=args['name'],
            type=args['type'],
            due_date=datetime.strptime(args['due_date'], '%Y-%m-%d').date(),
            responsible=args['responsible'],
            user_id=session.get('user_id')
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return reminder.to_dict(), 201

class ReminderResource(Resource):
    @login_required
    def get(self, reminder_id):
        reminder = Reminder.query.get_or_404(reminder_id)
        return reminder.to_dict()
    
    @login_required
    def put(self, reminder_id):
        reminder = Reminder.query.get_or_404(reminder_id)
        # Implementar atualização
        return reminder.to_dict()
    
    @login_required
    def delete(self, reminder_id):
        reminder = Reminder.query.get_or_404(reminder_id)
        db.session.delete(reminder)
        db.session.commit()
        return '', 204
```

#### **3.4 Adicionar Métodos to_dict() aos Modelos**
**Arquivo**: `app/models.py`
**Tempo Estimado**: 1 hora

```python
class Reminder(db.Model):
    # ... campos existentes ...
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'due_date': self.due_date.isoformat(),
            'responsible': self.responsible,
            'frequency': self.frequency,
            'status': self.status,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

#### **3.5 Criar Documentação da API**
**Arquivo**: `API_DOCUMENTATION.md`
**Tempo Estimado**: 2 horas

**📅 Cronograma Fase 3**: 2 dias
**🎯 Entregável**: API REST completa com documentação

---

## 💾 FASE 4: BACKUP AUTOMÁTICO (Prioridade MÉDIA)

### **Objetivo**: Implementar sistema de backup automático

#### **4.1 Criar Serviço de Backup**
**Arquivo**: `app/backup_service.py`
**Tempo Estimado**: 3 horas

```python
import os
import shutil
import zipfile
from datetime import datetime
from flask import current_app
from .models import db

class BackupService:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.backup_folder = app.config.get('BACKUP_FOLDER', 'backups')
        os.makedirs(self.backup_folder, exist_ok=True)
    
    def create_backup(self):
        """Cria backup completo do sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}'
        backup_path = os.path.join(self.backup_folder, backup_name)
        
        try:
            # Criar pasta do backup
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup do banco de dados
            db_path = current_app.config.get('DATABASE_URL', 'instance/reminder.db')
            if db_path.startswith('sqlite:///'):
                db_file = db_path.replace('sqlite:///', '')
                if os.path.exists(db_file):
                    shutil.copy2(db_file, os.path.join(backup_path, 'reminder.db'))
            
            # Backup de uploads
            uploads_path = os.path.join(current_app.root_path, 'static', 'uploads')
            if os.path.exists(uploads_path):
                uploads_backup = os.path.join(backup_path, 'uploads.zip')
                with zipfile.ZipFile(uploads_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(uploads_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, uploads_path)
                            zipf.write(file_path, arcname)
            
            # Backup de logs
            logs_path = 'logs'
            if os.path.exists(logs_path):
                shutil.copytree(logs_path, os.path.join(backup_path, 'logs'))
            
            # Criar arquivo de metadados
            metadata = {
                'timestamp': timestamp,
                'version': '1.0',
                'backup_type': 'full',
                'files': {
                    'database': 'reminder.db',
                    'uploads': 'uploads.zip',
                    'logs': 'logs/'
                }
            }
            
            import json
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Compactar backup
            shutil.make_archive(backup_path, 'zip', backup_path)
            shutil.rmtree(backup_path)  # Remove pasta temporária
            
            return f'{backup_name}.zip'
            
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return None
    
    def restore_backup(self, backup_file):
        """Restaura backup do sistema"""
        # Implementar restauração
        pass
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove backups antigos"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for file in os.listdir(self.backup_folder):
            if file.startswith('backup_') and file.endswith('.zip'):
                file_path = os.path.join(self.backup_folder, file)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    print(f"Backup removido: {file}")
```

#### **4.2 Configurar Backup Automático**
**Arquivo**: `app/__init__.py`
**Tempo Estimado**: 1 hora

```python
from .backup_service import BackupService

backup_service = BackupService()

def create_app():
    # ... configuração existente ...
    
    backup_service.init_app(app)
    
    # Agendar backup diário às 2h da manhã
    if not app.debug:
        scheduler.add_job(
            func=backup_service.create_backup,
            trigger='cron',
            hour=2,
            id='daily_backup'
        )
        
        # Limpeza semanal de backups antigos
        scheduler.add_job(
            func=backup_service.cleanup_old_backups,
            trigger='cron',
            day_of_week='sun',
            hour=3,
            id='cleanup_backups'
        )
```

#### **4.3 Criar Rota de Backup Manual**
**Arquivo**: `app/routes.py`
**Tempo Estimado**: 30 minutos

```python
@bp.route('/admin/backup', methods=['POST'])
@admin_required
def create_manual_backup():
    backup_file = backup_service.create_backup()
    if backup_file:
        flash(f'Backup criado com sucesso: {backup_file}', 'success')
    else:
        flash('Erro ao criar backup', 'danger')
    return redirect(url_for('main.dashboard'))
```

**📅 Cronograma Fase 4**: 1 dia
**🎯 Entregável**: Sistema de backup automático

---

## 📊 FASE 5: SISTEMA DE KPIs (Prioridade BAIXA)

### **Objetivo**: Implementar métricas de produtividade e performance

#### **5.1 Criar Serviço de KPIs**
**Arquivo**: `app/kpi_service.py`
**Tempo Estimado**: 4 horas

```python
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from .models import User, Task, Reminder, Chamado, db

class KPIService:
    def calculate_user_productivity(self, user_id, period='month'):
        """Calcula produtividade do usuário"""
        end_date = datetime.now()
        
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=365)
        
        # Tarefas completadas
        tasks_completed = Task.query.filter(
            and_(
                Task.user_id == user_id,
                Task.completed == True,
                Task.date >= start_date,
                Task.date <= end_date
            )
        ).count()
        
        # Total de tarefas
        tasks_total = Task.query.filter(
            and_(
                Task.user_id == user_id,
                Task.date >= start_date,
                Task.date <= end_date
            )
        ).count()
        
        # Lembretes completados
        reminders_completed = Reminder.query.filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.completed == True,
                Reminder.due_date >= start_date,
                Reminder.due_date <= end_date
            )
        ).count()
        
        # Total de lembretes
        reminders_total = Reminder.query.filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.due_date >= start_date,
                Reminder.due_date <= end_date
            )
        ).count()
        
        # Calcular produtividade
        task_productivity = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0
        reminder_productivity = (reminders_completed / reminders_total * 100) if reminders_total > 0 else 0
        
        return {
            'period': period,
            'tasks': {
                'completed': tasks_completed,
                'total': tasks_total,
                'productivity': round(task_productivity, 2)
            },
            'reminders': {
                'completed': reminders_completed,
                'total': reminders_total,
                'productivity': round(reminder_productivity, 2)
            },
            'overall_productivity': round((task_productivity + reminder_productivity) / 2, 2)
        }
    
    def get_department_metrics(self, sector_id, period='month'):
        """Métricas do departamento"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 if period == 'month' else 90)
        
        # Tempo médio de resposta para chamados
        avg_response_time = db.session.query(
            func.avg(func.extract('epoch', Chamado.data_ultima_atualizacao - Chamado.data_abertura))
        ).filter(
            and_(
                Chamado.setor_id == sector_id,
                Chamado.data_abertura >= start_date,
                Chamado.data_abertura <= end_date
            )
        ).scalar() or 0
        
        # Taxa de resolução
        total_chamados = Chamado.query.filter(
            and_(
                Chamado.setor_id == sector_id,
                Chamado.data_abertura >= start_date,
                Chamado.data_abertura <= end_date
            )
        ).count()
        
        resolved_chamados = Chamado.query.filter(
            and_(
                Chamado.setor_id == sector_id,
                Chamado.status.in_(['Resolvido', 'Fechado']),
                Chamado.data_abertura >= start_date,
                Chamado.data_abertura <= end_date
            )
        ).count()
        
        resolution_rate = (resolved_chamados / total_chamados * 100) if total_chamados > 0 else 0
        
        return {
            'avg_response_time_hours': round(avg_response_time / 3600, 2),
            'total_chamados': total_chamados,
            'resolved_chamados': resolved_chamados,
            'resolution_rate': round(resolution_rate, 2)
        }
    
    def get_system_metrics(self):
        """Métricas gerais do sistema"""
        total_users = User.query.count()
        active_users = User.query.filter_by(ativo=True).count()
        
        today = datetime.now().date()
        tasks_today = Task.query.filter_by(date=today).count()
        reminders_today = Reminder.query.filter_by(due_date=today).count()
        chamados_today = Chamado.query.filter(
            func.date(Chamado.data_abertura) == today
        ).count()
        
        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'today': {
                'tasks': tasks_today,
                'reminders': reminders_today,
                'chamados': chamados_today
            }
        }
```

#### **5.2 Criar Rotas de KPIs**
**Arquivo**: `app/routes.py`
**Tempo Estimado**: 1 hora

```python
@bp.route('/kpis/user/<int:user_id>')
@login_required
def user_kpis(user_id):
    period = request.args.get('period', 'month')
    kpi_service = KPIService()
    
    # Apenas admin pode ver KPIs de outros usuários
    if not session.get('is_admin') and user_id != session.get('user_id'):
        flash('Acesso negado', 'danger')
        return redirect(url_for('main.index'))
    
    productivity = kpi_service.calculate_user_productivity(user_id, period)
    return render_template('user_kpis.html', productivity=productivity, user_id=user_id)

@bp.route('/kpis/department/<int:sector_id>')
@admin_required
def department_kpis(sector_id):
    period = request.args.get('period', 'month')
    kpi_service = KPIService()
    
    metrics = kpi_service.get_department_metrics(sector_id, period)
    return render_template('department_kpis.html', metrics=metrics, sector_id=sector_id)

@bp.route('/kpis/system')
@admin_required
def system_kpis():
    kpi_service = KPIService()
    metrics = kpi_service.get_system_metrics()
    return render_template('system_kpis.html', metrics=metrics)
```

#### **5.3 Criar Templates de KPIs**
**Arquivo**: `app/templates/user_kpis.html`
**Tempo Estimado**: 2 horas

**📅 Cronograma Fase 5**: 2 dias
**🎯 Entregável**: Sistema completo de KPIs

---

## 📅 CRONOGRAMA GERAL

| Fase | Funcionalidade | Duração | Prioridade | Dependências |
|------|----------------|---------|------------|--------------|
| 1 | Controle de Lembretes | 1 dia | 🔥 ALTA | Nenhuma |
| 2 | Segurança Avançada | 2 dias | 🔥 ALTA | Fase 1 |
| 3 | API REST | 2 dias | ⚡ MÉDIA | Fase 2 |
| 4 | Backup Automático | 1 dia | ⚡ MÉDIA | Fase 2 |
| 5 | Sistema de KPIs | 2 dias | 💡 BAIXA | Fase 3 |

**📊 Total**: 8 dias úteis
**🎯 Entregável Final**: Sistema 100% completo

---

## 🚀 COMO EXECUTAR

### **Passo 1: Preparação**
```bash
# Atualizar dependências
pip install pyotp flask-limiter flask-restful flask-cors

# Verificar ambiente
python run.py
```

### **Passo 2: Executar Fases**
1. **Fase 1**: Controle de lembretes
2. **Fase 2**: Segurança avançada
3. **Fase 3**: API REST
4. **Fase 4**: Backup automático
5. **Fase 5**: Sistema de KPIs

### **Passo 3: Testes**
- Testar cada funcionalidade após implementação
- Verificar integração entre módulos
- Validar performance

### **Passo 4: Documentação**
- Atualizar README.md
- Criar documentação da API
- Documentar novos recursos

---

## 🎯 CRITÉRIOS DE SUCESSO

- [ ] Lembretes podem ser pausados/reativados
- [ ] 2FA funciona corretamente
- [ ] Logs de auditoria registram todas as ações
- [ ] API REST responde corretamente
- [ ] Backup automático executa sem erros
- [ ] KPIs calculam métricas corretas
- [ ] Sistema mantém performance
- [ ] Documentação está atualizada

---

**📝 Nota**: Este plano pode ser ajustado conforme necessidades específicas e feedback durante a implementação.
