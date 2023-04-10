from flask import Flask, render_template, send_file, url_for, request, flash
from flask_scheduler import Scheduler
from services.main_operations import execute_main_operations
from services.host_parameters import set_templates_to_types, set_templates_to_hosts, get_relations_xlsx
from db_scripts.local_db import get_type_template_view, get_host_template_view, get_zabbix_params_from_local_db, set_zabbix_params, get_recipients, delete_recipient, add_recipient
from db_scripts.ws_db import get_hosts_from_ws_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aboba1488'
scheduler = Scheduler(app)


@scheduler.runner(interval=28800)
def main_task():
    execute_main_operations()


@app.route('/')
def index():
    return render_template('index.html', class1='active')


@app.route('/management')
def management():
    return render_template('management.html', class2='active')


@app.route('/mgmt_operations', methods=(['POST', 'GET']))
def mgmt_operations():
    if request.method == 'POST':
        try:
            if execute_main_operations():
                flash(
                    f'Операция «{request.form["operation"]}» успешно выполнена', category='success')
        except Exception as exc:
            flash(
                f'Операция «{request.form["operation"]}» не выполнена: {str(exc)}', category='error')

    return render_template('mgmt_operations.html', class2='active', class2_1='active')


@app.route('/mgmt_relations', methods=(['POST', 'GET']))
def mgmt_relations():
    notes = []
    table_name = ''
    if request.method == 'POST':
        try:
            if request.form['operation'] == 'set_type_template':
                set_templates_to_types(request.files['file'])
                flash('Связи типов хостов с шаблонами успешно установлены',
                      category='success')
            if request.form['operation'] == 'set_host_template':
                set_templates_to_hosts(request.files['file'])
                flash('Связи хостов с шаблонами успешно установлены',
                      category='success')
            if request.form['operation'] == "show_type_template":
                notes = get_type_template_view()
                table_name = 'Тип хоста из WS - Шаблон Zabbix'
            if request.form['operation'] == "show_host_template":
                notes = get_host_template_view()
                table_name = 'Адрес хоста - Шаблон Zabbix'
            if request.form['operation'] == "get_type_template":
                file = get_relations_xlsx(relation="get_type_template")
                return send_file(file, as_attachment=True)
            if request.form['operation'] == "get_host_template":
                file = get_relations_xlsx(relation="get_host_template")
                return send_file(file, as_attachment=True)
        except Exception as exc:
            flash(
                f'Ошибка выполнения операции: {str(exc)}', category='error')
    return render_template('mgmt_relations.html', class2='active', class2_2='active', notes=notes, table_name=table_name)


@ app.route('/mgmt_zabbix_params', methods=(['POST', 'GET']))
def mgmt_zabbix_params():
    address = 'Отсутствует'
    version = 'Отсутствует'
    params = get_zabbix_params_from_local_db()
    if params:
        address = params[0][1]
        version = params[0][2]
    if request.method == 'POST':
        try:
            set_zabbix_params(
                [request.form['address'], request.form['version']])
            address = request.form['address']
            version = request.form['version']
            flash('Параметры изменены', category='success')
        except Exception as exc:
            flash(f'Ошибка изменения параметров: {str(exc)}', category='error')

    return render_template('mgmt_zabbix_params.html', class2='active', class2_3='active', address=address, version=version)


@ app.route('/mgmt_notifications', methods=(['POST', 'GET']))
def mgmt_notifications():
    if request.method == 'POST':
        try:
            if request.form['operation'] == 'delete':
                delete_recipient(request.form['recipient'])
            elif request.form['operation'] == 'add':
                add_recipient(request.form['recipient'], request.form['type'])
        except Exception as exc:
            flash(f'Операция не выполнена: {str(exc)}', category='error')
    recipients = get_recipients()
    return render_template('mgmt_notifications.html', class2='active', class2_4='active', recipients=recipients)


@ app.route('/mgmt_logs', methods=(['POST', 'GET']))
def mgmt_logs():
    if request.method == 'POST':
        try:
            return send_file('log.txt', as_attachment=True)
        except Exception as exc:
            flash(f'Ошибка выгрузки логов: {str(exc)}', category='error')
    return render_template('mgmt_logs.html', class2='active', class2_5='active')


@ app.route('/ws', methods=(['POST', 'GET']))
def ws():
    hosts = []
    if request.method == 'POST':
        if request.form['operation'] == 'find' and request.form['address']:
            hosts = [
                f'{host[0]} {host[1]} - {host[2]} ({host[3]})' for host in get_hosts_from_ws_db(request.form['address'])]
            if not hosts:
                hosts.append(
                    f"Хост с адресом {request.form['address']} не найден")
    return render_template('ws.html', class3='active', hosts=hosts)


@ app.route('/users')
def users():
    return render_template('users.html', class4='active')


@ app.route('/about')
def about():
    return render_template('about.html', class5='active')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
