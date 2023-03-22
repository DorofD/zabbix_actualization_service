from flask import Flask, render_template, send_file, url_for, request, flash
from models import model


app = Flask(__name__)
app.config['SECRET_KEY'] = 'aboba1488'


@app.route('/')
def index():
    return render_template('index.html', class1='active', class2='', class3='', class4='')


@app.route('/report', methods=['POST'])
def report():
    print(request.form['operator'])
    print(request.form['date'])
    file = model.get_report(
        int(request.form['operator']), request.form['date'])
    if file:
        return send_file(file, as_attachment=True)
    flash('Ошибка формирования отчёта', category='error')
    return render_template('index.html', class1='active', class2='')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
