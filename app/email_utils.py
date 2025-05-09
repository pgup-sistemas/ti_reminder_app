from flask_mail import Mail, Message

def mail_init_app(app, mail):
    mail.init_app(app)

def send_reminder_email(subject, recipients, body, mail):
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)
