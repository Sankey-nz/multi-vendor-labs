import sys
from pathlib import Path

from netmiko import ConnectHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_credentials import cisco_credentials


DEVICES = [
    ("R1", "10.0.0.76", "10.1.0.14"),
    ("CSW1", "10.0.0.77", "10.1.0.14"),
    ("CSW2", "10.0.0.78", "10.1.0.14"),
    ("DSW-A1", "10.0.0.79", "10.1.0.14"),
    ("DSW-A2", "10.0.0.80", "10.1.0.14"),
    ("DSW-B1", "10.0.0.81", "10.1.0.14"),
    ("DSW-B2", "10.0.0.82", "10.1.0.14"),
    ("ASW-A1", "10.0.0.4", "10.1.0.14"),
    ("ASW-A2", "10.0.0.5", "10.1.0.14"),
    ("ASW-A3", "10.0.0.6", "10.1.0.14"),
    ("ASW-B1", "10.0.0.20", "10.1.0.14"),
    ("ASW-B2", "10.0.0.21", "10.1.0.14"),
    ("ASW-B3", "10.0.0.22", "10.1.0.14"),
]


def test_all():
    credentials = cisco_credentials()
    failures = []
    for name, host, source_ip in DEVICES:
        try:
            connection = ConnectHandler(
                device_type="cisco_ios",
                host=host,
                source_address=source_ip,
                **credentials,
            )
            connection.disconnect()
            print(f"{name} ({host}): SSH connection succeeded")
        except Exception as error:
            failures.append(name)
            print(f"{name} ({host}): SSH connection failed: {error}")
    if failures:
        raise RuntimeError(f"SSH connection failed for: {', '.join(failures)}")


if __name__ == "__main__":
    try:
        test_all()
    except Exception as error:
        print(error, file=sys.stderr)
        raise
