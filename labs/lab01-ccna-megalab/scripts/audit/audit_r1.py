import paramiko

# Credentials
KALI_HOST = '192.168.146.129'
KALI_PORT = 30067
KALI_USER = 'kali'
KALI_PWD = 'kali'

R1_USER = 'cisco'
R1_PWD = 'CCNA'
R1_ENABLE = 'class'

def run_kali_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8')

try:
    print(f"Connecting to Kali at {KALI_HOST}:{KALI_PORT}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(KALI_HOST, port=KALI_PORT, username=KALI_USER, password=KALI_PWD)
    print("Connected to Kali!")

    # We will use a small python one-liner on Kali to use netmiko to connect to R1
    # This avoids having to upload a script to Kali first.
    # We'll fetch the running config of the WAN interfaces.

    netmiko_script = f"""
import sys
from netmiko import ConnectHandler

device = {{
    'device_type': 'cisco_ios',
    'host': '10.0.0.33', # This is a guess based on R1 configs seen earlier, but I should check the real IP
    'username': '{R1_USER}',
    'password': '{R1_PWD}',
    'secret': '{R1_ENABLE}',
}}

try:
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    output = net_connect.send_command('show run interface GigabitEthernet0/2')
    print('--- Gi0/2 ---')
    print(output)
    output = net_connect.send_command('show run interface GigabitEthernet0/3')
    print('--- Gi0/3 ---')
    print(output)
    net_connect.disconnect()
except Exception as e:
    print(f'Error: {{e}}')
"""
    # Since the R1 IP might be different (drift), I should first check what R1's IP is from Kali.
    # But let's assume the user can provide the R1 IP or I can try a few.
    # Actually, the user said "you can access kali", but didn't give me R1's IP from Kali's perspective.
    # I'll first try to find R1's IP by scanning or checking common ones.

    # Better: I'll just run a command on Kali to see if there's a known host or just try the IPs from the config.
    # Let's try 10.0.0.33 first as it was in R1.txt (though it might be drifted).

    # To be safe, I'll just start by checking connectivity from Kali to a few IPs.
    print("Checking connectivity from Kali to R1...")
    # Let's try the IP from the config: 10.0.0.33
    check_conn = run_kali_command(client, 'ping -c 1 10.0.0.33')
    print(f"Ping 10.0.0.33: {check_conn}")

    # Instead of guessing, I'll write the Netmiko script to a file on Kali and then run it.
    with client.open_sftp() as sftp:
        with open('netmiko_audit.py', 'w') as f:
            # I'll leave the IP as a variable to be filled or I'll try to find it.
            # Actually, I'll just use a script that takes the IP as an argument.
            f.write(f'''
import sys
from netmiko import ConnectHandler

if len(sys.argv) < 2:
    print("Usage: python3 netmiko_audit.py <ip>")
    sys.exit(1)

ip = sys.argv[1]
device = {{
    'device_type': 'cisco_ios',
    'host': ip,
    'username': '{R1_USER}',
    'password': '{R1_PWD}',
    'secret': '{R1_ENABLE}',
}}

try:
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    print(f"Successfully connected to {{ip}}")
    print(net_connect.send_command('show run interface GigabitEthernet0/2'))
    print(net_connect.send_command('show run interface GigabitEthernet0/3'))
    net_connect.disconnect()
except Exception as e:
    print(f"Error connecting to {{ip}}: {{e}}")
''')
        sftp.put('netmiko_audit.py', '/home/kali/netmiko_audit.py')

    print("Script uploaded to Kali. Now attempting to find R1...")
    # Try common IPs from config
    for ip in ['10.0.0.33', '10.0.0.37', '192.168.10.1']:
        print(f"Trying {ip}...")
        res = run_kali_command(client, f'python3 /home/kali/netmiko_audit.py {ip}')
        print(res)
        if 'Successfully connected' in res:
            print(f"Found R1 at {ip}!")
            break

    client.close()
except Exception as e:
    print(f"An error occurred: {e}")
