import getpass
import logging
import subprocess

from config.settings import settings
from sys_agent.core.policy import InterventionState, is_command_safe
from sys_agent.core.telemetry import write_audit_event

logger = logging.getLogger("sys_agent.intervention")

PASSWORD_KEYWORDS = ("sudo", "su ", "ssh ")


def build_intervention_tool(state: InterventionState):
    def execute_intervention(shell_command: str, reason: str) -> str:
        """Execute a remediation shell command only after user approval."""
        if not state.fix_approved:
            msg = "REJECTED: User has not explicitly approved a fix yet. Ask for confirmation first."
            logger.warning(
                "Intervention rejected: fix_approved=False | command=%r | reason=%r",
                shell_command,
                reason,
            )
            return msg

        safe, msg = is_command_safe(shell_command)
        if not safe:
            write_audit_event(
                settings.audit_log_path,
                "intervention_blocked",
                {"command": shell_command, "reason": reason, "policy_message": msg},
            )
            return f"BLOCKED: {msg}"

        password: str | None = None
        lowered = shell_command.lower()
        if any(keyword in lowered for keyword in PASSWORD_KEYWORDS):
            password = getpass.getpass("Password required for command. Enter password: ")

        res = subprocess.run(
            shell_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            stdin=subprocess.PIPE,
            input=(password + "\n") if password else None,
        )
        write_audit_event(
            settings.audit_log_path,
            "intervention_executed",
            {
                "command": shell_command,
                "reason": reason,
                "returncode": res.returncode,
            },
        )
        state.fix_approved = False
        return (
            f"Exit Code: {res.returncode}\n"
            f"STDOUT: {res.stdout.strip()}\n"
            f"STDERR: {res.stderr.strip()}"
        )

    return execute_intervention
