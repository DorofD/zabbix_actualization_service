from flask import Flask, render_template, send_file, url_for, request, flash
from flask_scheduler import Scheduler
from services.main_operations import execute_main_operations

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


@app.route('/mgmt_operations')
def mgmt_operations():
    return render_template('mgmt_operations.html', class2='active', class2_1='active')


@app.route('/mgmt_relations')
def mgmt_relations():
    return render_template('mgmt_relations.html', class2='active', class2_2='active')


@app.route('/mgmt_zabbix_params')
def mgmt_zabbix_params():
    return render_template('mgmt_zabbix_params.html', class2='active', class2_3='active')


@app.route('/mgmt_logs')
def mgmt_logs():
    return render_template('mgmt_logs.html', class2='active', class2_4='active')


@app.route('/mgmt_notifications')
def mgmt_notifications():
    return render_template('mgmt_notifications.html', class2='active', class2_5='active')


@app.route('/ws')
def ws():
    return render_template('ws.html', class3='active')


@app.route('/users')
def users():
    return render_template('users.html', class4='active')


@app.route('/about')
def about():
    return render_template('about.html', class5='active')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
