import os
import uuid
import card  # Importa o módulo que cria cartões personalizados
import imprimicard  # Importa o módulo que imprime cartões
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename

# Define o número de itens por página para a paginação
ITENS_POR_PAGINA = 10

# Cria a aplicação Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Define uma chave secreta para sessões

# Configuração do banco de dados SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://jose:123456@192.99.228.141/cadastro_cartao"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuração de upload de imagens
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'fotos')  # Caminho para salvar as fotos dos usuários
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Extensões de arquivo permitidas para upload
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)  # Inicializa o SQLAlchemy para interação com o banco de dados
migrate = Migrate(app, db)  # Inicializa o Flask-Migrate para migrações do banco de dados

# Função para verificar a extensão do arquivo
def allowed_file(filename):
    """
    Verifica se a extensão do arquivo é permitida.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define o modelo de dados para a tabela 'usuario'
class Usuario(db.Model):
    """
    Modelo de dados para representar um usuário no banco de dados.
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nome_mae = db.Column(db.String(100), nullable=False)
    dn = db.Column(db.Date, nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    foto = db.Column(db.String(255), nullable=True)  # Nome do arquivo da foto do usuário
    datacadastro = db.Column(db.DateTime, default=datetime.utcnow)

# Cria a pasta de uploads se ela não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rota principal que redireciona para o dashboard
@app.route('/')
def index():
    """
    Rota raiz que redireciona para o dashboard.
    """
    return redirect(url_for('dashboard'))

# Rota do dashboard
@app.route('/dashboard')
def dashboard():
    """
    Rota do dashboard que exibe informações gerais sobre os cadastros.
    """
    total_cadastros = Usuario.query.count()  # Conta o total de cadastros
    cadastros_hoje = Usuario.query.filter(db.func.date(Usuario.datacadastro) == datetime.today().date()).count()  # Cadastros do dia
    cadastros_mes = Usuario.query.filter(db.func.month(Usuario.datacadastro) == datetime.today().month,
                                         db.func.year(Usuario.datacadastro) == datetime.today().year).count()  # Cadastros do mês
    cadastros_ano = Usuario.query.filter(db.func.year(Usuario.datacadastro) == datetime.today().year).count()  # Cadastros do ano

    # Consulta para obter dados para o gráfico (data e quantidade de cadastros)
    dados_grafico = db.session.query(db.func.date(Usuario.datacadastro), db.func.count(Usuario.id)).group_by(
        db.func.date(Usuario.datacadastro)).all()
    labels = [str(dado[0]) for dado in dados_grafico]
    data = [dado[1] for dado in dados_grafico]

    return render_template('dashboard.html', total_cadastros=total_cadastros, cadastros_hoje=cadastros_hoje,
                           cadastros_mes=cadastros_mes, cadastros_ano=cadastros_ano, labels=labels, data=data)

# Rota para cadastrar um novo usuário
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """
    Rota para cadastro de novos usuários. 
    Se o método for POST, processa o formulário de cadastro.
    """
    if request.method == 'POST':
        cpf = request.form['cpf']
        # Verifica se o CPF já está cadastrado
        usuario_existente = Usuario.query.filter_by(cpf=cpf).first()

        if usuario_existente:
            flash('CPF já cadastrado. Redirecionando para atualização.', 'warning')
            return redirect(url_for('atualizar_usuario', id=usuario_existente.id))

        # Processa o upload da foto
        if 'foto-aluno' in request.files:
            foto = request.files['foto-aluno']
            if foto and allowed_file(foto.filename):
                # Gera um nome único para o arquivo usando uuid
                filename = str(uuid.uuid4()) + '_' + secure_filename(foto.filename)
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(foto_path)

                # Salva apenas o nome do arquivo no banco de dados
                foto_db = filename
            else:
                foto_db = None  # Define como None se não houver foto ou se o formato for inválido
        else:
            foto_db = None

        # Cria um novo usuário com os dados do formulário
        novo_usuario = Usuario(
            nome=request.form['nome'],
            nome_mae=request.form['nome_mae'],
            dn=datetime.strptime(request.form['dn'], '%Y-%m-%d').date(),
            rg=request.form['rg'],
            cpf=cpf,
            foto=foto_db  # Salva o nome do arquivo da foto no banco de dados
        )

        # Adiciona o novo usuário ao banco de dados
        db.session.add(novo_usuario)
        db.session.commit()

        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('usuarios_view'))

    return render_template('cadastro.html')

# Rota para visualizar a lista de usuários
@app.route('/usuarios', methods=['GET'])
def usuarios_view():
    """
    Rota que exibe a lista de usuários cadastrados com paginação.
    Permite pesquisa por nome, nome da mãe ou CPF.
    """
    page = request.args.get(get_page_parameter(), type=int, default=1)
    query = request.args.get('q', '').lower()

    # Consulta inicial
    usuarios_query = Usuario.query

    # Aplica filtro de pesquisa se houver
    if query:
        usuarios_query = usuarios_query.filter(
            db.or_(
                db.func.lower(Usuario.nome).like(f'%{query}%'),
                db.func.lower(Usuario.nome_mae).like(f'%{query}%'),
                Usuario.cpf.like(f'%{query}%')
            )
        )

    # Paginação
    usuarios_paginados = usuarios_query.paginate(page=page, per_page=ITENS_POR_PAGINA, error_out=False)

    return render_template('usuarios.html', usuarios=usuarios_paginados)

# Rota para atualizar um usuário existente
@app.route('/atualizar/<int:id>', methods=['GET', 'POST'])
def atualizar_usuario(id):
    """
    Rota para atualizar os dados de um usuário existente.
    """
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        # Atualiza os dados do usuário com base no formulário
        usuario.nome = request.form['nome']
        usuario.nome_mae = request.form['nome_mae']
        usuario.dn = datetime.strptime(request.form['dn'], '%Y-%m-%d').date()
        usuario.rg = request.form['rg']
        usuario.cpf = request.form['cpf']

        # Processa o upload da foto se uma nova for enviada
        if 'foto-aluno' in request.files:
            foto = request.files['foto-aluno']
            if foto and allowed_file(foto.filename):
                # Remove a foto antiga se existir
                if usuario.foto:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], usuario.foto))
                    except FileNotFoundError:
                        pass  # Ignora se a foto não for encontrada
                # Gera um nome único para o arquivo usando uuid
                filename = str(uuid.uuid4()) + '_' + secure_filename(foto.filename)
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(foto_path)

                # Salva apenas o nome do arquivo no banco de dados
                usuario.foto = filename

        db.session.commit()
        flash('Dados do usuário atualizados com sucesso!', 'success')
        return redirect(url_for('usuarios_view'))

    return render_template('atualizar_usuario.html', usuario=usuario)

# Rota para remover um usuário
@app.route('/remover/<int:id>', methods=['POST'])
def remover_usuario(id):
    """
    Rota para remover um usuário do banco de dados.
    """
    usuario = Usuario.query.get_or_404(id)

    # Remove a foto do usuário antes de remover o usuário do banco de dados
    if usuario.foto:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], usuario.foto))
        except FileNotFoundError:
            pass  # Ignora se a foto não for encontrada

    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário removido com sucesso!', 'success')
    return redirect(url_for('usuarios_view'))

@app.route('/imprimir_cartao/<int:id>', methods=['GET'])
def imprimir_cartao(id):
    """
    Rota que gera e imprime o cartão de um usuário específico.
    """
    try:
        # Tenta criar o cartão
        card.create_card(id)
        
        # Tenta imprimir o cartão
        imprimicard.print_card(id, "cartao")  # Substitua pelo nome da sua impressora

        # Se tudo correr bem, exibe uma mensagem de sucesso
        flash('Cartão impresso com sucesso!', 'success')
    except Exception as e:
        # Se ocorrer um erro, exibe uma mensagem de erro
        flash(f'Erro ao imprimir o cartão: {str(e)}', 'danger')
    
    # Redireciona de volta para a página de usuários
    return redirect(url_for('usuarios_view'))

# Inicia a aplicação se o script for executado diretamente
if __name__ == '__main__':
    app.run(debug=True)
