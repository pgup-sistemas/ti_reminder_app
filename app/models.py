from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_ti = db.Column(db.Boolean, default=False)  # Indica se o usuário é da equipe de TI
    ativo = db.Column(db.Boolean, default=True)  # Para ativação/desativação
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)
    sector = db.relationship('Sector', backref='usuarios')
    reminders = db.relationship('Reminder', backref='usuario', lazy=True)
    tasks = db.relationship('Task', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    reminders = db.relationship('Reminder', backref='sector', lazy=True)
    tasks = db.relationship('Task', backref='sector', lazy=True)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    responsible = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=True)
    notified = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    responsible = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)



class Chamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Aberto') # Ex: Aberto, Em Andamento, Resolvido, Fechado
    prioridade = db.Column(db.String(50), nullable=False, default='Media') # Ex: Baixa, Media, Alta, Critica
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_fechamento = db.Column(db.DateTime, nullable=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    responsavel_ti_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    solicitante = db.relationship('User', foreign_keys=[solicitante_id], backref='chamados_solicitados')
    setor = db.relationship('Sector', backref='chamados')
    responsavel_ti = db.relationship('User', foreign_keys=[responsavel_ti_id], backref='chamados_responsaveis')

    def __repr__(self):
        return f'<Chamado {self.id}: {self.titulo}>'


class ComentarioChamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), default='comentario')  # 'comentario' ou 'atualizacao'
    
    # Relacionamentos
    chamado = db.relationship('Chamado', backref=db.backref('comentarios', lazy=True, order_by='ComentarioChamado.data_criacao.desc()'))
    usuario = db.relationship('User')
    
    def __repr__(self):
        return f'<Comentario {self.id} do Chamado {self.chamado_id}>'

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)

    autor = db.relationship('User', backref='tutoriais')

    def __repr__(self):
        return f'<Tutorial {self.id}: {self.titulo}>'

class TutorialImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    tutorial = db.relationship('Tutorial', backref=db.backref('imagens', lazy=True))

    def __repr__(self):
        return f'<TutorialImage {self.id} - {self.filename}>'

class ComentarioTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=True)  # Integração opcional com chamado

    tutorial = db.relationship('Tutorial', backref=db.backref('comentarios', lazy=True, order_by='ComentarioTutorial.data_criacao.desc()'))
    usuario = db.relationship('User')
    chamado = db.relationship('Chamado')

    def __repr__(self):
        return f'<ComentarioTutorial {self.id} do Tutorial {self.tutorial_id}>'

class FeedbackTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    util = db.Column(db.Boolean, nullable=False)  # True = útil, False = não útil
    data = db.Column(db.DateTime, default=datetime.utcnow)

    tutorial = db.relationship('Tutorial', backref=db.backref('feedbacks', lazy=True))
    usuario = db.relationship('User')

    def __repr__(self):
        return f'<FeedbackTutorial {self.id} - Tutorial {self.tutorial_id} - Util: {self.util}>'

class VisualizacaoTutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Pode ser nulo para visitantes
    data = db.Column(db.DateTime, default=datetime.utcnow)

    tutorial = db.relationship('Tutorial', backref=db.backref('visualizacoes', lazy=True))
    usuario = db.relationship('User')

    def __repr__(self):
        return f'<VisualizacaoTutorial {self.id} - Tutorial {self.tutorial_id}>'

