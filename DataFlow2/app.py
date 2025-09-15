from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import (
    create_user, find_user_by_email_and_password, create_tables, get_all_users, get_all_professionals,
    create_professional, find_professional_by_email_and_password, delete_professional_by_id,
    update_professional_info, add_professional_voucher, get_professional_vouchers, get_total_vouchers_by_professional,
    create_agendamento, get_agendamentos_by_professional, get_users_for_agendamento, get_financial_summary,
    get_payment_methods_summary, create_sale, create_service_or_product, get_all_services_and_products,
    get_services_by_type,
    get_professional_sales_summary
)
import json
import bcrypt
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates')
app.secret_key = 'dataflow_secret_key'


# Inicialização do banco de dados
def setup_database():
    create_tables()
    # Criar usuário admin se não existir
    admin_email = "admin@dataflow.com"
    conn = sqlite3.connect('dataflow.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (admin_email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        create_user("Administrador", admin_email, "admin123", "", "", "", is_admin=1)
        print("Usuário administrador criado.")


@app.before_request
def check_database_initialized():
    if not hasattr(app, 'database_initialized'):
        setup_database()
        app.database_initialized = True


# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')


# Rota para a página de login
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


# Rota para a página de cadastro
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('cadastro.html')


# Rota para a página de profissional
@app.route('/profissional', methods=['GET'])
def profissional_page():
    if not session.get('logged_in') or not session.get('is_professional'):
        return redirect(url_for('login_page'))

    professional_email = session.get('user_email')
    professional = find_professional_by_email_and_password(professional_email, None, check_password=False)

    users = get_users_for_agendamento()

    return render_template('profissional.html', user_email=professional_email, users=users,
                           professional_id=professional['id'])


# Rota para a página de cliente
@app.route('/client', methods=['GET'])
def client_page():
    if not session.get('logged_in') or session.get('is_admin') or session.get('is_professional'):
        return redirect(url_for('login_page'))
    services = get_all_services_and_products()
    return render_template('client.html', user_email=session.get('user_email'), services=services)


# Rota para o painel de administrador
@app.route('/admin', methods=['GET'])
def admin_page():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    services = get_all_services_and_products()
    return render_template('admin.html', user_email=session.get('user_email'), services=services)


# Rota para autenticação de login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = find_user_by_email_and_password(email, password)
    if user:
        session['logged_in'] = True
        session['user_email'] = user['email']
        session['is_admin'] = (user['is_admin'] == 1)
        session['is_professional'] = False
        if user['is_admin'] == 1:
            return jsonify({'success': True, 'is_admin': True})
        else:
            return jsonify({'success': True, 'is_admin': False, 'is_professional': False})

    professional = find_professional_by_email_and_password(email, password)
    if professional:
        session['logged_in'] = True
        session['user_email'] = professional['email']
        session['is_admin'] = False
        session['is_professional'] = True
        return jsonify({'success': True, 'is_admin': False, 'is_professional': True})

    return jsonify({'success': False, 'message': 'E-mail ou senha incorretos'})


# Rota para cadastro de usuário
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    birth_date = data.get('birth_date')
    cpf = data.get('cpf')

    if create_user(name, email, password, phone, birth_date, cpf):
        return jsonify({'success': True, 'message': 'Cadastro realizado com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'E-mail já cadastrado.'})


# Rota para cadastro de profissional
@app.route('/register_professional', methods=['POST'])
def register_professional():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    cpf_cnpj = data.get('cpf_cnpj')
    commission_str = data.get('commission')

    try:
        commission = float(commission_str)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Comissão inválida. Por favor, insira um número.'}), 400

    if create_professional(name, email, password, phone, cpf_cnpj, commission):
        return jsonify({'success': True, 'message': 'Cadastro de profissional realizado com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'E-mail já cadastrado.'})


# Rota para excluir profissional
@app.route('/api/professionals/delete/<int:prof_id>', methods=['DELETE'])
def delete_professional(prof_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    delete_professional_by_id(prof_id)
    return jsonify({'success': True})


@app.route('/api/professionals/update/<int:prof_id>', methods=['POST'])
def update_professional(prof_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    cpf_cnpj = data.get('cpf_cnpj')
    commission_str = data.get('commission')

    try:
        commission = float(commission_str)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Comissão inválida. Por favor, insira um número.'}), 400

    if update_professional_info(prof_id, name, email, phone, cpf_cnpj, commission):
        return jsonify({'success': True, 'message': 'Profissional atualizado com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao atualizar profissional.'}), 500


@app.route('/api/professionals/voucher/<int:prof_id>', methods=['POST'])
def launch_voucher(prof_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    data = request.json
    amount_str = data.get('amount')
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify(
            {'success': False, 'message': 'Valor do vale inválido. Por favor, insira um número positivo.'}), 400

    add_professional_voucher(prof_id, amount)
    return jsonify({'success': True, 'message': 'Vale lançado com sucesso!'})


# Rota para agendamento
@app.route('/api/agendamentos/add', methods=['POST'])
def add_agendamento_api():
    if not session.get('logged_in') or not session.get('is_professional'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    data = request.json
    client_name = data.get('client_name')
    service = data.get('service')
    date = data.get('date')
    time = data.get('time')

    professional_email = session.get('user_email')
    professional = find_professional_by_email_and_password(professional_email, None, check_password=False)

    if create_agendamento(professional['id'], client_name, service, date, time):
        return jsonify({'success': True, 'message': 'Agendamento criado com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao criar agendamento.'}), 500


# Rota para adicionar uma venda
@app.route('/api/sales/add', methods=['POST'])
def add_sale_api():
    if not session.get('logged_in') or not session.get('is_professional'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    data = request.json
    client_name = data.get('client_name')
    service = data.get('service')
    amount = data.get('amount')
    payment_method = data.get('payment_method')

    professional_email = session.get('user_email')
    professional = find_professional_by_email_and_password(professional_email, None, check_password=False)

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Valor inválido. Por favor, insira um número positivo.'}), 400

    if create_sale(professional['id'], client_name, service, amount, payment_method):
        return jsonify({'success': True, 'message': 'Venda registrada com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao registrar venda.'}), 500


# Rotas da API para carregar dados
@app.route('/api/users', methods=['GET'])
def get_users_api():
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    users = get_all_users()
    return jsonify(users)


# Rota exclusiva para profissionais para buscar clientes
@app.route('/api/users_for_agendamento', methods=['GET'])
def get_users_for_agendamento_api():
    if not session.get('logged_in') or not session.get('is_professional'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    users = get_all_users()
    return jsonify(users)


@app.route('/api/professionals', methods=['GET'])
def get_professionals_api():
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    professionals = get_all_professionals()
    return jsonify(professionals)


@app.route('/api/vouchers', methods=['GET'])
def get_vouchers_api():
    if not session.get('logged_in') or not session.get('is_professional'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    professional_email = session.get('user_email')
    professional = find_professional_by_email_and_password(professional_email, None, check_password=False)

    vouchers = get_professional_vouchers(professional['id'])
    return jsonify(vouchers)


@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos_api():
    if not session.get('logged_in') or not session.get('is_professional'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    professional_email = session.get('user_email')
    professional = find_professional_by_email_and_password(professional_email, None, check_password=False)

    date_filter = request.args.get('date')
    agendamentos = get_agendamentos_by_professional(professional['id'], date_filter)

    return jsonify(agendamentos)


@app.route('/api/financial_summary', methods=['GET'])
def get_financial_summary_api():
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    summary = get_financial_summary()
    return jsonify(summary)


@app.route('/api/payment_summary', methods=['GET'])
def get_payment_summary_api():
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    summary = get_payment_methods_summary()
    return jsonify(summary)


@app.route('/api/services', methods=['GET'])
def get_services_api():
    services = get_all_services_and_products()
    return jsonify(services)


# Rota para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


if __name__ == '__main__':
    app.run(debug=True)
