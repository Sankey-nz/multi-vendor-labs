import subprocess

def run_ssh_cmd(ip, cmd):
    # Using the flags from the handoff
    ssh_cmd = [
        'ssh',
        '-oKexAlgorithms=+diffie-hellman-group14-sha1',
        '-oHostKeyAlgorithms=+ssh-rsa',
        '-oPubkeyAcceptedAlgorithms=+ssh-rsa',
        '-oStrictHostKeyChecking=no',
        f'cisco@{ip}',
        f'enable\npassword class\nterminal length 0\n{cmd}'
    ]
    # This won't work with simple subprocess because ssh is interactive.
    # But we can use 'sshpass' if available, or just rely on the fact that
    # we are running this on Kali where we might have keys or a specific environment.
    # Actually, the best way is to use the Netmiko logic but fix the connection.
    pass

# I'll just write a Python script that uses paramiko with the specific security options.
