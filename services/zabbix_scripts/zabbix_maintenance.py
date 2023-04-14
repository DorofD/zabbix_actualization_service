from services.zabbix_scripts.zabbix_operations import *
from services.zabbix_scripts.zabbix_groups import get_groups_from_zabbix
import pandas as pd


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


def update_zabbix_maintenance(key):
    # словарь существующих групп в формате name:id
    groups_dict = get_groups_from_zabbix(key)
    # словарь существующих обслуживаний в формате name:id
    existing_maintenance_dict = {maintenance['name']: maintenance['maintenanceid']
                                 for maintenance in get_maintenance_from_zabbix(key)}
    for group in groups_dict:
        if 'WT' in group and group not in existing_maintenance_dict:
            # шаблон добавления обслуживания
            maintenance_template = {'name': 'name',
                                    'start_time': '50400',
                                    'period': '43200',
                                    'group_names': ['name1', 'name2']}
            pass
            start_time, end_time = group.replace('WT ', '').split('-')
            end_time = end_time[0:5]
            # время начала работы в секундах
            start_time = int(pd.to_datetime(start_time, format='%H:%M').minute) * \
                60 + int(pd.to_datetime(start_time,
                         format='%H:%M').hour) * 60 * 60
            # время конца работы в секундах
            end_time = int(pd.to_datetime(end_time, format='%H:%M').minute) * \
                60 + int(pd.to_datetime(end_time, format='%H:%M').hour) * 60 * 60
            off_time = 86400 - (end_time - start_time)
            maintenance_template['name'] = f'{group}'
            maintenance_template['start_time'] = end_time
            maintenance_template['period'] = off_time
            maintenance_template['group_names'] = [group]
            add_maintenance_to_zabbix(
                key=key, maintenance=maintenance_template)
    return True
