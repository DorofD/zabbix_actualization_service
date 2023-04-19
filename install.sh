#!/bin/bash
sudo apt update
sudo apt install python3.9
sudo apt install python3.9-venv
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools libpython3.9-dev
sudo apt install unixodbc-dev
python3.9 -m venv zas_env
source zas_env/bin/activate
pip install -r requirements.txt
pip wheel uwsgi
mv .env.example .env
python init.py
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > sudo /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
