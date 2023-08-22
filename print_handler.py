def print_progress(progress: int, msg: str, max: int = 6):
    bar = progress*"▰"+(max-progress)*"▱"
    print(f"{bar} {msg}")

def human_readable_size(size_in_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    
    unit_index = 0
    while size_in_bytes >= 1024 and unit_index < len(units) - 1:
        size_in_bytes /= 1024
        unit_index += 1
    
    size_formatted = "{:.2f}".format(size_in_bytes)
    
    return f"{size_formatted} {units[unit_index]}"