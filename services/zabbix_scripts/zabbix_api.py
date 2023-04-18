import requests
import ast
from models.local_db import get_zabbix_params_from_local_db
from services.env_vars import get_var

ZABBIX_USER = get_var('ZABBIX_USER')
ZABBIX_PASSWORD = get_var('ZABBIX_PASSWORD')


def send_request_to_zabbix(request):
    params = get_zabbix_params_from_local_db()
    if not params:
        raise Exception('Zabbix server parameters not found')
    if params[0][2] == '5.0':
        zabbix_server = f'http://{params[0][1]}/zabbix/api_jsonrpc.php'
    elif params[0][2] == '5.2':
        zabbix_server = f'http://{params[0][1]}/api_jsonrpc.php'
    else:
        raise Exception(
            f'Unexpected Zabbix version ({params[0][2]}), versions 5.0 and 5.2 are currently available')
    responce = requests.post(
        zabbix_server, json=request, headers={'Content-Type': 'application/json-rpc'})
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
