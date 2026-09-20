import socket
import paramiko
import sys
import time
from netmiko import ConnectHandler

def get_config(ip, src_ip=None):
    username = 'cisco'
    password = 'CCNA'
    secret = 'class'

    try:
        if src_ip:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.bind((src_ip, 0))
            sock.connect((ip, 22))
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
            shell.send("terminal length 0\n")
            time.sleep(1)
            shell.send("show running-config\n")

            output = ""
            start_time = time.time()
            while time.time() - start_time < 30:
                if shell.recv_ready():
                    chunk = shell.recv(65535).decode('utf-8', errors='ignore')
                    output += chunk
                    if "end" in chunk.lower():
                        break
                time.sleep(0.5)
            client.close()
            return output
        else:
            device = {
                'device_type': 'cisco_ios',
                'host': ip,
                'username': username,
                'password': password,
                'secret': secret,
            }
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            output = net_connect.send_command('show running-config')
            net_connect.disconnect()
            return output
    except Exception as e:
        return f"ERROR: {e}"

def harvest():
    devices = [
        ('R1', '10.0.0.76', '10.1.0.14'),
        ('CSW1', '10.0.0.77', '10.1.0.14'),
        ('CSW2', '10.0.0.78', '10.1.0.14'),
        ('DSW-A1', '10.0.0.79', '10.1.0.14'),
        ('DSW-A2', '10.0.0.80', '10.1.0.14'),
        ('DSW-B1', '10.0.0.81', '10.1.0.14'),
        ('DSW-B2', '10.0.0.82', '10.1.0.14'),
        ('ASW-A1', '10.0.0.4', '10.0.0.14'),
        ('ASW-A2', '10.0.0.5', '10.0.0.14'),
        ('ASW-A3', '10.0.0.6', '10.0.0.14'),
        ('ASW-B1', '10.0.0.20', '10.0.0.14'),
        ('ASW-B2', '10.0.0.21', '10.0.0.14'),
        ('ASW-B3', '10.0.0.22', '10.0.0.14'),
    ]

    import os
    output_dir = '/home/kali/configs_final'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for name, ip, src in devices:
        print(f"Harvesting {name} ({ip})...", end=' ')
        res = get_config(ip, src)
        if "ERROR" in res:
            print(f"❌ {res}")
        else:
            # Clean the output: remove the prompt and banner if possible
            if "Building configuration..." in res:
                try:
                    res = res.split("Building configuration...")[1].split("end\n")[0]
                except: pass
            with open(f'{output_dir}/{name}.txt', 'w') as f:
                f.write(res)
            print("✅ Success")

if __name__ == '__main__':
    harvest()
