/**
 * Theme Manager for TI OSN System
 * Gerencia a troca de temas claro/escuro e preferências do usuário
 * @version 2.0.0
 */

class ThemeManager {
    constructor() {
        this.themeToggle = null;
        this.themeIcons = {
            light: null,
            dark: null
        };
        this.transitionDuration = 300; // ms
        this.init();
    }

    init() {
        // Encontra os elementos do tema
        this.themeToggle = document.getElementById('theme-toggle');
        this.themeIcons.light = document.querySelector('.theme-icon-light');
        this.themeIcons.dark = document.querySelector('.theme-icon-dark');
        
        // Carrega o tema salvo ou usa as preferências do sistema
        this.loadTheme();
        
        // Adiciona os event listeners
        this.addEventListeners();
        
        // Aplica o tema inicial
        this.applyTheme();
    }

    loadTheme() {
        // Tenta carregar o tema salvo no localStorage
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Define o tema com base no localStorage ou nas preferências do sistema
        this.currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
        
        // Se não houver tema salvo, usa o preferido pelo sistema
        if (!savedTheme) {
            this.currentTheme = prefersDark ? 'dark' : 'light';
        }
    }

    saveTheme() {
        localStorage.setItem('theme', this.currentTheme);
    }

    applyTheme() {
        const html = document.documentElement;
        
        // Desativa transições durante a mudança de tema
        document.body.classList.add('disable-transitions');
        
        // Aplica o tema ao HTML
        html.setAttribute('data-theme', this.currentTheme);
        // Ajusta color-scheme para controles nativos
        html.style.colorScheme = this.currentTheme === 'dark' ? 'dark' : 'light';

        // Atualiza meta theme-color (PWA/mobile)
        try {
            const metaTheme = document.querySelector('meta[name="theme-color"]') || (function(){
                const m = document.createElement('meta');
                m.setAttribute('name', 'theme-color');
                document.head.appendChild(m);
                return m;
            })();
            const styles = getComputedStyle(html);
            const bgBody = styles.getPropertyValue('--bg-body').trim() || styles.getPropertyValue('--bg-primary').trim() || '#ffffff';
            metaTheme.setAttribute('content', bgBody);
        } catch (e) { /* no-op */ }
        
        // Atualiza os ícones de tema
        this.updateIcons();
        
        // Dispara evento personalizado para notificar outras partes do sistema
        document.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { 
                theme: this.currentTheme,
                isDark: this.currentTheme === 'dark'
            }
        }));
        
        // Feedback para leitores de tela
        this.announceThemeChange();
        
        // Reativa as transições após um pequeno atraso
        setTimeout(() => {
            document.body.classList.remove('disable-transitions');
        }, 10);
    }

    toggleTheme() {
        // Adiciona classe para indicar que uma animação está ocorrendo
        document.body.classList.add('theme-changing');
        
        // Alterna o tema
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.saveTheme();
        this.applyTheme();
        
        // Remove a classe após a animação
        setTimeout(() => {
            document.body.classList.remove('theme-changing');
        }, this.transitionDuration);
    }

    updateIcons() {
        if (!this.themeIcons.light || !this.themeIcons.dark) return;
        
        if (this.currentTheme === 'dark') {
            // No tema escuro, o ícone visível deve ser o SOL (para mudar para o tema claro)
            this.themeIcons.light.classList.remove('d-none');
            this.themeIcons.dark.classList.add('d-none');
            this.themeToggle.setAttribute('aria-label', 'Alternar para tema claro');
            this.themeToggle.setAttribute('title', 'Alternar para tema claro');
        } else {
            // No tema claro, o ícone visível deve ser a LUA (para mudar para o tema escuro)
            this.themeIcons.light.classList.add('d-none');
            this.themeIcons.dark.classList.remove('d-none');
            this.themeToggle.setAttribute('aria-label', 'Alternar para tema escuro');
            this.themeToggle.setAttribute('title', 'Alternar para tema escuro');
        }
    }

    announceThemeChange() {
        const themeStatus = document.createElement('div');
        themeStatus.setAttribute('aria-live', 'polite');
        themeStatus.classList.add('visually-hidden');
        themeStatus.textContent = `Tema alterado para ${this.currentTheme === 'light' ? 'claro' : 'escuro'}`;
        
        document.body.appendChild(themeStatus);
        
        // Remove o elemento após a leitura
        setTimeout(() => {
            themeStatus.remove();
        }, 2000);
    }

    addEventListeners() {
        // Listener para o botão de alternar tema
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });
            
            // Suporte para teclado (Enter/Space)
            this.themeToggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }
        
        // Listener para mudanças nas preferências do sistema
        const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleSystemThemeChange = (e) => {
            // Só atualiza se não houver tema salvo
            if (!localStorage.getItem('theme')) {
                this.currentTheme = e.matches ? 'dark' : 'light';
                this.saveTheme();
                this.applyTheme();
            }
        };
        
        // Adiciona o listener
        if (colorSchemeQuery.addEventListener) {
            colorSchemeQuery.addEventListener('change', handleSystemThemeChange);
        } else {
            // Suporte para navegadores mais antigos
            colorSchemeQuery.addListener(handleSystemThemeChange);
        }
    }
}

// Inicializa o gerenciador de temas quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    
    // Adiciona uma classe ao body quando o JS estiver carregado
    document.body.classList.add('js-loaded');
});
