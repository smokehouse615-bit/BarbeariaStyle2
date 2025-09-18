import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessário para usar o flash


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    # Cria a tabela de usuários
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS usuarios
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     nome
                     TEXT
                     NOT
                     NULL,
                     email
                     TEXT
                     UNIQUE
                     NOT
                     NULL,
                     senha
                     TEXT
                     NOT
                     NULL
                 )
                 ''')
    # Cria a tabela de agendamentos
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS agendamentos
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     cliente_nome
                     TEXT
                     NOT
                     NULL,
                     profissional
                     TEXT
                     NOT
                     NULL,
                     servico
                     TEXT
                     NOT
                     NULL,
                     data
                     TEXT
                     NOT
                     NULL,
                     horario
                     TEXT
                     NOT
                     NULL
                 )
                 ''')
    # Cria a tabela de serviços
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS servicos
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     nome
                     TEXT
                     NOT
                     NULL,
                     descricao
                     TEXT,
                     preco
                     REAL
                 )
                 ''')
    # Cria a tabela de profissionais
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS profissionais
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     nome
                     TEXT
                     NOT
                     NULL,
                     email
                     TEXT
                     UNIQUE
                     NOT
                     NULL,
                     telefone
                     TEXT,
                     comissao
                     REAL,
                     cpf_cnpj
                     TEXT
                     UNIQUE
                     NOT
                     NULL
                 )
                 ''')
    # Cria a tabela de vendas para o financeiro do profissional
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS vendas
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     profissional_nome
                     TEXT
                     NOT
                     NULL,
                     valor
                     REAL
                     NOT
                     NULL,
                     forma_pagamento
                     TEXT
                     NOT
                     NULL,
                     observacao
                     TEXT,
                     data_venda
                     TEXT
                     NOT
                     NULL
                 )
                 ''')
    # Cria a tabela de configurações
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS configuracoes
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     chave
                     TEXT
                     UNIQUE
                     NOT
                     NULL,
                     valor
                     TEXT
                 )
                 ''')
    conn.commit()
    conn.close()


# Novo método para inicializar o banco de dados antes da primeira requisição
init_db()


@app.route('/')
def home():
    conn = get_db_connection()
    configuracoes = {row['chave']: row['valor'] for row in
                     conn.execute('SELECT chave, valor FROM configuracoes').fetchall()}
    servicos = conn.execute('SELECT * FROM servicos').fetchall()
    profissionais = conn.execute('SELECT * FROM profissionais').fetchall()
    conn.close()
    return render_template('index.html', configuracoes=configuracoes, servicos=servicos, profissionais=profissionais)


@app.route('/agendar_servico', methods=['POST'])
def agendar_servico():
    cliente_nome = request.form['cliente_nome']
    profissional = request.form['profissional']
    servico = request.form['servico']
    data = request.form['data']
    horario = request.form['horario']

    conn = get_db_connection()
    conn.execute('INSERT INTO agendamentos (cliente_nome, profissional, servico, data, horario) VALUES (?, ?, ?, ?, ?)',
                 (cliente_nome, profissional, servico, data, horario))
    conn.commit()
    conn.close()
    flash('Agendamento realizado com sucesso!', 'success')
    return redirect(url_for('painel_cliente', cliente_nome=cliente_nome))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Lógica de login para o administrador
        if email == 'admin@barbeariastyle.com' and senha == '12345':
            return redirect(url_for('admin'))

        # Lógica de login para usuários
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ? AND senha = ?', (email, senha)).fetchone()
        conn.close()

        if usuario:
            # Autenticação de usuário bem-sucedida, redirecionar para o painel do cliente
            return redirect(url_for('painel_cliente', cliente_nome=usuario['nome']))
        else:
            flash('Login ou senha incorretos!', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/login_profissional', methods=['GET', 'POST'])
def login_profissional():
    if request.method == 'POST':
        email = request.form['email']
        cpf_cnpj = request.form['senha']

        conn = get_db_connection()
        profissional = conn.execute('SELECT * FROM profissionais WHERE email = ? AND cpf_cnpj = ?',
                                    (email, cpf_cnpj)).fetchone()
        conn.close()

        if profissional:
            return redirect(url_for('painel_profissional', profissional_nome=profissional['nome']))
        else:
            flash('Email ou CPF/CNPJ incorretos.', 'error')
            return render_template('login_profissional.html')

    return render_template('login_profissional.html')


@app.route('/painel_cliente')
def painel_cliente():
    cliente_nome = request.args.get('cliente_nome')
    if not cliente_nome:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    agendamentos = conn.execute('SELECT * FROM agendamentos WHERE cliente_nome = ?', (cliente_nome,)).fetchall()
    servicos = conn.execute('SELECT * FROM servicos').fetchall()
    profissionais = conn.execute('SELECT nome FROM profissionais').fetchall()
    configuracoes = {row['chave']: row['valor'] for row in
                     conn.execute('SELECT chave, valor FROM configuracoes').fetchall()}
    conn.close()

    return render_template('painel_cliente.html', cliente_nome=cliente_nome, agendamentos=agendamentos,
                           servicos=servicos, profissionais=profissionais, configuracoes=configuracoes)


@app.route('/painel_cliente/cancelar_agendamento', methods=['POST'])
def painel_cliente_cancelar_agendamento():
    agendamento_id = request.form['id']
    cliente_nome = request.form['cliente_nome']

    conn = get_db_connection()
    conn.execute('DELETE FROM agendamentos WHERE id = ?', (agendamento_id,))
    conn.commit()
    conn.close()
    flash('Agendamento cancelado com sucesso!', 'success')
    return redirect(url_for('painel_cliente', cliente_nome=cliente_nome))


@app.route('/painel_profissional')
def painel_profissional():
    profissional_nome = request.args.get('profissional_nome')
    if not profissional_nome:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login_profissional'))

    conn = get_db_connection()
    profissional = conn.execute('SELECT * FROM profissionais WHERE nome = ?', (profissional_nome,)).fetchone()
    agendamentos_do_profissional = conn.execute('SELECT * FROM agendamentos WHERE profissional = ?',
                                                (profissional_nome,)).fetchall()
    conn.close()

    return render_template('painel_profissional.html', profissional=profissional,
                           agendamentos=agendamentos_do_profissional)


@app.route('/painel_profissional/adicionar_agendamento', methods=['POST'])
def painel_profissional_adicionar_agendamento():
    cliente_nome = request.form['cliente_nome']
    profissional_nome = request.form['profissional_nome']
    data = request.form['data']
    horario = request.form['horario']

    conn = get_db_connection()
    conn.execute('INSERT INTO agendamentos (cliente_nome, profissional, servico, data, horario) VALUES (?, ?, ?, ?, ?)',
                 (cliente_nome, profissional_nome, data, horario))
    conn.commit()
    conn.close()
    flash('Agendamento adicionado com sucesso!')
    return redirect(url_for('painel_profissional', profissional_nome=profissional_nome))


@app.route('/painel_profissional/excluir_agendamento', methods=['POST'])
def painel_profissional_excluir_agendamento():
    agendamento_id = request.form['id']
    profissional_nome = request.form['profissional_nome']
    conn = get_db_connection()
    conn.execute('DELETE FROM agendamentos WHERE id = ?', (agendamento_id,))
    conn.commit()
    conn.close()
    flash('Agendamento excluído com sucesso!')
    return redirect(url_for('painel_profissional', profissional_nome=profissional_nome))


@app.route('/painel_profissional/financeiro')
def painel_profissional_financeiro():
    profissional_nome = request.args.get('profissional_nome')
    if not profissional_nome:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login_profissional'))

    conn = get_db_connection()

    # Busca a comissão do profissional
    profissional = conn.execute('SELECT comissao FROM profissionais WHERE nome = ?', (profissional_nome,)).fetchone()
    comissao = profissional['comissao'] if profissional and profissional['comissao'] else 0

    # Lógica para calcular o faturamento em tempo real, já com a comissão aplicada
    faturamento_dia = \
    conn.execute("SELECT SUM(valor) FROM vendas WHERE profissional_nome = ? AND data_venda = date('now')",
                 (profissional_nome,)).fetchone()[0] or 0
    faturamento_semana = \
    conn.execute("SELECT SUM(valor) FROM vendas WHERE profissional_nome = ? AND data_venda >= date('now', '-7 days')",
                 (profissional_nome,)).fetchone()[0] or 0
    faturamento_mes = conn.execute(
        "SELECT SUM(valor) FROM vendas WHERE profissional_nome = ? AND strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')",
        (profissional_nome,)).fetchone()[0] or 0

    conn.close()

    faturamento_data = {
        'dia': faturamento_dia * (comissao / 100),
        'semana': faturamento_semana * (comissao / 100),
        'mes': faturamento_mes * (comissao / 100)
    }

    return render_template('painel_profissional_financeiro.html', profissional_nome=profissional_nome,
                           faturamento=faturamento_data)


@app.route('/painel_profissional/<profissional_nome>/adicionar_venda', methods=['POST'])
def painel_profissional_adicionar_venda(profissional_nome):
    valor_venda = request.form['valor_venda']
    forma_pagamento = request.form['forma_pagamento']
    observacao = request.form['observacao']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO vendas (profissional_nome, valor, forma_pagamento, observacao, data_venda) VALUES (?, ?, ?, ?, date("now"))',
        (profissional_nome, valor_venda, forma_pagamento, observacao))
    conn.commit()
    conn.close()
    flash('Venda adicionada com sucesso!')
    return redirect(url_for('painel_profissional_financeiro', profissional_nome=profissional_nome))


@app.route('/api/check_availability')
def check_availability():
    profissional = request.args.get('profissional')
    data = request.args.get('data')
    horario = request.args.get('horario')

    if not profissional or not data or not horario:
        return jsonify({'available': False, 'message': 'Informações incompletas.'})

    conn = get_db_connection()
    agendamento = conn.execute('SELECT * FROM agendamentos WHERE profissional = ? AND data = ? AND horario = ?',
                               (profissional, data, horario)).fetchone()
    conn.close()

    if agendamento:
        return jsonify({'available': False, 'message': 'Horário já agendado.'})
    else:
        return jsonify({'available': True, 'message': 'Horário disponível.'})


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
            conn.commit()
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('O email já está cadastrado.', 'error')
            return render_template('cadastro.html', error='O email já está cadastrado.')
        finally:
            conn.close()

    return render_template('cadastro.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


# Rotas para Gerenciar Usuários
@app.route('/usuarios')
def gerenciar_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)


@app.route('/adicionar_usuario', methods=['GET', 'POST'])
def adicionar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
        conn.commit()
        conn.close()
        flash('Usuário adicionado com sucesso!')
        return redirect(url_for('gerenciar_usuarios'))
    return render_template('adicionar_usuario.html')


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    conn = get_db_connection()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        conn.execute('UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?', (nome, email, senha, id))
        conn.commit()
        flash('Usuário atualizado com sucesso!')
        conn.close()
        return redirect(url_for('gerenciar_usuarios'))

    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('editar_usuario.html', usuario=usuario)


@app.route('/excluir_usuario/<int:id>')
def excluir_usuario(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído com sucesso!')
    return redirect(url_for('gerenciar_usuarios'))


# Rotas para Gerenciar Agendamentos
@app.route('/agendamentos', methods=['GET', 'POST'])
def gerenciar_agendamentos():
    conn = get_db_connection()
    agendamento_editar = None
    if request.method == 'POST':
        if 'adicionar' in request.form:
            cliente_nome = request.form['cliente_nome']
            profissional = request.form['profissional']
            servico = request.form['servico']
            data = request.form['data']
            horario = request.form['horario']
            conn.execute(
                'INSERT INTO agendamentos (cliente_nome, profissional, servico, data, horario) VALUES (?, ?, ?, ?, ?)',
                (cliente_nome, profissional, servico, data, horario))
            conn.commit()
            flash('Agendamento adicionado com sucesso!')
        elif 'editar' in request.form:
            agendamento_id = request.form['id']
            cliente_nome = request.form['cliente_nome']
            profissional = request.form['profissional']
            servico = request.form['servico']
            data = request.form['data']
            horario = request.form['horario']
            conn.execute(
                'UPDATE agendamentos SET cliente_nome = ?, profissional = ?, servico = ?, data = ?, horario = ? WHERE id = ?',
                (cliente_nome, profissional, servico, data, horario, agendamento_id))
            conn.commit()
            flash('Agendamento atualizado com sucesso!')
        elif 'excluir' in request.form:
            agendamento_id = request.form['id']
            conn.execute('DELETE FROM agendamentos WHERE id = ?', (agendamento_id,))
            conn.commit()
            flash('Agendamento excluído com sucesso!')

    if 'editar_id' in request.args:
        agendamento_editar = conn.execute('SELECT * FROM agendamentos WHERE id = ?',
                                          (request.args.get('editar_id'),)).fetchone()

    profissionais = conn.execute('SELECT nome FROM profissionais').fetchall()
    servicos = conn.execute('SELECT nome FROM servicos').fetchall()
    agendamentos = conn.execute('SELECT * FROM agendamentos').fetchall()
    conn.close()
    return render_template('gerenciar_agendamentos.html', agendamentos=agendamentos, profissionais=profissionais,
                           servicos=servicos, agendamento_editar=agendamento_editar)


# Rotas para Gerenciar Serviços
@app.route('/servicos', methods=['GET', 'POST'])
def gerenciar_servicos():
    conn = get_db_connection()
    servico_editar = None
    if request.method == 'POST':
        # Lógica para adicionar ou editar serviço
        if 'adicionar_servico' in request.form:
            nome = request.form['nome']
            descricao = request.form['descricao']
            preco = request.form['preco']
            conn.execute('INSERT INTO servicos (nome, descricao, preco) VALUES (?, ?, ?)', (nome, descricao, preco))
            conn.commit()
            flash('Serviço adicionado com sucesso!')
            return redirect(url_for('gerenciar_servicos'))
        elif 'editar_servico' in request.form:
            servico_id = request.form['id']
            nome = request.form['nome']
            descricao = request.form['descricao']
            preco = request.form['preco']
            conn.execute('UPDATE servicos SET nome = ?, descricao = ?, preco = ? WHERE id = ?',
                         (nome, descricao, preco, servico_id))
            conn.commit()
            flash('Serviço atualizado com sucesso!')
            return redirect(url_for('gerenciar_servicos'))
        elif 'excluir_servico' in request.form:
            servico_id = request.form['id']
            conn.execute('DELETE FROM servicos WHERE id = ?', (servico_id,))
            conn.commit()
            flash('Serviço excluído com sucesso!')
            return redirect(url_for('gerenciar_servicos'))

    if 'editar_id' in request.args:
        servico_editar = conn.execute('SELECT * FROM servicos WHERE id = ?',
                                      (request.args.get('editar_id'),)).fetchone()

    servicos = conn.execute('SELECT * FROM servicos').fetchall()
    conn.close()
    return render_template('gerenciar_servicos.html', servicos=servicos, servico_editar=servico_editar)


# Rotas para Gerenciar Profissionais
@app.route('/profissionais', methods=['GET', 'POST'])
def gerenciar_profissionais():
    conn = get_db_connection()
    profissional_editar = None
    if request.method == 'POST':
        if 'adicionar' in request.form:
            nome = request.form['nome']
            email = request.form['email']
            telefone = request.form['telefone']
            comissao = request.form['comissao']
            cpf_cnpj = request.form['cpf_cnpj']
            try:
                conn.execute(
                    'INSERT INTO profissionais (nome, email, telefone, comissao, cpf_cnpj) VALUES (?, ?, ?, ?, ?)',
                    (nome, email, telefone, comissao, cpf_cnpj))
                conn.commit()
                flash('Profissional adicionado com sucesso!')
            except sqlite3.IntegrityError:
                flash('Este email já está cadastrado para outro profissional.', 'error')
        elif 'editar' in request.form:
            profissional_id = request.form['id']
            nome = request.form['nome']
            email = request.form['email']
            telefone = request.form['telefone']
            comissao = request.form['comissao']
            cpf_cnpj = request.form['cpf_cnpj']
            conn.execute(
                'UPDATE profissionais SET nome = ?, email = ?, telefone = ?, comissao = ?, cpf_cnpj = ? WHERE id = ?',
                (nome, email, telefone, comissao, cpf_cnpj, profissional_id))
            conn.commit()
            flash('Profissional atualizado com sucesso!')
        elif 'excluir' in request.form:
            profissional_id = request.form['id']
            conn.execute('DELETE FROM profissionais WHERE id = ?', (profissional_id,))
            conn.commit()
            flash('Profissional excluído com sucesso!')

    if 'editar_id' in request.args:
        profissional_editar = conn.execute('SELECT * FROM profissionais WHERE id = ?',
                                           (request.args.get('editar_id'),)).fetchone()

    profissionais = conn.execute('SELECT * FROM profissionais').fetchall()
    conn.close()
    return render_template('gerenciar_profissionais.html', profissionais=profissionais,
                           profissional_editar=profissional_editar)


@app.route('/relatorios')
def relatorios():
    conn = get_db_connection()

    # Lógica para calcular o faturamento geral em tempo real
    faturamento_dia = conn.execute("SELECT SUM(valor) FROM vendas WHERE data_venda = date('now')").fetchone()[0] or 0
    faturamento_semana = \
    conn.execute("SELECT SUM(valor) FROM vendas WHERE data_venda >= date('now', '-7 days')").fetchone()[0] or 0
    faturamento_mes = conn.execute(
        "SELECT SUM(valor) FROM vendas WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')").fetchone()[
                          0] or 0

    faturamento_data = {
        'dia': faturamento_dia,
        'semana': faturamento_semana,
        'mes': faturamento_mes
    }

    # Lógica para calcular o faturamento por forma de pagamento
    pagamentos_data = {
        'dinheiro': conn.execute(
            "SELECT SUM(valor) FROM vendas WHERE forma_pagamento = 'dinheiro' AND data_venda = date('now')").fetchone()[
                        0] or 0,
        'pix': conn.execute(
            "SELECT SUM(valor) FROM vendas WHERE forma_pagamento = 'pix' AND data_venda = date('now')").fetchone()[
                   0] or 0,
        'debito': conn.execute(
            "SELECT SUM(valor) FROM vendas WHERE forma_pagamento = 'debito' AND data_venda = date('now')").fetchone()[
                      0] or 0,
        'credito': conn.execute(
            "SELECT SUM(valor) FROM vendas WHERE forma_pagamento = 'credito' AND data_venda = date('now')").fetchone()[
                       0] or 0,
    }

    conn.close()

    return render_template('relatorios.html', faturamento=faturamento_data, pagamentos=pagamentos_data)


@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    conn = get_db_connection()
    if request.method == 'POST':
        # Exclui todas as configurações antigas para inserir as novas
        conn.execute('DELETE FROM configuracoes')

        # Salva o horário e dias de funcionamento
        dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado',
                       'Domingo']
        for dia in dias_semana:
            abertura = request.form.get(f'abertura_{dia}')
            fechamento = request.form.get(f'fechamento_{dia}')
            if abertura and fechamento:
                conn.execute('INSERT INTO configuracoes (chave, valor) VALUES (?, ?)',
                             (f'horario_{dia}', f'{abertura}-{fechamento}'))

        # Salva as informações de contato
        conn.execute('INSERT INTO configuracoes (chave, valor) VALUES (?, ?)',
                     ('telefone', request.form.get('telefone', '')))
        conn.execute('INSERT INTO configuracoes (chave, valor) VALUES (?, ?)',
                     ('email_contato', request.form.get('email_contato', '')))
        conn.execute('INSERT INTO configuracoes (chave, valor) VALUES (?, ?)',
                     ('instagram', request.form.get('instagram', '')))
        conn.execute('INSERT INTO configuracoes (chave, valor) VALUES (?, ?)',
                     ('whatsapp', request.form.get('whatsapp', '')))

        conn.commit()
        flash('Configurações salvas com sucesso!')
        return redirect(url_for('configuracoes'))

    configuracoes_db = conn.execute('SELECT chave, valor FROM configuracoes').fetchall()
    configuracoes = {row['chave']: row['valor'] for row in configuracoes_db}
    conn.close()
    return render_template('configuracoes.html', configuracoes=configuracoes)


if __name__ == '__main__':
    app.run(debug=True)
