from flask import Flask, render_template, send_file, url_for, request, flash
from services import main_operations


app = Flask(__name__)
app.config['SECRET_KEY'] = 'aboba1488'


@app.route('/')
def index():
    return render_template('index.html', class1='active', class2='', class3='', class4='')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
