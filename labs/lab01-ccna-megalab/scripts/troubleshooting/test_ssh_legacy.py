import sys
import subprocess

def try_ssh(ip):
    cmd = [
        'ssh',
        '-oKexAlgorithms=+diffie-hellman-group14-sha1',
        '-oHostKeyAlgorithms=+ssh-rsa',
        '-oPubkeyAcceptedKeyTypes=+ssh-rsa',
        '-oStrictHostKeyChecking=no',
        f'cisco@{ip}',
        'show version | include Sysname'
    ]
    try:
        # We can't easily provide the password to ssh via subprocess without sshpass.
        # But let's see if it asks for a password or just refuses.
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
        process.stdin.write('CCNA\n')
        process.stdin.flush()
        stdout, stderr = process.communicate(timeout=10)
        return stdout
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    for ip in ['10.0.0.1', '10.0.0.5']:
        print(f"Trying {ip}...")
        print(try_ssh(ip))
