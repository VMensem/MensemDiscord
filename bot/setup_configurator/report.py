import json

def generate_report(new_vars):
    with open("output/scan_result.json", "w") as f:
        json.dump(new_vars, f, indent=4)
    with open("output/missing_variables.txt", "w") as f:
        for k, v in new_vars.items():
            f.write(f"{k}={v}\n")
