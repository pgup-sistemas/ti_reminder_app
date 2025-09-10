/* ========================================
   FASE 3 - SISTEMA DE ANIMAÇÕES JAVASCRIPT
   TI OSN System - Helpers de Animação
   ======================================== */

// Intersection Observer para animações on scroll
document.addEventListener('DOMContentLoaded', function() {
    // Configuração do Intersection Observer
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Remove o observer após a animação para performance
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observar todos os elementos com classe animate-on-scroll
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(el => observer.observe(el));

    // Loading states para formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Adicionar spinner ao botão
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="loading-spinner"></span>' + submitBtn.textContent;
                submitBtn.disabled = true;
                
                // Restaurar após 3 segundos (fallback)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });

    // Animação de entrada escalonada para cards
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    dashboardCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate-on-scroll');
    });

    // Animação de entrada para itens de lista
    const listItems = document.querySelectorAll('.list-item-animated');
    listItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
    });

    // Feedback visual para inputs
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.classList.add('form-control-animated');
        
        // Animação de validação
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else if (this.value) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            }
        });
    });

    // Animação para badges
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.classList.add('badge-animated');
    });

    // Hover effects para tabelas
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        if (!row.classList.contains('table-row-animated')) {
            row.classList.add('table-row-animated');
        }
    });

    // Animação de loading para exportações
    const exportButtons = document.querySelectorAll('[href*="export"], [onclick*="export"]');
    exportButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const loadingText = '<span class="loading-spinner"></span>Exportando<span class="loading-dots"></span>';
            const originalText = this.innerHTML;
            
            this.innerHTML = loadingText;
            this.disabled = true;
            
            // Restaurar após 5 segundos
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 5000);
        });
    });

    // Animação suave para dropdowns
    const dropdowns = document.querySelectorAll('.dropdown-menu');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('show.bs.dropdown', function() {
            this.style.opacity = '0';
            this.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                this.style.transition = 'all 0.3s ease';
                this.style.opacity = '1';
                this.style.transform = 'translateY(0)';
            }, 10);
        });
    });

    // Animação para alertas
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.classList.add('animate-on-scroll');
    });

    // Animação para modais
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            const modalDialog = this.querySelector('.modal-dialog');
            modalDialog.style.transform = 'scale(0.8)';
            modalDialog.style.opacity = '0';
            
            setTimeout(() => {
                modalDialog.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                modalDialog.style.transform = 'scale(1)';
                modalDialog.style.opacity = '1';
            }, 10);
        });
    });

    // Performance: Reduzir animações em dispositivos móveis
    if (window.innerWidth <= 768) {
        document.documentElement.style.setProperty('--animation-speed-normal', '0.2s');
        document.documentElement.style.setProperty('--animation-speed-slow', '0.3s');
    }

    // Respeitar preferências de movimento reduzido
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--animation-speed-fast', '0.01s');
        document.documentElement.style.setProperty('--animation-speed-normal', '0.01s');
        document.documentElement.style.setProperty('--animation-speed-slow', '0.01s');
    }
});

// Função para adicionar animação de loading a qualquer elemento
function addLoadingAnimation(element, duration = 3000) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<span class="loading-spinner"></span>' + element.textContent;
    element.disabled = true;
    
    setTimeout(() => {
        element.innerHTML = originalContent;
        element.disabled = false;
    }, duration);
}

// Função para animar contadores
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = Math.floor(current);
        
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, 16);
}

// Função para toast notifications animadas
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-animated bg-${type} text-white position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
            <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Função para smooth scroll
function smoothScrollTo(target, duration = 800) {
    const targetElement = document.querySelector(target);
    if (!targetElement) return;
    
    const targetPosition = targetElement.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }
    
    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }
    
    requestAnimationFrame(animation);
}
