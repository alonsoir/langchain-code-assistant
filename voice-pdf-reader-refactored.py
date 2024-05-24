import subprocess
from io import BytesIO

import PyPDF2 as pypdf2
import requests
import speech_recognition as sr

# Inicialización del reconocedor de voz
recognizer = sr.Recognizer()


def speak(text):
    """Función para convertir texto a voz usando el comando `say` de macOS."""
    subprocess.run(["say", text])


def download_pdf(url):
    """Descarga un archivo PDF desde una URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Error downloading PDF: {response.status_code}")


# Al tratar de refactorizar el código, me di cuenta que la variable pdf_reader al abrir un fichero local
# se cerraba, aunque hayas usado el metodo open() para abrir el fichero.
def read_pdf(source):
    """

    :param source: source es un recurso que puede ser una URL o un nombre de fichero local
    :return: nada, el sistema usa la voz al para los sordomudos.
    """
    try:
        # Leer el PDF desde una URL remota
        pdf_data = download_pdf(source)
        pdf_reader = pypdf2.PdfReader(pdf_data)
        # Extraer texto de las páginas del PDF
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                speak(text)
    except ValueError:
        try:
            # Leer el PDF desde un archivo local
            with open(source, "rb") as f:
                pdf_reader = pypdf2.PdfReader(f)
                # Extraer texto de las páginas del PDF
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        speak(text)
        except FileNotFoundError:
            print("File not found")
            return
    except Exception as e:
        print(e)
        return

    print("All done")


def main():
    source = input("Enter PDF URL or file name: ")
    read_pdf(source)


if __name__ == "__main__":
    main()
