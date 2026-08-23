import importlib
import os
import inspect

def load_modules(bot):
    modules_path = "voice"

    for root, dirs, files in os.walk(modules_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            if file in ["__init__.py", "bot.py", "config.py", "loader.py"]:
                continue

            # Need to fix the module name calculation. If running from MensemBot, root is 'voice'
            # path is 'voice/events.py'. Module name should be 'voice.events'
            module_name = f"voice.{file[:-3]}"

            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    result = module.setup(bot)
                    if inspect.isawaitable(result):
                        # We cannot await here because load_modules is sync.
                        # We need to make load_modules async or use create_task
                        import asyncio
                        asyncio.create_task(result)
                    print(f"OK Voice submodule loaded: {module_name}")
            except Exception as exc:
                print(f"FAIL Voice submodule {module_name}: {exc}")
