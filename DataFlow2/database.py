import sqlite3
import bcrypt
from datetime import datetime, timedelta

DATABASE_NAME = 'dataflow.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password
                       TEXT
                       NOT
                       NULL,
                       phone
                       TEXT,
                       birth_date
                       TEXT,
                       cpf
                       TEXT,
                       is_admin
                       INTEGER
                       NOT
                       NULL
                       DEFAULT
                       0
                   )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS professionals
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password
                       TEXT
                       NOT
                       NULL,
                       phone
                       TEXT,
                       cpf_cnpj
                       TEXT,
                       commission
                       REAL
                   )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS vouchers
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       professional_id
                       INTEGER
                       NOT
                       NULL,
                       amount
                       REAL
                       NOT
                       NULL,
                       date_launched
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       professional_id
                   ) REFERENCES professionals
                   (
                       id
                   )
                       )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS agendamentos
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       professional_id
                       INTEGER
                       NOT
                       NULL,
                       client_name
                       TEXT
                       NOT
                       NULL,
                       service
                       TEXT
                       NOT
                       NULL,
                       date
                       TEXT
                       NOT
                       NULL,
                       time
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       professional_id
                   ) REFERENCES professionals
                   (
                       id
                   )
                       )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS sales
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       professional_id
                       INTEGER
                       NOT
                       NULL,
                       client_name
                       TEXT
                       NOT
                       NULL,
                       service
                       TEXT
                       NOT
                       NULL,
                       amount
                       REAL
                       NOT
                       NULL,
                       payment_method
                       TEXT
                       NOT
                       NULL,
                       date_of_sale
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       professional_id
                   ) REFERENCES professionals
                   (
                       id
                   )
                       )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS services_and_products
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       price
                       REAL
                       NOT
                       NULL,
                       is_product
                       INTEGER
                       NOT
                       NULL
                       DEFAULT
                       0
                   )
                   ''')
    conn.commit()
    conn.close()


def create_user(name, email, password, phone, birth_date, cpf, is_admin=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (name, email, password, phone, birth_date, cpf, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, email, hashed_password.decode('utf-8'), phone, birth_date, cpf, is_admin)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def find_user_by_email_and_password(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user
    return None


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, cpf FROM users WHERE is_admin = 0")
    users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in users]


def create_professional(name, email, password, phone, cpf_cnpj, commission):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO professionals (name, email, password, phone, cpf_cnpj, commission) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, hashed_password.decode('utf-8'), phone, cpf_cnpj, commission)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def find_professional_by_email_and_password(email, password=None, check_password=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professionals WHERE email = ?", (email,))
    professional = cursor.fetchone()
    conn.close()
    if professional and (
            not check_password or bcrypt.checkpw(password.encode('utf-8'), professional['password'].encode('utf-8'))):
        return professional
    return None


def get_all_professionals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, commission, phone, cpf_cnpj FROM professionals")
    professionals = cursor.fetchall()
    conn.close()
    return [dict(prof) for prof in professionals]


def get_professional_by_id(prof_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professionals WHERE id = ?", (prof_id,))
    prof = cursor.fetchone()
    conn.close()
    return dict(prof) if prof else None


def update_professional_info(prof_id, name, email, phone, cpf_cnpj, commission):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE professionals SET name = ?, email = ?, phone = ?, cpf_cnpj = ?, commission = ? WHERE id = ?",
            (name, email, phone, cpf_cnpj, commission, prof_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def delete_professional_by_id(prof_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM professionals WHERE id = ?", (prof_id,))
    conn.commit()
    conn.close()


def add_professional_voucher(prof_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vouchers (professional_id, amount, date_launched) VALUES (?, ?, DATE('now'))",
        (prof_id, amount)
    )
    conn.commit()
    conn.close()


def get_professional_vouchers(prof_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vouchers WHERE professional_id = ?", (prof_id,))
    vouchers = cursor.fetchall()
    conn.close()
    return [dict(voucher) for voucher in vouchers]


def get_total_vouchers_by_professional(prof_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) as total FROM vouchers WHERE professional_id = ?", (prof_id,))
    total = cursor.fetchone()['total']
    conn.close()
    return total if total else 0


def get_professional_vouchers_realtime(prof_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vouchers WHERE professional_id = ?", (prof_id,))
    vouchers = cursor.fetchall()
    total_amount = sum(v['amount'] for v in vouchers)
    conn.close()
    return {'vouchers': [dict(v) for v in vouchers], 'total_amount': total_amount}


def create_agendamento(professional_id, client_name, service, date, time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO agendamentos (professional_id, client_name, service, date, time) VALUES (?, ?, ?, ?, ?)",
        (professional_id, client_name, service, date, time)
    )
    conn.commit()
    conn.close()
    return True


def get_agendamentos_by_professional(professional_id, date_filter):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agendamentos WHERE professional_id = ? AND date = ?", (professional_id, date_filter))
    agendamentos = cursor.fetchall()
    conn.close()
    return [dict(agendamento) for agendamento in agendamentos]


def get_users_for_agendamento():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, cpf FROM users WHERE is_admin = 0")
    users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in users]


def create_sale(professional_id, client_name, service, amount, payment_method):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO sales (professional_id, client_name, service, amount, payment_method, date_of_sale) VALUES (?, ?, ?, ?, ?, ?)",
            (professional_id, client_name, service, amount, payment_method, datetime.now().strftime('%Y-%m-%d'))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_all_sales():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales")
    sales = cursor.fetchall()
    conn.close()
    return [dict(sale) for sale in sales]


def get_financial_summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    start_of_week = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
    start_of_month = datetime.now().strftime('%Y-%m-01')

    # Faturamento por período
    cursor.execute("SELECT SUM(amount) FROM sales")
    total_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM sales WHERE date_of_sale = ?", (today,))
    daily_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM sales WHERE date_of_sale >= ?", (start_of_week,))
    weekly_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM sales WHERE date_of_sale >= ?", (start_of_month,))
    monthly_revenue = cursor.fetchone()[0] or 0

    # Vales lançados
    cursor.execute("SELECT SUM(amount) FROM vouchers")
    total_vouchers = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_revenue': total_revenue,
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_vouchers': total_vouchers,
        'net_revenue': total_revenue - total_vouchers
    }


def get_payment_methods_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT payment_method, SUM(amount) as total FROM sales GROUP BY payment_method")
    summary = cursor.fetchall()
    conn.close()
    return {item['payment_method']: item['total'] for item in summary}


def create_service_or_product(name, price, is_product):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO services_and_products (name, price, is_product) VALUES (?, ?, ?)",
            (name, price, is_product)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_all_services_and_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services_and_products")
    services = cursor.fetchall()
    conn.close()
    return [dict(service) for service in services]


def get_services_by_type(is_product):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services_and_products WHERE is_product = ?", (is_product,))
    services = cursor.fetchall()
    conn.close()
    return [dict(service) for service in services]
