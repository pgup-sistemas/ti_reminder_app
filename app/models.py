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
    ativo = db.Column(db.Boolean, default=True)  # Novo campo para ativação/desativação
    reminders = db.relationship('Reminder', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)

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
