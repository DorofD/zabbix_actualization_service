#!/bin/bash
sudo apt install python3.9
sudo apt install python3.9-venv
sudo apt install unixodbc-dev
python3.9 -m venv zas_env
source zas_env/bin/activate
pip install -r requirements.txt
pip install wheel uwsgi
mv .env.example .env
python init.py