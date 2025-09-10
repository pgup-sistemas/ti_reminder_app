# Guia de Testes - TI Reminder App

## 📋 Visão Geral

Este documento descreve a suíte completa de testes automatizados implementada para o TI Reminder App, incluindo testes unitários, de integração e end-to-end (E2E).

## 🏗️ Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                 # Configurações globais
├── unit/                       # Testes unitários
│   ├── __init__.py
│   ├── test_models.py         # Testes dos models
│   └── test_utils.py          # Testes dos utilitários
├── integration/                # Testes de integração
│   ├── __init__.py
│   ├── test_routes.py         # Testes das rotas
│   └── test_auth.py           # Testes de autenticação
└── e2e/                       # Testes end-to-end
    ├── __init__.py
    ├── conftest.py            # Config específica E2E
    └── test_user_flows.py     # Fluxos completos de usuário
```

## 🔧 Configuração do Ambiente

### 1. Instalar Dependências

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Para testes locais
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///test.db
export SECRET_KEY=test-secret-key
```

## 🧪 Tipos de Teste

### Testes Unitários

Testam componentes individuais isoladamente:

- **Models**: Validação de criação, relacionamentos, métodos
- **Utils**: Funções utilitárias e helpers
- **Validações**: Regras de negócio específicas

**Executar:**
```bash
pytest tests/unit/ -v
```

### Testes de Integração

Testam interação entre componentes:

- **Rotas**: Endpoints da API
- **Autenticação**: Login, logout, permissões
- **Fluxos de dados**: Criação, edição, exclusão

**Executar:**
```bash
pytest tests/integration/ -v
```

### Testes End-to-End (E2E)

Testam fluxos completos do usuário:

- **Interface web**: Navegação, formulários
- **Fluxos de usuário**: Login → Ação → Resultado
- **Responsividade**: Diferentes tamanhos de tela

**Executar:**
```bash
pytest tests/e2e/ -v
```

## 🚀 Scripts de Automação

### 1. Script Principal de Testes

```bash
# Executar todos os testes
python scripts/run_tests.py --all

# Executar apenas testes unitários
python scripts/run_tests.py --unit

# Executar com verificações de código
python scripts/run_tests.py --lint

# Instalar dependências e executar tudo
python scripts/run_tests.py --install --all
```

### 2. Health Check

```bash
# Verificar saúde da aplicação
python scripts/health_check.py

# Com URL customizada
python scripts/health_check.py --url http://localhost:8000

# Com retry
python scripts/health_check.py --retry 3 --wait 5
```

### 3. Deploy Automatizado

```bash
# Deploy para staging
python scripts/deploy.py --env staging

# Deploy para produção
python scripts/deploy.py --env production

# Simular deploy (dry-run)
python scripts/deploy.py --dry-run
```

## 📊 Relatórios e Coverage

### Coverage de Código

```bash
# Gerar relatório de coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Ver relatório HTML
open htmlcov/index.html
```

### Relatórios de Teste

```bash
# Gerar relatório HTML
pytest --html=reports/report.html --self-contained-html

# Gerar relatório JUnit XML
pytest --junitxml=reports/junit.xml
```

## 🔍 Marcadores de Teste

Use marcadores para executar grupos específicos:

```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes E2E
pytest -m e2e

# Pular testes lentos
pytest -m "not slow"

# Apenas testes de autenticação
pytest -m auth

# Apenas testes de banco de dados
pytest -m database
```

## 🛠️ Fixtures Disponíveis

### Fixtures Globais (conftest.py)

- `app`: Instância da aplicação Flask
- `client`: Cliente de teste Flask
- `db_session`: Sessão de banco para cada teste
- `admin_user`: Usuário administrador
- `regular_user`: Usuário comum
- `ti_user`: Usuário da equipe TI
- `sample_sector`: Setor de exemplo
- `authenticated_client`: Cliente logado como admin
- `test_factory`: Factory para criar dados de teste

### Fixtures E2E (e2e/conftest.py)

- `selenium_app`: Aplicação para testes Selenium
- `live_server`: Servidor Flask rodando
- `driver`: Driver Chrome do Selenium
- `logged_in_driver`: Driver com usuário logado

## 📝 Exemplos de Uso

### Teste Unitário Simples

```python
@pytest.mark.unit
def test_user_creation(db_session):
    user = User(username='test', email='test@test.com')
    user.set_password('password123')
    
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.check_password('password123')
```

### Teste de Integração

```python
@pytest.mark.integration
def test_login_flow(client, regular_user):
    response = client.post('/auth/login', data={
        'username': regular_user.username,
        'password': 'user123'
    })
    
    assert response.status_code == 302
    assert '/dashboard' in response.location
```

### Teste E2E

```python
@pytest.mark.e2e
def test_create_reminder_flow(logged_in_driver, live_server):
    logged_in_driver.get(f'{live_server}/add_reminder')
    
    name_field = logged_in_driver.find_element(By.NAME, 'name')
    name_field.send_keys('Teste E2E')
    
    submit_button = logged_in_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_button.click()
    
    assert 'Teste E2E' in logged_in_driver.page_source
```

## 🔄 CI/CD Pipeline

### GitHub Actions

O pipeline automatizado executa:

1. **Verificações de código**: flake8, black, isort
2. **Testes unitários**: com coverage
3. **Testes de integração**: com banco PostgreSQL
4. **Verificações de segurança**: safety, bandit
5. **Testes E2E**: apenas no branch main
6. **Deploy automático**: staging (develop) e produção (main)

### Configuração Local

```bash
# Instalar pre-commit hooks
pre-commit install

# Executar verificações antes do commit
pre-commit run --all-files
```

## 🐛 Debugging de Testes

### Testes Falhando

```bash
# Executar com mais detalhes
pytest -v --tb=long

# Parar no primeiro erro
pytest -x

# Executar apenas testes que falharam
pytest --lf

# Modo debug interativo
pytest --pdb
```

### Testes E2E

```bash
# Executar com browser visível (sem headless)
HEADLESS=false pytest tests/e2e/

# Salvar screenshots em caso de erro
pytest tests/e2e/ --screenshot-on-failure
```

## 📈 Métricas de Qualidade

### Metas de Coverage

- **Unitários**: > 90%
- **Integração**: > 80%
- **Geral**: > 85%

### Tempo de Execução

- **Unitários**: < 30 segundos
- **Integração**: < 2 minutos
- **E2E**: < 5 minutos
- **Pipeline completo**: < 10 minutos

## 🔧 Troubleshooting

### Problemas Comuns

1. **Banco de dados não limpo entre testes**
   - Solução: Verificar fixture `db_session`

2. **Testes E2E falhando por timeout**
   - Solução: Aumentar `implicitly_wait` ou usar `WebDriverWait`

3. **Dependências conflitantes**
   - Solução: Usar ambiente virtual isolado

4. **Permissões de arquivo**
   - Solução: `chmod +x scripts/*.py`

### Logs e Debug

```bash
# Logs detalhados
pytest --log-cli-level=DEBUG

# Capturar stdout/stderr
pytest -s

# Executar teste específico
pytest tests/unit/test_models.py::TestUser::test_create_user -v
```

## 📚 Recursos Adicionais

- [Documentação pytest](https://docs.pytest.org/)
- [Selenium Python](https://selenium-python.readthedocs.io/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Última atualização**: 2024-12-10
**Versão**: 1.0.0
