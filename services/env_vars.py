from sys import platform
import os
from dotenv import load_dotenv


def get_var(var_name):
    if platform == "linux" or platform == "linux2":
        project_path = str(os.path.join(os.path.dirname(__file__))[0:(os.path.join(
            os.path.dirname(__file__)).index('zabbix_actualization_service') + 29)])
        dotenv_path = project_path + '/.env'
    elif platform == "win32":
        project_path = str(os.path.join(os.path.dirname(__file__))[0:(os.path.join(
            os.path.dirname(__file__)).index('zabbix_actualization_service') + 29)])
        dotenv_path = project_path + '.env'
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    return os.environ[var_name]
