from zabbix_operations import *


def get_groups_from_zabbix(key):
    request = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": "extend"
        },
        "auth": key,
        "id": 1
    }

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't get groups from zabbix: {responce['error']['data']}")
    return responce['result']


def add_groups_to_zabbix(key):
    pass


def delete_groups_from_zabbix(key):
    pass
