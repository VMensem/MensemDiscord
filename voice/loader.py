import importlib
import os


def load_modules(bot):
    modules_path = "voice"

    for root, dirs, files in os.walk(modules_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            if file in ["__init__.py", "bot.py", "config.py", "loader.py"]:
                continue

            path = os.path.join(root, file)
            module_name = path.replace("\\", ".").replace("/", ".").replace(".py", "")

            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    module.setup(bot)
                    print(f"OK Voice submodule loaded: {module_name}")
            except Exception as exc:
                print(f"FAIL Voice submodule {module_name}: {exc}")
