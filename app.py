from flask import Flask, render_template, send_file, url_for, request, flash, session, redirect
from flask_scheduler import Scheduler
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from services.main_operations import execute_main_operations
from services.host_parameters import set_templates_to_types, set_templates_to_hosts, get_relations_xlsx, get_hosts_xlsx, get_events_from_log
from services.users import *
from db_scripts.local_db import get_type_template_view, get_host_template_view, get_zabbix_params_from_local_db, set_zabbix_params, get_recipients, delete_recipient, add_recipient, delete_user, add_user
from db_scripts.ws_db import get_hosts_from_ws_db, get_types_from_ws_db
from zabbix_scripts.zabbix_templates import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gDLKWIgkuygwdf23'
scheduler = Scheduler(app)
login_manager = LoginManager(app)


@scheduler.runner(interval=28800)
def main_task():
    execute_main_operations()


@login_manager.user_loader
def load_user(user_name):
    return UserLogin().get_user_from_db(user_name)


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    events = get_events_from_log()
    return render_template('index.html', class1='active', login=session['username'], events=events)


@app.route('/management')
def management():
    if not current_user.is_authenticated:
        return render_template('login.html')
    return render_template('management.html', class2='active', login=session['username'])


@app.route('/mgmt_operations', methods=(['POST', 'GET']))
def mgmt_operations():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        try:
            if execute_main_operations():
                flash(
                    f'Операция «{request.form["operation"]}» успешно выполнена', category='success')
        except Exception as exc:
            flash(
                f'Операция «{request.form["operation"]}» не выполнена: {str(exc)}', category='error')

    return render_template('mgmt_operations.html', class2='active', class2_1='active', login=session['username'])


@app.route('/mgmt_relations', methods=(['POST', 'GET']))
def mgmt_relations():
    if not current_user.is_authenticated:
        return render_template('login.html')
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
    return render_template('mgmt_relations.html', class2='active', class2_2='active', notes=notes, table_name=table_name, login=session['username'])


@ app.route('/mgmt_zabbix_params', methods=(['POST', 'GET']))
def mgmt_zabbix_params():
    if not current_user.is_authenticated:
        return render_template('login.html')
    address = 'Отсутствует'
    version = 'Отсутствует'
    params = get_zabbix_params_from_local_db()
    key = get_zabbix_auth_key()
    templates = get_templates_from_zabbix(key)
    if params:
        address = params[0][1]
        version = params[0][2]
    if request.method == 'POST':
        try:
            if not request.form['address'] or not request.form['version']:
                raise Exception('Оба поля обязательны к заполнению')
            set_zabbix_params(
                [request.form['address'], request.form['version']])
            request.form['address']
            address = request.form['address']
            version = request.form['version']
            flash('Параметры изменены', category='success')
        except Exception as exc:
            flash(f'Ошибка изменения параметров: {str(exc)}', category='error')

    return render_template('mgmt_zabbix_params.html', class2='active', class2_3='active', address=address, version=version, templates=templates, login=session['username'])


@ app.route('/mgmt_notifications', methods=(['POST', 'GET']))
def mgmt_notifications():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        try:
            if request.form['operation'] == 'delete':
                delete_recipient(request.form['recipient'])
            elif request.form['operation'] == 'add':
                add_recipient(request.form['recipient'], request.form['type'])
        except Exception as exc:
            flash(f'Операция не выполнена: {str(exc)}', category='error')
    recipients = get_recipients()
    return render_template('mgmt_notifications.html', class2='active', class2_4='active', recipients=recipients, login=session['username'])


@ app.route('/mgmt_logs', methods=(['POST', 'GET']))
def mgmt_logs():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        try:
            return send_file('log.txt', as_attachment=True)
        except Exception as exc:
            flash(f'Ошибка выгрузки логов: {str(exc)}', category='error')
    return render_template('mgmt_logs.html', class2='active', class2_5='active', login=session['username'])


@ app.route('/ws', methods=(['POST', 'GET']))
def ws():
    if not current_user.is_authenticated:
        return render_template('login.html')
    hosts = []
    types = [host_type[0] for host_type in get_types_from_ws_db()]
    if request.method == 'POST':
        try:
            if request.form['operation'] == 'find' and request.form['address']:
                hosts = [
                    f'{host[0]} {host[1]} - {host[2]} ({host[3]})' for host in get_hosts_from_ws_db(request.form['address'])]
                if not hosts:
                    hosts.append(
                        f"Хост с адресом {request.form['address']} не найден")
            elif request.form['operation'] == 'export':
                notes = [name for name in request.form]
                file = get_hosts_xlsx(types=types, notes=notes)
                return send_file(file, as_attachment=True)
        except Exception as exc:
            flash(f'Ошибка выполнения операции: {str(exc)}', category='error')

    return render_template('ws.html', class3='active', hosts=hosts, types=types, login=session['username'])


@ app.route('/users', methods=(['POST', 'GET']))
def users():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        try:
            if request.form['operation'] == 'delete':
                delete_user(login=request.form['login'])
            if request.form['operation'] == 'add':
                add_user(login=request.form['login'],
                         password='', auth_type='LDAP')
            if request.form['operation'] == 'change':
                if request.form['password1'] != request.form['password2']:
                    raise Exception("Пароли не совпадают")
                change_password(
                    request.form['login'], request.form['password1'])
                flash(
                    f"Пароль пользователя {request.form['login']} успешно изменен", category='success')
        except Exception as exc:
            flash(f'Операция не выполнена: {str(exc)}', category='error')
    users = get_users()

    return render_template('users.html', class4='active', users=users, login=session['username'])


@ app.route('/about')
def about():
    if not current_user.is_authenticated:
        return render_template('login.html')
    return render_template('about.html', class5='active', login=session['username'])


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user = signin(request.form['login'], request.form['password'])
        if user:
            userlogin = UserLogin().create(user)
            session['username'] = request.form['login']
            login_user(userlogin)
            return redirect(url_for('index'))
        else:
            flash('Не удалось войти', category='wrongpass')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
