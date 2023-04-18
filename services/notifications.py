import smtplib
from email.message import EmailMessage
from models.local_db import get_recipients
from services.env_vars import get_var


SMTP_SERVER = get_var('SMTP_SERVER')


def send_email(text):
    try:
        recipients = [recipient[1]
                      for recipient in get_recipients(recipient_type='Email')]
        message = EmailMessage()
        message.set_content(text)
        # тема письма
        message['Subject'] = f'Actualization error'
        # отправитель
        message['From'] = 'Zabbix Actualization Service@bookcentre.ru'
        # получатель
        message['To'] = ','.join(recipients)

        s = smtplib.SMTP(SMTP_SERVER)
        s.send_message(message)
        s.quit()
        return True
    except:
        return False
