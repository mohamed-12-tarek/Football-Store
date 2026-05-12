import smtplib
from email.message import EmailMessage
from typing import Optional, Tuple

from flask import current_app


def _bool_from_config(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def send_email(to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str]]:
    """
    Send an email using SMTP settings stored in Flask config.
    Returns True if the email was sent, False otherwise.
    """
    app = current_app._get_current_object()
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    sender = app.config.get('MAIL_DEFAULT_SENDER') or username

    if not all([username, password, sender]):
        msg = 'SMTP credentials are missing. Set MAIL_USERNAME/MAIL_PASSWORD/MAIL_DEFAULT_SENDER.'
        app.logger.warning(msg)
        return False, msg

    mail_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(app.config.get('MAIL_PORT', 465))
    use_tls = _bool_from_config(app.config.get('MAIL_USE_TLS'))
    use_ssl = _bool_from_config(app.config.get('MAIL_USE_SSL'), not use_tls)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(mail_server, mail_port) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(mail_server, mail_port) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)
        app.logger.info('Email sent to %s', to_email)
        return True, None
    except Exception as exc:
        error_msg = f'Failed to send email: {exc}'
        app.logger.error('Failed to send email to %s: %s', to_email, exc)
        return False, error_msg

