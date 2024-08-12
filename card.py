from PIL import Image, ImageDraw, ImageFont
import qrcode
import pymysql
import os
import sys
import imprimicard  # Importa o módulo que contém a lógica de impressão dos cartões

# Configurações do banco de dados
host = "192.99.228.141"
user = "jose"
password = "123456"
database = "cadastro_cartao"

def fetch_user_data(user_id):
    """
    Busca os dados do usuário no banco de dados com base no ID fornecido.
    Retorna um dicionário com os dados do usuário ou None se o usuário não for encontrado.
    """
    connection = pymysql.connect(host=host, user=user, password=password, database=database)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT nome, nome_mae, dn, rg, cpf, foto FROM usuario WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return {
                    'nome': user_data[0],
                    'nome_mae': user_data[1],
                    'dn': user_data[2],
                    'rg': user_data[3],
                    'cpf': user_data[4],
                    'foto': user_data[5]
                }
            else:
                print(f"Usuário com id {user_id} não encontrado.")
                return None
    finally:
        connection.close()

def draw_text(draw, position, text, font, color, max_chars=None):
    """
    Desenha texto na imagem, quebrando linhas se necessário.
    """
    if max_chars and len(text) > max_chars:
        break_index = text[:max_chars+1].rfind(' ')
        if break_index == -1:
            break_index = max_chars
        first_part = text[:break_index].rstrip()
        second_part = text[break_index:].lstrip()
        draw.text(position, first_part, fill=color, font=font)
        bbox = draw.textbbox(position, first_part, font=font)
        second_line_position = (position[0], bbox[3] + 5)
        draw.text(second_line_position, second_part, fill=color, font=font)
    else:
        draw.text(position, text, fill=color, font=font)

def calculate_break_index(text, font, max_width, draw):  
    """
    Calcula o índice para quebra de linha com base na largura máxima permitida.
    """
    words = text.split()
    current_width = 0
    break_index = 0

    for i, word in enumerate(words):
        word_width = draw.textlength(word + " ", font=font)
        current_width += word_width

        if current_width > max_width:
            break_index = len(" ".join(words[:i]))
            break

    return break_index

def abbreviate_name(Nome):
    """
    Abrevia um nome longo, mantendo o último sobrenome completo e abreviando os demais.
    """
    parts = Nome.split()
    short_words = ["de", "da", "do", "dos", "e", "a"]

    if len(parts) > 2:
        abbreviated_parts = [parts[0]]
        for i in range(1, len(parts) - 1):
            if parts[i].lower() not in short_words:
                abbreviated_parts.append(parts[i][0] + ".")
            else:
                abbreviated_parts.append(parts[i])
        abbreviated_parts.append(parts[-1])
        return " ".join(abbreviated_parts)
    else:
        return Nome

def add_circular_image(draw, base_img, photo_filename, position, circle_width, circle_height):
    """
    Adiciona uma imagem circular à base da imagem, utilizando uma máscara circular.
    """
    photo_path = os.path.join('static', 'uploads', 'fotos', photo_filename)
    if not os.path.exists(photo_path):
        print(f"Arquivo de foto {photo_path} não encontrado.")
        return

    img_to_insert = Image.open(photo_path)

    # Redimensiona a imagem para o tamanho exato de 322x321 pixels
    img_to_insert = img_to_insert.resize((circle_width, circle_height))

    # Cria uma máscara circular com base nas novas dimensões
    mask = Image.new('L', (circle_width, circle_height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, circle_width, circle_height), fill=255)

    img_to_insert.putalpha(mask)

    # Coloca a imagem circular na posição desejada na base da imagem
    base_img.paste(img_to_insert, position, img_to_insert)

def fill_card(input_image_path, output_image_path, info):
    """
    Preenche as informações no template do cartão e salva a imagem final.
    """
    img = Image.open(input_image_path)
    draw = ImageDraw.Draw(img)

    font_path = "arial.ttf"
    font_sizes = {
        'Nome': 43,
        'Mãe': 43,
        'Data-nascimento': 40,
        'RG': 40,
        'CPF': 40,
        'validity': 35
    }
    
    coordinates = {
        'Nome': (559, 220),
        'Mãe': (559, 349),
        'Data-nascimento': (559, 459),
        'RG': (559, 513),
        'CPF': (559, 570)
    }
    
    color = (0, 0, 0)

    max_name_width = 450

    for key in info:
        if key == 'foto':
            continue
        font = ImageFont.truetype(font_path, font_sizes[key])
        if key == 'Nome':
            abbreviated_name = abbreviate_name(info[key])
            break_index = calculate_break_index(abbreviated_name, font, max_name_width, draw)  
            draw_text(draw, coordinates[key], abbreviated_name, font, color, break_index)  
        elif key == 'Mãe':
            mae_abbreviated = abbreviate_name(info['Mãe']) 
            break_index_mae = calculate_break_index(mae_abbreviated, font, max_name_width, draw)
            draw_text(draw, coordinates[key], mae_abbreviated, font, color, break_index_mae) 
        else:
            draw_text(draw, coordinates[key], info[key], font, color)

    # Adiciona a imagem circular ao cartão, redimensionada para 322x321 pixels
    add_circular_image(draw, img, info['foto'], position=(20, 136), circle_width=322, circle_height=321)

    img.save(output_image_path)

def generate_qr_code(data):
    """
    Gera um código QR com os dados fornecidos.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=4,
        border=5,
    )
    qr.add_data(data)
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white")

def fill_card_verso(input_image_path, output_image_path, info):
    """
    Preenche o verso do cartão com um QR code e salva a imagem final.
    """
    qr_code_data = "\n".join([f"{key}: {value}" for key, value in info.items()])
    qr_code_img = generate_qr_code(qr_code_data)
    verso_img = Image.open(input_image_path)
    qr_code_position = (529, 178)
    verso_img.paste(qr_code_img, qr_code_position)
    verso_img.save(output_image_path)

def create_card(user_id):
    """
    Função principal que cria e preenche o cartão com base no ID do usuário e, em seguida, imprime o cartão.
    """
    # Caminho das imagens de template
    front_template_path = "static/uploads/cartao/cardVazio.jpg"
    back_template_path = "static/uploads/cartao/cardSemQRcode.jpg"

    # Nome dos arquivos de saída com base no ID do usuário
    front_output_path = f"static/uploads/usuarios/{user_id}_frente.jpg"
    back_output_path = f"static/uploads/usuarios/{user_id}_verso.jpg"

    # Busca os dados do usuário
    info = fetch_user_data(user_id)
    if info is None:
        return None

    # Preenche e salva a imagem da frente do cartão
    fill_card(front_template_path, front_output_path, {
        'Nome': info['nome'],
        'Mãe': info['nome_mae'],
        'Data-nascimento': info['dn'].strftime("%d/%m/%Y"),
        'RG': info['rg'],
        'CPF': info['cpf'],
        'foto': info['foto']
    })

    # Preenche e salva a imagem do verso do cartão
    fill_card_verso(back_template_path, back_output_path, {
        'Nome': info['nome'],
        'Mãe': info['nome_mae'],
        'Data-nascimento': info['dn'].strftime("%d/%m/%Y"),
        'RG': info['rg'],
        'CPF': info['cpf']
    })

    # Chama a função de impressão, passando o ID do usuário
    printer_name = "impressora"  # Substitua pelo nome exato da sua impressora
    imprimicard.print_card(user_id, printer_name)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        create_card(user_id)
    else:
        print("Por favor, forneça um ID de usuário.")
