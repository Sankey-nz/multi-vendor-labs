import sys
from pathlib import Path

from netmiko import ConnectHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python netmiko_audit.py <device-host>")

    host = sys.argv[1]
    connection = ConnectHandler(
        device_type="cisco_ios",
        host=host,
        **cisco_credentials(),
    )
    try:
        connection.enable()
        print(f"Connected to {host}.")
        for interface in ("GigabitEthernet0/2", "GigabitEthernet0/3"):
            print(f"--- {interface} ---")
            print(connection.send_command(f"show running-config interface {interface}"))
    finally:
        connection.disconnect()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        raise
