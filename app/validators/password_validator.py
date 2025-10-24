"""
Validador de Senha Dinâmico
Usa configurações do banco de dados para validar requisitos de senha
"""

import re
from flask import current_app
from wtforms.validators import ValidationError


class PasswordValidator:
    """Valida senhas de acordo com configurações do sistema"""
    
    @staticmethod
    def validate(password, return_errors=False):
        """
        Valida senha de acordo com configurações do sistema
        
        Args:
            password: Senha a ser validada
            return_errors: Se True, retorna lista de erros. Se False, retorna bool
            
        Returns:
            bool ou list: True/False ou lista de erros
        """
        from ..services.system_config_service import SystemConfigService
        
        errors = []
        
        # Buscar configurações do banco
        min_length = SystemConfigService.get('security', 'password_min_length', 6)
        require_uppercase = SystemConfigService.get('security', 'password_require_uppercase', True)
        require_lowercase = SystemConfigService.get('security', 'password_require_lowercase', True)
        require_numbers = SystemConfigService.get('security', 'password_require_numbers', True)
        require_special = SystemConfigService.get('security', 'password_require_special', False)
        
        # Validar comprimento mínimo
        if len(password) < min_length:
            errors.append(f"A senha deve ter pelo menos {min_length} caracteres")
        
        # Validar maiúsculas
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula")
        
        # Validar minúsculas
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("A senha deve conter pelo menos uma letra minúscula")
        
        # Validar números
        if require_numbers and not re.search(r'\d', password):
            errors.append("A senha deve conter pelo menos um número")
        
        # Validar caracteres especiais
        if require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
            errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&* etc)")
        
        if return_errors:
            return errors
        
        return len(errors) == 0
    
    @staticmethod
    def get_requirements():
        """
        Retorna os requisitos de senha atuais
        
        Returns:
            dict: Dicionário com requisitos
        """
        from ..services.system_config_service import SystemConfigService
        
        return {
            'min_length': SystemConfigService.get('security', 'password_min_length', 6),
            'require_uppercase': SystemConfigService.get('security', 'password_require_uppercase', True),
            'require_lowercase': SystemConfigService.get('security', 'password_require_lowercase', True),
            'require_numbers': SystemConfigService.get('security', 'password_require_numbers', True),
            'require_special': SystemConfigService.get('security', 'password_require_special', False),
        }
    
    @staticmethod
    def get_requirements_text():
        """
        Retorna texto descritivo dos requisitos
        
        Returns:
            str: Texto formatado com requisitos
        """
        reqs = PasswordValidator.get_requirements()
        text_parts = [f"pelo menos {reqs['min_length']} caracteres"]
        
        if reqs['require_uppercase']:
            text_parts.append("letras maiúsculas")
        if reqs['require_lowercase']:
            text_parts.append("letras minúsculas")
        if reqs['require_numbers']:
            text_parts.append("números")
        if reqs['require_special']:
            text_parts.append("caracteres especiais")
        
        if len(text_parts) == 1:
            return text_parts[0]
        elif len(text_parts) == 2:
            return f"{text_parts[0]} e {text_parts[1]}"
        else:
            return ", ".join(text_parts[:-1]) + f" e {text_parts[-1]}"
    
    @staticmethod
    def get_strength(password):
        """
        Calcula a força da senha (0-100)
        
        Args:
            password: Senha a ser analisada
            
        Returns:
            int: Pontuação de 0 a 100
        """
        score = 0
        
        # Comprimento (até 40 pontos)
        length_score = min(len(password) * 3, 40)
        score += length_score
        
        # Variedade de caracteres (60 pontos distribuídos)
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'\d', password):
            score += 15
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
            score += 15
        
        return min(score, 100)
    
    @staticmethod
    def get_strength_text(score):
        """
        Retorna texto descritivo da força
        
        Args:
            score: Pontuação de 0 a 100
            
        Returns:
            tuple: (texto, cor)
        """
        if score < 30:
            return ("Muito Fraca", "danger")
        elif score < 50:
            return ("Fraca", "warning")
        elif score < 70:
            return ("Razoável", "info")
        elif score < 90:
            return ("Forte", "primary")
        else:
            return ("Muito Forte", "success")


# WTForms Validators

class StrongPassword:
    """
    Validador WTForms para senha forte
    Usa as configurações dinâmicas do sistema
    """
    
    def __init__(self, message=None):
        self.message = message
    
    def __call__(self, form, field):
        password = field.data
        errors = PasswordValidator.validate(password, return_errors=True)
        
        if errors:
            if self.message:
                raise ValidationError(self.message)
            else:
                # Junta todos os erros em uma mensagem
                raise ValidationError(". ".join(errors) + ".")


class UsernameValidator:
    """
    Validador WTForms para nome de usuário
    """
    
    def __init__(self, message=None):
        if not message:
            message = "Nome de usuário deve conter apenas letras, números, sublinhado (_) e hífen (-)."
        self.message = message
    
    def __call__(self, form, field):
        username = field.data
        # Permite letras, números, sublinhado e hífen
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(self.message)


class NoCommonPassword:
    """
    Validador WTForms para evitar senhas comuns
    """
    
    # Lista de senhas mais comuns que devem ser bloqueadas
    COMMON_PASSWORDS = {
        '123456', 'password', '12345678', 'qwerty', '123456789',
        '12345', '1234', '111111', '1234567', 'dragon',
        '123123', 'baseball', 'iloveyou', 'trustno1', '1234567890',
        'senha', 'senha123', 'admin', 'admin123', 'root',
        'toor', 'pass', 'test', 'guest', 'master'
    }
    
    def __init__(self, message=None):
        if not message:
            message = "Esta senha é muito comum. Por favor, escolha uma senha mais segura."
        self.message = message
    
    def __call__(self, form, field):
        password = field.data.lower()
        if password in self.COMMON_PASSWORDS:
            raise ValidationError(self.message)
