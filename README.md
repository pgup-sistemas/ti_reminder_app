# TI Reminder App

Aplicativo web para gestão de lembretes e tarefas, com painel de relatórios, exportação de dados e interface intuitiva.

## Funcionalidades

- **Cadastro, edição e exclusão de tarefas**
- **Cadastro, edição e exclusão de lembretes**
- **Lembretes recorrentes** (diários, quinzenais, mensais, anuais)
- **Marcação de lembretes e tarefas como concluídos**
- **Seção "do dia" na tela inicial** mostrando status (✔️/⏰) de tudo que foi feito ou está pendente
- **Filtros avançados** para tarefas e lembretes (status, busca, data)
- **Dashboard de relatórios** com:
  - Resumo visual de tarefas e lembretes
  - Gráficos (pizza) com distribuição dos status
  - Exportação de dados para Excel e PDF (total ou parcial: só tarefas, só lembretes, período, status, etc.)
- **Interface responsiva** com Bootstrap
- **Mensagens de feedback amigáveis** e navegação facilitada

## Bibliotecas necessárias

- flask
- flask-sqlalchemy
- flask-wtf
- python-dateutil
- pandas
- xlsxwriter
- reportlab

Instale todas de uma vez:
```sh
pip install flask flask-sqlalchemy flask-wtf python-dateutil pandas xlsxwriter reportlab
```

## Como usar

1. Clone o repositório e entre na pasta do projeto.
2. Crie um ambiente virtual (opcional, mas recomendado):
   ```sh
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
   ```
3. Instale as dependências:
   ```sh
   pip install -r requirements.txt  # ou use o comando acima
   ```
4. Execute as migrações do banco:
   ```sh
   flask db upgrade
   ```
5. Rode o sistema:
   ```sh
   python run.py
   ```
6. Acesse no navegador: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Próximos Passos

- **Implementação do sistema de login/autenticação de usuários**
  - Controle de acesso às funcionalidades
  - Usuários diferentes com lembretes/tarefas separados

---

Se tiver dúvidas ou quiser sugerir novas funcionalidades, fique à vontade para abrir uma issue ou contribuir!

## Descrição
Aplicação web para gestão de lembretes e tarefas diárias, com envio automático de notificações por e-mail.

---

## 1. Stack Tecnológica
- **Backend:** Python + Flask
- **Frontend:** HTML + Bootstrap 5
- **Banco de Dados:** SQLite (padrão), com possibilidade de uso de PostgreSQL
- **Notificações:** Envio de e-mails via SMTP (ex: Gmail)
- **Outros:**
  - SQLAlchemy (ORM)
  - Flask-Mail
  - Cron (para tarefas agendadas) ou APScheduler

---

## 2. Estrutura de Diretórios
```
ti_reminder_app/
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
│   │   └── reminders.html
│   └── static/
│       └── style.css
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

---

## 3. Funcionalidades
### a. Gestão de Lembretes
- Cadastro de lembretes (nome, tipo, vencimento, responsável, frequência)
- Listagem com status por cor:
  - ✅ Ok
  - 🟡 Alerta
  - 🔴 Vencido
- Edição e exclusão de lembretes

### b. Lista de Tarefas Diárias
- Adição de tarefas diárias
- Marcar tarefas como concluídas
- Exibição separada por data e responsável

### c. Notificações Automáticas
- Envio automático de e-mails X dias antes do vencimento
- Execução diária agendada com cron ou APScheduler

---

## 4. Setup do Projeto
1. Criar ambiente virtual:
    ```sh
    python -m venv venv
    venv\Scripts\activate     # Windows
    # ou
    source venv/bin/activate  # Linux/macOS
    ```
2. Instalar dependências:
    ```sh
    pip install -r requirements.txt
    ```
3. Rodar a aplicação:
    ```sh
    python run.py
    ```

---

## 5. Agendamento de Notificações
- Configurar cron (Linux) para execução diária de lembretes
- Alternativamente, usar APScheduler integrado ao Python para controle programático

---

## 6. Telas Frontend
- **index.html – Resumo Geral**
  - Cards com número de lembretes ativos
  - Lista de tarefas do dia
- **reminders.html – Gestão de Lembretes**
  - Tabela com lembretes, filtros e ações (editar, excluir)
  - Botão “Adicionar Lembrete”
- **tasks.html – Lista de Tarefas**
  - Tarefas pendentes por data
  - Checkbox para marcar como concluída

---

## 7. To-Do para o Desenvolvedor
- Criar formulários com WTForms (ou HTML puro)
- Adicionar login simples (opcional)
- Implementar opção de recorrência (mensal, anual)
- Tornar a interface responsiva com Bootstrap

---

## 8. Etapas Futuras / Melhorias
- Sistema de login de usuário com autenticação
- Melhorias no painel (filtros avançados e cores dinâmicas)
- Adição de recorrência automática de lembretes
- Exportação de dados (CSV, Excel, etc.)
- Dashboard visual com gráficos (ex: Chart.js)
