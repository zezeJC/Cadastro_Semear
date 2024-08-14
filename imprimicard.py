import os
import platform
import subprocess
import sys
from PIL import Image

def install_package(package_name):
    """
    Função para instalar pacotes dinamicamente usando pip.
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Verifica o sistema operacional
current_system = platform.system()

# Importa bibliotecas específicas de acordo com o sistema operacional
if current_system == "Windows":
    try:
        import win32print
        import win32ui
        from PIL import ImageWin
    except ImportError:
        print("Instalando pacotes necessários para Windows...")
        install_package('pywin32')
        install_package('pillow')
        import win32print
        import win32ui
        from PIL import ImageWin

elif current_system == "Linux" or current_system == "Darwin":  # Darwin é o nome do sistema para macOS
    try:
        import cups
    except ImportError:
        print("Instalando pacotes necessários para Linux/macOS...")
        install_package('pycups')

def print_card(user_id, printer_name):
    """
    Função principal para imprimir cartões de usuário.
    Baseia-se no ID do usuário para encontrar as imagens frontais e traseiras do cartão
    e enviá-las para impressão, com suporte para múltiplos sistemas operacionais.
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

    if current_system == "Windows":
        # Implementação para Windows usando win32print
        try:
            hprinter = win32print.OpenPrinter(printer_name)
            hjob = win32print.StartDocPrinter(hprinter, 1, ("Impressão de Cartão", None, "RAW"))
            win32print.StartPagePrinter(hprinter)

            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Card Print")
            hdc.StartPage()

            # Imprimir a frente
            img_front = Image.open(front_image_path)
            img_front = img_front.convert("RGB")
            dib_front = ImageWin.Dib(img_front)
            dib_front.draw(hdc.GetHandleOutput(), (0, 0, img_front.size[0], img_front.size[1]))

            hdc.EndPage()
            hdc.StartPage()

            # Imprimir o verso
            img_back = Image.open(back_image_path)
            img_back = img_back.convert("RGB")
            dib_back = ImageWin.Dib(img_back)
            dib_back.draw(hdc.GetHandleOutput(), (0, 0, img_back.size[0], img_back.size[1]))

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

            win32print.EndPagePrinter(hprinter)
        except Exception as e:
            print(f"Erro durante o processo de impressão no Windows: {e}")
        finally:
            try:
                win32print.EndDocPrinter(hprinter)
                win32print.ClosePrinter(hprinter)
            except Exception as e:
                print(f"Erro ao finalizar ou fechar a impressora no Windows: {e}")

    elif current_system == "Linux" or current_system == "Darwin":
        # Implementação para Linux e macOS usando CUPS
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            if printer_name not in printers:
                print(f"Erro: Impressora '{printer_name}' não encontrada.")
                return

            # Cria a tarefa de impressão para frente e verso
            for image in [front_image_path, back_image_path]:
                conn.printFile(printer_name, image, f"Job {user_id}", {})
            print("Impressão concluída com sucesso no Linux/macOS.")
        except Exception as e:
            print(f"Erro durante o processo de impressão no Linux/macOS: {e}")
