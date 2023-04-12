import pandas as pd
from db_scripts.local_db import *
from db_scripts.ws_db import *
from zabbix_scripts.zabbix_templates import *


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


def update_types():
    # обновление типов хостов на основе типов из WS
    types_from_ws = [host_type[0] for host_type in get_types_from_ws_db()]
    types_from_local_db = [host_type[1]
                           for host_type in get_types_from_local_db()]
    types_to_add = []
    for host_type in types_from_ws:
        if host_type not in types_from_local_db:
            types_to_add.append(tuple([host_type]))
    if types_to_add:
        add_types_to_local_db(types_to_add)


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
    # обновление типов
    update_types()
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


def set_templates_to_hosts(file):
    # обновление типов
    update_types()
    # обновление шаблонов
    update_templates()
    sheet = pd.read_excel(file)
    # словарь шаблонов в формате template:id
    templates_dict = {template[1]: template[0]
                      for template in get_templates_from_local_db()}
    # словарь хостов в формате ip:id
    hosts_dict = {host[1]: host[3] for host in get_hosts_from_local_db()}
    # список записей из импортируемого файла
    notes_list_from_xlsx = []
    for i in sheet.index:
        if str(sheet['hosts'][i]) != 'nan' and str(sheet['host_template'][i]) != 'nan':
            notes_list_from_xlsx.append(
                [sheet['hosts'][i], sheet['host_template'][i]])

    notes_to_add = []
    for note in notes_list_from_xlsx:
        if note[0] not in hosts_dict:
            raise Exception(
                f"Can't set templates to hosts: unknown host ({note[0]}) in imported file")
        if note[1] not in templates_dict:
            raise Exception(
                f"Can't set templates to hosts: unknown template ({note[1]}) in imported file")
        notes_to_add.append(
            tuple([hosts_dict[note[0]], templates_dict[note[1]]]))

    # удаление всех записей из таблицы
    delete_host_template_notes_from_local_db()
    # добавление записей
    if notes_to_add:
        add_host_template_notes(notes_to_add)
    return True


def get_relations_xlsx(relation):
    try:
        if os.path.exists('export.xlsx'):
            os.remove('export.xlsx')
        if relation == "get_type_template":
            notes = get_type_template_view()
            column1 = 'type'
            column2 = 'template'
        elif relation == "get_host_template":
            notes = get_host_template_view()
            column1 = 'host'
            column2 = 'template'
        writer = pd.ExcelWriter("export.xlsx")
        data = pd.DataFrame({
            column1: [note[0] for note in notes],
            column2: [note[1] for note in notes],
        })
        data.to_excel(writer, 'Sheet1', index=False)
        writer.save()
        return 'export.xlsx'
    except Exception as exc:
        raise Exception(f'Ошибка формирования .xlsx: {exc}')


def get_hosts_xlsx(notes, types):
    if os.path.exists('export.xlsx'):
        os.remove('export.xlsx')

    if 'all' in notes:
        hosts = get_hosts_from_ws_db(types='all')
    elif 'models' in notes:
        notes = get_routers_from_ws_db()
        writer = pd.ExcelWriter("export.xlsx")
        data = pd.DataFrame({
            'PID': [note[0] for note in notes],
            'Магазин': [note[1] for note in notes],
            'Модель роутера': [note[2] for note in notes],
        })
        data.to_excel(writer, 'Sheet1', index=False)
        writer.save()
        return 'export.xlsx'
    elif 'shops' in notes:
        notes = get_shops_from_ws_db()
        writer = pd.ExcelWriter("export.xlsx")
        data = pd.DataFrame({
            'PID': [note[0] for note in notes],
            'Магазин': [note[1] for note in notes],
        })
        data.to_excel(writer, 'Sheet1', index=False)
        writer.save()
        return 'export.xlsx'
    else:
        types_to_export = []
        for note in notes:
            if note in types:
                types_to_export.append(note)
        if not types_to_export:
            raise Exception("Не выбрано ни одного типа")
        hosts = get_hosts_from_ws_db(types=types_to_export)

    writer = pd.ExcelWriter("export.xlsx")
    data = pd.DataFrame({
        'PID': [host[0] for host in hosts],
        'Магазин': [host[1] for host in hosts],
        'Тип': [host[2] for host in hosts],
        'IP': [host[3] for host in hosts],
        'Хост': [host[4] for host in hosts],
        'Комментарий': [host[5] for host in hosts],
        'Автор записи': [host[6] for host in hosts],

    })
    data.to_excel(writer, 'Sheet1', index=False)
    writer.save()
    return 'export.xlsx'


def get_events_from_log():
    event_list = []
    if not os.path.exists('log.txt'):
        event_list.append(['...', 'На данный момент события отсутствуют'])
        return event_list
    with open('log.txt') as file:
        for line in (file.readlines()[-10:]):
            event_list.append(line.replace('\n', ''))
    if not event_list:
        event_list.append(['...', 'На данный момент события отсутствуют'])
        return event_list
    final_list = []
    for note in reversed(event_list):
        final_list.append([note[0:16], note[24:]])
    return final_list
