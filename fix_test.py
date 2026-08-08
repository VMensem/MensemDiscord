
with open(r'C:\hueta\MensemBot\logs\events.py', 'r', encoding='utf-8') as f:
    content = f.read()
    # Remove BOM
    if content.startswith('\ufeff'):
        content = content[1:]
    
    fixed = content.encode('cp1251').decode('utf-8')
    print(fixed[:500])
