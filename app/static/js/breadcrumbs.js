/**
 * Sistema de Breadcrumbs - TI OSN System
 * Navegação clara e intuitiva entre seções
 */

class BreadcrumbManager {
    constructor() {
        this.routes = {
            // Workspace & inteligência
            '/': { title: 'Meu Workspace', icon: 'fas fa-house' },
            '/dashboard': { title: 'Business Intelligence', icon: 'fas fa-chart-line', parent: '/' },

            // Atividades & notificações
            '/tasks': { title: 'Atividades & Projetos', icon: 'fas fa-clipboard-check', parent: '/' },
            '/tasks/\\d+/edit': { title: 'Editar Atividade', icon: 'fas fa-pen-to-square', parent: '/tasks', regex: true },
            '/reminders': { title: 'Notificações Programadas', icon: 'fas fa-bell-concierge', parent: '/' },
            '/reminders/novo': { title: 'Nova Notificação', icon: 'fas fa-square-plus', parent: '/reminders' },
            '/reminders/\\d+/edit': { title: 'Editar Notificação', icon: 'fas fa-pen', parent: '/reminders', regex: true },

            // Service Desk
            '/chamados': { title: 'Tickets & Suporte', icon: 'fas fa-ticket-alt', parent: '/' },
            '/chamados/abrir': { title: 'Abrir Ticket', icon: 'fas fa-plus-circle', parent: '/chamados' },
            '/chamados/\\d+': { title: 'Detalhes do Ticket', icon: 'fas fa-eye', parent: '/chamados', regex: true },
            '/chamados/\\d+/editar': { title: 'Editar Ticket', icon: 'fas fa-pen-to-square', parent: '/chamados', regex: true },
            '/chamados/\\d+/admin': { title: 'Gestão Avançada', icon: 'fas fa-user-shield', parent: '/chamados', regex: true },

            // Gestão de Ativos (equipment_v2)
            '/equipment': { title: 'Gestão de Ativos', icon: 'fas fa-boxes-stacked', parent: '/' },
            '/equipment/': { title: 'Gestão de Ativos', icon: 'fas fa-boxes-stacked', parent: '/' },
            '/equipment/catalog': { title: 'Catálogo de Ativos', icon: 'fas fa-list', parent: '/equipment' },
            '/equipment/request/\\d+': { title: 'Solicitar Ativo', icon: 'fas fa-paper-plane', parent: '/equipment/catalog', regex: true },
            '/equipment/my-requests': { title: 'Minhas Solicitações', icon: 'fas fa-file-signature', parent: '/equipment' },
            '/equipment/my-loans': { title: 'Meus Empréstimos', icon: 'fas fa-handshake', parent: '/equipment' },
            '/equipment/admin/pending': { title: 'Aprovações Pendentes', icon: 'fas fa-inbox', parent: '/equipment' },
            '/equipment/admin/loans': { title: 'Empréstimos Ativos', icon: 'fas fa-arrows-spin', parent: '/equipment' },
            '/equipment/admin/equipment': { title: 'Inventário de Ativos', icon: 'fas fa-database', parent: '/equipment' },
            '/equipment/admin/equipment/new': { title: 'Novo Ativo', icon: 'fas fa-plus', parent: '/equipment/admin/equipment' },
            '/equipment/admin/equipment/edit/\\d+': { title: 'Editar Ativo', icon: 'fas fa-pen', parent: '/equipment/admin/equipment', regex: true },

            // Base de Conhecimento
            '/tutoriais': { title: 'Base de Conhecimento', icon: 'fas fa-graduation-cap', parent: '/' },
            '/tutoriais/novo': { title: 'Novo Artigo', icon: 'fas fa-square-plus', parent: '/tutoriais' },
            '/tutoriais/\\d+': { title: 'Artigo', icon: 'fas fa-file-lines', parent: '/tutoriais', regex: true },
            '/tutoriais/\\d+/editar': { title: 'Editar Artigo', icon: 'fas fa-pen-to-square', parent: '/tutoriais', regex: true },

            // Administração
            '/admin/users': { title: 'Gestão de Usuários', icon: 'fas fa-users-gear', parent: '/' },
            '/admin/users/edit/\\d+': { title: 'Editar Usuário', icon: 'fas fa-user-pen', parent: '/admin/users', regex: true },
            '/admin/users/reset_password/\\d+': { title: 'Resetar Senha', icon: 'fas fa-key', parent: '/admin/users', regex: true },
            '/admin/users/history/\\d+': { title: 'Histórico do Usuário', icon: 'fas fa-clock-rotate-left', parent: '/admin/users', regex: true },
            '/register-admin': { title: 'Cadastrar Administrador', icon: 'fas fa-user-plus', parent: '/admin/users' },

            // Outros módulos
            '/help': { title: 'Central de Ajuda', icon: 'fas fa-circle-question', parent: '/' }
        };
        
        this.init();
    }

    init() {
        // Aguardar o DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupBreadcrumbs();
            });
        } else {
            this.setupBreadcrumbs();
        }
    }

    setupBreadcrumbs() {
        try {
            // Criar container de breadcrumbs se não existir
            this.createBreadcrumbContainer();
            
            // Gerar breadcrumbs para a página atual
            this.generateBreadcrumbs();
            
            // Observar mudanças na URL (para SPAs futuras)
            window.addEventListener('popstate', () => {
                this.generateBreadcrumbs();
            });
        } catch (error) {
            console.warn('Erro ao inicializar breadcrumbs:', error);
        }
    }

    createBreadcrumbContainer() {
        // Verificar se já existe
        if (document.querySelector('.breadcrumb-container')) return;

        // Encontrar onde inserir (após o navbar)
        const navbar = document.querySelector('.navbar');
        const mainContent = document.querySelector('.main-content');
        
        if (!navbar || !mainContent) return;

        const breadcrumbHTML = `
            <div class="breadcrumb-container">
                <div class="container-fluid">
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb" id="dynamic-breadcrumb">
                            <!-- Breadcrumbs serão inseridos aqui -->
                        </ol>
                    </nav>
                </div>
            </div>
        `;

        // Inserir após o navbar
        navbar.insertAdjacentHTML('afterend', breadcrumbHTML);
    }

    generateBreadcrumbs() {
        const breadcrumbElement = document.getElementById('dynamic-breadcrumb');
        if (!breadcrumbElement) return;

        const currentPath = window.location.pathname;
        const breadcrumbs = this.buildBreadcrumbPath(currentPath);
        
        // Limpar breadcrumbs existentes
        breadcrumbElement.innerHTML = '';
        
        // Gerar HTML dos breadcrumbs
        breadcrumbs.forEach((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;
            const li = document.createElement('li');
            li.className = `breadcrumb-item ${isLast ? 'active' : ''}`;
            
            if (isLast) {
                li.setAttribute('aria-current', 'page');
                li.innerHTML = `
                    <i class="${crumb.icon} me-2"></i>
                    <span>${crumb.title}</span>
                `;
            } else {
                li.innerHTML = `
                    <a href="${crumb.path}" class="breadcrumb-link">
                        <i class="${crumb.icon} me-2"></i>
                        <span>${crumb.title}</span>
                    </a>
                `;
            }
            
            breadcrumbElement.appendChild(li);
        });

        // Mostrar/esconder container baseado no conteúdo
        const container = document.querySelector('.breadcrumb-container');
        if (container) {
            container.style.display = breadcrumbs.length > 1 ? 'block' : 'none';
        }
    }

    buildBreadcrumbPath(currentPath) {
        const breadcrumbs = [];
        let path = this.normalizePath(currentPath);
        
        // Construir caminho de breadcrumbs
        while (path) {
            const route = this.findRoute(path);
            if (route) {
                breadcrumbs.unshift({
                    title: route.title,
                    icon: route.icon,
                    path: path
                });
                path = route.parent;
            } else {
                break;
            }
        }
        
        return breadcrumbs;
    }

    findRoute(path) {
        const normalized = this.normalizePath(path);

        // Busca exata primeiro
        if (this.routes[normalized]) {
            return this.routes[normalized];
        }

        // Busca por regex
        for (const [pattern, route] of Object.entries(this.routes)) {
            if (route.regex) {
                const regex = new RegExp(`^${pattern}$`);
                if (regex.test(normalized)) {
                    return route;
                }
            }
        }

        return null;
    }

    normalizePath(path) {
        if (!path) return '/';
        let normalized = path;

        // Remover query string e hash se presentes
        normalized = normalized.split('?')[0].split('#')[0];

        // Remover trailing slash (exceto raiz)
        if (normalized.length > 1 && normalized.endsWith('/')) {
            normalized = normalized.slice(0, -1);
        }

        return normalized || '/';
    }

    // Método para adicionar rotas dinamicamente
    addRoute(path, config) {
        this.routes[path] = config;
    }

    // Método para atualizar breadcrumbs manualmente
    update() {
        this.generateBreadcrumbs();
    }

    // Método para definir título personalizado da página atual
    setCurrentTitle(title, icon = null) {
        const breadcrumbElement = document.getElementById('dynamic-breadcrumb');
        if (!breadcrumbElement) return;

        const activeItem = breadcrumbElement.querySelector('.breadcrumb-item.active');
        if (activeItem) {
            const span = activeItem.querySelector('span');
            const iconElement = activeItem.querySelector('i');
            
            if (span) span.textContent = title;
            if (icon && iconElement) iconElement.className = `${icon} me-2`;
        }
    }

    // Método para adicionar breadcrumb customizado
    addCustomBreadcrumb(title, icon = 'fas fa-folder', path = null) {
        const breadcrumbElement = document.getElementById('dynamic-breadcrumb');
        if (!breadcrumbElement) return;

        // Remover active do último item
        const currentActive = breadcrumbElement.querySelector('.breadcrumb-item.active');
        if (currentActive) {
            currentActive.classList.remove('active');
            currentActive.removeAttribute('aria-current');
            
            // Converter para link
            const content = currentActive.innerHTML;
            currentActive.innerHTML = `<a href="${window.location.pathname}" class="breadcrumb-link">${content}</a>`;
        }

        // Adicionar novo item ativo
        const li = document.createElement('li');
        li.className = 'breadcrumb-item active';
        li.setAttribute('aria-current', 'page');
        li.innerHTML = `
            <i class="${icon} me-2"></i>
            <span>${title}</span>
        `;
        
        breadcrumbElement.appendChild(li);
        
        // Mostrar container
        const container = document.querySelector('.breadcrumb-container');
        if (container) {
            container.style.display = 'block';
        }
    }
}

// Instância global
window.Breadcrumbs = new BreadcrumbManager();

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BreadcrumbManager;
}
