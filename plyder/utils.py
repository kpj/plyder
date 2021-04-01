import os
import datetime

import psutil


_proc = psutil.Process(os.getpid())
_proc.cpu_percent()  # first call will always return 0


def get_process_memory():
    mem = _proc.memory_percent()
    for child in _proc.children(recursive=True):
        mem += child.memory_percent()

    return mem


def get_process_cpu():
    cpu = _proc.cpu_percent()
    for child in _proc.children(recursive=True):
        cpu += child.cpu_percent(interval=0.01)  # TODO: performance impact?

    return cpu


def get_current_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
