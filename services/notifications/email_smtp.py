import smtplib
from email.message import EmailMessage
from models.local_db import get_recipients
from services.env_vars import get_var


SMTP_SERVER = get_var('SMTP_SERVER')


def send_email(text, recipient=0):
    try:
        if not recipient:
            recipients = [note[1] for note in get_recipients()]
        else:
            recipients = [recipient, ]
        message = EmailMessage()
        message.set_content(text)
        # тема письма
        message['Subject'] = f'Actualization error'
        # отправитель
        message['From'] = 'Zabbix Actualization Service@bookcentre.ru'
        # получатель
        message['To'] = ','.join(recipients)

        smtplib.SMTP(SMTP_SERVER).send_message(message)
        smtplib.SMTP(SMTP_SERVER).quit()
        return True
    except:
        return False
