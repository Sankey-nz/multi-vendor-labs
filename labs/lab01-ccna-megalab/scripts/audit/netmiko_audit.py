
import sys
from netmiko import ConnectHandler

if len(sys.argv) < 2:
    print("Usage: python3 netmiko_audit.py <ip>")
    sys.exit(1)

ip = sys.argv[1]
device = {
    'device_type': 'cisco_ios',
    'host': ip,
    'username': 'cisco',
    'password': 'CCNA',
    'secret': 'class',
}

try:
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    print(f"Successfully connected to {ip}")
    print(net_connect.send_command('show run interface GigabitEthernet0/2'))
    print(net_connect.send_command('show run interface GigabitEthernet0/3'))
    net_connect.disconnect()
except Exception as e:
    print(f"Error connecting to {ip}: {e}")
