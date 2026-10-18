import sys
from pathlib import Path

from netmiko import ConnectHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials


def try_ssh(host):
    connection = ConnectHandler(
        device_type="cisco_ios",
        host=host,
        disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
        **cisco_credentials(),
    )
    try:
        connection.enable()
        return connection.send_command("show version | include System image| uptime")
    finally:
        connection.disconnect()


if __name__ == "__main__":
    failures = []
    for host in ("10.0.0.1", "10.0.0.5"):
        try:
            print(f"--- {host} ---")
            print(try_ssh(host))
        except Exception as error:
            print(f"{host}: SSH test failed: {error}", file=sys.stderr)
            failures.append(host)
    if failures:
        raise SystemExit(f"SSH test failed for: {', '.join(failures)}")
