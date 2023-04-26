FROM ubuntu:20.04

COPY . /zabbix_actualization_service
WORKDIR /zabbix_actualization_service
# установка необходимых пакетов
RUN apt update
RUN apt install -y python3.9
RUN apt install -y python3.9-venv
RUN apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
RUN apt install -y libpython3.9-dev
RUN apt install -y libpcre3 libpcre3-dev
RUN apt install -y unixodbc-dev
RUN apt-get install apt-transport-https
RUN apt-get update
# настройка пакетов python
RUN python3.9 -m pip install wheel
RUN python3.9 -m pip install -r requirements.txt
RUN python3.9 -m pip install uwsgi
RUN mv .env.example .env
RUN mv ubuntu_deploy/wsgi.py wsgi.py
RUN python3.9 init.py
# установка драйвера MSSQL
RUN apt install -y curl
RUN su -c 'curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -'
RUN su -c 'curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list'
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

CMD uwsgi --socket 0.0.0.0:3031 --protocol=http --enable-threads -w wsgi:app