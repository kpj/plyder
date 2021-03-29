import os

import psutil


def get_process_memory():
    print(os.getpid())
    proc = psutil.Process(os.getpid())

    mem = proc.memory_percent()
    for child in proc.children(recursive=True):
        mem += child.memory_percent()

    return mem


def get_process_cpu():
    proc = psutil.Process(os.getpid())

    cpu = proc.cpu_percent()
    for child in proc.children(recursive=True):
        cpu += child.cpu_percent()

    return cpu
