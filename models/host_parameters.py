import pandas as pd


def import_host_parameters(file):
    try:
        sheet = pd.read_excel(file)
        # импорт groups
        query = f"""
                    SELECT * FROM groups
                    """
        groups_from_local_db = execute_db_query(query)
        if groups_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get groups from local DB"}
            return result
        current_groups_list = []
        for group in groups_from_local_db['result']:
            current_groups_list.append(group[1])
        groups_to_add = []
        for cell in sheet['groups']:
            if cell not in current_groups_list and type(cell) == str:
                groups_to_add.append(tuple([cell]))
        groups_add_count = len(groups_to_add)
        query = f"""
                    INSERT INTO groups ('group') VALUES(?);
                """
        if groups_to_add:
            if execute_db_query(query, groups_to_add)['status'] == False:
                result = {'status': False,
                          'message': "Can't insert groups"}
                return result

        # импорт types
        query = f"""
                    SELECT * FROM groups
                    """
        groups_from_local_db = execute_db_query(query)
        if groups_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get groups from local DB"}
            return result

        query = f"""
                    SELECT * FROM types
                """
        types_from_local_db = execute_db_query(query)
        if types_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get types from local DB"}
            return result

        groups_dict = {}
        for group in groups_from_local_db['result']:
            groups_dict[group[1]] = group[0]

        current_types_dict = {}
        for host_type in types_from_local_db['result']:
            current_types_dict[host_type[1]] = tuple(
                [host_type[1], host_type[2]])
        types_to_add = []
        types_to_update = []
        for i in sheet.index:
            if type(sheet['types'][i]) == str:
                if sheet['type_group'][i] in groups_dict:
                    num = groups_dict[sheet['type_group'][i]]
                    if sheet['types'][i] not in current_types_dict:
                        types_to_add.append(
                            tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                    elif groups_dict[sheet['type_group'][i]] != current_types_dict[sheet['types'][i]][1]:
                        types_to_update.append(
                            tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                    else:
                        continue
                else:
                    result = {'status': False,
                              'message': "Unknown group in import file"}
                    return result

        # добавление отсутствующих типов
        query = f"""
                    INSERT INTO types ('type', 'group_id') VALUES(?, ?);
                """
        types_add_count = len(types_to_add)
        if types_to_add:
            if execute_db_query(query, types_to_add)['status'] == False:
                result = {'status': True,
                          'message': 'Error types adding', 'result': ''}

        # обновление значений измененных типов
        types_update_count = 0
        for host_type in types_to_update:
            query = f"""
                        UPDATE types SET (group_id) = ('{host_type[1]}')
                        WHERE type = '{host_type[0]}';
                    """
            groups_update_count += 1
            execute_db_query(query)

        # импорт tags
        query = """
            SELECT tag, value FROM tags
        """
        tags_from_local_db = execute_db_query(query)
        if tags_from_local_db['status'] == False:
            result = {'status': False,
                      'message': "Can't get tags from local DB"}
            return result

        current_tags_dict = {}
        for tag in tags_from_local_db['result']:
            current_tags_dict[tag[0]] = tag

        tags_to_add = []
        tags_to_update = []
        for i in sheet.index:
            if type(sheet['tags'][i]) == str:
                if sheet['tags'][i] not in current_tags_dict:
                    if type(sheet['tag_value'][i]) == str:
                        tags_to_add.append(tuple(
                            [sheet['tags'][i], sheet['tag_value'][i]]))
                    else:
                        tags_to_add.append(tuple(
                            [sheet['tags'][i], '']))
                elif sheet['tag_value'][i] != current_tags_dict[sheet['tags'][i]][1]:
                    if type(sheet['tag_value'][i]) == str or type(sheet['tag_value'][i]) == int:
                        tags_to_update.append(tuple(
                            [sheet['tags'][i], sheet['tag_value'][i]]))
                    elif type(sheet['tag_value'][i]) == float:
                        tags_to_update.append(tuple(
                            [sheet['tags'][i], '']))
                    else:
                        continue

        # добавление отсутствующих тегов
        query = f"""
                    INSERT INTO tags ('tag', 'value') VALUES(?, ?);
                """
        tags_add_count = len(tags_to_add)
        if tags_to_add:
            if execute_db_query(query, tags_to_add)['status'] == False:
                result = {'status': True,
                          'message': 'Error tags adding', 'result': ''}

        # обновление значений измененных тегов
        tags_update_count = 0
        for tag in tags_to_update:
            query = f"""
                        UPDATE tags SET (value) = ('{tag[1]}')
                        WHERE tag = '{tag[0]}';
                    """
            tags_update_count += 1
            execute_db_query(query)

        result = {'status': True, 'message': f"groups add: {groups_add_count}, types add/update: {types_add_count}/{types_update_count}, tags add/update: {tags_add_count}/{tags_update_count}"}
        return result

    except Exception as exc:
        result = {'status': False, 'message': exc}
        return result
