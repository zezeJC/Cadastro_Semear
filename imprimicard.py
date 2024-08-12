import os
import win32print
import win32ui
from PIL import Image, ImageWin

def print_card(user_id, printer_name):
    """
    Função principal para imprimir cartões de usuário.
    Baseia-se no ID do usuário para encontrar as imagens frontais e traseiras do cartão
    e enviá-las para impressão.
    """

    # Define os caminhos das imagens com base no ID do usuário
    front_image_path = f"static/uploads/usuarios/{user_id}_frente.jpg"
    back_image_path = f"static/uploads/usuarios/{user_id}_verso.jpg"

    # Verifica se as imagens existem antes de prosseguir
    if not os.path.exists(front_image_path):
        print(f"Erro: Imagem da frente para o usuário ID {user_id} não encontrada.")
        return

    if not os.path.exists(back_image_path):
        print(f"Erro: Imagem do verso para o usuário ID {user_id} não encontrada.")
        return

    try:
        # Tenta abrir a impressora especificada
        hprinter = win32print.OpenPrinter(printer_name)
    except Exception as e:
        print(f"Erro ao tentar abrir a impressora '{printer_name}': {e}")
        return
    
    try:
        # Tenta iniciar o documento de impressão
        hjob = win32print.StartDocPrinter(hprinter, 1, ("Impressão de Cartão", None, "RAW"))
    except Exception as e:
        print(f"Erro ao iniciar o documento de impressão: {e}")
        win32print.ClosePrinter(hprinter)
        return
    
    try:
        # Inicia a página de impressão
        win32print.StartPagePrinter(hprinter)

        # Preparar para impressão da frente do cartão
        try:
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)  # Cria um contexto de dispositivo para a impressora
            hdc.StartDoc("Card Print")  # Inicia o documento de impressão
            hdc.StartPage()  # Inicia a página de impressão

            # Imprimir a frente
            img_front = Image.open(front_image_path)  # Abre a imagem da frente do cartão
            img_front = img_front.convert("RGB")  # Converte a imagem para RGB
            dib_front = ImageWin.Dib(img_front)  # Cria uma representação da imagem para a impressão
            dib_front.draw(hdc.GetHandleOutput(), (0, 0, img_front.size[0], img_front.size[1]))  # Desenha a imagem na página

            hdc.EndPage()  # Finaliza a página
        except Exception as e:
            print(f"Erro ao imprimir a frente do cartão: {e}")
            return

        # Preparar para impressão do verso do cartão
        try:
            hdc.StartPage()  # Inicia uma nova página para o verso

            # Imprimir o verso
            img_back = Image.open(back_image_path)  # Abre a imagem do verso do cartão
            img_back = img_back.convert("RGB")  # Converte a imagem para RGB
            dib_back = ImageWin.Dib(img_back)  # Cria uma representação da imagem para a impressão
            dib_back.draw(hdc.GetHandleOutput(), (0, 0, img_back.size[0], img_back.size[1]))  # Desenha a imagem na página

            hdc.EndPage()  # Finaliza a página
            hdc.EndDoc()  # Finaliza o documento de impressão
            hdc.DeleteDC()  # Deleta o contexto de dispositivo da impressora
        except Exception as e:
            print(f"Erro ao imprimir o verso do cartão: {e}")
            return

        win32print.EndPagePrinter(hprinter)  # Finaliza a página na impressora
    except Exception as e:
        print(f"Erro durante o processo de impressão: {e}")
        return
    finally:
        try:
            win32print.EndDocPrinter(hprinter)  # Finaliza o documento na impressora
            win32print.ClosePrinter(hprinter)  # Fecha a conexão com a impressora
        except Exception as e:
            print(f"Erro ao finalizar ou fechar a impressora: {e}")
