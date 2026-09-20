import socket
import paramiko
import sys
import time

def audit_nat_acls():
    src_ip = '10.1.0.14'
    dst_ip = '10.0.0.76'
    dst_port = 22
    username = 'cisco'
    password = 'CCNA'
    secret = 'class'

    try:
        print(f"Binding to {src_ip} and connecting to {dst_ip}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((src_ip, 0))
        sock.connect((dst_ip, dst_port))

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        transport = paramiko.Transport(sock)
        transport.connect(username=username, password=password)
        client._transport = transport

        shell = client.invoke_shell()
        shell.send("enable\n")
        time.sleep(1)
        shell.send(f"{secret}\n")
        time.sleep(1)

        print("Gathering NAT and ACL diagnostics...")
        commands = [
            "show ip nat translations",
            "show ip access-lists",
            "show ip route 0.0.0.0",
            "show ip interface brief"
        ]

        for cmd in commands:
            shell.send(f"{cmd}\n")
            time.sleep(1)

        output = shell.recv(65535).decode('utf-8')
        print(f"Diagnostics output:\n{output}")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    audit_nat_acls()
