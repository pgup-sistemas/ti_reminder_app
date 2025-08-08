"""
Melhorias para o sistema de lembretes - Controle de Recorrência
"""

# 1. NOVOS CAMPOS NO MODELO (já adicionados via migration)
"""
class Reminder(db.Model):
    # ... campos existentes ...
    status = db.Column(db.String(20), default='ativo')  # ativo, pausado, cancelado
    pause_until = db.Column(db.Date, nullable=True)  # data até quando está pausado
    end_date = db.Column(db.Date, nullable=True)  # data de fim da recorrência
"""

# 2. NOVOS CAMPOS NO FORMULÁRIO (já adicionados)
"""
class ReminderForm(FlaskForm):
    # ... campos existentes ...
    status = SelectField('Status', choices=[('ativo','Ativo'),('pausado','Pausado'),('cancelado','Cancelado')], default='ativo')
    pause_until = DateField('Pausar até', validators=[Optional()])
    end_date = DateField('Data de fim', validators=[Optional()])
"""

# 3. NOVA ROTA PARA CONTROLAR STATUS
"""
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
    elif reminder.status == 'cancelado':
        reminder.status = 'ativo'
        flash('Lembrete reativado!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.reminders'))
"""

# 4. LÓGICA DE RECORRÊNCIA MELHORADA
"""
# Recorrência automática
for r in reminders:
    # Verificar se o lembrete deve continuar gerando recorrências
    if (r.due_date < date.today() and 
        not r.notified and 
        r.frequency and 
        r.status == 'ativo' and
        (not r.end_date or r.end_date > date.today()) and
        (not r.pause_until or r.pause_until <= date.today())):
        
        # ... lógica de criação do novo lembrete ...
        novo = Reminder(
            # ... campos existentes ...
            status=r.status,  # herda o status
            pause_until=r.pause_until,  # herda a data de pausa
            end_date=r.end_date,  # herda a data de fim
        )
"""

# 5. BOTÕES NA INTERFACE
"""
<!-- Botão para pausar/reativar -->
<form method="POST" action="/reminders/toggle_status/{{ reminder.id }}" class="d-inline">
    <button type="submit" class="btn btn-sm btn-{{ 'success' if reminder.status == 'pausado' else 'warning' }}" 
            title="{{ 'Reativar' if reminder.status == 'pausado' else 'Pausar' }}">
        <i class="fas fa-{{ 'play' if reminder.status == 'pausado' else 'pause' }}"></i>
    </button>
</form>
"""

print("✅ Melhorias documentadas! Implemente conforme necessário.")
