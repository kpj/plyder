from importlib import metadata

from .main import main


__version__ = metadata.version('plyder')


__all__ = ['__version__', 'main']
