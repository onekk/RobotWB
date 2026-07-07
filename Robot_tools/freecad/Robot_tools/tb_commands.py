""" Robot_tools Custom TB

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence: LGPL 2.1
"""

import os
import FreeCAD as App  # type: ignore
import FreeCADGui as Gui  # type: ignore

# service import
from . import tb_locator

wb_path = os.path.dirname(tb_locator.__file__)


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
                                   'resources/icons/rbt_createRobot.svg'),
            # 'Accel': "F11",
            'MenuText': "Define Robot",
            'ToolTip': "<b>Define a Robot from CAD elements</b>"
                }

    def Activated(self):
        """Activated."""
        from freecad.Robot_tools.Gui import taskpanel_rbt_creator
        taskpanel_rbt_creator.run()

    def IsActive(self):
        """IsActive."""
        return not Gui.Control.activeDialog()


class rbt_cmd5:
    def GetResources(self):
        return {"Pixmap":   os.path.join(wb_path,
                                         'resources/icons/rbt_defineTool.svg'),
                "MenuText": "Define Tool",
                "ToolTip":  "Define a Tool and TCP on the active robot"}

    def IsActive(self):
        doc = App.ActiveDocument
        return bool(doc) and any(hasattr(o, "Robot_joints")
                                 for o in doc.Objects)

    def Activated(self):
        from freecad.Robot_tools.Gui import define_tool
        define_tool.run()


Gui.addCommand('RBT_anrob', rbt_cmd3())
Gui.addCommand('RBT_defrob', rbt_cmd4())
Gui.addCommand('RBT_deftool', rbt_cmd5())
