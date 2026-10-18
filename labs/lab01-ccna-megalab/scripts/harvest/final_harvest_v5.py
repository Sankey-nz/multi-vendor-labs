import socket
import sys
import time
from pathlib import Path

import paramiko
from netmiko import ConnectHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials, sanitize_config


def get_config(ip, src_ip, credentials):
    try:
        if src_ip:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.bind((src_ip, 0))
            sock.connect((ip, 22))
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            transport = paramiko.Transport(sock)
            transport.connect(
                username=credentials["username"],
                password=credentials["password"],
            )
            client._transport = transport
            shell = client.invoke_shell()
            shell.send("enable\n")
            time.sleep(1)
            shell.send(f'{credentials["secret"]}\n')
            time.sleep(1)
            shell.send("terminal length 0\n")
            time.sleep(1)
            shell.send("show running-config\n")

            output = ""
            start_time = time.time()
            while time.time() - start_time < 30:
                if shell.recv_ready():
                    chunk = shell.recv(65535).decode("utf-8", errors="ignore")
                    output += chunk
                    if "end" in chunk.lower():
                        break
                time.sleep(0.5)
            client.close()
            return output

        device = {
            "device_type": "cisco_ios",
            "host": ip,
            **credentials,
        }
        net_connect = ConnectHandler(**device)
        net_connect.enable()
        output = net_connect.send_command("show running-config")
        net_connect.disconnect()
        return output
    except Exception as error:
        return f"ERROR: {error}"


def harvest():
    credentials = cisco_credentials()
    devices = [
        ("R1", "10.0.0.76", "10.1.0.14"),
        ("CSW1", "10.0.0.77", "10.1.0.14"),
        ("CSW2", "10.0.0.78", "10.1.0.14"),
        ("DSW-A1", "10.0.0.79", "10.1.0.14"),
        ("DSW-A2", "10.0.0.80", "10.1.0.14"),
        ("DSW-B1", "10.0.0.81", "10.1.0.14"),
        ("DSW-B2", "10.0.0.82", "10.1.0.14"),
        ("ASW-A1", "10.0.0.4", "10.0.0.14"),
        ("ASW-A2", "10.0.0.5", "10.0.0.14"),
        ("ASW-A3", "10.0.0.6", "10.0.0.14"),
        ("ASW-B1", "10.0.0.20", "10.0.0.14"),
        ("ASW-B2", "10.0.0.21", "10.0.0.14"),
        ("ASW-B3", "10.0.0.22", "10.0.0.14"),
    ]
    output_dir = Path(__file__).resolve().parents[2] / "configs"
    output_dir.mkdir(parents=True, exist_ok=True)
    failures = []

    for name, ip, source_ip in devices:
        print(f"Harvesting {name} ({ip})...", end=" ")
        result = get_config(ip, source_ip, credentials)
        if result.startswith("ERROR:"):
            print(result)
            failures.append(name)
            continue
        if len(result.strip()) < 100:
            print("No usable configuration was collected.")
            failures.append(name)
            continue
        if "Building configuration..." in result:
            result = result.split("Building configuration...", 1)[1]
            if "\nend" in result:
                result = result.rsplit("\nend", 1)[0]
        destination = output_dir / f"{name}.txt"
        destination.write_text(sanitize_config(result), encoding="utf-8")
        print("Saved sanitized configuration.")
    if failures:
        raise RuntimeError(f"Configuration collection failed for: {', '.join(failures)}")


if __name__ == "__main__":
    harvest()
