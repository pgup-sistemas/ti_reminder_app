# Debug - Sistema de Reservas

## Problema Reportado
As rotas `/equipment/admin/dashboard` e `/equipment/admin/pending-approvals` não estão carregando nenhuma solicitação de reserva.

## Correções Aplicadas

### 1. Rota `/equipment/admin/dashboard` Refatorada

**Antes:**
```python
pending_reservations = EquipmentReservation.query.filter_by(status='pendente')\
    .join(Equipment)\
    .order_by(EquipmentReservation.created_at)\
    .all()
```

**Problema:** 
- Só buscava status='pendente' (sem considerar 'pending')
- Sem eager loading (pode causar N+1 queries)
- Sem logs para debug

**Depois:**
```python
pending_reservations = EquipmentReservation.query\
    .filter(
        or_(
            EquipmentReservation.status == 'pendente',
            EquipmentReservation.status == 'pending'
        )
    )\
    .options(
        joinedload(EquipmentReservation.equipment),
        joinedload(EquipmentReservation.user)
    )\
    .order_by(EquipmentReservation.created_at)\
    .all()
```

**Melhorias:**
- ✅ Busca ambos status ('pendente' E 'pending')
- ✅ Eager loading com joinedload
- ✅ Logs detalhados:
  - `[ADMIN_DASHBOARD] Usuário X acessou o dashboard`
  - `[ADMIN_DASHBOARD] Encontradas Y reservas pendentes`
  - `[ADMIN_DASHBOARD] Reserva {i}: ID=X, Status='...', Equipment=..., User=...`

### 2. Rota `/equipment/admin/pending-approvals`

Já estava utilizando `EquipmentService.get_pending_reservations()` que faz a busca correta:

```python
reservations = EquipmentService.get_pending_reservations()
```

**Service implementação:**
```python
def get_pending_reservations():
    query = EquipmentReservation.query\
        .filter(or_(
            EquipmentReservation.status == 'pendente',
            EquipmentReservation.status == 'pending'
        ))\
        .options(
            joinedload(EquipmentReservation.equipment),
            joinedload(EquipmentReservation.user).joinedload(User.sector),
            joinedload(EquipmentReservation.approved_by)
        )\
        .order_by(EquipmentReservation.created_at.desc())
    
    return query.all()
```

### 3. Template Melhorado

Adicionado botão "Ver Todas" no dashboard quando há reservas pendentes.

## Como Verificar

### Passo 1: Verificar Logs do Servidor

Após acessar o dashboard, verifique os logs:

```bash
# No console onde o Flask está rodando, procure por:
[ADMIN_DASHBOARD] Usuário X (admin=True, ti=True) acessou o dashboard administrativo
[ADMIN_DASHBOARD] Encontradas X reservas pendentes
```

### Passo 2: Criar Nova Reserva para Testar

1. Acesse: `http://192.168.1.86:5000/equipment/catalog`
2. Clique em "Reservar" em um equipamento disponível
3. Preencha datas e horários
4. Confirme a reserva

### Passo 3: Verificar se Aparece no Dashboard

1. Acesse: `http://192.168.1.86:5000/equipment/admin/dashboard`
2. Procure pela seção "Reservas Pendentes"
3. A reserva criada deve aparecer na lista

### Passo 4: Verificar Aprovações Pendentes

1. Acesse: `http://192.168.1.86:5000/equipment/admin/pending-approvals`
2. A mesma reserva deve aparecer aqui
3. Verifique os logs:
```bash
[DEBUG] Buscando reservas pendentes...
Usuário X (admin=True, ti=True) acessou pending-approvals. Encontradas X reservas pendentes.
```

## Possíveis Causas se Ainda Não Aparecer

### 1. Status Incorreto
As reservas podem estar sendo criadas com status diferente de 'pendente' ou 'pending'.

**Como verificar:**
```python
# No terminal Python do servidor
from app import create_app
from app.models import EquipmentReservation

app = create_app()
with app.app_context():
    reservas = EquipmentReservation.query.all()
    for r in reservas:
        print(f"ID: {r.id}, Status: '{r.status}'")
```

### 2. Regras de Auto-Aprovação
O método `_check_auto_approval_rules()` pode estar aprovando automaticamente as reservas:

```python
# Verificar o status retornado
requires_approval = EquipmentService._check_auto_approval_rules(user, equipment, days_requested)
# Se retornar False, a reserva é criada como 'confirmada' ao invés de 'pendente'
```

**Regras que causam auto-aprovação:**
- Equipamento não requer aprovação (`equipment.requires_approval == False`)
- Usuário é Admin ou TI
- Empréstimo curto (≤ 7 dias)
- Equipamento de baixo risco (Acessórios, Monitor) e ≤ 14 dias
- Usuário com bom histórico

### 3. Conversão Automática para Empréstimo
Se a reserva não requer aprovação, ela é IMEDIATAMENTE convertida em empréstimo:

```python
if not requires_approval:
    loan, error = EquipmentService.convert_reservation_to_loan(reservation.id)
    # Status muda de 'confirmada' para 'convertida'
```

**Neste caso, a reserva NÃO aparecerá em "Pendentes", mas sim em "Meus Empréstimos"!**

## Solução Temporária para Teste

Para FORÇAR que todas as reservas sejam pendentes (apenas para teste), edite temporariamente:

**Arquivo:** `app/services/equipment_service.py`  
**Linha:** ~229

```python
# ANTES:
status="pendente" if requires_approval else "confirmada"

# DEPOIS (TEMPORÁRIO - APENAS PARA TESTE):
status="pendente"  # TODAS as reservas ficarão pendentes
```

E comente a parte que converte automaticamente:

```python
# Se não requer aprovação, criar empréstimo automaticamente
# if not requires_approval:
#     loan, error = EquipmentService.convert_reservation_to_loan(reservation.id)
```

**IMPORTANTE:** Reverta essas mudanças após o teste!

## Checklist de Verificação

- [ ] Servidor Flask está rodando
- [ ] Você está logado como Admin ou TI
- [ ] Criou pelo menos uma reserva após as correções
- [ ] Verificou os logs do servidor
- [ ] Acessou `/equipment/admin/dashboard`
- [ ] Acessou `/equipment/admin/pending-approvals`
- [ ] Verificou o status das reservas no banco de dados

## Logs Esperados

```
[ADMIN_DASHBOARD] Usuário admin (admin=True, ti=True) acessou o dashboard administrativo
[ADMIN_DASHBOARD] Encontradas 3 reservas pendentes
[ADMIN_DASHBOARD] Reserva 1: ID=5, Status='pendente', Equipment=Dell Inspiron 15, User=raphael
[ADMIN_DASHBOARD] Reserva 2: ID=6, Status='pendente', Equipment=HP EliteBook, User=maria
[ADMIN_DASHBOARD] Reserva 3: ID=7, Status='pending', Equipment=MacBook Pro, User=joao
```

## Próximos Passos

1. Acesse o dashboard e verifique os logs
2. Se não houver reservas pendentes, crie uma nova
3. Verifique se a nova reserva aparece
4. Se ainda não aparecer, execute o script de debug para verificar o banco de dados
5. Reporte os logs encontrados para análise adicional
