# sys-stability-agent

Modular AI stability and intervention agent with a Diagnose -> Approve -> Fix workflow.

## Quickstart
```bash
make setup
# Set OPENROUTER_API_KEY in .env (default provider: OpenRouter)
make run
```

To use Gemini instead, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` in `.env`.

## System Dependencies

On Ubuntu, install the screenshot tool for desktop capture capability:

```bash
sudo apt update && sudo apt install -y gnome-screenshot
```

Alternative tools (auto-detected as fallbacks):
- Wayland: `grim` (`sudo apt install grim`)
- X11: `scrot` (`sudo apt install scrot`)
- ImageMagick: `import` (`sudo apt install imagemagick`)

## Quality Checks
```bash
make lint
make typecheck
make test
```



## How It Works (Diagnose → Approve → Fix → Verify)

1. **Diagnose:** Inspects logs, system metrics, or report generation errors using read-only terminal commands.
2. **Approve:** Presents any proposed remediation command to the user for explicit confirmation before execution.
3. **Fix:** Executes the approved fix directly in the Ubuntu terminal to resolve the underlying issue.
4. **Capture Proof:** Automatically takes a desktop/terminal screenshot (`take_screenshot`) after execution to visually verify the fix and attach evidence to the report.