import os

def append_to_env(new_vars: dict):
    # Пишем данные в id.txt в рабочей директории (корень проекта при запуске из корня)
    output_path = "id.txt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Generated configuration IDs\n")
        for key, value in new_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Данные успешно записаны в {os.path.abspath(output_path)}")
