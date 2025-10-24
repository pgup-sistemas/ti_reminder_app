from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (BooleanField, DateField, PasswordField, SelectField,
                      StringField, SubmitField, TextAreaField, ValidationError)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from markupsafe import Markup


class ReminderForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired()])
    type = StringField("Tipo", validators=[DataRequired()])
    due_date = DateField("Vencimento", validators=[DataRequired()])
    responsible = StringField("Responsável", validators=[DataRequired()])
    frequency = SelectField(
        "Frequência",
        choices=[
            ("", "Nenhuma"),
            ("diario", "Diário"),
            ("quinzenal", "Quinzenal"),
            ("mensal", "Mensal"),
            ("anual", "Anual"),
        ],
    )
    sector_id = SelectField("Setor", coerce=int, choices=[], validators=[])
    new_sector = StringField("Novo setor")
    status = SelectField(
        "Status",
        choices=[
            ("ativo", "Ativo"),
            ("pausado", "Pausado"),
            ("cancelado", "Cancelado"),
        ],
        default="ativo",
    )
    pause_until = DateField("Pausar até", validators=[Optional()])
    end_date = DateField("Data de fim", validators=[Optional()])
    
    # Novos campos para melhorias profissionais
    priority = SelectField(
        "Prioridade",
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
            ("critica", "Crítica"),
        ],
        default="media",
    )
    category = SelectField(
        "Categoria",
        choices=[
            ("", "Selecione"),
            ("licenca_software", "Licença de Software"),
            ("licenca_banco", "Licença de Banco de Dados"),
            ("contrato", "Contrato"),
            ("certificado", "Certificado SSL/Digital"),
            ("manutencao", "Manutenção"),
            ("backup", "Backup"),
            ("atualizacao", "Atualização"),
            ("auditoria", "Auditoria"),
            ("outro", "Outro"),
        ],
        validators=[Optional()],
    )
    contract_number = StringField("Nº Contrato/Licença", validators=[Optional()])
    cost = StringField("Valor/Custo (R$)", validators=[Optional()])
    supplier = StringField("Fornecedor/Fabricante", validators=[Optional()])
    notes = TextAreaField("Observações", validators=[Optional()])
    
    submit = SubmitField("Salvar")


class TaskForm(FlaskForm):
    description = StringField("Descrição", validators=[DataRequired()])
    date = DateField("Data", validators=[DataRequired()])
    responsible = StringField("Responsável", validators=[DataRequired()])
    completed = BooleanField("Concluída")
    priority = SelectField(
        "Prioridade",
        choices=[
            ("Baixa", "Baixa"),
            ("Normal", "Normal"),
            ("Alta", "Alta"),
            ("Critica", "Crítica"),
        ],
        default="Normal",
        validators=[DataRequired()],
    )
    sector_id = SelectField("Setor", coerce=int, choices=[], validators=[])
    new_sector = StringField("Novo setor")
    submit = SubmitField("Salvar")


from wtforms import (BooleanField, SelectField, StringField, SubmitField,
                     TextAreaField, validators)


class ChamadoForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired()])
    descricao = TextAreaField("Descrição", validators=[DataRequired()])
    prioridade = SelectField(
        "Prioridade",
        choices=[
            ("Baixa", "Baixa"),
            ("Media", "Média"),
            ("Alta", "Alta"),
            ("Critica", "Crítica"),
        ],
        default="Media",
        validators=[DataRequired()],
    )
    setor_id = SelectField("Setor", coerce=int, validators=[Optional()])
    new_sector = StringField("Novo setor")
    submit = SubmitField("Abrir Chamado")

    def __init__(self, *args, **kwargs):
        super(ChamadoForm, self).__init__(*args, **kwargs)
        from .models import Sector

        # Carrega os setores disponíveis
        self.setor_id.choices = [(0, "-- Selecione um setor --")] + [
            (s.id, s.name) for s in Sector.query.order_by("name").all()
        ]


class ChamadoEditForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired()])
    descricao = TextAreaField("Descrição", validators=[DataRequired()])
    setor_id = SelectField("Setor", coerce=int, validators=[Optional()])
    new_sector = StringField("Novo setor")
    submit = SubmitField("Salvar Alterações")

    def __init__(self, *args, **kwargs):
        super(ChamadoEditForm, self).__init__(*args, **kwargs)
        from .models import Sector

        # Carrega os setores disponíveis
        self.setor_id.choices = [(0, "-- Selecione um setor --")] + [
            (s.id, s.name) for s in Sector.query.order_by("name").all()
        ]


class UserRegisterForm(FlaskForm):
    username = StringField("Nome de Usuário", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres"),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar Senha",
        validators=[
            DataRequired(),
            EqualTo("password", message="As senhas não conferem"),
        ],
    )
    is_admin = BooleanField("É Administrador")
    is_ti = BooleanField("É da Equipe de TI")
    submit = SubmitField("Registrar")


class UserEditForm(FlaskForm):
    username = StringField(
        "Nome de Usuário",
        validators=[
            DataRequired(message="Informe o nome de usuário"),
            Length(min=3, max=64, message="O nome de usuário deve ter entre 3 e 64 caracteres"),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Informe o email"),
            Email(message="Informe um email válido"),
            Length(max=120, message="O email deve ter no máximo 120 caracteres"),
        ],
    )
    is_admin = BooleanField("É Administrador")
    is_ti = BooleanField("É da Equipe de TI")
    sector_id = SelectField("Setor", coerce=int, validators=[Optional()], choices=[])
    change_password = BooleanField("Alterar Senha")
    new_password = PasswordField(
        "Nova Senha",
        validators=[Optional()],  # Validação dinâmica será feita no método validate()
    )
    confirm_password = PasswordField(
        "Confirmar Nova Senha",
        validators=[
            Optional(),
            EqualTo("new_password", message="As senhas não conferem"),
        ],
    )
    submit = SubmitField("Salvar Alterações")

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        from .models import Sector

        # Carrega os setores disponíveis
        self.sector_id.choices = [(0, "-- Selecione um setor --")] + [
            (s.id, s.name) for s in Sector.query.order_by("name").all()
        ]

    def validate(self, extra_validators=None):
        """Normaliza dados e executa validações adicionais."""
        if self.username.data:
            self.username.data = self.username.data.strip()

        if self.email.data:
            self.email.data = self.email.data.strip().lower()

        # Validação padrão do Flask-WTF
        if not super().validate(extra_validators):
            return False

        # Validação personalizada para a senha
        # Só valida se change_password estiver marcado E o campo existir (não for disabled)
        if self.change_password.data:
            if not self.new_password.data:
                self.new_password.errors.append("Por favor, insira a nova senha")
                return False
            
            # Validar senha usando PasswordValidator (configurações dinâmicas do banco)
            if self.new_password.data:
                from .validators.password_validator import PasswordValidator
                errors = PasswordValidator.validate(self.new_password.data, return_errors=True)
                if errors:
                    for error in errors:
                        self.new_password.errors.append(error)
                    return False
            
            if self.new_password.data and self.confirm_password.data:
                if self.new_password.data != self.confirm_password.data:
                    self.confirm_password.errors.append("As senhas não conferem")
                    return False

        return True


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Senha Atual",
        validators=[DataRequired(message="Por favor, insira sua senha atual")],
    )
    new_password = PasswordField(
        "Nova Senha",
        validators=[DataRequired(message="Por favor, insira a nova senha")],  # Validação dinâmica em validate()
    )
    confirm_password = PasswordField(
        "Confirmar Nova Senha",
        validators=[
            DataRequired(message="Por favor, confirme a nova senha"),
            EqualTo("new_password", message="As senhas não conferem"),
        ],
    )
    submit = SubmitField("Alterar Senha")
    
    def validate_new_password(self, field):
        """Valida senha usando configurações dinâmicas do banco"""
        if field.data:
            from .validators.password_validator import PasswordValidator
            errors = PasswordValidator.validate(field.data, return_errors=True)
            if errors:
                # Lança apenas o primeiro erro (WTForms padrão)
                raise ValidationError(errors[0])


class ChamadoAdminForm(FlaskForm):
    """Formulário para ações administrativas em chamados"""

    status = SelectField(
        "Status",
        choices=[
            ("Aberto", "Aberto"),
            ("Em Andamento", "Em Andamento"),
            ("Pendente", "Pendente"),
            ("Resolvido", "Resolvido"),
            ("Fechado", "Fechado"),
        ],
        validators=[validators.DataRequired()],
    )

    # Usando StringField em vez de SelectField com coerce=int para evitar erros com valores vazios
    responsavel_ti_id = StringField(
        "Responsável TI", validators=[validators.Optional()]
    )

    comentario = TextAreaField(
        "Adicionar Comentário",
        validators=[
            validators.Optional(),
            validators.Length(
                max=1000, message="O comentário não pode ter mais que 1000 caracteres"
            ),
        ],
    )

    notificar_solicitante = BooleanField("Notificar solicitante", default=True)

    submit = SubmitField("Atualizar Chamado")

    def validate_responsavel_ti_id(self, field):
        # Permite valor vazio ou um número inteiro
        if field.data and not field.data.strip():
            field.data = None
        elif field.data:
            try:
                # Tenta converter para inteiro, mas não armazena o valor convertido
                # apenas valida que é um número inteiro válido
                int(field.data)
            except ValueError:
                raise validators.ValidationError(
                    "ID do responsável deve ser um número inteiro"
                )


class TutorialForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired()])
    conteudo = TextAreaField("Conteúdo", validators=[DataRequired()])
    categoria = StringField("Categoria", validators=[Optional()])
    imagem = FileField(
        "Imagem",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "gif"], "Apenas imagens são permitidas!")
        ],
    )
    submit = SubmitField("Salvar Tutorial")


class ComentarioTutorialForm(FlaskForm):
    texto = TextAreaField("Comentário", validators=[DataRequired()])
    submit = SubmitField("Enviar Comentário")


class FeedbackTutorialForm(FlaskForm):
    util = BooleanField("Este tutorial foi útil para você?")
    submit = SubmitField("Enviar Feedback")
