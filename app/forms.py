from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired

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
