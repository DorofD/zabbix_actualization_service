from services.zabbix_scripts.zabbix_operations import *


def get_templates_from_zabbix(key):
    request = {
        "jsonrpc": "2.0",
        "method": "template.get",
        "params": {
            "output": "extend"
        },
        "auth": key,
        "id": 1
    }
    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't get templates from zabbix: {responce['error']['data']}")
    # создание списка имен шаблонов
    result = [template['name'] for template in responce['result']]
    return result
