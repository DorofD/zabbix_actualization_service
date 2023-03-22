import os
from dotenv import load_dotenv
import requests
import ast
import json

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
ZABBIX_SERVER = os.environ['ZABBIX_SERVER']
ZABBIX_USER = os.environ['ZABBIX_USER']
ZABBIX_PASSWORD = os.environ['ZABBIX_PASSWORD']


def send_request_to_zabbix(request):
    try:
        responce = requests.post(
            # rf'{ZABBIX_SERVER}/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.2
            rf'{ZABBIX_SERVER}/zabbix/api_jsonrpc.php', json=request, headers={'Content-Type': 'application/json-rpc'})  # для Zabbix 5.0
        decode_responce = responce.content.decode('utf-8')
        decode_responce = decode_responce.replace('true', 'True')
        decode_responce = decode_responce.replace('false', 'False')
        dict_responce = ast.literal_eval(decode_responce)
        result = {'status': True, 'message': '', 'result': dict_responce}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_zabbix_auth_key():
    try:
        login = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": f"{ZABBIX_USER}",
                "password": f"{ZABBIX_PASSWORD}"
            },
            "id": 1
        }

        responce = send_request_to_zabbix(login)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result

    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_hosts_from_zabbix(key, groupid, tag):
    try:
        request = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "tags": [{
                    "tag": tag,
                }],
                "groupids": groupid,
                "selectTags": ["tag", "value"],
                "selectGroups": "extend",
                "output": [
                    "hostid",
                    "host",
                    "name",
                ],
            },
            "auth": key,
            "id": 1
        }
        if not groupid:
            del request["params"]["groupids"]
        if not tag:
            del request["params"]["tags"]

        responce = send_request_to_zabbix(request)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def get_groups_from_zabbix(key):
    try:
        request = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend"
            },
            "auth": key,
            "id": 1
        }

        responce = send_request_to_zabbix(request)['result']
        result = {'status': True, 'message': '', 'result': responce['result']}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result


def import_hosts_to_zabbix(key, host_list):
    try:

        hosts = {"zabbix_export":
                 # {"version": "5.2",
                 {
                     "version": "5.0",
                     "hosts": host_list}}

        json_hosts = json.dumps(hosts)

        request = {
            "jsonrpc": "2.0",
            "method": "configuration.import",
            "params": {
                "format": "json",
                "rules": {"applications": {
                    "createMissing": True,
                },
                    "discoveryRules": {"createMissing": True, "updateExisting": True},
                    "graphs": {"createMissing": True, "updateExisting": True},
                    "groups": {"createMissing": True},
                    "hosts": {"createMissing": True, "updateExisting": False},
                    "images": {"createMissing": True, "updateExisting": True},
                    "items": {"createMissing": True, "updateExisting": True},
                    "maps": {"createMissing": True, "updateExisting": True},
                    "screens": {"createMissing": True, "updateExisting": True},
                    "templateLinkage": {"createMissing": True},
                    "templates": {"createMissing": True, "updateExisting": True},
                    "triggers": {"createMissing": True, "updateExisting": True},
                    "valueMaps": {"createMissing": True, "updateExisting": True},
                },
                "source": json_hosts
            },
            "auth": key,
            "id": 1
        }

        responce = send_request_to_zabbix(request)['result']
        result = {'status': '', 'message': ''}
        if 'result' in responce:
            result['status'] = True
        elif 'error' in responce:
            result['status'] = False
            result['message'] = responce['error']
        else:
            result['status'] = False
            result['message'] = 'Unexpected error'
        return result

    except Exception as exc:
        result['status'] = False
        result['message'] = exc
        return result
