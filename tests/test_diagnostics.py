from sys_agent.tools.diagnostics import inspect_process_or_logs


def test_inspect_requires_target():
    result = inspect_process_or_logs()
    assert "Provide a valid pid" in result
