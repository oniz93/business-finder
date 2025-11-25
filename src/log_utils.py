import builtins
from datetime import datetime

def setup_timestamped_logging():
    """
    Replaces the built-in print function with a version that prepends a timestamp
    with milliseconds.
    """
    # Ensure we don't patch it more than once, which can happen in multiprocessing contexts.
    if getattr(builtins, '_timestamped_print_patched', False):
        return

    original_print = builtins.print

    def timestamped_print(*args, **kwargs):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        original_print(f"[{timestamp}]", *args, **kwargs)

    builtins.print = timestamped_print
    builtins._timestamped_print_patched = True
