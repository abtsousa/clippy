def print_progress(progress: int, msg: str, max: int = 6):
    """
    Prints a progress bar with associated message.

    Args:
        progress (int): The progress to display (X out of max).
        msg (str): The associated message to display.
        max (int): The number of total steps (represents 100%)

    Usage:
        print_progress(1,"This is 20% or 1/5",5)
    """
    bar = progress*"▰"+(max-progress)*"▱"
    print(f"\033[K\r{bar} {msg}", flush=True) #force line clear before print

def human_readable_size(size_in_bytes):
    """
    Converts a size in bytes to a corresponding string in the appropriate size (B, KB, MB, GB or TB).
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    
    unit_index = 0
    while size_in_bytes >= 1024 and unit_index < len(units) - 1:
        size_in_bytes /= 1024
        unit_index += 1
    
    size_formatted = "{:.2f}".format(size_in_bytes)
    
    return f"{size_formatted} {units[unit_index]}"

def fixed_string_length(input_string, target_length=30):
    """
    Truncates or pads strings to a fixed length.
    """
    if len(input_string) <= target_length:
        padding_length = target_length - len(input_string)
        padded_string = input_string + ' ' * padding_length
        return padded_string
    else:
        truncation_length = target_length - 3  # Account for the '...' part
        truncated_string = input_string[:truncation_length//2+1] + '...' + input_string[-(truncation_length//2):]
        return truncated_string