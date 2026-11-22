"""Tests for the screenshot capture tool."""

import base64
import os
import subprocess
import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sys_agent.tools.screenshot import take_screenshot


def test_take_screenshot_returns_dict():
    """Test that take_screenshot returns a dict with expected keys."""
    result = take_screenshot()
    assert isinstance(result, dict)
    assert "filepath" in result
    assert "image_base64" in result
    assert "error" in result


def test_take_screenshot_filepath_format():
    """Test that filepath follows expected naming pattern when successful."""
    result = take_screenshot()
    if not result["error"]:
        assert result["filepath"].startswith("/tmp/agent_screenshots/screen_")
        assert result["filepath"].endswith(".png")
        # Verify timestamp format YYYYMMDD_HHMMSS
        import re
        assert re.search(r"screen_\d{8}_\d{6}\.png$", result["filepath"])


def test_take_screenshot_base64_valid():
    """Test that base64 string is valid and decodes to PNG when successful."""
    result = take_screenshot()
    if not result["error"] and result["image_base64"]:
        # Should be valid base64
        try:
            decoded = base64.b64decode(result["image_base64"])
            assert len(decoded) > 0
            # Check PNG signature (first 8 bytes)
            assert decoded[:8] == b"\x89PNG\r\n\x1a\n"
        except Exception as exc:
            pytest.fail(f"Invalid base64 or not a PNG: {exc}")


def test_take_screenshot_file_exists():
    """Test that file actually exists on disk when successful."""
    result = take_screenshot()
    if not result["error"]:
        path = Path(result["filepath"])
        assert path.exists(), f"Screenshot file not found at {result['filepath']}"
        assert path.stat().st_size > 0, "Screenshot file is empty"


def test_take_screenshot_directory_created():
    """Test that the screenshot directory is created."""
    result = take_screenshot()
    screenshot_dir = Path("/tmp/agent_screenshots")
    assert screenshot_dir.exists(), "Screenshot directory was not created"
    assert screenshot_dir.is_dir(), "Screenshot path is not a directory"


def test_has_screenshot_tool_available():
    """Check if at least one screenshot tool is available on the system."""
    tools = ["gnome-screenshot", "grim", "scrot", "import"]
    available = [t for t in tools if shutil.which(t)]
    if not available:
        pytest.skip("No screenshot tools installed (gnome-screenshot, grim, scrot, or import)")


def test_screenshot_in_headless_environment():
    """Test behavior in headless environments (should return error gracefully)."""
    # In a headless environment (no display), the tool should return an error
    # rather than crashing
    result = take_screenshot()
    # Either succeeds (if display available) or returns error gracefully
    assert isinstance(result["error"], str)
    # If there's an error, it should be a meaningful message
    if result["error"]:
        assert len(result["error"]) > 0
        assert "failed" in result["error"].lower() or "available" in result["error"].lower()


# Need to import shutil for the test above
import shutil


if __name__ == "__main__":
    pytest.main([__file__, "-v"])