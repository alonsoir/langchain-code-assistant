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


def main():
    print("main...")
    pdf_url = input("Enter PDF URL: ")
    try:
        # Download PDF using requests
        pdf_data = download_pdf(pdf_url)

        # Use BytesIO to treat downloaded data as a file
        pdf_reader = pypdf2.PdfReader(pdf_data)

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                speak(text)
        print("All done")
    except Exception as e:
        print(e)

    pdf_file = input("Enter PDF file name: ")

    try:
        with open(pdf_file, "rb") as f:
            pdf_reader = pypdf2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    speak(text)
            print("All done")
    except FileNotFoundError:
        print("File not found")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
