"""Robot FreeCAD Python Object

Name: rbt_robot.py

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence: LGPL 2.1
"""

import FreeCAD as App  # type: ignore

from freecad.Robot_tools.App.rbt_kine import invalidate
from freecad.Robot_tools.App.rbt_constants import DEFAULT_KIN_LIB


# ------------------------------------------------
#                   Robot Objects
# ------------------------------------------------


class Robot:
    def __init__(self, obj):
        '''Add some custom properties to our box feature'''
        obj.addProperty(
            "App::PropertyLinkGlobal",
            "Robot_assembly",
            "Robot",
            "Robot_assembly")

        obj.addProperty(
            "App::PropertyLinkListGlobal",
            "Robot_joints",
            "Robot",
            "Robot joints list")

        obj.addProperty(
            "App::PropertyPlacementList",
            "Robot_links",
            "Robot",
            "Robot link lists")

        obj.addProperty(
            "App::PropertyIntegerList", "Robot_joints_dir", "Robot",
            "Robot joints direction CW/CCW")

        obj.addProperty(
            "App::PropertyLinkListGlobal",
            "Tools",
            "Tools",
            "Tool FPOs attached to the robot")

        obj.addProperty(
           "App::PropertyLinkGlobal",
           "Active_tool",
           "Tools",
           "Currently active tool")

        # TODO: this is useful in case of unfinished editing
        obj.addProperty(
            "App::PropertyFile", "STEPFile", "General",
            "File from where elements have been loaded.")

        obj.addProperty(
            "App::PropertyFloatList", "Robot_home_pos", "Robot",
            "Robot home position angles")

        obj.addProperty(
            "App::PropertyEnumeration", "Kinematics_lib", "Kinematics",
            "Solver to use for FK/IK")
        # add more in future
        obj.Kinematics_lib = ["pinocchio", "tesseract", "ikpy", "numpy_dls"]
        obj.Kinematics_lib = DEFAULT_KIN_LIB

        obj.Proxy = self

    def onChanged(self, fp, prop):
        '''Do something when a property has changed'''
        if prop in ("Robot_joints", "Robot_joints_dir",
                    "Active_tool", "Kinematics_lib"):
            try:
                invalidate(fp)
            except Exception:
                pass

    def onDocumentRestored(self, obj):
        # when restoring the document, create a default tool
        # if no active tool is found. TODO: Check if this is
        # really necessary or not
        if (App.GuiUp and obj.Robot_joints
                and obj.Active_tool is None):

            from PySide.QtCore import QTimer  # type: ignore

            def _mk(o=obj):
                if getattr(o, "Active_tool", None) is None:

                    from freecad.Robot_tools.Gui.taskpanel_rbt_tool \
                        import create_default_tool

                    create_default_tool(o, name="Default_Tool")

            QTimer.singleShot(0, _mk)

        # -------------------------------------------------
        #   add missing props for back compatability
        # -------------------------------------------------

        if not hasattr(obj, "Robot_home_pos"):
            obj.addProperty(
                "App::PropertyFloatList", "Robot_home_pos", "Robot",
                "Robot home position angles")
        if not hasattr(obj, "Tools"):
            obj.addProperty(
                "App::PropertyLinkList", "Tools", "Tools",
                "Tool FPOs attached to the robot")
        if not hasattr(obj, "Active_tool"):
            obj.addProperty(
                "App::PropertyLink", "Active_tool", "Tools",
                "Currently active tool")
        if not hasattr(obj, "Kinematics_lib"):
            obj.addProperty(
                "App::PropertyEnumeration", "Kinematics_lib", "Kinematics",
                "Solver to use for FK/IK")
            obj.Kinematics_lib = ["pinocchio", "tesseract",
                                  "ikpy", "numpy_dls"]
            obj.Kinematics_lib = DEFAULT_KIN_LIB
        elif hasattr(obj, "Kinematics_lib") and (len(obj.Kinematics_lib) < 4):
            obj.Kinematics_lib = ["pinocchio", "tesseract",
                                  "ikpy", "numpy_dls"]
            obj.Kinematics_lib = DEFAULT_KIN_LIB

        if not hasattr(obj, "Robot_joints_dir"):
            obj.addProperty(
                "App::PropertyIntegerList", "Robot_joints_dir",
                "Robot", "Robot joints direction CW/CCW"
            )

        n = len(obj.Robot_joints or [])
        raw_dirs = (obj.Robot_joints_dir or [])[:n]
        dirs = [(-1 if d < 0 else 1) for d in raw_dirs]
        dirs += [1] * (n - len(dirs))
        if dirs != list(raw_dirs):
            obj.Robot_joints_dir = dirs

    def execute(self, fp):
        '''Do something when doing a recomputation, this method is mandatory'''

        pass
