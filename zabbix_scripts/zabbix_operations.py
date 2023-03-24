import os
from dotenv import load_dotenv
import requests
import ast


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
ZABBIX_SERVER = os.environ['ZABBIX_SERVER']
ZABBIX_USER = os.environ['ZABBIX_USER']
ZABBIX_PASSWORD = os.environ['ZABBIX_PASSWORD']


def send_request_to_zabbix(request):
    responce = requests.post(
        # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
        rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
    decode_responce = responce.content.decode('utf-8')
    decode_responce = decode_responce.replace('true', 'True')
    decode_responce = decode_responce.replace('false', 'False')
    result = ast.literal_eval(decode_responce)
    return result


def get_zabbix_auth_key():
    login = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": f"{ZABBIX_USER}",
            "password": f"{ZABBIX_PASSWORD}"
        },
        "id": 1
    }
    responce = send_request_to_zabbix(login)
    if 'error' in responce:
        raise Exception(f"Can't get auth key: {responce['error']['data']}")
    key = responce['result']
    return key
