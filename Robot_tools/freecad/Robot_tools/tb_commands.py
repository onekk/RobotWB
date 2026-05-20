""" Robot_tools Custom TB

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence: LGPL 2.1
"""

import os
import FreeCAD as App
import FreeCADGui as Gui
from importlib import import_module, reload

# service import
from . import tb_locator

wb_path = os.path.dirname(tb_locator.__file__)


def _reload_module(module_name: str) -> None:
    try:
        module = import_module(module_name)
    except ImportError:
        return
    reload(module)


class rbt_cmd2:
    """Robot tools command 1."""
    def GetResources(self):
        """Resources."""
        return {
            'Pixmap': os.path.join(wb_path,
                                   'resources/icons/rbt_studyRobot.svg'),
            # 'Accel': "F11",
            'MenuText': "Study Robot Object",
            'ToolTip': "<b>Study Robot Object</b>"
                }

    def Activated(self):
        """Activated."""
        from . import study_robot
        study_robot.run()

    def IsActive(self):
        """IsActive."""
        return True


class rbt_cmd3:
    """Robot tools command 3."""
    def GetResources(self):
        """Resources."""
        return {
            'Pixmap': os.path.join(wb_path,
                                   'resources/icons/rbt_animateRobot.svg'),
            # 'Accel': "F11",
            'MenuText': "Animate Robot",
            'ToolTip': "<b>Animate Robot</b>"
                }

    def Activated(self):
        """Activated."""
        from . import animate
        _reload_module("animate")
        animate.run()

    def IsActive(self):
        """IsActive."""
        return True


class rbt_cmd4:
    """Robot tools command 3."""
    def GetResources(self):
        """Resources."""
        return {
            'Pixmap': os.path.join(wb_path,
                                   'resources/icons/rbt_defineRobot.svg'),
            # 'Accel': "F11",
            'MenuText': "Define Robot",
            'ToolTip': "<b>Define a Robt from CAD elements</b>"
                }

    def Activated(self):
        """Activated."""
        from . import define_robot
        _reload_module("define_robot")
        define_robot.run()

    def IsActive(self):
        """IsActive."""
        return True


class rbt_cmd5:
    def GetResources(self):
        return {"Pixmap":   os.path.join(wb_path,
                                         'resources/icons/rbt_defineTool.svg'),
                "MenuText": "Define Tool",
                "ToolTip":  "Define a Tool and TCP on the active robot"}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        from freecad.Robot_tools.Gui import define_tool
        define_tool.run()


Gui.addCommand('RBT_strob', rbt_cmd2())
Gui.addCommand('RBT_anrob', rbt_cmd3())
Gui.addCommand('RBT_defrob', rbt_cmd4())
Gui.addCommand('RBT_deftool', rbt_cmd5())
