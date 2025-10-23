"""
Validadores customizados para formulários.
"""
import re
from wtforms.validators import ValidationError


class StrongPassword:
    """
    Validador de senha forte que garante:
    - Mínimo de 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    
    def __init__(self, message=None):
        if not message:
            message = (
                'A senha deve ter no mínimo 8 caracteres, incluindo: '
                '1 letra maiúscula, 1 letra minúscula, 1 número e 1 caractere especial (!@#$%^&*)'
            )
        self.message = message
    
    def __call__(self, form, field):
        password = field.data
        
        # Verificar comprimento mínimo
        if len(password) < 8:
            raise ValidationError('A senha deve ter no mínimo 8 caracteres.')
        
        # Verificar letra maiúscula
        if not re.search(r'[A-Z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra maiúscula.')
        
        # Verificar letra minúscula
        if not re.search(r'[a-z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra minúscula.')
        
        # Verificar número
        if not re.search(r'\d', password):
            raise ValidationError('A senha deve conter pelo menos um número.')
        
        # Verificar caractere especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('A senha deve conter pelo menos um caractere especial (!@#$%^&*).')


class UsernameValidator:
    """
    Validador de nome de usuário que garante:
    - Mínimo de 3 caracteres
    - Apenas letras, números, underscore e hífen
    - Não começa com número
    """
    
    def __init__(self, message=None):
        if not message:
            message = (
                'Nome de usuário deve ter no mínimo 3 caracteres e conter apenas '
                'letras, números, underscore (_) e hífen (-)'
            )
        self.message = message
    
    def __call__(self, form, field):
        username = field.data
        
        # Verificar comprimento mínimo
        if len(username) < 3:
            raise ValidationError('Nome de usuário deve ter no mínimo 3 caracteres.')
        
        # Verificar caracteres permitidos
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
            raise ValidationError(self.message)


# Lista de senhas comuns que devem ser rejeitadas
COMMON_PASSWORDS = [
    'password', 'password123', '12345678', 'qwerty', 'abc123',
    'monkey', '1234567890', 'letmein', 'trustno1', 'dragon',
    'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
    'bailey', 'passw0rd', 'shadow', '123123', '654321',
    'superman', 'qazwsx', 'michael', 'football', 'admin',
    'Admin123', 'Password1', 'Welcome1', 'Teste123', 'Senha123'
]


class NoCommonPassword:
    """
    Validador que rejeita senhas comuns.
    """
    
    def __init__(self, message=None):
        if not message:
            message = 'Esta senha é muito comum. Por favor, escolha uma senha mais segura.'
        self.message = message
    
    def __call__(self, form, field):
        password = field.data.lower()
        
        # Verificar contra lista de senhas comuns
        if password in [p.lower() for p in COMMON_PASSWORDS]:
            raise ValidationError(self.message)
