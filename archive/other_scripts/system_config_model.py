"""
MODELO CONCEITUAL PARA REORGANIZAÇÃO DAS CONFIGURAÇÕES DO SISTEMA TI OSN

Este modelo propõe uma reestruturação das funcionalidades administrativas,
movendo o gerenciamento de usuários e outras configurações para um módulo
centralizado de "Configurações do Sistema".
"""

# ========================================
# ESTRUTURA PROPOSTA DE CONFIGURAÇÕES
# ========================================

SYSTEM_CONFIG_STRUCTURE = {
    "configuracoes": {
        "titulo": "Configurações do Sistema",
        "icone": "cogs",
        "permissoes": ["admin"],
        "modulos": {
            "usuarios": {
                "titulo": "Gerenciamento de Usuários",
                "icone": "users",
                "submodulos": {
                    "listar": {
                        "titulo": "Usuários do Sistema",
                        "rota": "/configuracoes/usuarios",
                        "acao": "Visualizar e gerenciar todos os usuários",
                        "permissoes": ["admin"]
                    },
                    "cadastrar": {
                        "titulo": "Novo Usuário",
                        "rota": "/configuracoes/usuarios/novo",
                        "acao": "Cadastrar novo usuário no sistema",
                        "permissoes": ["admin"]
                    },
                    "perfis": {
                        "titulo": "Perfis e Permissões",
                        "rota": "/configuracoes/usuarios/perfis",
                        "acao": "Gerenciar perfis e permissões de usuários",
                        "permissoes": ["admin"]
                    },
                    "bulk_actions": {
                        "titulo": "Ações em Lote",
                        "rota": "/configuracoes/usuarios/bulk",
                        "acao": "Executar ações em múltiplos usuários",
                        "permissoes": ["admin"]
                    }
                }
            },
            "sistema": {
                "titulo": "Configurações Gerais",
                "icone": "server",
                "submodulos": {
                    "geral": {
                        "titulo": "Configurações Gerais",
                        "rota": "/configuracoes/sistema/geral",
                        "acao": "Configurações básicas do sistema",
                        "permissoes": ["admin"]
                    },
                    "seguranca": {
                        "titulo": "Segurança",
                        "rota": "/configuracoes/sistema/seguranca",
                        "acao": "Configurações de segurança e autenticação",
                        "permissoes": ["admin"]
                    },
                    "backup": {
                        "titulo": "Backup e Restauração",
                        "rota": "/configuracoes/sistema/backup",
                        "acao": "Gerenciar backups do sistema",
                        "permissoes": ["admin"]
                    },
                    "logs": {
                        "titulo": "Logs do Sistema",
                        "rota": "/configuracoes/sistema/logs",
                        "acao": "Visualizar logs e auditoria",
                        "permissoes": ["admin"]
                    }
                }
            },
            "notificacoes": {
                "titulo": "Notificações",
                "icone": "bell",
                "submodulos": {
                    "templates": {
                        "titulo": "Templates de Email",
                        "rota": "/configuracoes/notificacoes/templates",
                        "acao": "Gerenciar templates de notificações",
                        "permissoes": ["admin"]
                    },
                    "regras": {
                        "titulo": "Regras de Notificação",
                        "rota": "/configuracoes/notificacoes/regras",
                        "acao": "Configurar regras de notificações automáticas",
                        "permissoes": ["admin"]
                    },
                    "historico": {
                        "titulo": "Histórico de Notificações",
                        "rota": "/configuracoes/notificacoes/historico",
                        "acao": "Visualizar histórico de notificações enviadas",
                        "permissoes": ["admin"]
                    }
                }
            },
            "integracoes": {
                "titulo": "Integrações",
                "icone": "plug",
                "submodulos": {
                    "email": {
                        "titulo": "Configuração de Email",
                        "rota": "/configuracoes/integracoes/email",
                        "acao": "Configurar servidor de email",
                        "permissoes": ["admin"]
                    },
                    "api": {
                        "titulo": "APIs Externas",
                        "rota": "/configuracoes/integracoes/api",
                        "acao": "Gerenciar integrações com APIs externas",
                        "permissoes": ["admin"]
                    },
                    "rfid": {
                        "titulo": "Sistema RFID",
                        "rota": "/configuracoes/integracoes/rfid",
                        "acao": "Configurar integração RFID",
                        "permissoes": ["admin"]
                    }
                }
            },
            "performance": {
                "titulo": "Performance e Monitoramento",
                "icone": "chart-line",
                "submodulos": {
                    "metricas": {
                        "titulo": "Métricas do Sistema",
                        "rota": "/configuracoes/performance/metricas",
                        "acao": "Monitorar performance do sistema",
                        "permissoes": ["admin"]
                    },
                    "otimizacao": {
                        "titulo": "Otimização",
                        "rota": "/configuracoes/performance/otimizacao",
                        "acao": "Executar otimizações de performance",
                        "permissoes": ["admin"]
                    },
                    "alertas": {
                        "titulo": "Alertas de Sistema",
                        "rota": "/configuracoes/performance/alertas",
                        "acao": "Configurar alertas de sistema",
                        "permissoes": ["admin"]
                    }
                }
            }
        }
    }
}

# ========================================
# ROTAS ATUAIS A SEREM MIGRADAS
# ========================================

CURRENT_ROUTES_TO_MIGRATE = {
    "admin_users": "/admin/users",
    "admin_users_edit": "/admin/users/edit/<int:id>",
    "admin_users_toggle": "/admin/users/toggle/<int:id>",
    "admin_users_delete": "/admin/users/delete/<int:id>",
    "admin_users_reset_password": "/admin/users/reset_password/<int:id>",
    "register": "/register",
    "user_profile": "/profile",
    "performance_dashboard": "/performance/dashboard",
    "satisfaction_dashboard": "/satisfaction/dashboard",
    "rfid_dashboard": "/rfid/dashboard",
    "certifications_dashboard": "/certifications/dashboard"
}

# ========================================
# NOVAS ROTAS PROPOSTAS
# ========================================

NEW_ROUTES_STRUCTURE = {
    # Usuários
    "/configuracoes/usuarios": "system_config.list_users",
    "/configuracoes/usuarios/novo": "system_config.create_user",
    "/configuracoes/usuarios/<int:id>/editar": "system_config.edit_user",
    "/configuracoes/usuarios/<int:id>/toggle": "system_config.toggle_user",
    "/configuracoes/usuarios/<int:id>/deletar": "system_config.delete_user",
    "/configuracoes/usuarios/<int:id>/reset-senha": "system_config.reset_user_password",
    "/configuracoes/usuarios/perfis": "system_config.manage_profiles",
    "/configuracoes/usuarios/bulk": "system_config.bulk_user_actions",

    # Sistema Geral
    "/configuracoes/sistema/geral": "system_config.general_settings",
    "/configuracoes/sistema/seguranca": "system_config.security_settings",
    "/configuracoes/sistema/backup": "system_config.backup_settings",
    "/configuracoes/sistema/logs": "system_config.system_logs",

    # Notificações
    "/configuracoes/notificacoes/templates": "system_config.notification_templates",
    "/configuracoes/notificacoes/regras": "system_config.notification_rules",
    "/configuracoes/notificacoes/historico": "system_config.notification_history",

    # Integrações
    "/configuracoes/integracoes/email": "system_config.email_integration",
    "/configuracoes/integracoes/api": "system_config.api_integrations",
    "/configuracoes/integracoes/rfid": "system_config.rfid_integration",

    # Performance
    "/configuracoes/performance/metricas": "system_config.performance_metrics",
    "/configuracoes/performance/otimizacao": "system_config.performance_optimization",
    "/configuracoes/performance/alertas": "system_config.system_alerts"
}

# ========================================
# ESTRUTURA DE PERMISSÕES
# ========================================

PERMISSIONS_STRUCTURE = {
    "admin": {
        "nivel": 1,
        "descricao": "Administrador completo do sistema",
        "permissoes": [
            "usuarios.criar", "usuarios.editar", "usuarios.deletar", "usuarios.ativar",
            "sistema.configurar", "sistema.backup", "sistema.logs",
            "notificacoes.configurar", "notificacoes.enviar",
            "integracoes.configurar", "integracoes.gerenciar",
            "performance.monitorar", "performance.otimizar"
        ]
    },
    "ti": {
        "nivel": 2,
        "descricao": "Equipe de TI",
        "permissoes": [
            "usuarios.visualizar", "sistema.visualizar",
            "notificacoes.visualizar", "integracoes.visualizar",
            "performance.visualizar"
        ]
    },
    "user": {
        "nivel": 3,
        "descricao": "Usuário comum",
        "permissoes": [
            "perfil.editar", "notificacoes.pessoais"
        ]
    }
}

# ========================================
# TEMPLATE PROPOSTO PARA O MENU
# ========================================

TEMPLATE_NAVIGATION = """
<!-- Menu lateral de configurações -->
<div class="config-sidebar">
    <div class="config-header">
        <h4><i class="fas fa-cogs"></i> Configurações</h4>
    </div>

    <nav class="config-nav">
        <!-- Usuários -->
        <div class="nav-section">
            <div class="nav-section-header" data-toggle="collapse" data-target="#users-menu">
                <i class="fas fa-users"></i> Usuários
                <i class="fas fa-chevron-down float-right"></i>
            </div>
            <div id="users-menu" class="collapse show">
                <a href="{{ url_for('system_config.list_users') }}" class="nav-link">
                    <i class="fas fa-list"></i> Gerenciar Usuários
                </a>
                <a href="{{ url_for('system_config.create_user') }}" class="nav-link">
                    <i class="fas fa-plus"></i> Novo Usuário
                </a>
                <a href="{{ url_for('system_config.manage_profiles') }}" class="nav-link">
                    <i class="fas fa-user-shield"></i> Perfis e Permissões
                </a>
            </div>
        </div>

        <!-- Sistema -->
        <div class="nav-section">
            <div class="nav-section-header" data-toggle="collapse" data-target="#system-menu">
                <i class="fas fa-server"></i> Sistema
                <i class="fas fa-chevron-down float-right"></i>
            </div>
            <div id="system-menu" class="collapse">
                <a href="{{ url_for('system_config.general_settings') }}" class="nav-link">
                    <i class="fas fa-sliders-h"></i> Configurações Gerais
                </a>
                <a href="{{ url_for('system_config.security_settings') }}" class="nav-link">
                    <i class="fas fa-shield-alt"></i> Segurança
                </a>
                <a href="{{ url_for('system_config.backup_settings') }}" class="nav-link">
                    <i class="fas fa-save"></i> Backup
                </a>
            </div>
        </div>

        <!-- Outros módulos seguem o mesmo padrão -->
    </nav>
</div>
"""

# ========================================
# VANTAGENS DA REORGANIZAÇÃO
# ========================================

REORGANIZATION_BENEFITS = [
    "Interface mais intuitiva e organizada",
    "Centralização de todas as configurações administrativas",
    "Melhor controle de permissões por módulo",
    "Facilita manutenção e expansão futura",
    "Experiência mais consistente para administradores",
    "Separação clara entre funcionalidades operacionais e administrativas",
    "Possibilita delegação de responsabilidades por módulo"
]

# ========================================
# PLANO DE IMPLEMENTAÇÃO
# ========================================

IMPLEMENTATION_PLAN = {
    "fase_1": {
        "titulo": "Criar estrutura base",
        "tarefas": [
            "Criar blueprint 'system_config' em app/__init__.py",
            "Criar módulo app/routes/system_config.py",
            "Criar templates base para configurações",
            "Implementar sistema de permissões por módulo"
        ]
    },
    "fase_2": {
        "titulo": "Migrar usuários",
        "tarefas": [
            "Migrar rotas de usuários para /configuracoes/usuarios/*",
            "Atualizar templates de usuários",
            "Testar funcionalidades migradas",
            "Atualizar navegação do admin"
        ]
    },
    "fase_3": {
        "titulo": "Expandir configurações",
        "tarefas": [
            "Implementar configurações gerais do sistema",
            "Migrar configurações de notificações",
            "Adicionar configurações de segurança",
            "Implementar configurações de backup"
        ]
    },
    "fase_4": {
        "titulo": "Otimização e testes",
        "tarefas": [
            "Testes de integração completos",
            "Otimização de performance",
            "Documentação das novas funcionalidades",
            "Treinamento da equipe"
        ]
    }
}

print("MODELO CONCEITUAL CRIADO COM SUCESSO!")
print("Este modelo propõe uma reorganização completa das configurações administrativas,")
print("centralizando todas as funcionalidades em um módulo único e intuitivo.")