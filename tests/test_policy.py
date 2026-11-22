from sys_agent.core.policy import is_command_safe


def test_blocks_destructive_commands():
    ok, _ = is_command_safe("rm -rf /")
    assert not ok


def test_allows_targeted_remediation():
    ok, _ = is_command_safe("kill -15 4321")
    assert ok
