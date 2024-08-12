import pymysql

# Configurações do banco de dados
host = "192.99.228.141"  # Endereço do servidor MySQL
user = "jose"  # Nome de usuário para acessar o banco de dados
password = "123456"  # Senha para acessar o banco de dados
database = "cadastro_cartao"  # Nome do banco de dados a ser criado/utilizado

# Conecta ao servidor MySQL
connection = pymysql.connect(host=host, user=user, password=password)

try:
    with connection.cursor() as cursor:
        # Cria o banco de dados se ele não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")

        # Seleciona o banco de dados
        cursor.execute(f"USE {database};")

        # Cria a tabela 'usuario' se ela não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                nome_mae VARCHAR(100) NOT NULL,
                dn DATE NOT NULL,
                rg VARCHAR(20) NOT NULL,
                cpf VARCHAR(14) UNIQUE NOT NULL,
                foto VARCHAR(255) NULL,
                datacadastro DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # Confirma as mudanças no banco de dados
    connection.commit()
    print(f"Banco de dados '{database}' e tabela 'usuario' criados com sucesso!")

finally:
    # Fecha a conexão com o banco de dados
    connection.close()
