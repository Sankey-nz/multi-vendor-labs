import sys
from pathlib import Path

from netmiko import ConnectHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials, runtime_value


def main():
    host = runtime_value("R1_HOST", "R1 host: ")
    credentials = cisco_credentials()
    connection = ConnectHandler(
        device_type="cisco_ios",
        host=host,
        **credentials,
    )
    try:
        connection.enable()
        print(f"Connected to R1 at {host}.")
        for interface in ("GigabitEthernet0/2", "GigabitEthernet0/3"):
            print(f"--- {interface} ---")
            print(connection.send_command(f"show running-config interface {interface}"))
    finally:
        connection.disconnect()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"R1 audit failed: {error}", file=sys.stderr)
        raise
