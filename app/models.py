import secrets
from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .utils.timezone_utils import get_current_time_for_db, now_local


class User(db.Model):
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
    reminders = db.relationship("Reminder", backref="usuario", lazy=True)
    tasks = db.relationship("Task", backref="usuario", lazy=True)
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
    status = db.Column(db.String(20), default="ativo")  # ativo, pausado, cancelado
    pause_until = db.Column(
        db.Date, nullable=True
    )  # Data até quando o lembrete está pausado
    end_date = db.Column(db.Date, nullable=True)  # Data de término da recorrência
    created_at = db.Column(db.DateTime, default=get_current_time_for_db)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    responsible = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    sector_id = db.Column(db.Integer, db.ForeignKey("sector.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


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


class EquipmentRequest(db.Model):
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
