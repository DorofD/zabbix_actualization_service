from zabbix_operations import *
from zabbix_groups import get_groups_from_zabbix


def get_maintenance_from_zabbix(key):
    request = {
        "jsonrpc": "2.0",
        "method": "maintenance.get",
        "params": {
            "output": "extend",
            "selectGroups": "extend",
            "selectTimeperiods": "extend",
            "selectTags": "extend"
        },
        "auth": key,
        "id": 1
    }
    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't get maintenance from zabbix: {responce['error']['data']}")
    return responce['result']


def add_maintenance_to_zabbix(key, maintenance):
    existing_groups_dict = get_groups_from_zabbix(key)
    groupids = []
    for group in maintenance['group_names']:
        if group in existing_groups_dict:
            groupids.append(existing_groups_dict[group])
        else:
            raise Exception(
                f"Can't add maintenance to zabbix, group does not exist: {group}")
    request = {
        "jsonrpc": "2.0",
        "method": "maintenance.create",
        "params": {
            "name": maintenance['name'],
            "active_since": '1672606800',
            "active_till": '2062008000',
            "tags_evaltype": 0,
            "groupids": groupids,
            'timeperiods': [{'timeperiodid': '51',
                             'timeperiod_type': '2',
                             'every': '1',
                             'month': '0',
                             'dayofweek': '0',
                             'day': '1',
                                    'start_time': maintenance['start_time'],
                                    'period': maintenance['period'],
                                    'start_date': '0'}],
            # 'tags': [{"tag": "tag1", "value": "value1", }]
        },
        "auth": key,
        "id": 1
    }
    if 'tags' in maintenance:
        request['params']['tags'] = maintenance['tags']

    responce = send_request_to_zabbix(request)
    if 'error' in responce:
        raise Exception(
            f"Can't add maintenance to zabbix: {responce['error']['data']}")
    return True


# key = get_zabbix_auth_key()

# maintenance = {'name': 'zalupa1488',
#                'start_time': '50400',
#                'period': '43200',
#                'group_names': ['WAN2', 'WAN1']}
# print(add_maintenance_to_zabbix(key, maintenance))

# sas = get_maintenance_from_zabbix(key)
# for i in sas:
#     print(i)
