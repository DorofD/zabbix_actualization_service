import requests
import ast
import json
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

DB_SERVER = os.environ['DB_SERVER']
DATABASE = os.environ['DATABASE']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DRIVER = os.environ['DB_DRIVER']
ZABBIX_SERVER = os.environ['ZABBIX_SERVER']
ZABBIX_USER = os.environ['ZABBIX_USER']
ZABBIX_PASSWORD = os.environ['ZABBIX_PASSWORD']

login = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": f"{ZABBIX_USER}",
        "password": f"{ZABBIX_PASSWORD}"
    },
    "id": 1
}

try:
    responce = requests.post(
        rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=login, headers={'Content-Type': 'application/json-rpc'})
    decode_responce = responce.content.decode('utf-8')
    dict_responce = ast.literal_eval(decode_responce)
    auth = dict_responce['result']
    print(auth)

    request = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": [
                "hostid",
                "host",
                "name"
            ],
            "selectInterfaces": [
                "interfaceid",
                "ip"
            ]
        },
        "id": 2,
        "auth": auth
    }

    responce = requests.post(
        rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})
    decode_responce = responce.content.decode('utf-8')
    dict_responce = ast.literal_eval(decode_responce)

    for i in dict_responce['result']:
        print(i)
    print(len(dict_responce['result']))
except Exception as exc:
    print(exc)
