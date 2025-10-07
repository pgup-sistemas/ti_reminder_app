// JavaScript personalizado para documentação TI OSN System

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar funcionalidades extras
    initializeCards();
    initializeAnimations();
    initializeSearch();
    initializeNavigation();
});

// Cards interativos
function initializeCards() {
    const cards = document.querySelectorAll('.card, .md-typeset .grid > div');

    cards.forEach(card => {
        // Adicionar efeito de hover
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });

        // Tornar cards clicáveis se tiverem link
        const link = card.querySelector('a');
        if (link) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', function(e) {
                if (e.target.tagName !== 'A') {
                    link.click();
                }
            });
        }
    });
}

// Animações suaves
function initializeAnimations() {
    // Intersection Observer para animações de entrada
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observar elementos que devem ser animados
    const animateElements = document.querySelectorAll('.card, .hero, .info');
    animateElements.forEach(el => observer.observe(el));
}

// Melhorar experiência de busca
function initializeSearch() {
    const searchInput = document.querySelector('input[name="q"]');

    if (searchInput) {
        // Adicionar placeholder personalizado
        searchInput.placeholder = 'Buscar na documentação...';

        // Adicionar atalho de teclado
        document.addEventListener('keydown', function(e) {
            // Ctrl+K ou Cmd+K para focar na busca
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
}

// Navegação melhorada
function initializeNavigation() {
    // Adicionar indicador de scroll
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;

        // Atualizar barra de progresso se existir
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = scrollPercent + '%';
        }
    });

    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Função utilitária para copiar código
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Copiado para área de transferência!', 'success');
        }).catch(function(err) {
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

// Fallback para navegadores antigos
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Copiado para área de transferência!', 'success');
        } else {
            showToast('Erro ao copiar', 'error');
        }
    } catch (err) {
        showToast('Erro ao copiar', 'error');
    }

    document.body.removeChild(textArea);
}

// Toast notifications
function showToast(message, type = 'info') {
    // Remover toasts existentes
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        </div>
    `;

    // Adicionar estilos
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideInRight 0.3s ease;
    `;

    document.body.appendChild(toast);

    // Fechar toast
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', function() {
        toast.remove();
    });

    // Auto-remover após 3 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

// Adicionar CSS para animações
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .animate-in {
        animation: fadeInUp 0.6s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .progress-bar {
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: var(--md-primary-fg-color);
        transition: width 0.3s ease;
        z-index: 999;
    }
`;
document.head.appendChild(style);

// Adicionar barra de progresso
const progressBar = document.createElement('div');
progressBar.className = 'progress-bar';
document.body.appendChild(progressBar);