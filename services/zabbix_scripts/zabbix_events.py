from services.zabbix_scripts.zabbix_api import *
import re


def add_problem_message(data):
    executor = data['executor']
    sd_request_id = int(data['request_id'])
    zabbix_event_id = re.findall("--(.+?)--", data['description'])
    if zabbix_event_id:
        zabbix_event_id = zabbix_event_id[0]
    else:
        return True
    key = get_zabbix_auth_key()
    request = {
        "jsonrpc": "2.0",
        "method": "event.acknowledge",
        "params": {
            "eventids": zabbix_event_id,
            "action": 4,
            "message": f"SD: #{sd_request_id}, исполнитель: {executor}"
        },
        "auth": key,
        "id": 1
    }
    send_request_to_zabbix(request)
