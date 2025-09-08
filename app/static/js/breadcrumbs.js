/**
 * Sistema de Breadcrumbs - TI OSN System
 * Navegação clara e intuitiva entre seções
 */

class BreadcrumbManager {
    constructor() {
        this.routes = {
            '/': { title: 'Dashboard', icon: 'fas fa-home' },
            '/dashboard': { title: 'Relatórios', icon: 'fas fa-chart-bar', parent: '/' },
            
            // Atividades
            '/tasks': { title: 'Tarefas', icon: 'fas fa-tasks', parent: '/' },
            '/reminders': { title: 'Lembretes', icon: 'fas fa-bell', parent: '/' },
            
            // Suporte
            '/chamados': { title: 'Chamados', icon: 'fas fa-headset', parent: '/' },
            '/chamados/abrir': { title: 'Abrir Chamado', icon: 'fas fa-plus', parent: '/chamados' },
            '/chamados/\\d+': { title: 'Detalhes do Chamado', icon: 'fas fa-eye', parent: '/chamados', regex: true },
            
            // Equipamentos
            '/equipment': { title: 'Equipamentos', icon: 'fas fa-laptop', parent: '/' },
            '/equipment/list': { title: 'Lista de Equipamentos', icon: 'fas fa-list', parent: '/' },
            '/equipment/new': { title: 'Nova Solicitação', icon: 'fas fa-plus', parent: '/equipment/list' },
            '/equipment/\\d+': { title: 'Detalhes do Equipamento', icon: 'fas fa-eye', parent: '/equipment/list', regex: true },
            '/equipment/\\d+/edit': { title: 'Editar Equipamento', icon: 'fas fa-edit', parent: '/equipment/list', regex: true },
            
            '/tutoriais': { title: 'Tutoriais', icon: 'fas fa-book', parent: '/' },
            '/tutoriais/novo': { title: 'Novo Tutorial', icon: 'fas fa-plus', parent: '/tutoriais' },
            '/tutoriais/\\d+': { title: 'Tutorial', icon: 'fas fa-eye', parent: '/tutoriais', regex: true },
            '/tutoriais/\\d+/editar': { title: 'Editar Tutorial', icon: 'fas fa-edit', parent: '/tutoriais', regex: true },
            
            // Administração
            '/users': { title: 'Usuários', icon: 'fas fa-users', parent: '/' },
            '/users/\\d+/edit': { title: 'Editar Usuário', icon: 'fas fa-user-edit', parent: '/users', regex: true },
            '/register-admin': { title: 'Cadastrar Admin', icon: 'fas fa-user-plus', parent: '/users' },
            
            // Ajuda
            '/help': { title: 'Ajuda', icon: 'fas fa-question-circle', parent: '/' }
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
        let path = currentPath;
        
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
        // Busca exata primeiro
        if (this.routes[path]) {
            return this.routes[path];
        }
        
        // Busca por regex
        for (const [pattern, route] of Object.entries(this.routes)) {
            if (route.regex) {
                const regex = new RegExp(`^${pattern}$`);
                if (regex.test(path)) {
                    return route;
                }
            }
        }
        
        return null;
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
