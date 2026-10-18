import socket
import sys
import time
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials


def audit_nat_acls():
    credentials = cisco_credentials()
    src_ip = "10.1.0.14"
    dst_ip = "10.0.0.76"

    try:
        print(f"Binding to the configured source interface and connecting to R1...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((src_ip, 0))
        sock.connect((dst_ip, 22))

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        transport = paramiko.Transport(sock)
        transport.connect(
            username=credentials["username"],
            password=credentials["password"],
        )
        client._transport = transport

        shell = client.invoke_shell()
        shell.send("enable\n")
        time.sleep(1)
        shell.send(f'{credentials["secret"]}\n')
        time.sleep(1)

        print("Gathering NAT and ACL diagnostics...")
        for command in (
            "show ip nat translations",
            "show ip access-lists",
            "show ip route 0.0.0.0",
            "show ip interface brief",
        ):
            shell.send(f"{command}\n")
            time.sleep(1)

        print(shell.recv(65535).decode("utf-8", errors="replace"))
        client.close()
    except Exception as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        raise


if __name__ == "__main__":
    audit_nat_acls()
