from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                ValidationError)

from .models import User


class RegistrationForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    password2 = PasswordField(
        "Repita a senha", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Registrar")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Nome de usuário já existe.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email já cadastrado.")


class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember_me = BooleanField("Lembrar-me")
    submit = SubmitField("Entrar")


class RequestPasswordResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Solicitar Redefinição")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError("Não existe uma conta com esse email.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nova Senha", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Confirmar Nova Senha", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Redefinir Senha")
