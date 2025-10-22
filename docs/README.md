# Documentação do TI OSN System

Esta pasta contém toda a documentação do sistema em formato Markdown, que é processada pelo MKDocs para gerar um site de documentação profissional.

## 📁 Estrutura

```
docs/
├── index.md                    # Página inicial da documentação
├── user-guide/                 # Guias para usuários finais
│   ├── overview.md            # Visão geral do sistema
│   ├── reminders.md           # Lembretes
│   ├── chamados.md            # Sistema de chamados
│   ├── tasks.md               # Tarefas
│   ├── tutorials.md           # Tutoriais
│   ├── equipment.md           # Equipamentos
│   ├── dashboard.md           # Dashboard
│   ├── rfid.md                # Sistema RFID (NOVO)
│   ├── satisfaction.md        # Avaliação de Satisfação (NOVO)
│   ├── certifications.md      # Certificações (NOVO)
│   └── performance.md         # Performance (NOVO)
├── admin-guide/               # Guias para administradores
│   ├── equipment-admin.md     # Gestão de equipamentos
│   ├── performance-admin.md   # Performance do sistema
│   ├── rfid-admin.md          # Administração RFID
│   ├── satisfaction-admin.md  # Gestão de satisfação
│   └── certifications-admin.md # Gestão de certificações
├── javascripts/               # Scripts personalizados
└── stylesheets/               # Estilos personalizados
```

## 🚀 Como Usar

### Visualizar Documentação Localmente

```bash
# Servir documentação em modo desenvolvimento
mkdocs serve

# Acessar em: http://127.0.0.1:8000
```

### Construir Documentação

```bash
# Gerar site estático na pasta 'site/'
mkdocs build

# Gerar com limpeza de arquivos antigos
mkdocs build --clean
```

### Acessar no Sistema

A documentação é acessível através da rota `/help` do sistema:
- **URL**: http://192.168.1.86:5000/help
- A documentação é construída automaticamente na primeira visita
- Arquivos estáticos são servidos via `/docs/<path>`

## 📝 Editando a Documentação

### Formato Markdown

Todos os arquivos usam Markdown padrão com algumas extensões:

```markdown
# Título Principal

## Seção

### Subseção

- Lista não ordenada
- Item 2

1. Lista ordenada
2. Item 2

**Negrito** e *itálico*

[Link](url)

![Imagem](caminho/imagem.png)

> Citação

`código inline`

\`\`\`python
# Bloco de código
def exemplo():
    return "Hello"
\`\`\`
```

### Admonitions (Avisos)

```markdown
!!! note "Nota"
    Conteúdo da nota

!!! warning "Atenção"
    Conteúdo do aviso

!!! tip "Dica"
    Conteúdo da dica

!!! danger "Perigo"
    Conteúdo do alerta
```

## 🎨 Personalização

### Tema Atual

O sistema usa o tema **ReadTheDocs** por padrão, que não requer dependências extras.

### Tema Material (Opcional)

Para usar o tema Material Design:

1. Instalar dependências:
```bash
pip install -r requirements-docs-full.txt
```

2. Atualizar `mkdocs.yml`:
```yaml
theme:
  name: material
  language: pt-BR
  palette:
    primary: blue
    accent: blue
```

## 📊 Versão Atual

- **Versão**: 2.2.0
- **Última Atualização**: Outubro 2025
- **Novidades**: Sistema RFID, Avaliação de Satisfação, Certificações, Dashboard de Performance

## 🔗 Links Úteis

- [MKDocs Documentation](https://www.mkdocs.org/)
- [Material for MKDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)

## 📞 Suporte

Para dúvidas sobre a documentação, entre em contato com a equipe de desenvolvimento através do sistema de chamados.
