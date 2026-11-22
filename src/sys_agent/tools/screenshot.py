"""Screenshot capture tool for Ubuntu desktop environments."""

import base64
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


def take_screenshot() -> dict[str, Any]:
    """
    Capture a screenshot of the Ubuntu desktop and return file path + base64 encoded image.

    Returns:
        dict with keys:
        - "filepath": str - path to saved PNG file
        - "image_base64": str - base64 encoded PNG data
        - "error": str - error message if capture failed (optional)
    """
    # Create timestamped filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path("/tmp/agent_screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    filepath = screenshot_dir / f"screen_{timestamp}.png"

    # Ensure DISPLAY is set for X11
    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"

    # Detect display server type
    session_type = env.get("XDG_SESSION_TYPE", "").lower()
    is_wayland = session_type == "wayland"

    # Build fallback command list based on environment
    commands = []

    # 1. gnome-screenshot (primary for Ubuntu GNOME)
    if shutil.which("gnome-screenshot"):
        commands.append(["gnome-screenshot", "-f", str(filepath)])

    # 2. grim (Wayland native)
    if is_wayland and shutil.which("grim"):
        commands.append(["grim", str(filepath)])

    # 3. scrot (X11)
    if not is_wayland and shutil.which("scrot"):
        commands.append(["scrot", str(filepath)])

    # 4. import (ImageMagick fallback)
    if shutil.which("import"):
        commands.append(["import", "-window", "root", str(filepath)])

    if not commands:
        return {
            "filepath": "",
            "image_base64": "",
            "error": (
                "No screenshot tool available. Install one of: "
                "gnome-screenshot (recommended), grim (Wayland), scrot (X11), or imagemagick (import)"
            ),
        }

    # Try each command in order
    last_error = ""
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=env,
            )
            if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
                # Success - read and encode as base64
                with open(filepath, "rb") as f:
                    image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                return {
                    "filepath": str(filepath),
                    "image_base64": image_base64,
                    "error": "",
                }
            else:
                last_error = (
                    f"Command '{' '.join(cmd)}' failed with exit code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
        except subprocess.TimeoutExpired:
            last_error = f"Command '{' '.join(cmd)}' timed out after 10 seconds"
        except OSError as exc:
            last_error = f"Command '{' '.join(cmd)}' raised OSError: {exc}"

    return {
        "filepath": "",
        "image_base64": "",
        "error": f"All screenshot methods failed. Last error: {last_error}",
    }