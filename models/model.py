
from db_scripts import ws_db as db
import logging
print(db.get_hosts_from_ws_db('WAN2'))


logging.basicConfig(level=logging.INFO,
                    filename="log.txt", filemode="w", format=f'%(asctime)s %(levelname)s: %(message)s')


def import_hosts(types=[]):
    # получение типов из WS
    try:
        types_from_ws = get_types_from_ws_db()
        if types_from_ws['status'] == False:
            result = {'status': False, 'message': "Can't get types from WS"}
            return result
        types_from_ws = types_from_ws['result']
        types_from_ws_list = []
        for host_type in types_from_ws:
            types_from_ws_list.append(host_type[0])

        # получение типов из локальной БД
        query = """
                SELECT * FROM types
            """
        types_from_local_db = execute_db_query(query)
        if types_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get types from local DB"}
            return result
        types_from_local_db_dict = {}
        for host_type in types_from_local_db['result']:
            types_from_local_db_dict[host_type[1]] = host_type

        # проверка совпадения типов в локальной БД и БД WS
        for host_type in types_from_local_db_dict:
            if host_type not in types_from_ws_list:
                result = {'status': False,
                          'message': f"Unknown type in local DB: {host_type}"}
                return result
        for host_type in types_from_ws_list:
            if host_type not in types_from_local_db_dict:
                result = {'status': False,
                          'message': f"Unknown type in WS DB: {host_type}"}
                return result
        types_dict = types_from_local_db_dict

        # выбор финального списка типов для импорта
        if types:
            for host_type in types:
                if host_type not in types_dict:
                    result = {'status': False,
                              'message': f"Unknown type was given: {host_type}"}
                    return result
            types_list = types
        else:
            types_list = types_from_ws_list

        # получение всех хостов из локальной БД
        query = """
            SELECT hosts.ip, hosts.shop_pid, types.type FROM hosts
            INNER JOIN types ON hosts.type_id = types.id
        """
        hosts_from_local_db = execute_db_query(query)
        if hosts_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get hosts from local DB"}
            return result
        hosts_from_local_db = hosts_from_local_db['result']
        hosts_from_local_db_dict = {}
        for host in hosts_from_local_db:
            hosts_from_local_db_dict[host[0]] = host
        import_results = {}
        update_count = 0
        add_count = 0
        spent_addresses = []
        for host_type in types_list:
            # получение хостов из WS по типу
            hosts_from_ws_db = get_hosts_from_ws_db(host_type)
            if hosts_from_ws_db['status'] == False:
                import_results[host_type] = {
                    'status': False, 'message': f"Can't get {host_type} from WS DB"}
                continue
            hosts_from_ws_db = hosts_from_ws_db['result']

            hosts_to_add = []
            hosts_to_update = []
            # сортировка хостов на добавляемые/обновляемые
            for host in hosts_from_ws_db:
                if host[2] in spent_addresses:
                    result = {'status': False,
                              'message': f"Duplicate host ip: {host}"}
                    return result
                else:
                    spent_addresses.append(host[2])
                if host[2] not in hosts_from_local_db_dict:
                    hosts_to_add.append(
                        tuple([host[2], host[0], types_dict[host[3]][0]]))
                elif host[3] != hosts_from_local_db_dict[host[2]][2] or host[0] != hosts_from_local_db_dict[host[2]][1]:
                    hosts_to_update.append(
                        tuple([host[2], host[0], types_dict[host[3]][0]]))
                else:
                    continue

            # добавление новых хостов
            add_count += len(hosts_to_add)
            query = f"""
                        INSERT INTO hosts ('ip', 'shop_pid', 'type_id') VALUES(?, ?, ?);
                    """
            if hosts_to_add:
                if execute_db_query(query, hosts_to_add)['status'] == False:
                    result = {'status': False,
                              'message': f"Can't add new hosts: {host_type}"}
                    return result

            # обновление измененных хостов
            for host in hosts_to_update:
                query = f"""
                            UPDATE hosts SET (shop_pid, type_id) = ('{host[1]}', '{host[2]}')
                            WHERE ip = '{host[0]}';
                        """
                update_count += 1
                if execute_db_query(query, hosts_to_add)['status'] == False:
                    result = {'status': False,
                              'message': f"Can't update hosts: {host_type}"}
                    return result
        result = {'status': True,
                  'message': f'hosts added: {add_count}, hosts updated: {update_count}', 'result': ''}
        return result
    except Exception as exc:
        result = {'status': False, 'message': exc, 'result': ''}
        return result
