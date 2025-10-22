# 🔄 INSTRUÇÕES PARA LIMPAR CACHE

## ⚠️ PROBLEMA

O navegador está mostrando a **versão antiga** do template (com FullCalendar) ao invés da **versão nova** (simples e funcional).

---

## ✅ SOLUÇÃO: LIMPAR CACHE DO NAVEGADOR

### **Método 1: Hard Refresh (RECOMENDADO)**

**Windows/Linux:**
```
Ctrl + Shift + R
ou
Ctrl + F5
```

**Mac:**
```
Cmd + Shift + R
```

---

### **Método 2: Limpar Cache Completo**

**Chrome/Edge:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Imagens e arquivos em cache"
3. Clique em "Limpar dados"
4. Recarregue a página

**Firefox:**
1. Pressione `Ctrl + Shift + Delete`
2. Selecione "Cache"
3. Clique em "Limpar agora"
4. Recarregue a página

---

### **Método 3: Modo Anônimo/Privado**

**Chrome/Edge:**
```
Ctrl + Shift + N
```

**Firefox:**
```
Ctrl + Shift + P
```

Depois acesse:
```
http://192.168.1.86:5000/equipment/reserve-calendar
```

---

## 🔍 COMO SABER SE FUNCIONOU

### **Versão ANTIGA (errada):**
```
Título: "Reservar Equipamento"
Lado esquerdo: Campo de busca + spinner girando
Lado direito: Calendário (não carrega)
```

### **Versão NOVA (correta):**
```
Título: "Reservar Equipamento [VERSÃO SIMPLES]"
Lado esquerdo: Lista de equipamentos (JÁ VISÍVEL)
Lado direito: Formulário de reserva
```

---

## ✅ CHECKLIST

Após limpar o cache, você deve ver:

- [ ] Badge verde "VERSÃO SIMPLES" no título
- [ ] Lista de equipamentos à esquerda (sem spinner)
- [ ] Equipamento "Dell Inspiron 15 Latitude" visível
- [ ] Formulário à direita com campos de data/hora
- [ ] Botões "Solicitar Reserva" e "Limpar"

---

## 🧪 TESTE

1. **Limpe o cache** (Ctrl + Shift + R)
2. **Acesse:** http://192.168.1.86:5000/equipment/reserve-calendar
3. **Verifique:** Badge "VERSÃO SIMPLES" aparece?
4. **Clique** em "Dell Inspiron 15 Latitude"
5. **Veja:** Card fica azul?
6. **Preencha** datas
7. **Clique** em "Solicitar Reserva"
8. **Resultado:** Modal de sucesso deve aparecer

---

## 🚨 SE AINDA NÃO FUNCIONAR

### **Opção 1: Fechar e Reabrir Navegador**
1. Feche TODAS as abas
2. Feche o navegador completamente
3. Abra novamente
4. Acesse a URL

### **Opção 2: Usar Outro Navegador**
- Se está no Chrome, teste no Firefox
- Se está no Firefox, teste no Chrome
- Se está no Edge, teste no Chrome

### **Opção 3: Verificar Console (F12)**
1. Pressione F12
2. Vá para aba "Console"
3. Veja se tem erros em vermelho
4. Me envie print do console

---

## 📊 LOGS DO SERVIDOR

Quando acessar a versão correta, o servidor deve mostrar:

```
INFO:app:[RESERVE_SIMPLE] Usuário equipe_ti acessou reserva simples
INFO:app:[RESERVE_SIMPLE] 1 equipamentos carregados
```

Se mostrar `[RESERVE_CALENDAR]` ao invés de `[RESERVE_SIMPLE]`, o cache ainda está ativo.

---

## 🎯 RESUMO

1. ✅ Servidor está correto (código atualizado)
2. ✅ Template novo existe (`equipment_reserve_simple.html`)
3. ❌ Navegador mostra versão antiga (cache)

**Solução:** Limpar cache com `Ctrl + Shift + R`

---

**Teste agora e me avise se aparece o badge "VERSÃO SIMPLES"!** 🚀
