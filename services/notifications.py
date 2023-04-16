import smtplib
from email.message import EmailMessage
from models.local_db import get_recipients
from dotenv import load_dotenv
import os

project_path = os.path.join(os.path.dirname(__file__))
dotenv_path = str(project_path[0:(project_path.index(
    'zabbix_actualization_service') + 29)]) + '.env'

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
SMTP_SERVER = os.environ['SMTP_SERVER']


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
