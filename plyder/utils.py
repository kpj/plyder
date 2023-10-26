import datetime

import psutil


_proc = psutil.Process()
_proc.cpu_percent()  # first call will always return 0


def get_process_memory() -> float:
    mem = _proc.memory_percent()
    for child in _proc.children(recursive=True):
        mem += child.memory_percent()

    return mem


def get_process_cpu() -> float:
    cpu = _proc.cpu_percent()
    for child in _proc.children(recursive=True):
        cpu += child.cpu_percent(interval=0.1)

    return cpu


def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
