from models.local_db import get_telegram_params
import requests


def send_tg_message(text):
    tg_params = get_telegram_params()
    if not tg_params[0][2]:
        return False
    bot_token = tg_params[0][1]
    chat_id = tg_params[0][0]
    tg_api = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    request = {'chat_id': chat_id, 'text': text}
    responce = requests.post(tg_api, json=request, headers={
                             'Content-Type': 'application/json-rpc'})
    if not responce:
        return False
    return True
