#!/bin/bash
# установка необходимых пакетов
sudo apt update
sudo apt install python3.9
sudo apt install python3.9-venv
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
sudo apt install libpython3.9-dev
sudo apt install unixodbc-dev
sudo apt-get install apt-transport-https
sudo apt-get update
# настройка окружения
python3.9 -m venv zas_env
source zas_env/bin/activate
pip install wheel
pip install -r requirements.txt
pip install uwsgi
mv .env.example .env
python init.py
deactivate
# установка драйвера MSSQL
sudo su -c 'curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -'
sudo su -c 'curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list'
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
# настройка службы uWSGI
folder="$PWD"
user="$USER"
sed -i "s:User=.*:User=$user:g" ubuntu_deploy/zas.service
sed -i "s:WorkingDirectory=.*:WorkingDirectory=$folder:g" ubuntu_deploy/zas.service
sed -i "s:Environment=.*:Environment="PATH=$folder'/zas_env/bin'":g" ubuntu_deploy/zas.service
sed -i "s:ExecStart=.*:ExecStart=$folder/zas_env/bin/uwsgi --ini zas.ini:g" ubuntu_deploy/zas.service
sudo cp ubuntu_deploy/zas.service /etc/systemd/system/zas.service
cp $folder/ubuntu_deploy/zas.ini $folder/zas.ini
cp $folder/ubuntu_deploy/wsgi.py $folder/wsgi.py 
sudo systemctl daemon-reload
sudo systemctl start zas
sudo systemctl enable zas
# настройка NGINX
sed -i "s|uwsgi_pass unix:.*|uwsgi_pass unix:$folder/zas.sock;|g" ubuntu_deploy/zas_nginx
sudo cp ubuntu_deploy/zas_nginx /etc/nginx/sites-available/zas_nginx
sudo ln -s /etc/nginx/sites-available/zas_nginx /etc/nginx/sites-enabled/zas_nginx
sudo nginx -t
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx