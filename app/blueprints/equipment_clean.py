"""
SISTEMA DE EQUIPAMENTOS - VERSÃO LIMPA E SIMPLIFICADA
Criado do zero com apenas funcionalidades essenciais

FLUXO:
1. Usuário solicita equipamento (cria EquipmentReservation com status='pendente')
2. TI/Admin aprova ou rejeita
3. Se aprovado, vira empréstimo ativo (EquipmentLoan)
4. Usuário devolve
5. TI/Admin confirma devolução
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from app.utils import flash_success, flash_error, flash_info
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

from app import db
from app.models import Equipment, EquipmentReservation, EquipmentLoan, User

bp = Blueprint('equipment_v2', __name__, url_prefix='/equipment')


# ==================== PÁGINAS PRINCIPAIS ====================

@bp.route('/')
@login_required
def index():
    """Página inicial - Dashboard simples"""
    # Estatísticas básicas
    total_equipments = Equipment.query.count()
    available = Equipment.query.filter_by(status='disponivel').count()
    
    # Minhas solicitações pendentes
    my_pending = EquipmentReservation.query.filter_by(
        user_id=current_user.id,
        status='pendente'
    ).count()
    
    # Meus empréstimos ativos
    my_loans = EquipmentLoan.query.filter_by(
        user_id=current_user.id,
        status='ativo'
    ).count()
    
    # Para TI/Admin: Aprovações pendentes
    pending_approvals = 0
    if current_user.is_ti or current_user.is_admin:
        pending_approvals = EquipmentReservation.query.filter_by(
            status='pendente'
        ).count()
    
    return render_template('equipment_v2/index.html',
        total_equipments=total_equipments,
        available=available,
        my_pending=my_pending,
        my_loans=my_loans,
        pending_approvals=pending_approvals
    )


@bp.route('/catalog')
@login_required
def catalog():
    """Lista todos os equipamentos disponíveis"""
    equipments = Equipment.query.filter_by(status='disponivel').order_by(Equipment.name).all()
    return render_template('equipment_v2/catalog.html', equipments=equipments)


# ==================== SOLICITAÇÕES (USUÁRIO) ====================

@bp.route('/request/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def request_equipment(equipment_id):
    """Solicitar empréstimo de equipamento"""
    from datetime import datetime as dt
    equipment = Equipment.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        try:
            # Pegar dados do form
            start_date_str = request.form.get('start_date')
            start_time_str = request.form.get('start_time', '09:00')
            end_date_str = request.form.get('end_date')
            end_time_str = request.form.get('end_time', '18:00')
            purpose = request.form.get('purpose', '')
            
            # Converter para date e time
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Criar datetime completos para validação
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            
            # Validações básicas
            if start_datetime < datetime.now():
                flash_error('Data e horário de início não podem ser no passado!')
                return redirect(url_for('equipment_v2.request_equipment', equipment_id=equipment_id))
            
            if end_datetime <= start_datetime:
                flash_error('Data e horário de término devem ser posteriores à data e horário de início!')
                return redirect(url_for('equipment_v2.request_equipment', equipment_id=equipment_id))
            
            # Criar solicitação
            reservation = EquipmentReservation(
                equipment_id=equipment_id,
                user_id=current_user.id,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                expected_return_date=end_date,
                expected_return_time=end_time,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                purpose=purpose,
                status='pendente'
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            flash_success(f'Solicitação enviada com sucesso! Aguarde aprovação da equipe de TI.')
            return redirect(url_for('equipment_v2.my_requests'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro ao criar solicitação: {str(e)}')
            flash_error(f'Erro ao criar solicitação: {str(e)}')
    
    # Passar data de hoje para o template
    today = datetime.now().date().isoformat()
    return render_template('equipment_v2/request_form.html', equipment=equipment, today=today)


@bp.route('/my-requests')
@login_required
def my_requests():
    """Minhas solicitações"""
    requests = EquipmentReservation.query.filter_by(
        user_id=current_user.id
    ).order_by(EquipmentReservation.created_at.desc()).all()
    
    return render_template('equipment_v2/my_requests.html', requests=requests)


@bp.route('/my-loans')
@login_required
def my_loans():
    """Meus empréstimos ativos"""
    loans = EquipmentLoan.query.filter_by(
        user_id=current_user.id
    ).order_by(EquipmentLoan.loan_date.desc()).all()
    
    return render_template('equipment_v2/my_loans.html', loans=loans)


# ==================== APROVAÇÕES (TI/ADMIN) ====================

@bp.route('/admin/pending')
@login_required
def admin_pending():
    """Lista de solicitações pendentes de aprovação"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado! Apenas TI/Admin podem acessar.')
        return redirect(url_for('equipment_v2.index'))
    
    pending = EquipmentReservation.query.filter_by(
        status='pendente'
    ).order_by(EquipmentReservation.created_at).all()
    
    return render_template('equipment_v2/admin_pending.html', pending=pending)


@bp.route('/admin/approve/<int:reservation_id>', methods=['POST'])
@login_required
def admin_approve(reservation_id):
    """Aprovar solicitação e criar empréstimo"""
    if not (current_user.is_ti or current_user.is_admin):
        flash('Acesso negado!', 'danger')
        return redirect(url_for('equipment_v2.index'))
    
    reservation = EquipmentReservation.query.get_or_404(reservation_id)
    
    try:
        # Atualizar reserva
        reservation.status = 'confirmada'
        reservation.approved_by_id = current_user.id
        reservation.approval_date = datetime.now()
        reservation.approval_notes = request.form.get('notes', '')
        
        # Criar empréstimo ativo
        loan = EquipmentLoan(
            equipment_id=reservation.equipment_id,
            user_id=reservation.user_id,
            loan_date=datetime.now(),
            expected_return_date=reservation.expected_return_date,
            expected_return_time=reservation.expected_return_time,
            status='ativo',
            delivered_by_id=current_user.id,
            reservation_id=reservation.id,
            condition_at_loan=Equipment.query.get(reservation.equipment_id).condition,
            delivery_notes=request.form.get('notes', '')
        )
        
        # Atualizar status do equipamento
        equipment = Equipment.query.get(reservation.equipment_id)
        equipment.status = 'emprestado'
        
        db.session.add(loan)
        db.session.commit()
        
        flash_success(f'Solicitação aprovada! Empréstimo criado com sucesso.')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao aprovar: {str(e)}')
        flash_error(f'Erro ao aprovar: {str(e)}')
    
    return redirect(url_for('equipment_v2.admin_pending'))


@bp.route('/admin/reject/<int:reservation_id>', methods=['POST'])
@login_required
def admin_reject(reservation_id):
    """Rejeitar solicitação"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    reservation = EquipmentReservation.query.get_or_404(reservation_id)
    
    try:
        reservation.status = 'rejeitada'
        reservation.approved_by_id = current_user.id
        reservation.approval_date = datetime.now()
        reservation.approval_notes = request.form.get('notes', 'Solicitação rejeitada')
        
        db.session.commit()
        
        flash_info('Solicitação rejeitada.')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao rejeitar: {str(e)}')
        flash_error(f'Erro ao rejeitar: {str(e)}')
    
    return redirect(url_for('equipment_v2.admin_pending'))


@bp.route('/admin/loans')
@login_required
def admin_loans():
    """Lista todos os empréstimos ativos"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    loans = EquipmentLoan.query.filter_by(
        status='ativo'
    ).order_by(EquipmentLoan.loan_date.desc()).all()
    
    return render_template('equipment_v2/admin_loans.html', loans=loans)


@bp.route('/admin/return/<int:loan_id>', methods=['POST'])
@login_required
def admin_return(loan_id):
    """Confirmar devolução de equipamento"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    loan = EquipmentLoan.query.get_or_404(loan_id)
    
    try:
        # Atualizar empréstimo
        loan.status = 'devolvido'
        loan.actual_return_date = datetime.now()
        loan.return_notes = request.form.get('notes', '')
        loan.received_by_id = current_user.id
        loan.condition_at_return = Equipment.query.get(loan.equipment_id).condition
        
        # Liberar equipamento
        equipment = Equipment.query.get(loan.equipment_id)
        equipment.status = 'disponivel'
        
        db.session.commit()
        
        flash_success('Devolução confirmada! Equipamento disponível novamente.')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao confirmar devolução: {str(e)}')
        flash_error(f'Erro ao confirmar devolução: {str(e)}')
    
    return redirect(url_for('equipment_v2.admin_loans'))


# ==================== GESTÃO DE EQUIPAMENTOS (ADMIN) ====================

@bp.route('/admin/equipment')
@login_required
def admin_equipment():
    """Lista todos os equipamentos (gestão)"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    equipments = Equipment.query.order_by(Equipment.name).all()
    return render_template('equipment_v2/admin_equipment.html', equipments=equipments)


@bp.route('/admin/equipment/new', methods=['GET', 'POST'])
@login_required
def admin_equipment_new():
    """Cadastrar novo equipamento"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    if request.method == 'POST':
        try:
            equipment = Equipment(
                name=request.form.get('name'),
                description=request.form.get('description'),
                patrimony=request.form.get('patrimony'),
                category=request.form.get('category'),
                brand=request.form.get('brand'),
                model=request.form.get('model'),
                status='disponivel',
                condition='bom',
                location=request.form.get('location')
            )
            
            db.session.add(equipment)
            db.session.commit()
            
            flash_success('Equipamento cadastrado com sucesso!')
            return redirect(url_for('equipment_v2.admin_equipment'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro ao cadastrar equipamento: {str(e)}')
            flash_error(f'Erro ao cadastrar: {str(e)}')
    
    return render_template('equipment_v2/admin_equipment_form.html', equipment=None)


@bp.route('/admin/equipment/edit/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def admin_equipment_edit(equipment_id):
    """Editar equipamento"""
    if not (current_user.is_ti or current_user.is_admin):
        flash_error('Acesso negado!')
        return redirect(url_for('equipment_v2.index'))
    
    equipment = Equipment.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        try:
            equipment.name = request.form.get('name')
            equipment.description = request.form.get('description')
            equipment.patrimony = request.form.get('patrimony')
            equipment.category = request.form.get('category')
            equipment.brand = request.form.get('brand')
            equipment.model = request.form.get('model')
            equipment.status = request.form.get('status')
            equipment.condition = request.form.get('condition')
            equipment.location = request.form.get('location')
            
            db.session.commit()
            
            flash_success('Equipamento atualizado com sucesso!')
            return redirect(url_for('equipment_v2.admin_equipment'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro ao atualizar equipamento: {str(e)}')
            flash_error(f'Erro ao atualizar: {str(e)}')
    
    return render_template('equipment_v2/admin_equipment_form.html', equipment=equipment)
