"""
harvest_aswb_v2.py
------------------
Harvest ASW-B1, ASW-B2, ASW-B3 using the exact manual path:

  Windows (paramiko) -> Kali shell
  Kali: ssh -oKexAlgorithms=+... -l cisco -b 10.1.0.14 10.3.0.2  (DSW-B1)
  DSW-B1: ssh -l cisco 10.0.0.2x  (ASW-Bx)
"""

import paramiko, time, os

KALI_HOST = '192.168.146.129'
KALI_PORT = 30067
KALI_USER = 'kali'
KALI_PASS = 'kali'
USERNAME  = 'cisco'
PASSWORD  = 'CCNA'
SECRET    = 'class'
JUMP_IP   = '10.3.0.2'

KALI_SSH  = (
    'ssh -oKexAlgorithms=+diffie-hellman-group14-sha1 '
    '-oHostKeyAlgorithms=+ssh-rsa '
    '-oStrictHostKeyChecking=no '
    f'-l {USERNAME} -b 10.1.0.14 {JUMP_IP}'
)

OUTPUT_DIR = r'C:\Users\Sankey\OneDrive\multi-vendor-labs\labs\lab01-ccna-megalab\configs'

TARGETS = [
    ('ASW-B1', '10.0.0.20'),
    ('ASW-B2', '10.0.0.21'),
    ('ASW-B3', '10.0.0.22'),
]


def recv_until(shell, markers, timeout=15):
    buf = ''
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        if shell.recv_ready():
            buf += shell.recv(65535).decode('utf-8', errors='ignore')
            if any(m in buf for m in markers):
                return buf
    return buf


def harvest(name, target_ip):
    print(f'\n[{name}] Connecting to Kali...')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(KALI_HOST, port=KALI_PORT, username=KALI_USER, password=KALI_PASS)
    shell = client.invoke_shell(width=200, height=200)

    # drain Kali prompt
    recv_until(shell, ['$', '#'], timeout=5)

    # Step 1: Kali -> DSW-B1 with legacy SSH flags
    print(f'[{name}] Kali -> DSW-B1 ({JUMP_IP})...')
    shell.send(KALI_SSH + '\n')
    buf = recv_until(shell, ['Password:', 'yes/no'], timeout=15)
    if 'yes/no' in buf:
        shell.send('yes\n')
        buf = recv_until(shell, ['Password:'], timeout=10)
    shell.send(PASSWORD + '\n')
    recv_until(shell, ['>'], timeout=10)

    # Enable on DSW-B1
    shell.send('enable\n')
    buf = recv_until(shell, ['Password:', '#'], timeout=5)
    if 'Password:' in buf:
        shell.send(SECRET + '\n')
        recv_until(shell, ['#'], timeout=5)

    # Step 2: DSW-B1 -> ASW using plain cisco SSH (no extra flags)
    print(f'[{name}] DSW-B1 -> {target_ip}...')
    shell.send(f'ssh -l {USERNAME} {target_ip}\n')
    buf = recv_until(shell, ['Password:', 'yes/no', '>'], timeout=15)
    if 'yes/no' in buf:
        shell.send('yes\n')
        buf = recv_until(shell, ['Password:'], timeout=10)
    if 'Password:' in buf:
        shell.send(PASSWORD + '\n')
        buf = recv_until(shell, ['>', '#'], timeout=10)

    if '>' not in buf and '#' not in buf:
        print(f'[{name}] ERROR: no ASW prompt. Got: {repr(buf[-150:])}')
        client.close()
        return None

    # Enable on ASW
    if '>' in buf and '#' not in buf:
        shell.send('enable\n')
        buf = recv_until(shell, ['Password:', '#'], timeout=5)
        if 'Password:' in buf:
            shell.send(SECRET + '\n')
            recv_until(shell, ['#'], timeout=5)

    # Collect config
    shell.send('terminal length 0\n')
    time.sleep(0.8)
    shell.recv_ready() and shell.recv(65535)

    print(f'[{name}] Collecting show running-config...')
    shell.send('show running-config\n')
    config = ''
    deadline = time.time() + 45
    while time.time() < deadline:
        time.sleep(0.5)
        if shell.recv_ready():
            chunk = shell.recv(65535).decode('utf-8', errors='ignore')
            config += chunk
            if '\nend\n' in chunk or chunk.strip().endswith('\nend'):
                break

    client.close()
    return config


def main():
    for name, ip in TARGETS:
        config = harvest(name, ip)
        if not config or len(config.strip()) < 100:
            print(f'[{name}] FAILED - no config')
            continue

        hostname_lines = [l for l in config.splitlines() if l.startswith('hostname')]
        print(f'[{name}] hostname line: {hostname_lines}')

        out_path = os.path.join(OUTPUT_DIR, f'{name}.txt')
        with open(out_path, 'w') as f:
            f.write(config)
        print(f'[{name}] Saved {len(config)} bytes -> {out_path}')

    print('\nDone.')


if __name__ == '__main__':
    main()
