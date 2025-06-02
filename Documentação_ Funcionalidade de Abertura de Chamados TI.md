# Documentação: Funcionalidade de Abertura de Chamados TI

## Visão Geral

Este documento descreve a nova funcionalidade de abertura e gestão de chamados implementada no sistema "ti_reminder". O objetivo principal é centralizar as solicitações de suporte técnico para a equipe de TI, permitindo que usuários de todos os setores possam registrar e acompanhar seus pedidos de forma organizada e eficiente.

## Funcionalidades Implementadas

A implementação atual inclui as seguintes funcionalidades básicas:

1.  **Abertura de Novos Chamados:** Usuários autenticados podem criar novos chamados para a TI através de um formulário dedicado. É necessário fornecer um título claro, uma descrição detalhada do problema ou solicitação e definir a prioridade inicial (Baixa, Média, Alta, Crítica).
2.  **Listagem de Chamados:** Uma nova seção permite visualizar os chamados existentes. Usuários comuns podem ver os chamados que abriram ou os chamados relacionados ao seu setor (a lógica exata de visibilidade por setor pode precisar de refinamento conforme as regras de negócio específicas). Administradores e a equipe de TI (assumindo que administradores representam a TI por enquanto) têm uma visão completa de todos os chamados.
3.  **Filtros de Listagem:** A tela de listagem oferece filtros por status (Aberto, Em Andamento, Resolvido, Fechado), prioridade e, para administradores/TI, por setor. Isso facilita a localização e o gerenciamento dos chamados.
4.  **Detalhes do Chamado:** É possível visualizar os detalhes completos de um chamado específico, incluindo todas as informações registradas na abertura, datas de criação e atualização, solicitante, setor e o responsável pela TI (se atribuído).
5.  **Notificações por E-mail (Abertura):** Ao abrir um novo chamado, o sistema envia automaticamente notificações por e-mail:
    *   Uma para o usuário solicitante, confirmando a abertura e fornecendo o ID do chamado.
    *   Uma para a equipe de TI (um endereço de e-mail configurável), informando sobre o novo chamado, quem o abriu, o setor e a descrição.
6.  **Integração com Usuários e Setores:** A funcionalidade utiliza os modelos `User` e `Sector` já existentes no sistema. A identificação do setor do solicitante é crucial para o fluxo multi-setorial. **Observação Importante:** A lógica atual para determinar o setor do usuário ao abrir um chamado (`app/routes.py`, função `abrir_chamado`) é uma simplificação (tenta buscar o setor do primeiro lembrete associado ao usuário). Esta lógica **precisa ser revisada e ajustada** de acordo com a regra de negócio definitiva da organização para associar usuários a setores (ex: um campo `sector_id` no modelo `User`, um grupo/perfil, etc.).
7.  **Permissões Básicas:** O acesso às funcionalidades de chamados requer autenticação (`@login_required`). A visibilidade dos chamados na listagem e nos detalhes é controlada com base no perfil do usuário (administrador/TI vs. usuário comum), embora a definição exata de "equipe de TI" e as regras de visibilidade por setor possam necessitar de ajustes mais finos.

## Como Utilizar

1.  **Acessar:** Após fazer login no sistema, um novo item de menu (ou link) para "Chamados" estará disponível (será necessário adicionar este link ao `base.html` ou menu de navegação).
2.  **Abrir Chamado:** Clique em "Abrir Novo Chamado" na tela de listagem. Preencha o formulário com título, descrição e prioridade. Clique em "Abrir Chamado" para submeter.
3.  **Listar e Filtrar:** Acesse a seção "Chamados" para ver a lista. Utilize os filtros na parte superior para refinar a visualização por status, prioridade ou setor (se aplicável).
4.  **Ver Detalhes:** Clique no botão "Detalhes" na linha correspondente ao chamado na lista para visualizar todas as informações.

## Próximos Passos e Melhorias Sugeridas

A implementação atual estabelece a base para o sistema de chamados. As seguintes melhorias e funcionalidades podem ser adicionadas em fases futuras:

*   **Atualização de Status e Atribuição:** Implementar rotas e interfaces para que a equipe de TI possa atualizar o status do chamado (Em Andamento, Resolvido, etc.) e atribuir um técnico responsável.
*   **Comentários:** Adicionar um sistema de comentários para permitir a comunicação entre o solicitante e a equipe de TI dentro da página de detalhes do chamado.
*   **Notificações Adicionais:** Configurar e-mails para atualizações de status, atribuição de responsável, adição de comentários e fechamento de chamados.
*   **Gestão de Setores e Usuários:** Refinar a associação entre usuários e setores e implementar uma interface administrativa para gerenciar essa associação, se necessário.
*   **Permissões Granulares:** Implementar um sistema de papéis (roles) ou grupos (ex: "TI Nível 1", "TI Nível 2", "Usuário Comum", "Gestor Setor") para um controle mais fino sobre quem pode ver e fazer o quê com os chamados.
*   **Dashboard de Chamados:** Integrar métricas e gráficos relacionados aos chamados no dashboard existente.
*   **Anexos:** Permitir que usuários anexem arquivos (logs, screenshots) ao abrir ou comentar em um chamado.
*   **Integração com Menu:** Adicionar os links para as novas páginas de chamados no menu de navegação principal (`base.html`).

## Considerações Técnicas

*   **Configuração de E-mail:** Certifique-se de que as configurações de e-mail (servidor SMTP, usuário, senha, remetente padrão) estejam corretamente definidas no arquivo `config.py` ou variáveis de ambiente para que as notificações funcionem.
*   **Endereço de E-mail da TI:** O endereço de e-mail para onde as notificações de novos chamados são enviadas está atualmente definido como um valor padrão em `app/email_utils.py`. Recomenda-se torná-lo configurável (via `config.py` ou variável de ambiente).
*   **Associação Usuário-Setor:** Como mencionado, a lógica para determinar o setor do usuário precisa ser definida e implementada corretamente em `app/routes.py`.

Esta documentação fornece uma visão geral da funcionalidade implementada. Testes adicionais em um ambiente de homologação são recomendados antes da implantação em produção.
