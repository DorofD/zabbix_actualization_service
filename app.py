from flask import Flask, render_template, send_file, url_for, request, flash, session, redirect, abort
from flask_scheduler import Scheduler
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from services.main_operations import *
from services.ws_entities.host_parameters import set_templates_to_types, set_templates_to_hosts, get_relations_xlsx, get_hosts_xlsx, get_events_from_log
from services.users import *
from services.ws_entities.shops import update_excel_path
from models.local_db import get_users, get_excel_path, get_type_template_view, get_host_template_view, get_zabbix_params_from_local_db, set_zabbix_params, get_recipients, delete_recipient, add_recipient, delete_user, add_user, get_telegram_params, update_telegram_parameter
from models.ws_db import get_hosts_from_ws_db, get_types_from_ws_db
from services.zabbix_scripts.zabbix_templates import *
from services.zabbix_scripts.zabbix_hosts import delete_hosts_from_zabbix
from services.zabbix_scripts.zabbix_events import add_problem_message
from services.notifications.email_smtp import send_email
from services.notifications.telegram import send_tg_message

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
        if request.form['operation'] == 'main':
            try:
                if execute_main_operations():
                    flash(
                        f'Операция «Полная актуализация» успешно выполнена', category='success')
            except Exception as exc:
                flash(
                    f'Операция «Полная актуализация» не выполнена: {str(exc)}', category='error')
        if request.form['operation'] == 'update_local_data':
            try:
                if update_local_data():
                    flash(
                        f'Операция «Обновление локальных данных» успешно выполнена', category='success')
            except Exception as exc:
                flash(
                    f'Операция «Обновление локальных данных» не выполнена: {str(exc)}', category='error')
        if request.form['operation'] == 'delete_zabbix_hosts':
            try:
                key = get_zabbix_auth_key()
                if delete_hosts_from_zabbix(key=key, ip_list=[]):
                    flash(
                        f'Операция «Удаление хостов» успешно выполнена', category='success')
            except Exception as exc:
                flash(
                    f'Операция «Удаление хостов» не выполнена: {str(exc)}', category='error')

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
                if not notes:
                    notes = [['Связи отсутствуют', '']]
                table_name = 'Тип хоста из WS - Шаблон Zabbix'
            if request.form['operation'] == "show_host_template":
                notes = get_host_template_view()
                if not notes:
                    notes = [['Связи отсутствуют', '']]
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


@ app.route('/mgmt_params', methods=(['POST', 'GET']))
def mgmt_params():
    if not current_user.is_authenticated:
        return render_template('login.html')
    address = 'Отсутствует'
    version = 'Отсутствует'
    templates = ['Шаблоны не найдены']
    msg_type = ''
    try:
        params = get_zabbix_params_from_local_db()
        key = get_zabbix_auth_key()
        templates = get_templates_from_zabbix(key)
    except:
        flash(
            f'Ошибка доступа к Zabbix серверу, проверьте корректность введенных параметров', category='error')
        msg_type = 'zabbix'
    if params:
        address = params[0][1]
        version = params[0][2]
    excel_path = get_excel_path()
    if not excel_path:
        excel_path = 'Путь не найден'
    else:
        excel_path = excel_path[0][0]

    if request.method == 'POST':
        if request.form['operation'] == 'change_zabbix':
            try:
                if not request.form['address'] or not request.form['version']:
                    raise Exception(
                        'Оба поля обязательны к заполнению')
                set_zabbix_params(
                    [request.form['address'], request.form['version']])
                request.form['address']
                address = request.form['address']
                version = request.form['version']
                flash('Параметры изменены', category='success')
                msg_type = 'zabbix'
            except Exception as exc:
                flash(
                    f'Ошибка изменения параметров: {str(exc)}', category='error')
                msg_type = 'zabbix'
        if request.form['operation'] == 'change_excel':
            try:
                if not request.form['excel_path']:
                    raise Exception(
                        'Поле обязательно к заполнению')
                update_excel_path(request.form['excel_path'])
                flash('Параметры изменены', category='success')
                msg_type = 'excel'
                excel_path = get_excel_path()[0][0]
            except Exception as exc:
                flash(
                    f'Ошибка изменения параметров: {str(exc)}', category='error')
                msg_type = 'excel'

    return render_template('mgmt_params.html', class2='active', class2_3='active', excel_path=excel_path, address=address, version=version, templates=templates, msg_type=msg_type, login=session['username'])


@ app.route('/mgmt_notifications', methods=(['POST', 'GET']))
def mgmt_notifications():
    if not current_user.is_authenticated:
        return render_template('login.html')
    msg_type = ''

    if request.method == 'POST':
        try:
            if request.form['operation'] == 'delete_recipient':
                delete_recipient(request.form['recipient'])
            elif request.form['operation'] == 'add_recipient':
                add_recipient(request.form['recipient'])
            elif request.form['operation'] == 'send_email':
                if not request.form['recipient'] or not request.form['letter_text']:
                    flash(f'Заполните оба поля для отправки письма',
                          category='error')
                    msg_type = 'email'
                else:
                    if send_email(recipient=request.form['recipient'], text=request.form['letter_text']):
                        flash(f'Сообщение отправлено',
                              category='success')
                    else:
                        flash(
                            f'Ошибка отправки сообщения', category='error')
                    msg_type = 'email'
            elif request.form['operation'] == 'set_bot_token':
                update_telegram_parameter(
                    'bot_token', (request.form['bot_token']))
            elif request.form['operation'] == 'set_chat_id':
                update_telegram_parameter('chat_id', (request.form['chat_id']))
            elif request.form['operation'] == 'set_tg_condition':
                update_telegram_parameter('active', int(request.form['value']))
            elif request.form['operation'] == 'send_tg_message':
                if not request.form['letter_text']:
                    flash(f'Заполните поле для отправки сообщения',
                          category='error')
                    msg_type = 'telegram'
                else:
                    if send_tg_message(request.form['letter_text']):
                        flash(f'Сообщение отправлено',
                              category='success')
                    else:
                        flash(
                            f'Ошибка отправки сообщения', category='error')
                    msg_type = 'telegram'

        except Exception as exc:
            flash(
                f'Неопознанная ошибка {str(exc)}', category='error')
            msg_type = 'all'
    recipients = get_recipients()
    tg_params = get_telegram_params()
    return render_template('mgmt_notifications.html', class2='active', class2_4='active', chat_id=tg_params[0][0], bot_token=tg_params[0][1], recipients=recipients, tg_active=tg_params[0][2], msg_type=msg_type, login=session['username'])


@ app.route('/mgmt_logs', methods=(['POST', 'GET']))
def mgmt_logs():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        try:
            return send_file('log.txt', as_attachment=True)
        except Exception as exc:
            flash(
                f'Ошибка выгрузки логов: {str(exc)}', category='error')
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
            flash(
                f'Ошибка выполнения операции: {str(exc)}', category='error')

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
            flash(
                f'Операция не выполнена: {str(exc)}', category='error')
    users = get_users()

    return render_template('users.html', class4='active', users=users, login=session['username'])


@ app.route('/about', methods=(['POST', 'GET']))
def about():
    if not current_user.is_authenticated:
        return render_template('login.html')
    if request.method == 'POST':
        return send_file('readme.pdf', as_attachment=True)

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


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method != 'POST':
        abort(400)
    try:
        add_problem_message(request.json)
    except Exception as exc:
        app_logger.error(f"Can't set SD request number to Zabbix event: {exc}")
    return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
