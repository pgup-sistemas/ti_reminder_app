# 📊 Resumo - Badge de Notificação para Chamados

## 🎯 Objetivo

Adicionar um **badge visual com contador** no menu "Tickets & Suporte" (igual ao que existe em "Gestão de Ativos") para mostrar a quantidade de **chamados abertos** que requerem atenção.

---

## 📋 Situação Atual

### ✅ Como funciona em "Gestão de Ativos"

**Localização:** Menu "Gestão de Ativos" → "Aprovar Solicitações"

```
┌─────────────────────────────────────────┐
│ Gestão de Ativos                  ▼     │
├─────────────────────────────────────────┤
│ ✓ Dashboard de Ativos                   │
│ ✓ Solicitar Ativo                       │
│ ✓ Minhas Solicitações                   │
│ ✓ Aprovar Solicitações          [5]     │  ← Badge vermelho com contador
│ ✓ Gerenciar Empréstimos                 │
└─────────────────────────────────────────┘
```

**Arquivos envolvidos:**

1. **`app/__init__.py`** (linhas 187-203)
   - Função: `inject_pending_approvals()`
   - Conta solicitações com status "Solicitado"
   - Injeta variável `pending_approvals_count` em todos os templates
   - Visível apenas para Admin e TI

2. **`app/templates/base.html`** (linhas 317-322)
   ```html
   {% if pending_approvals_count and pending_approvals_count > 0 %}
   <span class="badge rounded-pill bg-danger">
     {{ pending_approvals_count }}
   </span>
   {% endif %}
   ```

3. **`app/services/equipment_service.py`**
   - Função: `EquipmentService.count_pending_approvals()`
   - Query: `EquipmentRequest.query.filter_by(status='Solicitado').count()`

---

## 🎨 O que vamos criar

### Badge para "Tickets & Suporte"

**Localização:** Menu "Tickets & Suporte" → "Meus Tickets"

```
┌─────────────────────────────────────────┐
│ Tickets & Suporte                 ▼     │
├─────────────────────────────────────────┤
│ ✓ Abrir Ticket                          │
│ ✓ Meus Tickets                  [3]     │  ← NOVO: Badge vermelho com contador
└─────────────────────────────────────────┘
```

### Lógica de Contagem

**Para usuários normais:**
- Contar chamados **ABERTOS** que o usuário criou
- Status considerados: "Aberto", "Em Andamento"
- Excluir: "Resolvido", "Fechado"

**Para Admin/TI:**
- Contar **TODOS** os chamados abertos no sistema
- Útil para ver rapidamente quantos tickets precisam de atenção

---

## 🔧 Implementação Planejada

### 1. **Criar serviço de contagem** (opcional, podemos fazer direto)

**Opção A: Direto no context_processor**
```python
# Em __init__.py
if current_user.is_authenticated:
    if current_user.is_admin or current_user.is_ti:
        # Todos os chamados abertos
        chamados_count = Chamado.query.filter(
            Chamado.status.in_(['Aberto', 'Em Andamento'])
        ).count()
    else:
        # Apenas chamados do usuário
        chamados_count = Chamado.query.filter(
            Chamado.solicitante_id == current_user.id,
            Chamado.status.in_(['Aberto', 'Em Andamento'])
        ).count()
```

**Opção B: Criar função no modelo Chamado** (mais organizado)
```python
# Em models.py
class Chamado(db.Model):
    @staticmethod
    def count_open_tickets(user=None):
        """Conta tickets abertos (para badge)"""
        query = Chamado.query.filter(
            Chamado.status.in_(['Aberto', 'Em Andamento'])
        )
        if user and not (user.is_admin or user.is_ti):
            query = query.filter(Chamado.solicitante_id == user.id)
        return query.count()
```

### 2. **Modificar context_processor**

```python
# Em __init__.py, linha ~203
@app.context_processor
def inject_pending_approvals():
    from flask_login import current_user
    from .services.equipment_service import EquipmentService
    from .models import Chamado  # NOVO
    
    pending_count = 0
    chamados_abertos_count = 0  # NOVO
    
    if current_user.is_authenticated:
        # Contagem de equipamentos (já existe)
        if current_user.is_admin or current_user.is_ti:
            try:
                pending_count = EquipmentService.count_pending_approvals()
            except Exception as e:
                app.logger.error(f"Erro ao contar aprovações: {str(e)}")
        
        # NOVO: Contagem de chamados
        try:
            chamados_abertos_count = Chamado.count_open_tickets(current_user)
        except Exception as e:
            app.logger.error(f"Erro ao contar chamados: {str(e)}")
    
    return {
        'pending_approvals_count': pending_count,
        'chamados_abertos_count': chamados_abertos_count  # NOVO
    }
```

### 3. **Adicionar badge no template**

```html
<!-- Em base.html, linha ~238-243 -->
<li>
  <a class="dropdown-item px-3 py-2 d-flex align-items-center position-relative {% if request.endpoint == 'main.listar_chamados' %}active{% endif %}" 
     href="{{ url_for('main.listar_chamados') }}"
     role="menuitem">
    <i class="fas fa-inbox me-2 text-info" aria-hidden="true"></i> Meus Tickets
    
    <!-- NOVO: Badge de chamados abertos -->
    {% if chamados_abertos_count and chamados_abertos_count > 0 %}
    <span class="badge rounded-pill bg-danger position-absolute top-10 start-100 translate-middle">
      {{ chamados_abertos_count }}
      <span class="visually-hidden">chamados abertos</span>
    </span>
    {% endif %}
  </a>
</li>
```

---

## 🎨 Design do Badge

### Estilos Bootstrap já aplicados:
- `badge rounded-pill` → Formato arredondado
- `bg-danger` → Fundo vermelho (cor de alerta)
- `position-absolute` → Posicionamento absoluto
- `top-10 start-100 translate-middle` → Canto superior direito
- `visually-hidden` → Acessibilidade (leitores de tela)

### Aparência visual:
```
┌────────────────────────────────────┐
│ 📫 Meus Tickets            (3)     │  ← Badge vermelho, branco
└────────────────────────────────────┘
```

---

## ✅ Benefícios

### Para Usuários:
- ✅ Visibilidade imediata dos tickets pendentes
- ✅ Não precisa abrir a página para ver se tem chamados
- ✅ Indicador visual de atenção necessária

### Para Admin/TI:
- ✅ Dashboard rápido de workload
- ✅ Ver quantos tickets precisam de resposta
- ✅ Priorização de trabalho

### UX:
- ✅ Padrão consistente (igual ao Gestão de Ativos)
- ✅ Feedback visual instantâneo
- ✅ Reduz cliques desnecessários

---

## 🔍 Filtros de Status

### Status considerados "Abertos" (para contagem):
- ✅ **"Aberto"** → Recém criado, aguardando atribuição
- ✅ **"Em Andamento"** → Sendo trabalhado, mas não finalizado

### Status NÃO contados:
- ❌ **"Resolvido"** → Aguardando confirmação do usuário
- ❌ **"Fechado"** → Finalizado completamente

**Justificativa:** Queremos alertar apenas sobre tickets que **requerem ação ativa**.

---

## 📊 Impacto no Desempenho

### Custo:
- **1 query adicional** por carregamento de página
- Query simples: `SELECT COUNT(*) WHERE status IN (...)`
- **Tempo estimado:** < 10ms

### Otimizações possíveis (futuro):
- Cache de 5 minutos no Redis
- Index composto em `(status, solicitante_id)`
- Materialização em tabela de estatísticas

---

## 🧪 Cenários de Teste

### Teste 1: Usuário com 0 chamados
- **Esperado:** Badge não aparece

### Teste 2: Usuário com 3 chamados abertos
- **Esperado:** Badge mostra "3"

### Teste 3: Admin com 15 chamados no sistema
- **Esperado:** Badge mostra "15"

### Teste 4: Chamados "Resolvidos" não contam
- **Esperado:** Badge não conta chamados resolvidos

### Teste 5: Responsividade mobile
- **Esperado:** Badge visível e bem posicionado

---

## 📝 Arquivos a Modificar

| Arquivo | Modificação | Linhas Aprox. |
|---------|------------|---------------|
| `app/__init__.py` | Adicionar contagem de chamados ao context_processor | ~203 |
| `app/templates/base.html` | Adicionar badge HTML no menu | ~241 |
| `app/models.py` (opcional) | Criar método `count_open_tickets()` | Após linha 400 |

---

## 🚀 Próximos Passos

1. ✅ **Aprovar o resumo**
2. ⏳ **Implementar código**
3. ⏳ **Testar em desenvolvimento**
4. ⏳ **Validar com usuários**
5. ⏳ **Deploy em produção**

---

## 💡 Melhorias Futuras (não agora)

- [ ] Badge diferente para chamados urgentes (vermelho piscante)
- [ ] Tooltip ao passar o mouse mostrando breakdown por prioridade
- [ ] Som de notificação quando novo chamado chega (admin)
- [ ] Badge separado para "Aguardando minha resposta"
- [ ] Integração com notificações push do navegador

---

## ❓ Perguntas para Confirmação

1. **Quais status devemos considerar como "abertos"?**
   - Sugestão: "Aberto" + "Em Andamento"
   
2. **Para usuários normais, mostrar apenas seus tickets ou incluir tickets do setor?**
   - Sugestão: Apenas tickets do próprio usuário
   
3. **Cor do badge:**
   - `bg-danger` (vermelho) → Urgência
   - `bg-warning` (amarelo) → Atenção
   - `bg-info` (azul) → Informação
   - **Sugestão:** Vermelho (consistente com Gestão de Ativos)

4. **Badge deve aparecer em "Abrir Ticket" ou "Meus Tickets"?**
   - **Sugestão:** "Meus Tickets" (onde o usuário vai para ver/gerenciar)

---

## ✅ Recomendação Final

**Implementar como descrito acima:**
- Badge vermelho em "Meus Tickets"
- Conta "Aberto" + "Em Andamento"
- Usuário vê apenas seus tickets
- Admin/TI vê todos os tickets do sistema
- Implementação simples no context_processor (sem criar service dedicado por enquanto)

**Tempo estimado:** 15-20 minutos de desenvolvimento + testes
