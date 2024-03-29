from services.zabbix_scripts.zabbix_api import *
import json

# !добавить поиск по значению тега


def get_hosts_from_zabbix(key, groupid=0, tag=0, tag_value=0, ip_list=0):
    request = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": ip_list
            },
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
    if not ip_list:
        del request["params"]["filter"]

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't get hosts from zabbix: {responce['error']['data']}")
    return responce['result']


def import_hosts_to_zabbix(key, host_list):
    params = get_zabbix_params_from_local_db()
    version = params[0][2]
    hosts = {"zabbix_export":
             {
                 "version": version,
                 "hosts": host_list}
             }

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

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(f"Can't import hosts: {responce['error']['data']}")
    return True


def delete_hosts_from_zabbix(key, ip_list):
    hosts = get_hosts_from_zabbix(key=key, ip_list=ip_list)
    hostid_list = [hosts[i]['hostid'] for i in range(len(hosts))]
    request = {
        "jsonrpc": "2.0",
        "method": "host.delete",
        "params": hostid_list,
        "auth": key,
        "id": 1
    }
    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(f"Can't delete hosts: {responce['error']['data']}")
    return True
