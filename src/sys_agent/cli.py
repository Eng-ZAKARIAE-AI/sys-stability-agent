import re

from config.settings import settings
from sys_agent.core.llm import create_agent_session
from sys_agent.core.policy import InterventionState
from sys_agent.core.telemetry import get_logger
from sys_agent.prompts.system_prompt import SYSTEM_INSTRUCTION
from sys_agent.tools.diagnostics import check_system_metrics, inspect_process_or_logs
from sys_agent.tools.intervention import build_intervention_tool
from sys_agent.tools.screenshot import take_screenshot

APPROVAL_PHRASES = {
    "yes",
    "y",
    "ok",
    "approve",
    "i approve",
    "i approve it",
    "fix it",
    "fix",
    "apply fix",
    "go ahead",
    "run it",
    "confirm",
}


def normalize_approval(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def is_approval_phrase(text: str) -> bool:
    return normalize_approval(text) in APPROVAL_PHRASES


def main() -> None:
    logger = get_logger("sys_agent", settings.log_level)
    state = InterventionState(fix_approved=False)
    execute_intervention = build_intervention_tool(state)

    chat = create_agent_session(
        provider=settings.llm_provider,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[check_system_metrics, inspect_process_or_logs, execute_intervention, take_screenshot],
        openrouter_api_key=settings.openrouter_api_key,
        openrouter_model=settings.openrouter_model,
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
        site_url=settings.openrouter_site_url,
        app_name=settings.openrouter_app_name,
    )

    print("System Stability Agent ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break

            if is_approval_phrase(user_input):
                state.fix_approved = True

            response = chat.send_message(user_input)
            print(f"\nAgent > {response}\n")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("Agent loop error: %s", exc)


if __name__ == "__main__":
    main()
