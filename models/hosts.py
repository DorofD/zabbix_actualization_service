from host_parameters import compare_local_and_ws_types
from db_scripts.local_db import get_hosts_from_local_db, get_types_from_local_db, add_hosts_to_local_db, update_hosts_from_local_db
from db_scripts.ws_db import get_hosts_from_ws_db
import logging


logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="w", format=f'%(asctime)s %(levelname)s: %(message)s')


def import_hosts():
    # проверка совпадения типов в локальной БД и БД WS
    compare_local_and_ws_types()

    hosts_from_ws_db = get_hosts_from_ws_db()
    hosts_from_local_db = get_hosts_from_local_db()

    addresses_from_local_db = []
    for host in hosts_from_local_db:
        addresses_from_local_db.append(host[1])

    types = get_types_from_local_db()
    types_dict = {types[i][1]: types[i][0] for i in range(len(types))}

    # сортировка хостов на добавляемые/обновляемые
    spent_addresses = []
    hosts_to_add = []
    hosts_to_update = []
    for host in hosts_from_ws_db:
        if host[1] in spent_addresses:
            raise Exception(f'Duplicate ip: {host}')
        spent_addresses.append(host[1])
        if host not in hosts_from_local_db:
            if host[1] not in addresses_from_local_db:
                hosts_to_add.append(
                    tuple([host[1], host[0], types_dict[host[2]]]))
            elif host[1] in addresses_from_local_db:
                hosts_to_update.append(
                    tuple([host[1], host[0], types_dict[host[2]]]))

    # добавление новых хостов
    if hosts_to_add:
        add_hosts_to_local_db(hosts_to_add)
    # обновление измененных хостов
    if hosts_to_update:
        update_hosts_from_local_db(hosts_to_update)
    return True


# print(import_hosts())
