from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def mail_init_app(app, mail_instance):
    global mail
    mail = mail_instance
    mail.init_app(app)


def send_email(subject, recipients, body, html_body=None):
    # Ensure we are using the mail instance initialized with the app context
    # This might require passing 'mail' around or using current_app.extensions['mail']
    # For simplicity, assuming 'mail' is globally accessible after init
    try:
        msg = Message(subject, recipients=recipients, body=body, html=html_body)
        # Ensure sender is configured, fallback to default if needed
        if not msg.sender:
            msg.sender = current_app.config.get("MAIL_DEFAULT_SENDER")
        mail.send(msg)
        print(f"Email sent to {recipients} with subject: {subject}")  # Log success
    except Exception as e:
        print(f"Error sending email: {e}")  # Log error
        # Handle error appropriately (log, flash message, etc.)


def send_chamado_aberto_email(chamado):
    user_email = chamado.solicitante.email
    # Define TI email recipient(s) - maybe from config or a specific group
    ti_recipients = [
        current_app.config.get("TI_EMAIL_GROUP", "ti@example.com")
    ]  # Example

    subject_user = f"Chamado #{chamado.id} Aberto: {chamado.titulo}"
    body_user = f"""Olá {chamado.solicitante.username},

Seu chamado "{chamado.titulo}" (ID: {chamado.id}) foi aberto com sucesso.

Prioridade: {chamado.prioridade}
Status: {chamado.status}

Você pode acompanhar o status em [link para o chamado].

Obrigado,
Sistema de Chamados TI"""
    # Potentially add HTML version
    send_email(subject_user, [user_email], body_user)

    subject_ti = f"Novo Chamado #{chamado.id} Aberto por {chamado.solicitante.username} ({chamado.setor.name}): {chamado.titulo}"
    body_ti = f"Um novo chamado foi aberto:\n\nID: {chamado.id}\nTítulo: {chamado.titulo}\nSolicitante: {chamado.solicitante.username} ({chamado.solicitante.email})\nSetor: {chamado.setor.name}\nPrioridade: {chamado.prioridade}\nStatus: {chamado.status}\nDescrição:\n{chamado.descricao}\n\nAcesse o sistema para mais detalhes e atribuição."
    # Potentially add HTML version
    send_email(subject_ti, ti_recipients, body_ti)


def send_password_reset_email(user, token):
    """Envia um email com instruções para redefinir a senha"""
    reset_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/reset_password/{token}"

    subject = "Redefinição de Senha - TI OSN System"
    body = f"""Olá {user.username},

Você solicitou a redefinição de sua senha no TI OSN System.

Para redefinir sua senha, clique no link abaixo ou copie e cole no seu navegador:

{reset_url}

Este link é válido por 1 hora.

Se você não solicitou esta redefinição, ignore este email e nenhuma alteração será feita.

Atenciosamente,
Equipe TI OSN System"""

    html_body = f"""<p>Olá {user.username},</p>
<p>Você solicitou a redefinição de sua senha no TI OSN System.</p>
<p>Para redefinir sua senha, <a href="{reset_url}">clique aqui</a> ou copie e cole o link abaixo no seu navegador:</p>
<p>{reset_url}</p>
<p>Este link é válido por 1 hora.</p>
<p>Se você não solicitou esta redefinição, ignore este email e nenhuma alteração será feita.</p>
<p>Atenciosamente,<br>Equipe TI OSN System</p>"""

    send_email(subject, [user.email], body, html_body)


def send_chamado_atualizado_email(chamado, atualizacao):
    """Envia e-mail de notificação quando um chamado é atualizado"""
    from flask import render_template_string, url_for

    # Destinatários: solicitante e responsável TI (se houver)
    recipients = [chamado.solicitante.email]
    if (
        chamado.responsavel_ti
        and chamado.responsavel_ti.email != chamado.solicitante.email
    ):
        recipients.append(chamado.responsavel_ti.email)

    # URL do chamado (usando _external=True para URL completa)
    chamado_url = url_for("main.detalhe_chamado", id=chamado.id, _external=True)

    # Assunto do e-mail
    subject = f"Atualização no Chamado #{chamado.id}: {chamado.titulo}"

    # Corpo do e-mail em texto simples
    body = f"""Olá,

O chamado "{chamado.titulo}" (ID: {chamado.id}) foi atualizado.

Atualização: {atualizacao.texto}

Status atual: {chamado.status}
Responsável TI: {chamado.responsavel_ti.username if chamado.responsavel_ti else 'Não atribuído'}

Acesse o chamado em: {chamado_url}

Atenciosamente,
Sistema de Chamados TI"""

    # Corpo do e-mail em HTML
    # Definir a cor do badge com base no status
    status_color = (
        "#198754"
        if chamado.status == "Resolvido"
        else "#fd7e14"
        if chamado.status == "Em Andamento"
        else "#dc3545"
        if chamado.status == "Fechado"
        else "#0d6efd"
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{subject}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .chamado-info {{ margin-bottom: 20px; }}
            .status-badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 0.9em;
                font-weight: bold;
                color: white;
            }}
            .btn-primary {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #0d6efd;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 15px;
            }}
            .footer {{ margin-top: 30px; font-size: 0.9em; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Atualização no Chamado #{chamado.id}</h2>
                <h3>{chamado.titulo}</h3>
            </div>
            
            <div class="chamado-info">
                <p><strong>Atualização:</strong> {atualizacao.texto}</p>
                <p>
                    <strong>Status:</strong> 
                    <span class="status-badge" style="background-color: {status_color}">
                        {chamado.status}
                    </span>
                </p>
                <p><strong>Responsável TI:</strong> {chamado.responsavel_ti.username if chamado.responsavel_ti else 'Não atribuído'}</p>
                <p><strong>Data da Atualização:</strong> {atualizacao.data_criacao.strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <a href="{chamado_url}" class="btn-primary">Ver Detalhes do Chamado</a>
            
            <div class="footer">
                <p>Este é um e-mail automático, por favor não responda.</p>
                <p>Atenciosamente,<br>Sistema de Chamados TI</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Envia o e-mail
    send_email(subject, recipients, body, html_body)
