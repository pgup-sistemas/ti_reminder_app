from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, BooleanField, SubmitField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class ReminderForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    type = StringField('Tipo', validators=[DataRequired()])
    due_date = DateField('Vencimento', validators=[DataRequired()])
    responsible = StringField('Responsável', validators=[DataRequired()])
    frequency = SelectField('Frequência', choices=[('','Nenhuma'),('diario','Diário'),('quinzenal','Quinzenal'),('mensal','Mensal'),('anual','Anual')])
    sector_id = SelectField('Setor', coerce=int, choices=[], validators=[])
    new_sector = StringField('Novo setor')
    submit = SubmitField('Salvar')

class TaskForm(FlaskForm):
    description = StringField('Descrição', validators=[DataRequired()])
    date = DateField('Data', validators=[DataRequired()])
    responsible = StringField('Responsável', validators=[DataRequired()])
    completed = BooleanField('Concluída')
    sector_id = SelectField('Setor', coerce=int, choices=[], validators=[])
    new_sector = StringField('Novo setor')
    submit = SubmitField('Salvar')



from wtforms import TextAreaField, SelectField, StringField, SubmitField, TextAreaField, BooleanField, validators

class ChamadoForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired()])
    descricao = TextAreaField("Descrição", validators=[DataRequired()])
    prioridade = SelectField("Prioridade", choices=[("Baixa", "Baixa"), ("Media", "Média"), ("Alta", "Alta"), ("Critica", "Crítica")], default="Media", validators=[DataRequired()])
    submit = SubmitField("Abrir Chamado")

class UserRegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas não conferem')
    ])
    is_admin = BooleanField('É Administrador')
    is_ti = BooleanField('É da Equipe de TI')
    submit = SubmitField('Registrar')

class UserEditForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    is_admin = BooleanField('É Administrador')
    is_ti = BooleanField('É da Equipe de TI')
    sector_id = SelectField('Setor', coerce=int, validators=[Optional()], choices=[])
    change_password = BooleanField('Alterar Senha')
    new_password = PasswordField('Nova Senha', validators=[
        Optional(),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[
        Optional(),
        EqualTo('new_password', message='As senhas não conferem')
    ])
    submit = SubmitField('Salvar Alterações')
    
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        from .models import Sector
        # Carrega os setores disponíveis
        self.sector_id.choices = [(0, '-- Selecione um setor --')] + [(s.id, s.name) for s in Sector.query.order_by('name').all()]

    def validate(self, **kwargs):
        # Executa as validações padrão primeiro
        if not super().validate():
            return False

        # Validação personalizada para a senha
        if self.change_password.data and not self.new_password.data:
            self.new_password.errors.append('Por favor, insira a nova senha')
            return False
            
        return True

class ChamadoAdminForm(FlaskForm):
    """Formulário para ações administrativas em chamados"""
    status = SelectField('Status', choices=[
        ('Aberto', 'Aberto'),
        ('Em Andamento', 'Em Andamento'),
        ('Pendente', 'Pendente'),
        ('Resolvido', 'Resolvido'),
        ('Fechado', 'Fechado')
    ], validators=[validators.DataRequired()])
    
    # Usando StringField em vez de SelectField com coerce=int para evitar erros com valores vazios
    responsavel_ti_id = StringField('Responsável TI', validators=[validators.Optional()])
    
    comentario = TextAreaField('Adicionar Comentário', validators=[
        validators.Optional(),
        validators.Length(max=1000, message='O comentário não pode ter mais que 1000 caracteres')
    ])
    
    notificar_solicitante = BooleanField('Notificar solicitante', default=True)
    
    submit = SubmitField('Atualizar Chamado')
    
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
                raise validators.ValidationError('ID do responsável deve ser um número inteiro')

