import pandas as pd
from db_scripts.local_db import *
from db_scripts.ws_db import *


def import_groups_from_excel(file):
    sheet = pd.read_excel(file)
    groups_from_local_db = get_groups_from_local_db()
    current_groups_list = []
    for group in groups_from_local_db:
        current_groups_list.append(group[1])
    groups_to_add = []
    for cell in sheet['groups']:
        if cell not in current_groups_list and type(cell) == str:
            groups_to_add.append(tuple([cell]))
    if groups_to_add:
        add_groups_to_local_db(groups_to_add)
    return True


def import_types_from_excel(file):
    sheet = pd.read_excel(file)
    groups_from_local_db = get_groups_from_local_db()
    types_from_local_db = get_types_from_local_db()

    groups_dict = {}
    for group in groups_from_local_db:
        groups_dict[group[1]] = group[0]

    current_types_dict = {}
    for host_type in types_from_local_db:
        current_types_dict[host_type[1]] = tuple([host_type[1], host_type[2]])

    # сортировка типов на добавляемые и изменяемые
    types_to_add = []
    types_to_update = []
    for i in sheet.index:
        if type(sheet['types'][i]) == str:
            if sheet['type_group'][i] in groups_dict:
                if sheet['types'][i] not in current_types_dict:
                    types_to_add.append(
                        tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                elif groups_dict[sheet['type_group'][i]] != current_types_dict[sheet['types'][i]][1]:
                    types_to_update.append(
                        tuple([sheet['types'][i], groups_dict[sheet['type_group'][i]]]))
                else:
                    continue
            else:
                raise Exception(
                    f'Unknown group in import .xlsx file: {sheet["type_group"][i]}')

    # добавление отсутствующих типов
    if types_to_add:
        add_types_to_local_db(types_to_add)

    # обновление значений изменяемых типов
    if types_to_update:
        update_types_from_local_db(types_to_update)
    return True


def import_tags_from_excel(file):
    sheet = pd.read_excel(file)
    tags_from_local_db = get_tags_from_local_db()

    current_tags_dict = {}
    for tag in tags_from_local_db:
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
    if tags_to_add:
        add_tags_to_local_db(tags_to_add)
    # обновление значений измененных тегов
    if tags_to_update:
        update_tags_from_local_db(tags_to_update)
    return True


def compare_local_and_ws_types():
    # получение типов из WS
    types_from_ws = []
    for host_type in get_types_from_ws_db():
        types_from_ws.append(host_type[0])
    # получение типов из локальной БД
    types_from_local_db = []
    for host_type in get_types_from_local_db():
        types_from_local_db.append(host_type[1])
    # проверка совпадения типов в локальной БД и БД WS
    types_difference = set(types_from_ws) ^ (set(types_from_local_db))
    if not types_difference:
        return True
    else:
        raise Exception(f"Unknown types: {', '.join(types_difference)}")


# import_groups_from_excel('data.xlsx')
# import_types_from_excel('data.xlsx')
# import_tags_from_excel('data.xlsx')

# print(compare_local_and_ws_types())