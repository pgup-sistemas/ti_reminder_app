# Documentação da API - Sistema de Gestão de Equipamentos

## Visão Geral

A API REST do Sistema de Gestão de Equipamentos permite integração com aplicações externas, mobile apps e outros sistemas. A API utiliza autenticação JWT e implementa rate limiting para segurança.

**Base URL:** `http://192.168.1.86:5000/equipment/api/v1`

## Autenticação

### Login JWT

**Endpoint:** `POST /api/v1/auth/login`

**Rate Limit:** 5 tentativas por minuto

**Request Body:**
```json
{
  "username": "usuario",
  "password": "senha"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@email.com",
    "is_admin": false,
    "is_ti": false
  }
}
```

**Uso do Token:**
Inclua o token no header `Authorization`:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Listar Equipamentos

**Endpoint:** `GET /api/v1/equipment`

**Rate Limit:** 100 requisições por hora

**Parâmetros de Query (opcionais):**
- `category`: Filtrar por categoria (Notebook, Monitor, etc.)
- `brand`: Filtrar por marca
- `search`: Busca por nome, patrimônio ou descrição

**Exemplo:**
```
GET /api/v1/equipment?category=Notebook&brand=Dell
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Notebook Dell Latitude 5420",
      "patrimony": "NB001",
      "category": "Notebook",
      "brand": "Dell",
      "model": "Latitude 5420",
      "status": "disponivel",
      "condition": "bom",
      "location": "Sala de TI - Prateleira A1",
      "max_loan_days": 30,
      "requires_approval": true
    }
  ],
  "count": 1
}
```

### 2. Detalhes do Equipamento

**Endpoint:** `GET /api/v1/equipment/{equipment_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Notebook Dell Latitude 5420",
    "description": "Notebook para desenvolvimento...",
    "patrimony": "NB001",
    "serial_number": "ABC123",
    "category": "Notebook",
    "brand": "Dell",
    "model": "Latitude 5420",
    "status": "disponivel",
    "condition": "bom",
    "location": "Sala de TI - Prateleira A1",
    "responsible_sector": "TI",
    "specifications": "{\"ram\": \"16GB\", \"hd\": \"512GB SSD\"}",
    "purchase_date": "2023-01-15",
    "purchase_value": 3500.00,
    "warranty_expiration": "2026-01-15",
    "max_loan_days": 30,
    "requires_approval": true,
    "last_maintenance": "2024-06-15",
    "next_maintenance": "2025-06-15",
    "rfid_tag": "RFID001",
    "created_at": "2023-01-15T10:00:00",
    "updated_at": "2024-06-15T14:30:00"
  }
}
```

### 3. Verificar Disponibilidade

**Endpoint:** `GET /api/v1/equipment/{equipment_id}/availability`

**Parâmetros obrigatórios:**
- `start_date`: Data inicial (YYYY-MM-DD)
- `end_date`: Data final (YYYY-MM-DD)

**Exemplo:**
```
GET /api/v1/equipment/1/availability?start_date=2025-10-20&end_date=2025-10-25
```

**Response:**
```json
{
  "success": true,
  "available": true,
  "message": "Equipamento disponível para o período solicitado"
}
```

### 4. Criar Reserva

**Endpoint:** `POST /api/v1/reservations`

**Rate Limit:** 20 reservas por hora

**Request Body:**
```json
{
  "equipment_id": 1,
  "user_id": 1,
  "start_date": "2025-10-20",
  "end_date": "2025-10-25",
  "purpose": "Desenvolvimento de projeto"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reserva criada com sucesso",
  "reservation_id": 123,
  "status": "confirmada"
}
```

### 5. Devolver Equipamento

**Endpoint:** `POST /api/v1/loans/{loan_id}/return`

**Request Body:**
```json
{
  "returned_by_id": 1,
  "condition": "bom",
  "notes": "Equipamento devolvido em perfeitas condições"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Equipamento devolvido com sucesso"
}
```

### 6. Estatísticas Gerais

**Endpoint:** `GET /api/v1/stats`

**Response:**
```json
{
  "success": true,
  "data": {
    "equipment": {
      "total_equipment": 50,
      "available_equipment": 35,
      "loaned_equipment": 15
    },
    "sla": {
      "total_loans": 150,
      "sla_cumpridos": 135,
      "sla_normais": 10,
      "sla_atencao": 3,
      "sla_vencidos": 2,
      "sla_compliance_rate": 90.0
    },
    "maintenance": {
      "total_with_maintenance": 45,
      "overdue_maintenance": 2,
      "due_soon_maintenance": 5,
      "upcoming_maintenance": 8
    }
  }
}
```

### 7. Empréstimos do Usuário

**Endpoint:** `GET /api/v1/user/{user_id}/loans`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "equipment": {
        "id": 1,
        "name": "Notebook Dell Latitude 5420",
        "patrimony": "NB001",
        "category": "Notebook"
      },
      "loan_date": "2025-10-15T09:00:00",
      "expected_return_date": "2025-10-20",
      "is_overdue": false,
      "days_overdue": 0,
      "sla_status": "normal",
      "sla_display": "Normal"
    }
  ],
  "count": 1
}
```

## Códigos de Status HTTP

- `200`: Sucesso
- `201`: Criado com sucesso
- `400`: Dados inválidos
- `401`: Não autorizado (token inválido/expirado)
- `403`: Acesso proibido
- `404`: Recurso não encontrado
- `429`: Rate limit excedido
- `500`: Erro interno do servidor

## Rate Limiting

- **Login:** 5 tentativas por minuto
- **Listar equipamentos:** 100 requisições por hora
- **Criar reservas:** 20 reservas por hora
- **Global:** 200 requisições por dia, 50 por hora

## Tratamento de Erros

Todos os erros seguem o formato padrão:

```json
{
  "success": false,
  "error": "Descrição do erro"
}
```

## Exemplos de Uso

### Python com Requests

```python
import requests

# Login
login_data = {"username": "usuario", "password": "senha"}
login_response = requests.post("http://192.168.1.86:5000/equipment/api/v1/auth/login", json=login_data)
token = login_response.json()["access_token"]

# Headers para requisições autenticadas
headers = {"Authorization": f"Bearer {token}"}

# Listar equipamentos
equipments = requests.get("http://192.168.1.86:5000/equipment/api/v1/equipment", headers=headers)
print(equipments.json())
```

### JavaScript/Fetch

```javascript
// Login
const loginResponse = await fetch('/equipment/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'usuario', password: 'senha' })
});
const { access_token } = await loginResponse.json();

// Usar token
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};

// Listar equipamentos
const equipmentResponse = await fetch('/equipment/api/v1/equipment', { headers });
const data = await equipmentResponse.json();
console.log(data);
```

## Considerações de Segurança

1. **Sempre use HTTPS** em produção
2. **Armazene tokens de forma segura** no cliente
3. **Implemente refresh tokens** para sessões longas
4. **Valide entrada de dados** no cliente e servidor
5. **Monitore logs de API** para detectar abusos

## Suporte

Para dúvidas sobre a API, consulte a documentação técnica ou entre em contato com a equipe de desenvolvimento.