import importlib
import inspect
import logging
import sys


MODULES = [
    "verify",
    "voice",
    "banner",
    "logs",
    "giveaways",
    "auto_roles",
    "reaction_roles",
    "suggestions",
    "ai_assistant",
    "moderation",
    "tickets",
    "events",
    "reports",
    "leveling",
    "clans",
    "economy",
    "profiles",
    "message_builder",
    "server_management",
    "staff",
]


def safe_print(message: str):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.buffer.write((message + "\n").encode(encoding, errors="replace"))
        sys.stdout.flush()


async def call_setup(module, bot):
    setup = getattr(module, "setup", None)
    if setup is None:
        raise RuntimeError(f"{module.__name__} is missing setup(bot)")

    result = setup(bot)
    if inspect.isawaitable(result):
        await result


async def load_modules(bot):
    safe_print("=" * 30)
    safe_print("MensemBot Loading...")
    safe_print("=" * 30)

    failures = []

    for module_name in MODULES:
        try:
            module = importlib.import_module(f"{module_name}.bot")
            await call_setup(module, bot)
            safe_print(f"OK {module_name} loaded")
        except Exception as exc:
            failures.append(f"{module_name}: {exc}")
            safe_print(f"FAIL {module_name}: {exc}")
            logging.exception("Module failed: %s", module_name)

    if failures:
        raise RuntimeError("Module loading failed: " + "; ".join(failures))
