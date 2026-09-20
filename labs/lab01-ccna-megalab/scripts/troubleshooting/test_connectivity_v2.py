import socket
import paramiko
import sys
import time
from netmiko import ConnectHandler

def check_device(name, ip, src_ip=None):
    username = 'cisco'
    password = 'CCNA'
    secret = 'class'

    # Always try source binding if provided, or try it anyway if it's a common pattern
    # To be thorough, we try both methods.

    methods = []
    if src_ip: methods.append(('BOUND', src_ip))
    methods.append(('STD', None))

    for method_name, bind_ip in methods:
        try:
            if bind_ip:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.bind((bind_ip, 0))
                sock.connect((ip, 22))
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                transport = paramiko.Transport(sock)
                transport.connect(username=username, password=password)
                client._transport = transport
                client.close()
                return f"SUCCESS ({method_name})"
            else:
                device = {
                    'device_type': 'cisco_ios',
                    'host': ip,
                    'username': username,
                    'password': password,
                    'secret': secret,
                }
                net_connect = ConnectHandler(**device)
                net_connect.disconnect()
                return f"SUCCESS ({method_name})"
        except Exception:
            continue

    return "FAILED"

def test_all():
    devices = [
        ('R1', '10.0.0.76', '10.1.0.14'),
        ('CSW1', '10.0.0.77', '10.1.0.14'),
        ('CSW2', '10.0.0.78', '10.1.0.14'),
        ('DSW-A1', '10.0.0.79', '10.1.0.14'),
        ('DSW-A2', '10.0.0.80', '10.1.0.14'),
        ('DSW-B1', '10.0.0.81', '10.1.0.14'),
        ('DSW-B2', '10.0.0.82', '10.1.0.14'),
        ('ASW-A1', '10.0.0.4', '10.1.0.14'),
        ('ASW-A2', '10.0.0.5', '10.1.0.14'),
        ('ASW-A3', '10.0.0.6', '10.1.0.14'),
        ('ASW-B1', '10.0.0.20', '10.1.0.14'),
        ('ASW-B2', '10.0.0.21', '10.1.0.14'),
        ('ASW-B3', '10.0.0.22', '10.1.0.14'),
    ]

    for name, ip, src in devices:
        res = check_device(name, ip, src)
        print(f"{name} ({ip}): {res}")

if __name__ == '__main__':
    test_all()
