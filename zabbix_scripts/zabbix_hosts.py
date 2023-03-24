from zabbix_operations import *
import json


def get_hosts_from_zabbix(key, groupid=0, tag=0):
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

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't get hosts from zabbix: {responce['error']['data']}")
    return responce['result']


def import_hosts_to_zabbix(key, host_list):
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
                "hosts": {"createMissing": True, "updateExisting": True},
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


hosts = [
    {'host': '172.16.49.1', 'name': 'BIBA', 'tags': [{'tag': 'aboba22282222', 'value': ''}], 'groups': [
        {'name': 'Discovered hosts'}], 'interfaces': [{'ip': '172.16.49.1', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'},
    {'host': '172.16.49.2', 'name': 'BOBA', 'tags': [{'tag': 'aboba2228', 'value': ''}, {'tag': 'zalupa', 'value': '1488'}], 'groups': [
        {'name': 'Discovered hosts'}, {'name': 'WAN2'}], 'interfaces': [{'ip': '172.16.49.2', 'interface_ref': 'if1'}], 'inventory_mode': 'DISABLED'}

]
key = get_zabbix_auth_key()
print(import_hosts_to_zabbix(key, hosts))
