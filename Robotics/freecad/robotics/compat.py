"""
compatability layer for old docs running
on freecad.Robot_tools namespace by inserting old namespace
in the sys.modules cache in advance
"""

import sys
import importlib
from types import ModuleType


OLD_PKG = "freecad.Robot_tools"
NEW_PKG = "freecad.robotics"

MODULES = (
    # App modules
    "App.rbt_robot",
    "App.rbt_tool",
    "App.rbt_traj",
    "App.rbt_api",

    # GUI modules
    "Gui.vp_rbt_robot",
    "Gui.vp_rbt_tool",
    "Gui.vp_rbt_joint",
    "Gui.g_rbt_traj_vp",
)


class _LegacyModule(ModuleType):
    """
    Forward attribute access to renamed implementation
    """

    def __init__(self, name, target):
        super().__init__(name)
        self.__package__ = name.rpartition(".")[0]
        self._target = target

    def __getattr__(self, name):
        if name.startswith("__") and name != "__all__":
            raise AttributeError(name)

        # forward module caching requests when legacy
        # names are not found
        module = importlib.import_module(self._target)
        value = getattr(module, name)
        setattr(self, name, value)
        return value


def _register(name, module):
    """
    register the modules once and expose them on parent pkg
    """
    existing = sys.modules.get(name)
    if existing is not None:
        return existing

    sys.modules[name] = module  # make import find module
    parent, _, child = name.rpartition(".")
    setattr(sys.modules[parent], child, module)  # register as parent arritbute
    return module


def install():
    """
    Register legacy package and module names
    """
    for name in (
        OLD_PKG,
        f"{OLD_PKG}.App",
        f"{OLD_PKG}.Gui"
    ):
        pkg = ModuleType(name)
        pkg.__package__ = name
        pkg.__path__ = []
        _register(name, pkg)

    for suffix in MODULES:
        old_name = f"{OLD_PKG}.{suffix}"
        new_name = f"{NEW_PKG}.{suffix}"
        _register(old_name, _LegacyModule(old_name, new_name))