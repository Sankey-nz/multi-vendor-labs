import socket
import sys
import time
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials


def get_ip_info(ip, source_ip, credentials):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if source_ip:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((source_ip, 0))
        sock.connect((ip, 22))
        transport = paramiko.Transport(sock)
        transport.connect(
            username=credentials["username"],
            password=credentials["password"],
        )
        client._transport = transport
    else:
        client.connect(
            ip,
            username=credentials["username"],
            password=credentials["password"],
        )

    try:
        shell = client.invoke_shell()
        shell.send("enable\n")
        time.sleep(0.5)
        shell.send(f'{credentials["secret"]}\n')
        time.sleep(0.5)
        shell.send("terminal length 0\n")
        time.sleep(0.5)
        shell.send("show ip interface brief\n")
        time.sleep(1)
        shell.send("show running-config | include interface|ip address\n")
        time.sleep(2)
        return shell.recv(65535).decode("utf-8", errors="replace")
    finally:
        client.close()


def run_audit():
    credentials = cisco_credentials()
    devices = [
        ("R1", "10.0.0.76", "10.1.0.14"),
        ("CSW1", "10.0.0.77", None),
        ("CSW2", "10.0.0.78", None),
        ("DSW-A1", "10.0.0.79", None),
        ("DSW-A2", "10.0.0.80", None),
        ("DSW-B1", "10.0.0.81", None),
        ("DSW-B2", "10.0.0.82", None),
    ]
    for name, ip, source_ip in devices:
        print(f"--- {name} ({ip}) ---")
        print(get_ip_info(ip, source_ip, credentials))


if __name__ == "__main__":
    run_audit()
