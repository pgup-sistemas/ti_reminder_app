import secrets
from datetime import datetime, timedelta, time
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .utils.timezone_utils import get_current_time_for_db, now_local


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_ti = db.Column(
        db.Boolean, default=False
    )  # Indica se o usuário é da equipe de TI
    ativo = db.Column(db.Boolean, default=True)  # Para ativação/desativação
    sector_id = db.Column(db.Integer, db.ForeignKey("sector.id"), nullable=True)
    sector = db.relationship("Sector", backref="usuarios")
    last_login = db.Column(db.DateTime, nullable=True)  # Último login do usuário
    created_at = db.Column(db.DateTime, default=get_current_time_for_db)  # Data de criação
    updated_at = db.Column(db.DateTime, default=get_current_time_for_db, onupdate=get_current_time_for_db)  # Última atualização
    reminders = db.relationship("Reminder", back_populates="user", lazy=True)
    tasks = db.relationship("Task", back_populates="user", lazy=True)
    equipment_reservations = db.relationship(
        "EquipmentReservation", 
        foreign_keys="[EquipmentReservation.user_id]",
        back_populates="user", 
        lazy=True,
        overlaps="user_reservations,user"
    )
    equipment_loans = db.relationship("EquipmentLoan", foreign_keys="[EquipmentLoan.user_id]", back_populates="user", lazy=True)
    equipment_deliveries = db.relationship("EquipmentLoan", foreign_keys="[EquipmentLoan.delivered_by_id]", back_populates="delivered_by", lazy=True)
    equipment_returns = db.relationship("EquipmentLoan", foreign_keys="[EquipmentLoan.received_by_id]", back_populates="received_by", lazy=True)
    approved_reservations = db.relationship("EquipmentReservation", foreign_keys="[EquipmentReservation.approved_by_id]", back_populates="approved_by", lazy=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        # Gera um token aleatório para redefinição de senha
        token = secrets.token_hex(32)
        self.reset_token = token
        # Define a expiração para 1 hora a partir de agora
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return token

    def verify_reset_token(self, token):
        # Verifica se o token é válido e não expirou
        if self.reset_token != token:
            return False
        if self.reset_token_expiry < datetime.utcnow():
            return False
        return True

    def clear_reset_token(self):
        # Limpa o token após uso
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()

    @property
    def is_active(self):
        """Sobrescreve o método is_active do UserMixin para usar o campo 'ativo'"""
        return self.ativo


class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    reminders = db.relationship("Reminder", backref="sector", lazy=True)
    tasks = db.relationship("Task", backref="sector", lazy=True)


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    responsible = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=True)
    notified = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    sector_id = db.Column(db.Integer, db.ForeignKey("sector.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", back_populates="reminders")
    status = db.Column(db.String(20), default="ativo")  # ativo, pausado, cancelado, encerrado
    pause_until = db.Column(
        db.Date, nullable=True
    )  # Data até quando o lembrete está pausado
    end_date = db.Column(db.Date, nullable=True)  # Data de término da recorrência
    created_at = db.Column(db.DateTime, default=get_current_time_for_db)
    escalation_level = db.Column(db.Integer, default=0)  # Nível de escalação atual
    last_escalation = db.Column(db.DateTime, nullable=True)  # Última data de escalação
    
    # Novos campos para melhorias profissionais
    priority = db.Column(db.String(20), default="media")  # baixa, media, alta, critica
    notes = db.Column(db.Text, nullable=True)  # Observações e notas adicionais
    contract_number = db.Column(db.String(100), nullable=True)  # Número de contrato/licença
    cost = db.Column(db.Float, nullable=True)  # Custo/valor da renovação
    supplier = db.Column(db.String(200), nullable=True)  # Fornecedor/fabricante
    category = db.Column(db.String(100), nullable=True)  # Categoria (Licença Software, Licença Banco, Contrato, etc.)
    
    # Relacionamento com histórico
    history = db.relationship("ReminderHistory", backref="reminder", lazy=True, cascade="all, delete-orphan")


class ReminderHistory(db.Model):
    """Histórico de ações realizadas em lembretes para auditoria"""
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey("reminder.id"), nullable=False)
    original_due_date = db.Column(db.Date, nullable=False)  # Data de vencimento quando a ação foi realizada
    action_type = db.Column(db.String(50), nullable=False)  # completed, recurring, skipped, delayed, etc.
    action_date = db.Column(db.DateTime, default=get_current_time_for_db)  # Quando a ação foi realizada
    completed = db.Column(db.Boolean, default=False)  # Se foi completado ou não
    completed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # Usuário que completou
    notes = db.Column(db.Text, nullable=True)  # Observações sobre a ação
    
    # Relacionamento com usuário que completou
    completed_by_user = db.relationship("User", foreign_keys=[completed_by], backref="completed_reminders")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    responsible = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    sector_id = db.Column(db.Integer, db.ForeignKey("sector.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", back_populates="tasks")


class Chamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(50), nullable=False, default="Aberto"
    )  # Ex: Aberto, Em Andamento, Resolvido, Fechado
    prioridade = db.Column(
        db.String(50), nullable=False, default="Media"
    )  # Ex: Baixa, Media, Alta, Critica


    data_abertura = db.Column(
        db.DateTime, nullable=False, default=get_current_time_for_db
    )
    data_ultima_atualizacao = db.Column(
        db.DateTime, default=get_current_time_for_db, onupdate=get_current_time_for_db
    )
    data_fechamento = db.Column(db.DateTime, nullable=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey("sector.id"), nullable=False)
    responsavel_ti_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Campos de SLA
    prazo_sla = db.Column(
        db.DateTime, nullable=True
    )  # Data limite para cumprimento do SLA
    data_primeira_resposta = db.Column(
        db.DateTime, nullable=True
    )  # Quando o chamado foi atendido pela primeira vez
    sla_cumprido = db.Column(
        db.Boolean, default=None, nullable=True
    )  # True=cumprido, False=vencido, None=em andamento
    tempo_resposta_horas = db.Column(
        db.Float, nullable=True
    )  # Tempo de resposta em horas

    # Campos de Satisfação
    satisfaction_rating = db.Column(
        db.Integer, nullable=True
    )  # Avaliação 1-5 estrelas
    satisfaction_comment = db.Column(
        db.Text, nullable=True
    )  # Comentário da avaliação
    satisfaction_date = db.Column(
        db.DateTime, nullable=True
    )  # Data da avaliação
    survey_sent = db.Column(
        db.Boolean, default=False
    )  # Se a pesquisa de satisfação foi enviada
    survey_sent_date = db.Column(
        db.DateTime, nullable=True
    )  # Data de envio da pesquisa

    solicitante = db.relationship(
        "User", foreign_keys=[solicitante_id], backref="chamados_solicitados"
    )
    setor = db.relationship("Sector", backref="chamados")
    responsavel_ti = db.relationship(
        "User", foreign_keys=[responsavel_ti_id], backref="chamados_responsaveis"
    )

    @property
    def status_sla(self):
        """Retorna o status visual do SLA: 'cumprido', 'vencido', 'atencao', 'normal'"""
        if self.sla_cumprido is True:
            return "cumprido"
        elif self.sla_cumprido is False:
            return "vencido"
        elif self.prazo_sla:
            agora = get_current_time_for_db()
            tempo_restante = self.prazo_sla - agora
            if tempo_restante.total_seconds() < 0:
                return "vencido"
            elif tempo_restante.total_seconds() < 3600:  # Menos de 1 hora restante
                return "atencao"
        return "normal"

    @property
    def tempo_restante_sla(self):
        """Retorna o tempo restante para o SLA em formato legível"""
        if not self.prazo_sla:
            return None

        agora = get_current_time_for_db()
        diferenca = self.prazo_sla - agora

        if diferenca.total_seconds() < 0:
            # SLA vencido
            diferenca = agora - self.prazo_sla
            horas = int(diferenca.total_seconds() // 3600)
            minutos = int((diferenca.total_seconds() % 3600) // 60)
            return f"Vencido há {horas}h {minutos}m"
        else:
            # SLA ainda válido
            horas = int(diferenca.total_seconds() // 3600)
            minutos = int((diferenca.total_seconds() % 3600) // 60)
            return f"{horas}h {minutos}m restantes"

    def calcular_sla(self):
        """Calcula e define o prazo de SLA baseado na prioridade"""
        # Verificar se data_abertura está definida
        if not self.data_abertura:
            # Se não estiver definida, usar o tempo atual
            self.data_abertura = get_current_time_for_db()

        sla_config = SlaConfig.query.filter_by(prioridade=self.prioridade).first()
        if sla_config:
            self.prazo_sla = self.data_abertura + timedelta(
                hours=sla_config.tempo_resposta_horas
            )

    def marcar_primeira_resposta(self):
        """Marca a primeira resposta e calcula o tempo de resposta"""
        if not self.data_primeira_resposta:
            self.data_primeira_resposta = get_current_time_for_db()
            if self.prazo_sla:
                diferenca = self.data_primeira_resposta - self.data_abertura
                self.tempo_resposta_horas = diferenca.total_seconds() / 3600
                self.sla_cumprido = self.data_primeira_resposta <= self.prazo_sla

    def __repr__(self):
        return f"<Chamado {self.id}: {self.titulo}>"


class ComentarioChamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey("chamado.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=get_current_time_for_db)
    tipo = db.Column(
        db.String(20), default="comentario"
    )  # 'comentario' ou 'atualizacao'

    # Relacionamentos
    chamado = db.relationship(
        "Chamado",
        backref=db.backref(
            "comentarios", lazy=True, order_by="ComentarioChamado.data_criacao.desc()"
        ),
    )
    usuario = db.relationship("User")

    def __repr__(self):
        return f"<Comentario {self.id} do Chamado {self.chamado_id}>"


class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(
        db.DateTime, default=get_current_time_for_db, nullable=False
    )
    autor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)

    autor = db.relationship("User", backref="tutoriais")

    def __repr__(self):
        return f"<Tutorial {self.id}: {self.titulo}>"


class TutorialImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutorial.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=get_current_time_for_db)

    tutorial = db.relationship("Tutorial", backref=db.backref("imagens", lazy=True))

    def __repr__(self):
        return f"<TutorialImage {self.id} - {self.filename}>"


class ComentarioTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutorial.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=get_current_time_for_db)
    chamado_id = db.Column(
        db.Integer, db.ForeignKey("chamado.id"), nullable=True
    )  # Integração opcional com chamado

    tutorial = db.relationship(
        "Tutorial",
        backref=db.backref(
            "comentarios", lazy=True, order_by="ComentarioTutorial.data_criacao.desc()"
        ),
    )
    usuario = db.relationship("User")
    chamado = db.relationship("Chamado")

    def __repr__(self):
        return f"<ComentarioTutorial {self.id} do Tutorial {self.tutorial_id}>"


class FeedbackTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutorial.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    util = db.Column(db.Boolean, nullable=False)  # True = útil, False = não útil
    data = db.Column(db.DateTime, default=get_current_time_for_db)

    tutorial = db.relationship("Tutorial", backref=db.backref("feedbacks", lazy=True))
    usuario = db.relationship("User")

    def __repr__(self):
        return f"<FeedbackTutorial {self.id} - Tutorial {self.tutorial_id} - Util: {self.util}>"


class VisualizacaoTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey("tutorial.id"), nullable=False)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Pode ser nulo para visitantes
    data = db.Column(db.DateTime, default=get_current_time_for_db)

    tutorial = db.relationship(
        "Tutorial", backref=db.backref("visualizacoes", lazy=True)
    )
    usuario = db.relationship("User")

    def __repr__(self):
        return f"<VisualizacaoTutorial {self.id} - Tutorial {self.tutorial_id}>"


class Equipment(db.Model):
    """Inventário central de equipamentos disponíveis para empréstimo"""
    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    name = db.Column(db.String(100), nullable=False)  # Nome do equipamento
    description = db.Column(db.Text, nullable=True)  # Descrição detalhada
    patrimony = db.Column(db.String(50), nullable=True, unique=True)  # Número do patrimônio
    serial_number = db.Column(db.String(100), nullable=True)  # Número de série

    # Classificação
    category = db.Column(db.String(50), nullable=False)  # Notebook, Monitor, Impressora, etc.
    subcategory = db.Column(db.String(50), nullable=True)  # Dell Latitude, HP LaserJet, etc.
    brand = db.Column(db.String(50), nullable=True)  # Marca
    model = db.Column(db.String(100), nullable=True)  # Modelo específico

    # Status e Disponibilidade
    status = db.Column(db.String(20), nullable=False, default="disponivel")
    # disponivel, emprestado, manutencao, danificado, perdido
    condition = db.Column(db.String(20), nullable=False, default="bom")
    # novo, bom, regular, danificado, inutilizavel

    # Localização e Controle
    location = db.Column(db.String(100), nullable=True)  # Localização física atual
    storage_location = db.Column(db.String(100), nullable=True)  # Local de armazenamento
    responsible_sector = db.Column(db.String(100), nullable=True)  # Setor responsável

    # Especificações Técnicas
    specifications = db.Column(db.Text, nullable=True)  # JSON com specs técnicas
    purchase_date = db.Column(db.Date, nullable=True)  # Data de compra/aquisição
    purchase_value = db.Column(db.Numeric(10, 2), nullable=True)  # Valor de compra
    warranty_expiration = db.Column(db.Date, nullable=True)  # Expiração da garantia

    # Controle de Uso
    max_loan_days = db.Column(db.Integer, default=30)  # Dias máximos de empréstimo
    requires_approval = db.Column(db.Boolean, default=True)  # Requer aprovação?
    restricted_to_sector = db.Column(db.Boolean, default=False)  # Restrito ao setor?

    # Imagens e Documentação
    image_filename = db.Column(db.String(255), nullable=True)  # Nome do arquivo da imagem
    manual_filename = db.Column(db.String(255), nullable=True)  # Manual do equipamento

    # Controle de Manutenção
    last_maintenance = db.Column(db.Date, nullable=True)  # Última manutenção
    next_maintenance = db.Column(db.Date, nullable=True)  # Próxima manutenção
    maintenance_notes = db.Column(db.Text, nullable=True)  # Notas de manutenção
    maintenance_alert_sent = db.Column(db.Boolean, default=False)  # Alerta enviado?

    # RFID e Rastreamento
    rfid_tag = db.Column(db.String(100), nullable=True, unique=True)  # Tag RFID
    rfid_status = db.Column(db.String(20), default="desconhecido")  # ativo, inativo, perdido

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db, onupdate=get_current_time_for_db)

    # Relacionamentos
    loans = db.relationship("EquipmentLoan", back_populates="equipment", lazy=True, overlaps="equipment_loan,loan_records")
    reservations = db.relationship("EquipmentReservation", back_populates="equipment", lazy=True, overlaps="equipment_reservation,reservation_links")

    def needs_maintenance(self):
        """Verifica se o equipamento precisa de manutenção"""
        if not self.next_maintenance:
            return False
        return datetime.utcnow().date() >= self.next_maintenance

    def days_until_maintenance(self):
        """Retorna dias até a próxima manutenção"""
        if not self.next_maintenance:
            return None
        today = datetime.utcnow().date()
        if self.next_maintenance <= today:
            return 0
        return (self.next_maintenance - today).days

    def __repr__(self):
        return f"<Equipment {self.id}: {self.name} ({self.patrimony or 'Sem patrimônio'})>"

    def is_available(self):
        """Verifica se o equipamento está disponível para empréstimo"""
        # Verifica status básico e condição
        if self.status != "disponivel" or self.condition not in ["novo", "bom", "regular"]:
            return False
            
        # Verifica se há reservas ativas
        now = datetime.utcnow().date()
        active_reservation = EquipmentReservation.query.filter(
            EquipmentReservation.equipment_id == self.id,
            EquipmentReservation.status == "confirmada",
            EquipmentReservation.start_date <= now,
            EquipmentReservation.end_date >= now
        ).first()
        
        # Se houver reserva ativa, não está disponível
        if active_reservation:
            return False
            
        return True

    def can_be_reserved_by(self, user):
        """Verifica se o usuário pode reservar este equipamento"""
        if self.restricted_to_sector and user.sector:
            return user.sector.name == self.responsible_sector
        return True

    def get_current_loan(self):
        """Retorna o empréstimo ativo atual, se existir"""
        return EquipmentLoan.query.filter_by(
            equipment_id=self.id,
            status="ativo"
        ).first()


class EquipmentReservation(db.Model):
    """Reservas futuras de equipamentos com suporte a horários"""
    __tablename__ = 'equipment_reservation'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Datas e horários
    start_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False, default='09:00')
    end_date = db.Column(db.Date, nullable=False, index=True)
    end_time = db.Column(db.Time, nullable=False, default='18:00')
    
    # Datas completas (para consultas e ordenação)
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=False, index=True)
    
    expected_return_date = db.Column(db.Date, nullable=False)
    expected_return_time = db.Column(db.Time, nullable=False, default='18:00')
    
    status = db.Column(db.String(20), nullable=False, default='pendente', index=True)  # pendente, confirmada, cancelada, rejeitada
    purpose = db.Column(db.Text, nullable=True)
    
    # Aprovação
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    
    # Controle
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db, onupdate=get_current_time_for_db)
    
    # Relacionamentos
    equipment = db.relationship(
        'Equipment', 
        foreign_keys=[equipment_id],
        back_populates='reservations', 
        overlaps="reservation_links,equipment_reservation"
    )
    user = db.relationship(
        'User', 
        foreign_keys=[user_id], 
        back_populates='equipment_reservations',
        overlaps="user_reservations,user"
    )
    approved_by = db.relationship(
        'User', 
        foreign_keys=[approved_by_id], 
        back_populates='approved_reservations',
        overlaps="user_approved_reservations,approved_by"
    )
    resulting_loan = db.relationship(
        "EquipmentLoan", 
        back_populates="reservation", 
        uselist=False, 
        foreign_keys="[EquipmentLoan.reservation_id]",
        overlaps="equipment_loan,loans,reservation_equipment_loan"
    )
    
    def __init__(self, **kwargs):
        # Garante que as datas completas sejam definidas corretamente
        if 'start_date' in kwargs and 'start_time' in kwargs:
            kwargs['start_datetime'] = datetime.combine(
                kwargs['start_date'],
                kwargs['start_time'] if isinstance(kwargs['start_time'], time) else datetime.strptime(kwargs['start_time'], '%H:%M').time()
            )
        if 'end_date' in kwargs and 'end_time' in kwargs:
            kwargs['end_datetime'] = datetime.combine(
                kwargs['end_date'],
                kwargs['end_time'] if isinstance(kwargs['end_time'], time) else datetime.strptime(kwargs['end_time'], '%H:%M').time()
            )
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f'<EquipmentReservation {self.id} - {self.equipment.name} - {self.status}>'
    
    def is_active(self):
        """Verifica se a reserva está ativa no momento"""
        now = datetime.utcnow()
        return (self.status == 'confirmada' and 
                self.start_datetime <= now <= self.end_datetime)
                
    def overlaps_with(self, start_datetime, end_datetime):
        """Verifica se há conflito de datas/horários com outra reserva"""
        return (self.start_datetime < end_datetime and 
                self.end_datetime > start_datetime)
                
    def get_duration_hours(self):
        """Retorna a duração total da reserva em horas"""
        duration = self.end_datetime - self.start_datetime
        return round(duration.total_seconds() / 3600, 2)
        
    def to_dict(self):
        """Converte a reserva para dicionário"""
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name,
            'user_id': self.user_id,
            'user_name': self.user.username,
            'start_date': self.start_date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_date': self.end_date.isoformat(),
            'end_time': self.end_time.strftime('%H:%M'),
            'start_datetime': self.start_datetime.isoformat(),
            'end_datetime': self.end_datetime.isoformat(),
            'status': self.status,
            'purpose': self.purpose,
            'duration_hours': self.get_duration_hours(),
            'created_at': self.created_at.isoformat()
        }


class EquipmentLoan(db.Model):
    """Empréstimos ativos de equipamentos"""
    __tablename__ = 'equipment_loan'
    
    id = db.Column(db.Integer, primary_key=True)

    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Período do empréstimo
    loan_date = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db)
    loan_time = db.Column(db.Time, nullable=False, default=datetime.now().time)
    expected_return_date = db.Column(db.Date, nullable=False)
    expected_return_time = db.Column(db.Time, nullable=False, default=time(18, 0))  # Horário padrão: 18:00
    actual_return_date = db.Column(db.DateTime, nullable=True)

    # Status do empréstimo
    status = db.Column(db.String(20), nullable=False, default="ativo")
    # ativo, devolvido, atrasado, perdido, danificado

    # Controle de entrega e devolução
    delivered_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)
    return_notes = db.Column(db.Text, nullable=True)

    # Condição na entrega e devolução
    condition_at_loan = db.Column(db.String(20), nullable=True)
    condition_at_return = db.Column(db.String(20), nullable=True)

    # Controle de SLA
    return_reminder_sent = db.Column(db.Boolean, default=False)
    overdue_notified = db.Column(db.Boolean, default=False)

    # SLA do empréstimo
    sla_hours = db.Column(db.Integer, nullable=True)  # SLA em horas para entrega
    sla_deadline = db.Column(db.DateTime, nullable=True)  # Prazo limite do SLA
    sla_status = db.Column(db.String(20), default="normal")  # normal, atencao, vencido, cumprido

    # Relacionamento com reserva (opcional)
    reservation_id = db.Column(db.Integer, db.ForeignKey("equipment_reservation.id"), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db)
    updated_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db, onupdate=get_current_time_for_db)

    # Relacionamentos
    equipment = db.relationship("Equipment", back_populates="loans", overlaps="loan_records,equipment_loan")
    user = db.relationship("User", foreign_keys=[user_id], back_populates="equipment_loans")
    delivered_by = db.relationship("User", foreign_keys=[delivered_by_id], back_populates="equipment_deliveries")
    received_by = db.relationship("User", foreign_keys=[received_by_id], back_populates="equipment_returns")
    reservation = db.relationship(
        "EquipmentReservation", 
        back_populates="resulting_loan",
        overlaps="equipment_reservation,reservations"
    )

    def __repr__(self):
        return f"<EquipmentLoan {self.id}: {self.equipment.name} para {self.user.username}>"

    def is_overdue(self):
        """Verifica se o empréstimo está atrasado considerando data e hora"""
        if self.status != "ativo":
            return False
            
        now = datetime.utcnow()
        expected_return = datetime.combine(self.expected_return_date, self.expected_return_time or time(23, 59))
        
        return now > expected_return

    def days_overdue(self):
        """Retorna quantos dias de atraso"""
        if not self.is_overdue():
            return 0
            
        now = datetime.utcnow()
        expected_return = datetime.combine(self.expected_return_date, self.expected_return_time or time(23, 59))
        delta = now - expected_return
        
        # Retorna o número de dias completos de atraso
        return delta.days

    def calculate_sla(self):
        """Calcula o SLA baseado na prioridade do equipamento"""
        # SLA baseado na categoria do equipamento
        sla_config = {
            'Notebook': 4,  # 4 horas para entrega
            'Monitor': 2,   # 2 horas
            'Projetor': 8,  # 8 horas (mais complexo)
            'Impressora': 6,# 6 horas
            'default': 4    # 4 horas padrão
        }

        hours = sla_config.get(self.equipment.category, sla_config['default'])
        self.sla_hours = hours
        
        # Garante que loan_date é um objeto datetime
        if isinstance(self.loan_date, str):
            self.loan_date = datetime.fromisoformat(self.loan_date)
            
        # Define o prazo do SLA considerando o horário
        self.sla_deadline = self.loan_date + timedelta(hours=hours)
        
        # Se houver um horário de retorno esperado, ajusta o SLA para não ultrapassar
        if hasattr(self, 'expected_return_time') and self.expected_return_time:
            expected_return = datetime.combine(
                self.expected_return_date,
                self.expected_return_time
            )
            if self.sla_deadline > expected_return:
                self.sla_deadline = expected_return

    def update_sla_status(self):
        """Atualiza o status do SLA"""
        if not self.sla_deadline:
            return

        now = get_current_time_for_db()

        if self.status == "devolvido":
            self.sla_status = "cumprido"
        elif now > self.sla_deadline:
            self.sla_status = "vencido"
        elif (self.sla_deadline - now).total_seconds() < 3600:  # Menos de 1 hora
            self.sla_status = "atencao"
        else:
            self.sla_status = "normal"

    def get_sla_display(self):
        """Retorna status do SLA em português"""
        status_map = {
            "normal": "Normal",
            "atencao": "Atenção",
            "vencido": "Vencido",
            "cumprido": "Cumprido"
        }
        return status_map.get(self.sla_status, self.sla_status)


class EquipmentRequest(db.Model):
    """Solicitações de empréstimo (mantido para compatibilidade)"""
    id = db.Column(db.Integer, primary_key=True)

    # Campos principais (solicitados)
    description = db.Column(db.Text, nullable=False)  # Descrição do equipamento
    patrimony = db.Column(db.String(50), nullable=True)  # Número do patrimônio
    delivery_date = db.Column(db.Date, nullable=True)  # Data de entrega
    return_date = db.Column(db.Date, nullable=True)  # Data de devolução
    conference_status = db.Column(db.String(50), nullable=True)  # Status de conferência
    observations = db.Column(db.Text, nullable=True)  # Observações

    # Campos de relacionamento
    requester_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # Solicitante
    received_by_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Quem recebeu
    approved_by_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Quem aprovou

    # Campos de status e controle
    status = db.Column(
        db.String(20), nullable=False, default="Solicitado"
    )  # Solicitado, Aprovado, Entregue, Devolvido, Negado
    request_date = db.Column(
        db.DateTime, nullable=False, default=get_current_time_for_db
    )  # Data da solicitação
    approval_date = db.Column(db.DateTime, nullable=True)  # Data de aprovação

    # Campos adicionais
    equipment_type = db.Column(
        db.String(50), nullable=True
    )  # Tipo de equipamento (notebook, monitor, etc.)
    destination_sector = db.Column(db.String(100), nullable=True)  # Setor/Destino
    request_reason = db.Column(db.Text, nullable=True)  # Motivo da solicitação

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time_for_db)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_current_time_for_db,
        onupdate=get_current_time_for_db,
    )

    # Campos RFID
    rfid_tag = db.Column(db.String(100), nullable=True, unique=True)  # Tag RFID única
    last_location = db.Column(db.String(100), nullable=True)  # Última localização
    return_alert_sent = db.Column(db.Boolean, default=False)  # Alerta de devolução enviado

    # Relacionamentos
    requester = db.relationship(
        "User", foreign_keys=[requester_id], backref="equipment_requests_solicitadas"
    )
    received_by = db.relationship(
        "User", foreign_keys=[received_by_id], backref="equipment_requests_recebidas"
    )
    approved_by = db.relationship(
        "User", foreign_keys=[approved_by_id], backref="equipment_requests_aprovadas"
    )

    def __repr__(self):
        return f"<EquipmentRequest {self.id}: {self.description[:50]}...>"

    def get_status_display(self):
        """Retorna o status em português"""
        status_map = {
            "Solicitado": "Solicitado",
            "Aprovado": "Aprovado",
            "Entregue": "Entregue",
            "Devolvido": "Devolvido",
            "Negado": "Negado",
        }
        return status_map.get(self.status, self.status)

    def can_be_approved_by(self, user):
        """Verifica se o usuário pode aprovar esta solicitação"""
        return user.is_admin or user.is_ti

    def can_be_edited_by(self, user):
        """Verifica se o usuário pode editar esta solicitação"""
        return user.id == self.requester_id or user.is_admin or user.is_ti


class SlaConfig(db.Model):
    """Tabela para configurar os tempos de SLA por prioridade"""

    id = db.Column(db.Integer, primary_key=True)
    prioridade = db.Column(
        db.String(50), nullable=False, unique=True
    )  # Baixa, Media, Alta, Critica
    tempo_resposta_horas = db.Column(
        db.Integer, nullable=False
    )  # Tempo em horas para primeira resposta
    tempo_resolucao_horas = db.Column(
        db.Integer, nullable=True
    )  # Tempo total para resolução (futuro)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<SlaConfig {self.prioridade}: {self.tempo_resposta_horas}h>"

    @classmethod
    def get_tempo_sla(cls, prioridade):
        """Retorna o tempo de SLA para uma prioridade específica"""
        config = cls.query.filter_by(prioridade=prioridade, ativo=True).first()
        return config.tempo_resposta_horas if config else 24  # Default 24 horas

    @classmethod
    def criar_configuracoes_padrao(cls):
        """Cria as configurações padrão de SLA"""
        configuracoes_padrao = [
            {"prioridade": "Critica", "tempo_resposta_horas": 2},
            {"prioridade": "Alta", "tempo_resposta_horas": 4},
            {"prioridade": "Media", "tempo_resposta_horas": 24},
            {"prioridade": "Baixa", "tempo_resposta_horas": 72},
        ]

        for config in configuracoes_padrao:
            if not cls.query.filter_by(prioridade=config["prioridade"]).first():
                nova_config = cls(**config)
                db.session.add(nova_config)

        db.session.commit()


class NotificationSettings(db.Model):
    """Configurações de notificação dos usuários"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Notificações por email
    email_reminders = db.Column(db.Boolean, default=True)
    email_tasks = db.Column(db.Boolean, default=True)
    email_chamados = db.Column(db.Boolean, default=True)
    email_equipment = db.Column(db.Boolean, default=True)

    # Notificações push/web
    push_reminders = db.Column(db.Boolean, default=True)
    push_tasks = db.Column(db.Boolean, default=True)
    push_chamados = db.Column(db.Boolean, default=True)
    push_equipment = db.Column(db.Boolean, default=True)

    # Frequência de resumos
    summary_frequency = db.Column(db.String(20), default="daily")  # never, daily, weekly

    user = db.relationship("User", backref=db.backref("notification_settings", uselist=False))

    def __repr__(self):
        return f"<NotificationSettings {self.user.username}>"


class TaskSlaConfig(db.Model):
    """Configuração de SLA para tarefas por prioridade"""
    id = db.Column(db.Integer, primary_key=True)
    priority = db.Column(db.String(50), nullable=False, unique=True)  # baixa, media, alta, critica
    sla_hours = db.Column(db.Integer, nullable=False)  # Horas para conclusão
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<TaskSlaConfig {self.priority}: {self.sla_hours}h>"


class UserCertification(db.Model):
    """Certificações de contribuidores da base de conhecimento"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    certification_type = db.Column(db.String(50), nullable=False)  # Ex: "Contribuidor Ativo", "Especialista", "Moderador"
    level = db.Column(db.Integer, default=1)  # Nível da certificação (1-5)
    points = db.Column(db.Integer, default=0)  # Pontos acumulados
    awarded_date = db.Column(db.DateTime, default=get_current_time_for_db)
    expires_at = db.Column(db.DateTime, nullable=True)  # Data de expiração
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship("User", backref=db.backref("certifications", lazy=True))

    def __repr__(self):
        return f"<UserCertification {self.user.username} - {self.certification_type} Level {self.level}>"


class ContributionMetrics(db.Model):
    """Métricas de contribuição dos usuários"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tutorials_created = db.Column(db.Integer, default=0)
    tutorial_views = db.Column(db.Integer, default=0)  # Visualizações dos tutoriais do usuário
    comments_made = db.Column(db.Integer, default=0)
    helpful_votes = db.Column(db.Integer, default=0)  # Votos "útil" recebidos
    total_points = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=get_current_time_for_db, onupdate=get_current_time_for_db)

    user = db.relationship("User", backref=db.backref("contribution_metrics", uselist=False))

    def calculate_points(self):
        """Calcula pontos baseado nas contribuições"""
        points = (
            self.tutorials_created * 10 +      # 10 pontos por tutorial
            self.tutorial_views * 0.1 +        # 0.1 ponto por visualização
            self.comments_made * 2 +          # 2 pontos por comentário
            self.helpful_votes * 5            # 5 pontos por voto útil
        )
        self.total_points = int(points)
        return self.total_points

    def get_certification_level(self):
        """Retorna nível de certificação baseado nos pontos"""
        if self.total_points >= 1000:
            return "Especialista", 5
        elif self.total_points >= 500:
            return "Contribuidor Sênior", 4
        elif self.total_points >= 200:
            return "Contribuidor Ativo", 3
        elif self.total_points >= 50:
            return "Contribuidor", 2
        else:
            return "Iniciante", 1

    def __repr__(self):
        return f"<ContributionMetrics {self.user.username} - {self.total_points} points>"
