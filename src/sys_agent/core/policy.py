from dataclasses import dataclass

BLOCKED_PATTERNS: tuple[str, ...] = (
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){",
    "shutdown",
    "reboot",
    "poweroff",
    "chmod -R 777 /",
    "> /dev/sd",
)


@dataclass
class InterventionState:
    fix_approved: bool = False


def is_command_safe(command: str) -> tuple[bool, str]:
    normalized = " ".join(command.strip().split())
    if not normalized:
        return False, "Empty command is not allowed."
    for pattern in BLOCKED_PATTERNS:
        if pattern in normalized:
            return False, f"Blocked dangerous pattern: '{pattern}'"
    return True, "OK"
