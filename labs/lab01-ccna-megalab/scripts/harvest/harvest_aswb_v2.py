"""Collect ASW-B1/B2/B3 through the documented Kali-to-DSW-B1 jump path."""

import shlex
import sys
import time
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials, kali_credentials, sanitize_config


JUMP_IP = "10.3.0.2"
KALI_SOURCE_IP = "10.1.0.14"
TARGETS = [
    ("ASW-B1", "10.0.0.20"),
    ("ASW-B2", "10.0.0.21"),
    ("ASW-B3", "10.0.0.22"),
]


def recv_until(shell, markers, timeout=15):
    buffer = ""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        if shell.recv_ready():
            buffer += shell.recv(65535).decode("utf-8", errors="ignore")
            if any(marker in buffer for marker in markers):
                break
    return buffer


def accept_host_key_if_needed(shell, buffer):
    if "yes/no" in buffer:
        shell.send("yes\n")
        return recv_until(shell, ["Password:", ">", "#"], timeout=10)
    return buffer


def enter_enable(shell, credentials):
    shell.send("enable\n")
    buffer = recv_until(shell, ["Password:", "#"], timeout=5)
    if "Password:" in buffer:
        shell.send(f'{credentials["secret"]}\n')
        buffer = recv_until(shell, ["#"], timeout=5)
    return buffer


def harvest(name, target_ip, kali, credentials):
    kali_host, kali_port, kali_user, kali_password = kali
    print(f"\n[{name}] Connecting to the configured Kali endpoint...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        kali_host,
        port=kali_port,
        username=kali_user,
        password=kali_password,
    )
    shell = client.invoke_shell(width=200, height=200)
    recv_until(shell, ["$", "#"], timeout=5)

    jump_command = (
        "ssh -oKexAlgorithms=+diffie-hellman-group14-sha1 "
        "-oHostKeyAlgorithms=+ssh-rsa -oStrictHostKeyChecking=no "
        f"-l {shlex.quote(credentials['username'])} "
        f"-b {KALI_SOURCE_IP} {JUMP_IP}"
    )
    shell.send(f"{jump_command}\n")
    buffer = accept_host_key_if_needed(
        shell, recv_until(shell, ["Password:", "yes/no", ">", "#"], timeout=15)
    )
    if "Password:" in buffer:
        shell.send(f'{credentials["password"]}\n')
        buffer = recv_until(shell, [">", "#"], timeout=10)
    if ">" not in buffer and "#" not in buffer:
        client.close()
        raise RuntimeError(f"{name}: no prompt from the DSW-B1 jump device.")

    enter_enable(shell, credentials)
    print(f"[{name}] Connecting from DSW-B1 to {target_ip}...")
    shell.send(
        f"ssh -l {shlex.quote(credentials['username'])} {target_ip}\n"
    )
    buffer = accept_host_key_if_needed(
        shell, recv_until(shell, ["Password:", "yes/no", ">", "#"], timeout=15)
    )
    if "Password:" in buffer:
        shell.send(f'{credentials["password"]}\n')
        buffer = recv_until(shell, [">", "#"], timeout=10)
    if ">" not in buffer and "#" not in buffer:
        client.close()
        raise RuntimeError(f"{name}: no prompt from the access switch.")

    if ">" in buffer and "#" not in buffer:
        enter_enable(shell, credentials)

    shell.send("terminal length 0\n")
    time.sleep(0.8)
    if shell.recv_ready():
        shell.recv(65535)
    shell.send("show running-config\n")
    config = ""
    deadline = time.time() + 45
    while time.time() < deadline:
        time.sleep(0.5)
        if shell.recv_ready():
            chunk = shell.recv(65535).decode("utf-8", errors="ignore")
            config += chunk
            if "\nend\n" in config or config.rstrip().endswith("end"):
                break
    client.close()
    return config


def main():
    kali = kali_credentials()
    credentials = cisco_credentials()
    output_dir = Path(__file__).resolve().parents[2] / "configs"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, ip in TARGETS:
        config = harvest(name, ip, kali, credentials)
        if len(config.strip()) < 100:
            raise RuntimeError(f"{name}: no usable configuration was collected.")
        destination = output_dir / f"{name}.txt"
        destination.write_text(sanitize_config(config), encoding="utf-8")
        print(f"[{name}] Saved sanitized configuration to {destination}.")


if __name__ == "__main__":
    main()
