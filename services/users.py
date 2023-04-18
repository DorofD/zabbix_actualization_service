from ldap3 import Connection
from werkzeug.security import generate_password_hash, check_password_hash
from models.local_db import get_user_by_name, update_user_password
from services.env_vars import get_var


LDAP_SERVER = get_var('LDAP_SERVER')
LDAP_USER = get_var('LDAP_USER')
LDAP_USER_CN = get_var('LDAP_USER_CN')
SEARCH_USER_CATALOG = get_var('SEARCH_USER_CATALOG')


def ldap_auth(login, password):
    try:
        conn = Connection(
            LDAP_SERVER, LDAP_USER_CN, LDAP_USER, auto_bind=True)
        conn.search(SEARCH_USER_CATALOG,
                    f'(sAMAccountName={login})', attributes=['Name'])
        name = conn.entries[0]['Name']
        conn = Connection(
            LDAP_SERVER, f"CN={name},{SEARCH_USER_CATALOG}", password, auto_bind=True, raise_exceptions=True)
        return True
    except:
        return False


def signin(login, password):
    user = get_user_by_name(login)
    if user:
        if user[0][3] == 'Local':
            if check_password_hash(user[0][2], password):
                return user[0]
            else:
                return False
        elif user[0][3] == 'LDAP':
            if ldap_auth(login, password):
                return user[0]
            else:
                return False
    else:
        return False


def change_password(login, new_password):
    user = get_user_by_name(login)
    if not user:
        raise Exception(f"Пользователь {login} не найден")
    if user[0][3] == 'LDAP':
        raise Exception(
            f"{user[0][1]} - доменный пользователь, локальная смена пароля невозможна")
    password_hash = generate_password_hash(new_password)
    update_user_password(login, password_hash)


class UserLogin():
    def get_user_from_db(self, login):
        self.__user = get_user_by_name(login)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user[0])
