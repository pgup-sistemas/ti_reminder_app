# TI Reminder App

Aplicação web para gestão de lembretes, tarefas e chamados de TI, com painel de relatórios, exportação de dados e interface intuitiva.

## Índice
- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Setup do Projeto](#setup-do-projeto)
- [Como Utilizar](#como-utilizar)
- [Próximos Passos](#próximos-passos)
- [Considerações Técnicas](#considerações-técnicas)

## Visão Geral

O TI Reminder é uma solução completa para gestão de tarefas, lembretes e chamados de TI. O sistema foi projetado para facilitar a organização e o acompanhamento de atividades diárias, além de centralizar as solicitações de suporte técnico para a equipe de TI, permitindo que usuários de todos os setores possam registrar e acompanhar seus pedidos de forma organizada e eficiente.

## Funcionalidades

### Gestão de Tarefas e Lembretes
- **Cadastro, edição e exclusão de tarefas**
- **Cadastro, edição e exclusão de lembretes**
- **Lembretes recorrentes** (diários, quinzenais, mensais, anuais)
- **Marcação de lembretes e tarefas como concluídos**
- **Seção "do dia" na tela inicial** mostrando status (✔️/⏰) de tudo que foi feito ou está pendente
- **Filtros avançados** para tarefas e lembretes (status, busca, data)
- **Lista de Tarefas Diárias** com marcação de conclusão
- **Notificações Automáticas** por e-mail para lembretes

### Sistema de Chamados de TI
- **Abertura de Novos Chamados** com título, descrição e prioridade
- **Listagem de Chamados** com filtros por status, prioridade e setor
- **Visualização Detalhada** de cada chamado
- **Notificações por E-mail** na abertura de novos chamados
- **Integração com Usuários e Setores**
- **Permissões Personalizadas** para diferentes níveis de acesso

### Relatórios e Análises
- **Dashboard de relatórios** com:
  - Resumo visual de tarefas e lembretes
  - Gráficos (pizza) com distribuição dos status
  - Exportação de dados para Excel e PDF

### Interface
- **Interface responsiva** com Bootstrap 5
- **Mensagens de feedback amigáveis**
- **Navegação intuitiva**
- **Design limpo e profissional**

## Stack Tecnológica
- **Backend:** Python + Flask
- **Frontend:** HTML + Bootstrap 5
- **Banco de Dados:** SQLite (padrão), com suporte a PostgreSQL
- **Notificações:** Envio de e-mails via SMTP (ex: Gmail)
- **Outras Bibliotecas:**
  - SQLAlchemy (ORM)
  - Flask-Mail
  - Flask-WTF
  - Python-dateutil
  - Pandas (exportação de dados)
  - XlsxWriter (exportação para Excel)
  - ReportLab (exportação para PDF)
  - APScheduler (tarefas agendadas)

## Estrutura de Diretórios
```
ti_reminder/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── forms.py
│   ├── email_utils.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── tasks.html
│   │   ├── reminders.html
│   │   ├── chamados/
│   │   │   ├── listar.html
│   │   │   ├── abrir.html
│   │   │   └── detalhes.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── migrations/
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

## Setup do Projeto

1. **Pré-requisitos**
   - Python 3.7+
   - pip (gerenciador de pacotes Python)
   - Banco de dados (SQLite incluso, PostgreSQL opcional)

2. **Configuração do Ambiente**
   ```bash
   # 1. Clone o repositório
   git clone [URL_DO_REPOSITORIO]
   cd ti_reminder

   # 2. Crie e ative o ambiente virtual (recomendado)
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate

   # 3. Instale as dependências
   pip install -r requirements.txt

   # 4. Configure as variáveis de ambiente
   # Crie um arquivo .env baseado no .env.example
   # Edite as configurações conforme necessário

   # 5. Inicialize o banco de dados
   flask db upgrade

   # 6. Execute a aplicação
   python run.py
   ```

3. **Acesse a aplicação**
   Abra seu navegador e acesse: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Como Utilizar

### Gestão de Tarefas e Lembretes
1. **Acesse** a aplicação e faça login
2. **Adicione tarefas** através da seção "Tarefas"
3. **Crie lembretes** recorrentes ou únicos
4. **Acompanhe** suas atividades na página inicial
5. **Receba notificações** por e-mail de lembretes

### Sistema de Chamados de TI
1. **Acesse** a seção "Chamados"
2. **Clique em** "Abrir Novo Chamado"
3. **Preencha** o formulário com as informações necessárias
4. **Acompanhe** o status do seu chamado na lista
5. **Receba notificações** por e-mail sobre atualizações

### Relatórios
1. **Acesse** o painel de relatórios
2. **Filtre** os dados conforme necessário
3. **Exporte** para Excel ou PDF

## Configuração de E-mail
Para que as notificações por e-mail funcionem, configure as seguintes variáveis de ambiente no arquivo `.env`:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-ou-app-password
MAIL_DEFAULT_SENDER=seu-email@gmail.com
TI_EMAIL=ti@empresa.com  # E-mail da equipe de TI para notificações
```

## Próximos Passos

### Melhorias para implementar
- [ ] **Sistema de Comentários** nos chamados
- [ ] **Atualização de Status** pelos técnicos de TI
- [ ] **Anexos** em chamados
- [ ] **Dashboard Avançado** com métricas


### Melhorias Futuras
- [ ] **API REST** para integração com outros sistemas
- [ ] **Aplicativo Móvel**
- [ ] **Autenticação de Dois Fatores**
- [ ] **Logs Detalhados**
- [ ] **Sistema de Pesquisa Avançada**

## Considerações Técnicas

1. **Segurança**
   - Todas as senhas são armazenadas com hash seguro
   - Proteção contra CSRF
   - Validação de entrada em todos os formulários
   - Controle de acesso baseado em papéis (RBAC)

2. **Desempenho**
   - Cache de consultas frequentes
   - Paginação de resultados
   - Otimização de consultas ao banco de dados

3. **Escalabilidade**
   - Projeto estruturado para escalar horizontalmente
   - Uso de filas para processamento assíncrono
   - Suporte a múltiplos workers

## Suporte

Em caso de dúvidas ou problemas, entre em contato com a equipe de TI ou abra uma issue no repositório do projeto.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo LICENSE para obter mais informações.
