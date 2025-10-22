# 🧪 GUIA DE TESTE - Calendário de Reservas

**Data:** 21/10/2025

---

## 🎯 O QUE FOI ADICIONADO

✅ **Logs detalhados no console** para debug  
✅ **Indicador de carregamento** visual (spinner)  
✅ **Mensagens de erro** claras e amigáveis  
✅ **Validação de elementos** HTML  

---

## 📋 PASSO A PASSO PARA TESTAR

### **1. Recarregue o Servidor**
```bash
# Pare o servidor (Ctrl+C se estiver rodando)
# Inicie novamente:
python run.py
```

### **2. Limpe o Cache do Navegador**
```
Pressione: Ctrl + Shift + R
ou
Ctrl + F5
```

### **3. Abra o Console do Navegador**
```
Pressione: F12
Vá para a aba: Console
```

### **4. Acesse o Calendário**
```
http://192.168.1.86:5000/equipment/reserve-calendar
```

---

## 🔍 O QUE VERIFICAR NO CONSOLE

### **Esperado (SUCESSO):**
```
🚀 Página carregada - Iniciando sistema de reservas...
📅 Inicializando calendário...
📋 Carregando equipamentos...
🔍 Configurando busca...
✅ Sistema inicializado!
🔄 Iniciando carregamento de equipamentos...
📍 URL da API: /equipment/api/equipments
📥 Resposta recebida: 200 OK
📦 Dados recebidos: {success: true, data: Array(X)}
✅ X equipamentos carregados: [...]
🎨 Renderizando lista de equipamentos: X
✅ Lista renderizada com sucesso!
```

### **Se der erro 404:**
```
❌ Erro ao carregar equipamentos: HTTP error! status: 404

SOLUÇÃO:
1. Verifique se o servidor foi reiniciado
2. Verifique se a rota existe em equipment.py
3. Acesse direto: http://192.168.1.86:5000/equipment/api/equipments
```

### **Se der erro 401:**
```
❌ Erro ao carregar equipamentos: HTTP error! status: 401

SOLUÇÃO:
1. Você não está logado
2. Faça login primeiro
3. Depois acesse o calendário
```

### **Se der erro 500:**
```
❌ Erro ao carregar equipamentos: HTTP error! status: 500

SOLUÇÃO:
1. Erro no servidor
2. Verifique o console do Python (terminal)
3. Procure por traceback/erro
```

---

## 🎬 TESTE VISUAL

### **O que deve aparecer:**

```
┌─────────────────────────────────────────────────────────┐
│ 📅 Reservar Equipamento                                 │
├─────────────┬───────────────────────────────────────────┤
│ Equipamentos│          CALENDÁRIO                       │
│             │                                           │
│ 🔍 Buscar...│   [Spinner girando]                       │
│             │   "Carregando equipamentos..."            │
│ [Loading...]│                                           │
│             │   Depois:                                 │
│ ↓ ↓ ↓       │   ╔════════════════════════════╗          │
│             │   ║  Seg  Ter  Qua  Qui  Sex  ║          │
│ [Notebook 1]│   ║  08h  ░░░  ░░░  ░░░  ░░░  ║          │
│ [Monitor 2] │   ║  09h  ░░░  ░░░  ░░░  ░░░  ║          │
│ [Mouse 3]   │   ║  10h  ░░░  ░░░  ░░░  ░░░  ║          │
│ ...         │   ╚════════════════════════════╝          │
└─────────────┴───────────────────────────────────────────┘
```

---

## 🐛 PROBLEMAS COMUNS E SOLUÇÕES

### **Problema 1: Spinner fica girando infinitamente**

**Causa:** API não está respondendo

**Debug:**
1. Abra F12 → Network
2. Procure por `api/equipments`
3. Veja o status code

**Soluções:**
- Status 404 → Rota não existe (reinicie servidor)
- Status 401 → Não está logado (faça login)
- Status 500 → Erro no servidor (veja console Python)
- Sem requisição → JavaScript não executou (veja console)

---

### **Problema 2: Console mostra erro "Elemento não encontrado"**

**Mensagem:**
```
❌ Elemento #equipmentList não encontrado!
```

**Causa:** Template HTML corrompido

**Solução:**
1. Verifique se salvou o arquivo
2. Recarregue com Ctrl+F5
3. Veja o HTML da página (Ctrl+U)

---

### **Problema 3: API retorna success: false**

**Mensagem no console:**
```
❌ Erro na resposta: {success: false, error: "..."}
```

**Solução:**
1. Veja a mensagem de erro
2. Verifique o banco de dados
3. Veja logs do Python

---

### **Problema 4: Nenhum equipamento cadastrado**

**Mensagem:**
```
⚠️ Nenhum equipamento para renderizar
```

**Solução:**
1. Cadastre equipamentos primeiro
2. Vá em: Equipamentos → Administração → Novo Equipamento
3. Cadastre pelo menos 1 equipamento

---

## 📊 TESTE COMPLETO

### **Checklist:**

- [ ] Servidor reiniciado
- [ ] Cache limpo (Ctrl+F5)
- [ ] Console aberto (F12)
- [ ] Página carregada
- [ ] Logs aparecem no console
- [ ] Spinner aparece
- [ ] Equipamentos carregam
- [ ] Lista aparece à esquerda
- [ ] Calendário renderiza à direita
- [ ] Busca funciona
- [ ] Pode selecionar equipamento
- [ ] Pode criar reserva

---

## 🔧 TESTE DA API DIRETAMENTE

### **Teste 1: API de Equipamentos**
```
Acesse no navegador:
http://192.168.1.86:5000/equipment/api/equipments

Esperado:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Notebook Dell",
      "status": "disponivel",
      "category": "Informática",
      ...
    }
  ]
}
```

### **Teste 2: Página do Calendário**
```
Acesse:
http://192.168.1.86:5000/equipment/reserve-calendar

Esperado:
- Página carrega
- Spinner aparece
- Equipamentos carregam
- Calendário renderiza
```

---

## 📝 INFORMAÇÕES PARA REPORTAR ERRO

Se ainda não funcionar, me envie:

### **1. Console do Navegador (F12):**
```
Copie TODOS os logs que aparecem
Especialmente os que começam com:
🚀 🔄 📥 📦 ❌
```

### **2. Network Tab:**
```
F12 → Network → Recarregue a página
Procure por: api/equipments
Clique nele
Me envie:
- Status code
- Response (aba Response)
- Headers (aba Headers)
```

### **3. Console do Python (Terminal):**
```
Copie qualquer erro que aparecer no terminal
Especialmente tracebacks
```

### **4. Print da Tela:**
```
Tire print mostrando:
- O que aparece na página
- Console aberto (F12)
```

---

## ✅ RESULTADO ESPERADO FINAL

**Quando tudo funcionar:**

1. ✅ Página carrega
2. ✅ Spinner aparece por 1-2 segundos
3. ✅ Lista de equipamentos aparece
4. ✅ Calendário renderiza
5. ✅ Console mostra logs de sucesso
6. ✅ Busca funciona
7. ✅ Pode selecionar equipamento
8. ✅ Pode criar reserva

---

**Teste agora e me envie os logs do console!** 🚀
