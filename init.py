from models.local_db import create_db, add_user
from werkzeug.security import generate_password_hash

# создание БД и учетной записи администратора
create_db()
admin_password = generate_password_hash('admin')
add_user(login='admin', password=admin_password, auth_type='Local')
