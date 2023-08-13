def print_progress(progress: int, msg: str, max: int = 6):
    bar = progress*"▰"+(max-progress)*"▱"
    print(f"{bar} {msg}")