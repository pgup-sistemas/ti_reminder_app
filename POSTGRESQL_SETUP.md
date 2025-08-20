# Configuração do PostgreSQL para TI OSN System

Este documento contém instruções para configurar o TI OSN System para utilizar o PostgreSQL como banco de dados.

## Pré-requisitos

1. PostgreSQL instalado e em execução
2. Python 3.8 ou superior
3. Todas as dependências do projeto instaladas (`pip install -r requirements.txt`)

## Configuração Automática

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

## Configuração Manual

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

## Verificação da Configuração

Para verificar se a configuração foi bem-sucedida:

1. Execute o aplicativo:
   ```
   python run.py
   ```
2. Acesse o sistema no navegador: `http://localhost:5000`
3. Faça login com suas credenciais

## Troubleshooting

### Erro de Conexão com o PostgreSQL

Se você encontrar erros de conexão com o PostgreSQL, verifique:

1. Se o PostgreSQL está em execução
2. Se as credenciais no arquivo `.env` estão corretas
3. Se o usuário do PostgreSQL tem permissão para criar bancos de dados

### Erro nas Migrações

Se você encontrar erros nas migrações:

1. Remova o arquivo `db_initialized.flag` (se existir)
2. Execute o script de configuração manual:
   ```
   python setup_postgres.py
   ```

## Backup e Restauração

### Backup do Banco de Dados

```bash
pg_dump -U postgres ti_reminder_db > backup_$(date +%Y%m%d).sql
```

### Restauração do Backup

```bash
psql -U postgres ti_reminder_db < backup_20231201.sql
```

## Migração de SQLite para PostgreSQL

Se você estava usando SQLite anteriormente e deseja migrar para PostgreSQL, entre em contato com o suporte para obter instruções específicas para migração de dados.