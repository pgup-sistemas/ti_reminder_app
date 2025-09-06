# TI OSN System - Sistema Profissional de Gerenciamento

Aplicação web completa para gestão de lembretes, tarefas, chamados de TI, tutoriais e equipamentos, com painel de relatórios avançados, exportação de dados e interface intuitiva. Disponível como Progressive Web App (PWA) com funcionalidade offline e sistema de notificações inteligente.

## 🎯 Status Atual do Sistema - Janeiro 2025

### ✅ **FASE ATUAL: SISTEMA TOTALMENTE FUNCIONAL E OTIMIZADO**

O TI OSN System encontra-se em sua **versão estável e completa**, com todas as funcionalidades principais implementadas e otimizadas. O sistema está pronto para uso em produção com alta performance e experiência de usuário profissional.

### 🚀 **Últimas Implementações Concluídas**

#### **Dashboard Avançado com SLA**
- ✅ **Sistema de Alertas Críticos**: Notificações visuais para SLAs vencidos
- ✅ **Relatórios SLA Completos**: Exportação Excel/PDF com dados de prazo e status
- ✅ **Paginação Inteligente**: Sistema JavaScript avançado para grandes volumes de dados
- ✅ **Filtros Dinâmicos**: Filtros rápidos e avançados para melhor usabilidade
- ✅ **Hierarquia Otimizada**: Cards de resumo em posição proeminente

#### **Sistema de Exportação Profissional**
- ✅ **Exportação SLA**: Relatórios completos com 11 colunas de dados
- ✅ **Correção de Bugs**: Problemas de relacionamento de dados resolvidos
- ✅ **Formatação Excel**: Auto-ajuste de colunas e formatação profissional
- ✅ **Tratamento de Casos Vazios**: Mensagens informativas quando não há dados

#### **Identidade Visual Consistente**
- ✅ **Cor Padrão**: #008BCD aplicada em todos os elementos principais
- ✅ **Favicon SVG**: Ícone vetorial otimizado na cor padrão
- ✅ **Consistência**: Menu, favicon e theme color harmonizados

### 📊 **Funcionalidades Principais - Status Completo**

#### **✅ Gestão de Lembretes e Tarefas** - 100% Implementado
- **Recorrência Automática**: Diários, quinzenais, mensais e anuais
- **Controle Inteligente**: Pausar, reativar ou cancelar lembretes
- **Status Visual**: Ativo, pausado, cancelado, concluído
- **Filtros Avançados**: Por status, data, responsável, setor
- **Notificações**: Alertas por e-mail para lembretes vencidos

#### **✅ Sistema de Chamados de TI** - 100% Implementado + SLA
- **Gestão Completa**: Abertura, acompanhamento e fechamento
- **Sistema SLA**: Controle de prazos com alertas visuais
- **Status em Tempo Real**: Aberto, Em Andamento, Resolvido, Fechado
- **Comentários**: Sistema de comentários nos chamados
- **Notificações**: E-mails automáticos na abertura e atualização
- **Relatórios SLA**: Exportação completa com dados de prazo

#### **✅ Sistema de Tutoriais** - 100% Implementado
- **Criação Avançada**: Suporte a Markdown e imagens
- **Categorização**: Organização por categorias
- **Sistema de Feedback**: Comentários e avaliação dos tutoriais
- **Controle de Visualizações**: Métricas de acesso
- **Exportação PDF**: Geração de tutoriais em PDF

#### **✅ Gestão de Equipamentos** - 100% Implementado
- **Fluxo Completo**: Solicitação, aprovação, entrega e devolução
- **Controle de Status**: Solicitado, Aprovado, Entregue, Devolvido, Negado
- **Dados Técnicos**: Especificações completas
- **Rastreamento**: Histórico completo de movimentações

#### **✅ Dashboard e Relatórios** - 100% Implementado + Melhorias
- **Métricas em Tempo Real**: Contadores de atividades
- **Sistema de Alertas**: Notificações visuais para SLAs críticos
- **Exportação Profissional**: Excel e PDF com formatação avançada
- **Paginação Inteligente**: Suporte para grandes volumes de dados
- **Filtros Dinâmicos**: Sistema de filtros rápidos e avançados

#### **✅ Progressive Web App (PWA)** - 100% Implementado
- **Funcionalidade Offline**: Cache inteligente e sincronização
- **Notificações Push**: Sistema anti-spam otimizado
- **Instalação**: Suporte completo para instalação como app nativo

#### **✅ Sistema de Usuários** - 100% Implementado
- **Controle de Acesso**: Admin, TI e Usuário comum
- **Gestão de Setores**: Criação e administração completa
- **Autenticação**: Sistema seguro com recuperação de senha

### 🎯 **Próximos Passos Recomendados**

O sistema está **completamente funcional** para uso em produção. Possíveis melhorias futuras:

1. **Autenticação 2FA** (opcional)
2. **API REST** para integrações externas (opcional)
3. **Dashboard Analytics** com gráficos avançados (opcional)
4. **Sistema de Backup Automático** (opcional)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Funcionalidades Principais](#funcionalidades-principais)
  - [Gestão de Lembretes e Tarefas](#gestão-de-lembretes-e-tarefas)
  - [Sistema de Chamados de TI](#sistema-de-chamados-de-ti)
  - [Sistema de Tutoriais](#sistema-de-tutoriais)
  - [Gestão de Equipamentos](#gestão-de-equipamentos)
  - [Dashboard e Relatórios](#dashboard-e-relatórios)
- [Progressive Web App (PWA)](#progressive-web-app-pwa)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação e Configuração](#instalação-e-configuração)
  - [Configuração do PostgreSQL](#configuração-do-postgresql)
- [Como Utilizar](#como-utilizar)
- [Planos de Implementação](#planos-de-implementação)
  - [Plano de Ação - Melhorias](#plano-de-ação---melhorias)
  - [Plano de Implementação - Controle de Equipamentos](#plano-de-implementação---controle-de-equipamentos)
- [Configurações Avançadas](#configurações-avançadas)
- [Troubleshooting](#troubleshooting)
- [Contribuição](#contribuição)

## 🎯 Visão Geral

O **TI OSN System** é uma solução completa para gerenciamento de atividades de TI, desenvolvida para facilitar a organização e o acompanhamento de tarefas diárias, lembretes recorrentes, solicitações de suporte técnico, tutoriais e gestão de equipamentos. O sistema centraliza todas as operações de TI em uma única plataforma, permitindo que usuários de todos os setores possam registrar e acompanhar suas solicitações de forma organizada e eficiente.

### 🚀 Principais Benefícios
- **Centralização**: Todas as operações de TI em um só lugar
- **Automação**: Lembretes recorrentes com controle inteligente
- **Rastreabilidade**: Histórico completo de todas as operações
- **Relatórios**: Exportação de dados em Excel e PDF
- **Interface Responsiva**: Funciona em desktop e mobile
- **Controle de Acesso**: Permissões baseadas em roles

## 🔧 Funcionalidades Principais

### 📅 Gestão de Lembretes e Tarefas
- **Lembretes Recorrentes**: Diários, quinzenais, mensais e anuais
- **Controle Inteligente**: Pausar, reativar ou cancelar lembretes
- **Data de Fim**: Definir término automático da recorrência
- **Status Visual**: Ativo, pausado, cancelado, concluído
- **Filtros Avançados**: Por status, data, responsável, setor
- **Recorrência Automática**: Criação automática de novos lembretes
- **Notificações**: Alertas por e-mail para lembretes vencidos

### 🎫 Sistema de Chamados de TI
- **Abertura de Chamados**: Título, descrição, prioridade e setor
- **Acompanhamento**: Status em tempo real (Aberto, Em Andamento, Resolvido, Fechado)
- **Comentários**: Sistema de comentários nos chamados
- **Notificações**: E-mails automáticos na abertura e atualização
- **Filtros**: Por status, prioridade, setor e data
- **Relatórios**: Exportação de chamados para Excel/PDF

#### Funcionalidades Implementadas

1. **Abertura de Novos Chamados:** Usuários autenticados podem criar novos chamados para a TI através de um formulário dedicado. É necessário fornecer um título claro, uma descrição detalhada do problema ou solicitação e definir a prioridade inicial (Baixa, Média, Alta, Crítica).

2. **Listagem de Chamados:** Uma seção permite visualizar os chamados existentes. Usuários comuns podem ver os chamados que abriram ou os chamados relacionados ao seu setor. Administradores e a equipe de TI têm uma visão completa de todos os chamados.

3. **Filtros de Listagem:** A tela de listagem oferece filtros por status (Aberto, Em Andamento, Resolvido, Fechado), prioridade e, para administradores/TI, por setor. Isso facilita a localização e o gerenciamento dos chamados.

4. **Detalhes do Chamado:** É possível visualizar os detalhes completos de um chamado específico, incluindo todas as informações registradas na abertura, datas de criação e atualização, solicitante, setor e o responsável pela TI (se atribuído).

5. **Notificações por E-mail:** Ao abrir um novo chamado, o sistema envia automaticamente notificações por e-mail para o usuário solicitante e para a equipe de TI.

#### Como Utilizar

1. **Acessar:** Após fazer login no sistema, acesse o menu "Chamados".
2. **Abrir Chamado:** Clique em "Abrir Novo Chamado" na tela de listagem. Preencha o formulário com título, descrição e prioridade. Clique em "Abrir Chamado" para submeter.
3. **Listar e Filtrar:** Acesse a seção "Chamados" para ver a lista. Utilize os filtros na parte superior para refinar a visualização por status, prioridade ou setor (se aplicável).
4. **Ver Detalhes:** Clique no botão "Detalhes" na linha correspondente ao chamado na lista para visualizar todas as informações.

### 📚 Sistema de Tutoriais
- **Criação de Tutoriais**: Suporte a Markdown e imagens
- **Categorização**: Organização por categorias
- **Comentários e Feedback**: Sistema de avaliação dos tutoriais
- **Visualizações**: Controle de visualizações por tutorial
- **Exportação PDF**: Geração de tutoriais em PDF
- **Permissões**: Apenas TI pode criar/editar tutoriais

### 🖥️ Gestão de Equipamentos
- **Solicitações**: Formulário completo para solicitar equipamentos
- **Aprovação**: Fluxo de aprovação por TI/Admin
- **Dados Técnicos**: Preenchimento de especificações técnicas
- **Controle de Status**: Solicitado, Aprovado, Entregue, Devolvido, Negado
- **Rastreamento**: Histórico completo de movimentações

#### Campos do Modelo

##### Campos Principais
- **Descrição** - Descrição detalhada do equipamento
- **Patrimônio** - Número do patrimônio do equipamento
- **Data de entrega** - Data prevista/real da entrega
- **Solicitante** - Usuário que solicitou o equipamento
- **Data de devolução** - Data de devolução do equipamento
- **Conferência** - Status de conferência do equipamento
- **Observação** - Observações adicionais
- **Quem recebeu** - Usuário que recebeu o equipamento

##### Campos Adicionais Essenciais
- **Status** - (Solicitado, Aprovado, Entregue, Devolvido, Negado)
- **Data da solicitação** - Data automática da solicitação
- **Quem aprovou** - Usuário TI que aprovou a solicitação
- **Data de aprovação** - Data em que foi aprovado
- **Tipo de equipamento** - Categoria (notebook, monitor, etc.)
- **Setor/Destino** - Para onde o equipamento vai
- **Motivo da solicitação** - Justificativa da solicitação

#### Fluxo de Usuário

##### Para Usuário Comum:
1. Acessar "Equipamentos" no menu
2. Clicar em "Nova Solicitação"
3. Preencher formulário com dados do equipamento
4. Enviar solicitação
5. Acompanhar status na listagem

##### Para TI/Admin:
1. Acessar "Equipamentos" no menu
2. Ver todas as solicitações pendentes
3. Aprovar ou recusar solicitações
4. Marcar como entregue quando equipamento for entregue
5. Marcar como devolvido quando equipamento for devolvido

### 📊 Dashboard e Relatórios
- **Métricas em Tempo Real**: Contadores de atividades
- **Gráficos Interativos**: Visualização de dados por período
- **Filtros Dinâmicos**: Por setor, usuário e período
- **Exportação**: Excel e PDF com formatação profissional
- **Análises**: Tendências e estatísticas de uso

### 👥 Gestão de Usuários
- **Controle de Acesso**: Admin, TI e Usuário comum
- **Gestão de Setores**: Criação e administração de setores
- **Perfis**: Edição de dados pessoais e setoriais
- **Ativação/Desativação**: Controle de acesso de usuários

## 📱 Progressive Web App (PWA)

### Visão Geral
O TI OSN System funciona como um Progressive Web App (PWA), permitindo que os usuários instalem o aplicativo em seus dispositivos e acessem funcionalidades mesmo quando estiverem offline. Esta funcionalidade melhora significativamente a experiência do usuário, garantindo acesso contínuo ao sistema independentemente do status da conexão.

### 🔄 Funcionalidades Offline
- **Navegação Offline**: Acesso às páginas já visitadas mesmo sem conexão com a internet
- **Cache Inteligente**: Armazenamento de recursos estáticos e dados importantes
- **Sincronização em Segundo Plano**: Envio automático de dados quando a conexão for restabelecida
- **Página Offline Personalizada**: Interface amigável informando o status de conexão
- **Armazenamento Local**: Dados temporários salvos no dispositivo até a reconexão

### 🔄 Como Funciona o Modo Offline

1. **Primeira Visita**:
   - O Service Worker é registrado e instalado automaticamente
   - Recursos essenciais são armazenados em cache (HTML, CSS, JS, imagens)
   - Dados básicos são sincronizados para uso offline
   - O cache inicial inclui a página offline personalizada

   ```javascript
   // Trecho do sw.js - Instalação do Service Worker
   self.addEventListener('install', event => {
       console.log('[SW] Installing...');
       event.waitUntil(
           caches.open(CACHE_NAME)
               .then(cache => {
                   console.log('[SW] Caching static assets');
                   return cache.addAll(STATIC_ASSETS);
               })
               .then(() => {
                   console.log('[SW] Installation complete');
                   return self.skipWaiting();
               })
       );
   });
   ```

2. **Durante a Navegação**:
   - Páginas visitadas são automaticamente armazenadas em cache
   - Dados importantes são salvos localmente
   - Interface indica quando o usuário está trabalhando offline através de um badge visual
   - O `OfflineManager` monitora constantemente o status da conexão

   ```javascript
   // Trecho do offline-support.js - Monitoramento de conexão
   window.addEventListener('online', () => {
       this.isOnline = true;
       this.showConnectionStatus('online');
       this.syncPendingData();
   });

   window.addEventListener('offline', () => {
       this.isOnline = false;
       this.showConnectionStatus('offline');
   });
   ```

3. **Quando Offline**:
   - O sistema detecta a falta de conexão usando `navigator.onLine`
   - Recursos são servidos do cache local através do Service Worker
   - Novas ações (criar tarefas, atualizar lembretes) são interceptadas e armazenadas no localStorage
   - Página offline personalizada (`offline.html`) é exibida para rotas não cacheadas
   - Um indicador visual mostra ao usuário que está trabalhando no modo offline

   ```javascript
   // Trecho do sw.js - Fallback para página offline
   .catch(() => {
       // Página offline para navegação
       if (request.mode === 'navigate') {
           return caches.match(OFFLINE_URL);
       }
   });
   ```

4. **Ao Reconectar**:
   - Detecção automática de conexão restabelecida através do evento 'online'
   - Sincronização em segundo plano dos dados pendentes usando Background Sync API
   - Os formulários armazenados no localStorage são enviados ao servidor
   - Atualização do cache com novos dados do servidor
   - Notificação ao usuário sobre a sincronização bem-sucedida

   ```javascript
   // Trecho do offline-support.js - Sincronização de dados
   async syncPendingData() {
       const pendingForms = JSON.parse(localStorage.getItem('pendingForms') || '[]');
       
       if (pendingForms.length === 0) return;

       let syncCount = 0;
       const errors = [];

       for (const formData of pendingForms) {
           try {
               const response = await fetch(formData.action, {
                   method: formData.method,
                   headers: {
                       'Content-Type': 'application/x-www-form-urlencoded',
                   },
                   body: new URLSearchParams(formData.data)
               });

               if (response.ok) {
                   syncCount++;
                   // Remover do localStorage
                   const remaining = pendingForms.filter(f => f.key !== formData.key);
                   localStorage.setItem('pendingForms', JSON.stringify(remaining));
               }
           } catch (error) {
               errors.push(`Erro de rede: ${error.message}`);
           }
       }

       // Mostrar resultados
       if (syncCount > 0) {
           window.components.toast('success', 'Sincronização', 
               `${syncCount} formulário(s) sincronizado(s) com sucesso!`);
       }
   }
   ```

### 🔔 Sistema de Notificações Inteligente

#### Tipos de Notificações e Regras de Negócio

**🔔 Lembretes Vencendo:**
- **Quando aparecem**: Lembretes vencendo em até 7 dias
- **Param quando**: Marcados como concluídos OU passam de 7 dias do vencimento
- **Frequência**: Máximo 1 notificação por 24 horas por lembrete
- **Condições**: `completed == False` e `status == 'ativo'`

**📞 Chamados Atualizados:**
- **Quando aparecem**: Chamados atualizados nas últimas 24 horas
- **Param quando**: Status = "Fechado" OU sem atualizações por 24h
- **Frequência**: Máximo 1 notificação por hora por chamado
- **Condições**: `status != 'Fechado'` e `data_ultima_atualizacao >= ontem`

**⚠️ Tarefas Vencidas:**
- **Quando aparecem**: Tarefas com data < hoje
- **Param quando**: Marcadas como concluídas
- **Frequência**: Máximo 1 notificação a cada 4 horas (agrupadas)
- **Condições**: `completed == False`

#### Sistema Anti-Spam
- **Verificação**: A cada 5 minutos (reduzido de 1 minuto)
- **Cooldown Inteligente**: Cada tipo tem seu próprio intervalo
- **Histórico**: Sistema rastreia notificações já enviadas
- **Limpeza Automática**: Remove dados antigos (24h)
- **Permissões por Usuário**:
  - Admin/TI: Veem todas as notificações do sistema
  - Usuários normais: Apenas seus próprios itens

#### Implementação Técnica
- **Controle de Permissões**: Solicitação inteligente baseada no status atual
- **Personalização**: Ícones, sons e ações personalizadas nas notificações
- **Polling Otimizado**: Verificação a cada 5 minutos com cooldowns individuais
- **Fallback Offline**: Retry automático em caso de falha de conexão

```javascript
// Trecho do notifications.js - Solicitação de permissão
async requestPermission() {
    if (Notification.permission === 'granted') {
        return 'granted';
    }

    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission;
    }

    return Notification.permission;
}

// Trecho do notifications.js - Verificação de atualizações
async checkForUpdates() {
    try {
        const response = await fetch('/api/notifications');
        const data = JSON.parse(await response.text());
        
        // Lembretes vencendo
        if (data.reminders_expiring && data.reminders_expiring.length > 0) {
            data.reminders_expiring.forEach(reminder => {
                this.showNotification('🔔 Lembrete Vencendo!', {
                    body: `${reminder.name} - Responsável: ${reminder.responsible}`,
                    tag: `reminder-${reminder.id}`,
                    requireInteraction: true
                });
            });
        }

        // Chamados atualizados e tarefas vencidas...
    } catch (error) {
        console.error('Erro ao verificar notificações:', error);
    }
}

// Trecho do sw.js - Tratamento de eventos de notificação
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação do TI OSN System',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        actions: [
            {
                action: 'explore',
                title: 'Ver detalhes',
                icon: '/static/icons/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/xmark.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('TI OSN System', options)
    );
});
```

#### Fluxo de Notificações Otimizado
1. **Inicialização Inteligente**: 
   - Verifica permissão atual (`granted`, `denied`, `default`)
   - Mostra mensagem contextual apropriada
   - Evita spam de solicitações

2. **Verificação Controlada**: 
   - A cada 5 minutos (otimizado)
   - Sistema de cooldown por tipo de notificação
   - Rastreamento de notificações já enviadas

3. **Exibição Inteligente**: 
   - Notificações com informações contextuais (status do chamado)
   - Ícones e ações personalizadas
   - URLs corretas para navegação direta

4. **Gerenciamento de Estado**:
   - Mensagens diferentes para cada estado de permissão
   - Opção "Agora Não" com pausa de 24h
   - Limpeza automática de dados antigos

5. **Interação do Usuário**:
   - Navegação direta para conteúdo relevante
   - Auto-fechamento após 10 segundos
   - Botões de teste e reativação

### 📲 Instalação do PWA

#### Recursos de Instalação
- **Chrome/Edge**: Clique no ícone de instalação na barra de endereços ou no menu "Instalar App"
- **Firefox**: Clique no menu e selecione "Instalar" quando a opção aparecer
- **Safari (iOS)**: Toque em "Compartilhar" e depois em "Adicionar à Tela de Início"
- **Página Dedicada**: Interface específica com instruções de instalação em `/install-pwa`
- **Atalhos**: Acesso rápido a funcionalidades específicas direto da tela inicial

#### Implementação

```javascript
// Trecho do install_pwa.html - Captura do evento de instalação
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Previne o comportamento padrão do navegador
    e.preventDefault();
    // Armazena o evento para uso posterior
    deferredPrompt = e;
    // Exibe o botão de instalação
    document.getElementById('installButton').style.display = 'block';
});

// Trecho do install_pwa.html - Manipulação do botão de instalação
document.getElementById('installButton').addEventListener('click', async () => {
    if (deferredPrompt) {
        // Mostra o prompt de instalação
        deferredPrompt.prompt();
        // Aguarda a escolha do usuário
        const { outcome } = await deferredPrompt.userChoice;
        // Registra a escolha do usuário
        console.log(`Usuário ${outcome === 'accepted' ? 'aceitou' : 'recusou'} a instalação`);
        // Limpa a referência ao prompt
        deferredPrompt = null;
        // Esconde o botão de instalação
        document.getElementById('installButton').style.display = 'none';
        
        if (outcome === 'accepted') {
            // Exibe mensagem de sucesso
            showToast('Aplicativo instalado com sucesso!', 'success');
        }
    }
});
```

#### Benefícios Destacados na Interface
1. **Acesso Rápido**: Ícone na tela inicial para acesso com um toque
2. **Experiência Imersiva**: Interface em tela cheia sem elementos do navegador
3. **Notificações Push**: Receba alertas mesmo com o aplicativo fechado
4. **Funcionamento Offline**: Acesse recursos essenciais sem conexão à internet
5. **Sincronização Automática**: Dados enviados automaticamente quando a conexão for restaurada

#### Processo de Instalação
1. O usuário acessa a página de instalação ou recebe o prompt automático
2. O sistema detecta o navegador e exibe instruções específicas
3. Ao clicar em "Instalar Agora", o prompt nativo do navegador é exibido
4. Após a confirmação, o aplicativo é instalado e pode ser acessado como um aplicativo nativo

### ⚙️ Implementação Técnica
- **Service Worker (sw.js)**:
  - Gerencia o ciclo de vida do cache e intercepta requisições de rede
  - Implementa diferentes estratégias de cache para diferentes tipos de conteúdo
  - Gerencia eventos de sincronização em segundo plano e notificações push
  - Fornece uma página offline personalizada quando não há conexão
  - Registrado automaticamente em `base.html` quando o navegador suporta

- **Manifest.json**:
  - Define metadados do aplicativo (nome, descrição, ícones, cores)
  - Configura comportamento de instalação e exibição (standalone)
  - Define atalhos para funcionalidades principais (Novo Lembrete, Nova Tarefa, Abrir Chamado)
  - Especifica screenshots para diferentes dispositivos
  - Configura orientação e tema do aplicativo

- **Estratégias de Cache**:
  - **Cache First**: Para recursos estáticos (CSS, JS, imagens)
    ```javascript
    // Exemplo do sw.js
    if (STATIC_ASSETS.includes(url.pathname) || url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    return response || fetch(request);
                })
        );
    }
    ```
  - **Network First**: Para APIs e conteúdo dinâmico
    ```javascript
    // Exemplo do sw.js
    if (url.pathname.startsWith('/api/') || request.method !== 'GET') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback para cache se offline
                    return caches.match(request);
                })
        );
    }
    ```
  - **Stale-While-Revalidate**: Para conteúdo que pode ser atualizado em segundo plano
  - **Fallback Offline**: Página personalizada quando não há conexão

- **Gerenciamento de Dados Offline**:
  - **OfflineManager**: Classe JavaScript que gerencia o estado de conexão
  - **Interceptação de Formulários**: Armazena dados de formulários enviados offline
  - **Sincronização Automática**: Envia dados armazenados quando a conexão é restabelecida
  - **Indicador Visual**: Badge que mostra o status de conexão atual

- **APIs Utilizadas**:
  - **Cache API**: Armazenamento de recursos para uso offline
  - **IndexedDB**: Armazenamento estruturado de dados para sincronização
  - **Background Sync API**: Sincronização de dados quando a conexão é restabelecida
    ```javascript
    // Exemplo do sw.js
    self.addEventListener('sync', event => {
        if (event.tag === 'background-sync-reminders') {
            event.waitUntil(syncReminders());
        }
        if (event.tag === 'background-sync-tasks') {
            event.waitUntil(syncTasks());
        }
    });
    ```
  - **Notification API**: Gerenciamento de notificações push
  - **Navigator.onLine**: Detecção de status de conexão
  - **localStorage**: Armazenamento temporário de dados offline

## 🛠️ Stack Tecnológica

### Backend
- **Python 3.7+**: Linguagem principal
- **Flask 3.1.1**: Framework web
- **SQLAlchemy 2.0.41**: ORM para banco de dados
- **Flask-WTF 1.2.2**: Formulários e validação
- **Flask-Mail 0.10.0**: Envio de e-mails
- **APScheduler 3.11.0**: Tarefas agendadas
- **Alembic 1.16.1**: Migrações de banco

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Font Awesome**: Ícones
- **JavaScript**: Interatividade e AJAX
- **Chart.js**: Gráficos interativos

### Banco de Dados
- **SQLite**: Banco padrão (desenvolvimento)
- **PostgreSQL**: Banco de produção (opcional)

### Bibliotecas de Suporte
- **Pandas 2.2.3**: Manipulação de dados
- **XlsxWriter 3.2.3**: Exportação Excel
- **ReportLab 4.4.1**: Geração de PDFs
- **Markdown 3.8.2**: Formatação de texto
- **python-dateutil 2.9.0**: Manipulação de datas

## 📁 Estrutura do Projeto

```
ti_reminder_app/
├── app/
│   ├── __init__.py              # Configuração da aplicação
│   ├── routes.py                # Rotas principais
│   ├── models.py                # Modelos do banco de dados
│   ├── forms.py                 # Formulários
│   ├── auth.py                  # Autenticação
│   ├── auth_utils.py            # Utilitários de autenticação
│   ├── forms_auth.py            # Formulários de auth
│   ├── email_utils.py           # Utilitários de e-mail
│   ├── templates/               # Templates HTML
│   │   ├── base.html           # Template base
│   │   ├── index.html          # Página inicial
│   │   ├── reminders.html      # Gestão de lembretes
│   │   ├── tasks.html          # Gestão de tarefas
│   │   ├── dashboard.html      # Dashboard
│   │   ├── users.html          # Gestão de usuários
│   │   ├── tutoriais.html      # Lista de tutoriais
│   │   ├── tutorial_form.html  # Formulário de tutoriais
│   │   ├── tutorial_detalhe.html # Detalhes do tutorial
│   │   ├── chamados/           # Templates de chamados
│   │   └── equipment/          # Templates de equipamentos
│   └── static/                 # Arquivos estáticos
│       ├── style.css           # Estilos CSS
│       ├── js/                 # JavaScript
│       ├── icons/              # Ícones PWA
│       ├── manifest.json       # Manifest PWA
│       └── sw.js              # Service Worker
├── migrations/                 # Migrações do banco
├── instance/                   # Banco de dados
├── config.py                   # Configurações
├── run.py                      # Script de execução
├── requirements.txt            # Dependências
├── wsgi.py                     # WSGI para produção
└── README.md                   # Esta documentação
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- **Python 3.7 ou superior**
- **pip** (gerenciador de pacotes Python)
- **Git** (para clonar o repositório)

### Passo a Passo

#### 1. Clone o Repositório
```bash
git clone [URL_DO_REPOSITORIO]
cd ti_reminder_app
```

#### 2. Crie o Ambiente Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

#### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

#### 4. Configure as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações Básicas
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
FLASK_DEBUG=True

# Banco de Dados (SQLite - padrão)
DATABASE_URL=sqlite:///reminder.db

# Banco de Dados (PostgreSQL - opcional)
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ti_reminder_db

# Configurações de E-mail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-ou-app-password
MAIL_DEFAULT_SENDER=seu-email@gmail.com
TI_EMAIL=ti@empresa.com

# Configurações Opcionais
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216
```

#### 5. Inicialize o Banco de Dados
```bash
# Criar as tabelas
flask db upgrade

# Ou se preferir, execute o script de migração
python migration_reminder_control.py
```

### Configuração do PostgreSQL

#### Pré-requisitos

1. PostgreSQL instalado e em execução
2. Python 3.8 ou superior
3. Todas as dependências do projeto instaladas (`pip install -r requirements.txt`)

#### Configuração Automática

O sistema foi configurado para inicializar automaticamente o banco de dados PostgreSQL na primeira execução. Siga os passos abaixo:

1. Certifique-se de que o PostgreSQL está instalado e em execução
2. Verifique se as credenciais no arquivo `.env` estão corretas:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ti_reminder_db
   ```
   Substitua `postgres:postgres` pelo seu usuário e senha do PostgreSQL, se necessário.
3. Execute o aplicativo normalmente:
   ```
   python run.py
   ```
   Na primeira execução, o sistema irá:
   - Criar o banco de dados `ti_reminder_db` se não existir
   - Inicializar as migrações do Flask-Migrate
   - Aplicar todas as migrações necessárias

#### Configuração Manual

Se preferir configurar manualmente o banco de dados, siga os passos abaixo:

1. Certifique-se de que o PostgreSQL está instalado e em execução
2. Verifique se as credenciais no arquivo `.env` estão corretas
3. Execute o script de configuração:
   ```
   python setup_postgres.py
   ```
   Este script irá:
   - Criar o banco de dados `ti_reminder_db` se não existir
   - Inicializar as migrações do Flask-Migrate
   - Aplicar todas as migrações necessárias

#### Backup e Restauração

##### Backup do Banco de Dados

```bash
pg_dump -U postgres ti_reminder_db > backup_$(date +%Y%m%d).sql
```

##### Restauração do Backup

```bash
psql -U postgres ti_reminder_db < backup_20231201.sql
```

#### 6. Crie um Usuário Administrador
```bash
python create_admin.py
```

#### 7. Execute a Aplicação
```bash
python run.py
```

#### 8. Acesse a Aplicação
Abra seu navegador e acesse: **http://127.0.0.1:5000**

### Configuração de E-mail (Opcional)

Para que as notificações funcionem:

1. **Gmail**: Use "App Password" em vez da senha normal
2. **Outros provedores**: Configure SMTP conforme necessário
3. **Teste**: Verifique se os e-mails estão sendo enviados

## 📖 Como Utilizar

### 🔐 Primeiro Acesso
1. Acesse a aplicação
2. Faça login com as credenciais criadas
3. Configure seu perfil e setor
4. **Ative as notificações** quando solicitado para receber alertas importantes

### 🔔 Configuração de Notificações

#### Estados das Notificações
- **Primeira visita**: Mensagem azul convidativa para ativar
- **Permissão concedida**: Inicia automaticamente, sem mensagens
- **Permissão negada**: Orientações para habilitar manualmente
- **Dispensado**: Não mostra novamente por 24 horas

#### Como Ativar
1. **Automático**: Clique em "Ativar Agora" na mensagem que aparece
2. **Manual**: Clique no ícone de cadeado na barra de endereços do navegador
3. **Configurações**: Acesse configurações do navegador > Notificações

#### Solução de Problemas
- **Não recebo notificações**: Verifique se estão habilitadas no navegador
- **Muitas notificações**: Sistema já otimizado com cooldowns automáticos
- **Notificações param**: Verifique se os itens foram resolvidos conforme as regras

## 📋 Planos de Implementação

### Plano de Ação - Melhorias

Este plano define a implementação das funcionalidades restantes do sistema TI OSN System, organizadas por prioridade e dependências.

#### FASE 1: CONTROLE DE LEMBRETES (Prioridade ALTA)

**Objetivo**: Completar a funcionalidade de controle de lembretes recorrentes

1. **Atualizar Lógica de Recorrência**
2. **Adicionar Rota de Controle de Status**
3. **Atualizar Formulário de Lembretes**
4. **Atualizar Template de Lembretes**

#### FASE 2: SEGURANÇA AVANÇADA (Prioridade ALTA)

**Objetivo**: Implementar autenticação de dois fatores e logs de auditoria

1. **Instalar Dependências**
2. **Criar Modelo de Logs de Auditoria**
3. **Adicionar Campos 2FA ao Usuário**
4. **Criar Utilitário de Auditoria**
5. **Implementar 2FA**

### Plano de Implementação - Controle de Equipamentos

**Objetivo**: Implementação de funcionalidade para controle de equipamentos solicitados para o setor de TI, permitindo solicitação, aprovação, entrega e devolução de equipamentos.

#### Plano de Implementação Detalhado

##### Fase 1: Modelo de Dados
1. **Criar modelo `EquipmentRequest`** em `app/models.py`
2. **Criar migration** para a nova tabela
3. **Executar migration** para criar a tabela no banco

##### Fase 2: Rotas e Controllers
4. **Criar rotas** em `app/routes.py`

##### Fase 3: Templates
5. **Criar templates** para listagem, formulário e detalhes

##### Fase 4: Menu e Navegação
6. **Adicionar item no menu** "Equipamentos"
7. **Configurar permissões** (usuário comum vs TI)

##### Fase 5: Funcionalidades Avançadas
8. **Relatórios** (opcional)
9. **Notificações** (opcional)
10. **Filtros e busca** (opcional)

### 📅 Gestão de Lembretes

#### Criar um Lembrete
1. Acesse **"Lembretes"** no menu
2. Preencha o formulário:
   - **Nome**: Descrição do lembrete
   - **Tipo**: Categoria do lembrete
   - **Vencimento**: Data de vencimento
   - **Responsável**: Quem deve executar
   - **Frequência**: Diário, quinzenal, mensal, anual
   - **Status**: Ativo, pausado, cancelado
   - **Pausar até**: Data para pausa temporária
   - **Data de fim**: Término da recorrência
   - **Setor**: Setor responsável

#### Controle de Recorrência
- **Pausar**: Clique no botão ⏸️ para pausar temporariamente
- **Reativar**: Clique no botão ▶️ para reativar
- **Cancelar**: Mude o status para "cancelado"
- **Data de fim**: Define quando a recorrência para automaticamente

#### Marcar como Concluído
- Clique no botão ✅ para marcar como realizado
- Lembretes concluídos ficam em verde na lista
- **Notificações param**: Automaticamente quando marcado como concluído

#### Regras de Notificação
- **Aparecem**: 7 dias antes do vencimento
- **Frequência**: Máximo 1x por dia por lembrete
- **Param**: Quando concluído ou passa de 7 dias do vencimento

### 🎫 Sistema de Chamados

#### Abrir um Chamado
1. Acesse **"Chamados"** → **"Abrir Novo Chamado"**
2. Preencha:
   - **Título**: Resumo do problema
   - **Descrição**: Detalhes completos
   - **Prioridade**: Baixa, Média, Alta, Crítica
3. Clique em **"Abrir Chamado"**
4. **Notificação automática**: TI é notificada por e-mail

#### Acompanhar Chamados
- **Lista**: Veja todos os seus chamados
- **Filtros**: Por status, prioridade, data
- **Detalhes**: Clique no chamado para ver informações completas
- **Comentários**: Adicione comentários para acompanhamento
- **Status**: Aberto → Em Andamento → Resolvido → Fechado

#### Regras de Notificação
- **Aparecem**: Quando atualizados nas últimas 24h
- **Frequência**: Máximo 1x por hora por chamado
- **Param**: Quando status = "Fechado" ou sem atualizações por 24h
- **Conteúdo**: Mostra número, título e status atual

### 📚 Tutoriais

#### Criar Tutorial (TI/Admin)
1. Acesse **"Tutoriais"** → **"Novo Tutorial"**
2. Preencha:
   - **Título**: Nome do tutorial
   - **Categoria**: Organização
   - **Conteúdo**: Use Markdown para formatação
   - **Imagens**: Adicione imagens explicativas
3. Clique em **"Salvar"**

#### Usar Tutoriais
- **Lista**: Veja todos os tutoriais disponíveis
- **Busca**: Encontre tutoriais por título ou categoria
- **Visualizar**: Clique para ver o tutorial completo
- **Feedback**: Marque se foi útil ou não
- **Comentários**: Adicione dúvidas ou sugestões
- **Exportar**: Baixe em PDF

### 🖥️ Equipamentos

#### Solicitar Equipamento
1. Acesse **"Equipamentos"** → **"Nova Solicitação"**
2. Preencha:
   - **Descrição**: O que precisa
   - **Tipo**: Computador, impressora, etc.
   - **Motivo**: Justificativa da solicitação
   - **Setor de destino**: Onde será usado
   - **Data de entrega**: Quando precisa
3. Clique em **"Solicitar"**

#### Aprovar/Rejeitar (TI/Admin)
- **Lista**: Veja todas as solicitações
- **Aprovar**: Mude status para "Aprovado"
- **Rejeitar**: Mude status para "Negado"
- **Dados técnicos**: Preencha especificações
- **Entregar**: Confirme a entrega

### 📊 Dashboard e Relatórios

#### Visualizar Dashboard
- **Métricas**: Contadores em tempo real
- **Gráficos**: Tendências por período
- **Filtros**: Por setor, usuário, data
- **Atualização**: Dados atualizados automaticamente

#### Exportar Relatórios
1. Acesse **"Dashboard"**
2. Configure os filtros desejados
3. Clique em **"Exportar Excel"** ou **"Exportar PDF"**
4. Baixe o arquivo gerado

## ⚙️ Configurações Avançadas

### Configuração de Banco de Dados

#### SQLite (Padrão)
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///reminder.db'
```

#### PostgreSQL (Produção)
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/ti_reminder'
```

### Configuração de E-mail

#### Gmail
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-app-password
```

#### Outlook/Hotmail
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

### Configuração de Upload

```python
# config.py
UPLOAD_FOLDER = 'app/static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
```

### Configuração de Logs

```python
# config.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('ti_reminder.log'),
        logging.StreamHandler()
    ]
)
```

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro de Módulo não Encontrado
```bash
# Solução: Instalar dependências
pip install -r requirements.txt
```

#### Erro de Banco de Dados
```bash
# Solução: Recriar banco
rm instance/reminder.db
flask db upgrade
```

#### Erro de E-mail
```bash
# Verificar configurações SMTP
# Usar App Password para Gmail
# Verificar firewall/antivírus
```

#### Erro de Permissões
```bash
# Windows: Executar como administrador
# Linux: sudo chmod +x run.py
```

#### Lembretes não Recorrem
```bash
# Verificar se o scheduler está ativo
# Verificar logs da aplicação
# Verificar status dos lembretes
```

### Logs e Debug

#### Habilitar Debug
```python
# config.py
FLASK_DEBUG = True
```

#### Verificar Logs
```bash
# Logs da aplicação
tail -f ti_reminder.log

# Logs do sistema
journalctl -u ti-reminder -f
```

### Backup e Restauração

#### Backup do Banco
```bash
# SQLite
cp instance/reminder.db backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump ti_reminder > backup_$(date +%Y%m%d).sql
```

#### Restaurar Backup
```bash
# SQLite
cp backup_20231201.db instance/reminder.db

# PostgreSQL
psql ti_reminder < backup_20231201.sql
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. **Crie** uma branch para sua feature
3. **Commit** suas mudanças
4. **Push** para a branch
5. **Abra** um Pull Request

### Padrões de Código

- **Python**: PEP 8
- **HTML**: Indentação de 2 espaços
- **CSS**: BEM methodology
- **JavaScript**: ES6+

### Testes

```bash
# Executar testes
python -m pytest tests/

# Cobertura de código
python -m pytest --cov=app tests/
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

### Contato
- **Email**: suporte@ti-reminder.com
- **Issues**: [GitHub Issues](https://github.com/seu-usuario/ti-reminder/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/ti-reminder/wiki)

### Comunidade
- **Discord**: [Servidor da Comunidade](https://discord.gg/ti-reminder)
- **Telegram**: [Grupo de Usuários](https://t.me/ti-reminder)

---

**PageUp Sistemas Desenvolvido com ❤️ por Oézios Normando**

*Última atualização: Dezembro 2024*
