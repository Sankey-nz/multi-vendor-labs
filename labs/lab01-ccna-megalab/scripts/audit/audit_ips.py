import socket
import paramiko
import sys
import time

def get_ip_info(ip, src_ip=None):
    username = 'cisco'
    password = 'CCNA'
    secret = 'class'

    try:
        if src_ip:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((src_ip, 0))
            sock.connect((ip, 22))
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            transport = paramiko.Transport(sock)
            transport.connect(username=username, password=password)
            client._transport = transport
            shell = client.invoke_shell()
            shell.send("enable\n")
            time.sleep(0.5)
            shell.send(f"{secret}\n")
            time.sleep(0.5)
            shell.send("terminal length 0\n")
            time.sleep(0.5)
            shell.send("show ip interface brief\n")
            time.sleep(1)
            shell.send("show running-config | include interface|ip address\n")
            time.sleep(2)
            output = shell.recv(65535).decode('utf-8')
            client.close()
            return output
        else:
            # Use paramiko for simplicity here
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, password=password)
            shell = client.invoke_shell()
            shell.send("enable\n")
            time.sleep(0.5)
            shell.send(f"{secret}\n")
            time.sleep(0.5)
            shell.send("terminal length 0\n")
            time.sleep(0.5)
            shell.send("show ip interface brief\n")
            time.sleep(1)
            shell.send("show running-config | include interface|ip address\n")
            time.sleep(2)
            output = shell.recv(65535).decode('utf-8')
            client.close()
            return output
    except Exception as e:
        return f"Error: {e}"

def run_audit():
    devices = [
        ('R1', '10.0.0.76', '10.1.0.14'),
        ('CSW1', '10.0.0.77', None),
        ('CSW2', '10.0.0.78', None),
        ('DSW-A1', '10.0.0.79', None),
        ('DSW-A2', '10.0.0.80', None),
        ('DSW-B1', '10.0.0.81', None),
        ('DSW-B2', '10.0.0.82', None),
    ]

    for name, ip, src in devices:
        print(f"--- {name} ({ip}) ---")
        print(get_ip_info(ip, src))
        print("\n")

if __name__ == '__main__':
    run_audit()
