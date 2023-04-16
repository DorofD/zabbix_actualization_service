from services.zabbix_scripts.zabbix_api import *


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
    # создание словаря в формате name:id
    result = {group['name']: group['groupid'] for group in responce['result']}
    return result


def add_group_to_zabbix(key, group_name):
    request = {
        "jsonrpc": "2.0",
        "method": "hostgroup.create",
        "params": {
            "name": group_name
        },
        "auth": key,
        "id": 1
    }

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't create zabbix groups: {responce['error']['data']}")
    return True


def delete_groups_from_zabbix(key, groups):
    existing_groups_dict = get_groups_from_zabbix(key)
    groupids_to_delete = []
    for group in groups:
        if group in existing_groups_dict:
            groupids_to_delete.append(existing_groups_dict[group])
    if groupids_to_delete:
        request = {
            "jsonrpc": "2.0",
            "method": "hostgroup.delete",
            "params": groupids_to_delete,
            "auth": key,
            "id": 1
        }
        responce = send_request_to_zabbix(request)
        if 'error' in responce:
            raise Exception(
                f"Can't delete group from zabbix: {responce['error']['data']}")
    return True
