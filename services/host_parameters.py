import pandas as pd
from db_scripts.local_db import *
from db_scripts.ws_db import *
from zabbix_scripts.zabbix_templates import *


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

    # получение словаря тегов (имя/значение) из локальной БД
    tags = get_tags_from_local_db()
    tags_from_local_db = {tags[i][0]: tags[i][1] for i in range(len(tags))}

    # получение словаря тегов (имя/значение) из Excel
    tags_from_excel = {}
    for i in sheet.index:
        if type(sheet['tags'][i]) == str:
            if str(sheet['tag_value'][i]) == 'nan':
                tags_from_excel[sheet['tags'][i]] = ''
            else:
                tags_from_excel[sheet['tags'][i]] = str(sheet['tag_value'][i])

    # сортировка тегов на добавляемые и изменяемые
    tags_to_add = []
    tags_to_update = []
    for tag in tags_from_excel:
        if tag not in tags_from_local_db:
            tags_to_add.append(tuple([tag, tags_from_excel[tag]]))
        elif tags_from_local_db[tag] != tags_from_excel[tag]:
            tags_to_update.append(tuple([tag, tags_from_excel[tag]]))

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


def update_templates():
    # обновление шаблонов в локальной БД на основе шаблонов zabbix
    key = get_zabbix_auth_key()
    templates_from_zabbix = get_templates_from_zabbix(key)
    templates_from_local_db = [template[1]
                               for template in get_templates_from_local_db()]
    # сортировка шаблонов на добавляемые и удаляемые
    templates_to_add = []
    templates_to_delete = []
    for template in templates_from_zabbix:
        if template not in templates_from_local_db:
            templates_to_add.append(tuple([template,]))
    for template in templates_from_local_db:
        if template not in templates_from_zabbix:
            templates_to_delete.append(template)
    # добавление новых шаблонов
    if templates_to_add:
        add_templates_to_local_db(templates_to_add)
    # удаление отсутствующих шаблонов
    if templates_to_delete:
        delete_templates_from_local_db(templates_to_delete)
    return True


def set_templates_to_types(file):
    # ! перед выполнением этой функции необходим импорт хостов,
    # т.к. в нём проверяется совпадение типов в локальной БД и WS

    # обновление шаблонов
    update_templates()

    sheet = pd.read_excel(file)
    # словарь типов в формате type:id
    types_dict = {host_type[1]: host_type[0]
                  for host_type in get_types_from_local_db()}
    # словарь шаблонов в формате template:id
    templates_dict = {template[1]: template[0]
                      for template in get_templates_from_local_db()}
    notes_to_add = []
    for i in sheet.index:
        if str(sheet['types'][i]) != 'nan' and sheet['types'][i] in types_dict and str(sheet['type_template'][i]) != 'nan':
            notes_to_add.append(tuple(
                [types_dict[sheet['types'][i]], templates_dict[sheet['type_template'][i]]]))

    # проверка уникальности записей и удаление дубликатов
    existing_notes = get_type_template_notes()
    not_unique = []
    for note in notes_to_add:
        if note in existing_notes:
            not_unique.append(note)
    for note in not_unique:
        notes_to_add.remove(note)
    # добавление записей
    if notes_to_add:
        add_type_template_notes(notes_to_add)
    return (True)


# set_templates_to_types('set_templates.xlsx')
# update_templates()
# print(get_type_template_view())

# import_groups_from_excel('data.xlsx')
# import_types_from_excel('data.xlsx')
# import_tags_from_excel('data.xlsx')

# print(compare_local_and_ws_types())
