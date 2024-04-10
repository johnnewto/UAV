"""
This module provides a base class for creating plugins and a function for loading modules.

Classes:
- Base: Basic resource class

Functions:
- load_module: Load a module from the given path.
"""

import os
import traceback
from importlib import util


class Base:
    """Basic resource class. Inherit from this one."""
    plugins = []
    plugins_dict = {}

    def __init_subclass__(cls, **kwargs):
        """Add the subclass to the list of plugins and plugins_dict."""
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)
        cls.plugins_dict[cls.__name__] = cls


def load_module(path):
    """Load a module from the given path.

    Args:
        path (str): The path to the module file.

    Returns:
        module: The loaded module.

    Raises:
        Exception: If an error occurs while loading the module.
    """
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Get current path
path = os.path.abspath(__file__)
dirpath = os.path.dirname(path)

for fname in os.listdir(dirpath):
    # Load only "real modules"
    if not fname.startswith('.') and \
       not fname.startswith('__') and fname.endswith('.py'):
        try:
            load_module(os.path.join(dirpath, fname))
        except Exception:
            traceback.print_exc()