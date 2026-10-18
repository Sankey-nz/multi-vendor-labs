"""Runtime credential input and credential-safe config output."""

import getpass
import os
import re
import sys


def runtime_value(name: str, prompt: str, *, secret: bool = False) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if not sys.stdin.isatty():
        raise RuntimeError(
            f"{name} is required. Set it in the environment or run interactively."
        )
    return getpass.getpass(prompt) if secret else input(prompt)


def cisco_credentials() -> dict[str, str]:
    return {
        "username": runtime_value("CISCO_USERNAME", "Cisco username: "),
        "password": runtime_value(
            "CISCO_PASSWORD", "Cisco password: ", secret=True
        ),
        "secret": runtime_value(
            "CISCO_ENABLE_SECRET", "Cisco enable secret: ", secret=True
        ),
    }


def kali_credentials() -> tuple[str, int, str, str]:
    host = runtime_value("KALI_HOST", "Kali SSH host: ")
    port_value = runtime_value("KALI_PORT", "Kali SSH port: ")
    try:
        port = int(port_value)
    except ValueError as error:
        raise RuntimeError("KALI_PORT must be an integer.") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("KALI_PORT must be between 1 and 65535.")
    username = runtime_value("KALI_USERNAME", "Kali username: ")
    password = runtime_value("KALI_PASSWORD", "Kali password: ", secret=True)
    return host, port, username, password


_CREDENTIAL_LINE = re.compile(
    r"^[ \t]*(?:"
    r"enable[ \t]+(?:secret|password)|"
    r"enable[ \t]+algorithm-type[ \t]+\S+[ \t]+secret|"
    r"username[ \t]+\S+.*[ \t]+(?:secret|password)|"
    r"password(?:[ \t]+\d+)?|"
    r"secret(?:[ \t]+\d+)?|"
    r"snmp-server[ \t]+community|"
    r"ntp[ \t]+authentication-key|"
    r"(?:tacacs|radius)-server[ \t]+key|"
    r"key-string|"
    r"ip[ \t]+ftp[ \t]+password"
    r")\b[^\r\n]*",
    re.IGNORECASE | re.MULTILINE,
)


def sanitize_config(config: str) -> str:
    return _CREDENTIAL_LINE.sub("", config)
