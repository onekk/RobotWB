"""Robot Tools - create_robot.

Name: create_robot_obj.

See Changelog after import statements.

Author: Carlo Dormeletti
Copyright: 2026
Licence: All right reserved
"""
__version__ = "0.03"
__build__ = "20260409_1154"

import FreeCAD as App
import FreeCADGui as Gui

# Assembly imports
import UtilsAssembly
import JointObject

from pivy import coin

from PySide import QtGui, QtCore  # noqa  # QtWidgets
from PySide.QtWidgets import (  # noqa
    QApplication, QCheckBox, QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox,
    QTextEdit,  # Widgets
    QDialog, QFileDialog, QInputDialog, QMessageBox,  # Dialogs
    QGridLayout, QVBoxLayout)  # Layouts

from PySide.QtCore import QObject, Qt  # noqa

"""
----------------------------------------
Changelog:
----------------------------------------
v0.03 - added some properties
"""

fcl_err = App.Console.PrintError
fcl_msg = App.Console.PrintMessage
fcl_warn = App.Console.PrintWarning

ap_clr = {
    "Black": [(0.0, 0.0, 0.0), "#000000"],
    "Grey75": [(0.25, 0.25, 0.25), "#404040"],
    "White": [(1.0, 1.0, 1.0), "#FFFFFF"],
    # Vibrant
    "V_Blue": [(0.0, 0.467, 0.733), "#0077BB"],
    "V_Cyan": [(0.20, 0.733, 0.933), "#33BBEE"],
    "V_Teal": [(0.0, 0.6, 0.533), "#009988"],
    "V_Orange": [(0.933, 0.467, 0.2), "#EE7733"],
    "V_Red": [(0.8, 0.2, 0.67), "#CC3311"],
    "V_Magenta": [(0.933, 0.2, 0.467), "#EE3377"],
    "V_Grey": [(0.733, 0.733, 0.733), "#BBBBBB"],
    # Bright
    "B_Blue": [(0.267, 0.467, 0.667), "#4477AA"],
    "B_Cyan": [(0.4, 0.8, 0.933), "#66CCEE"],
    "B_Green": [(0.133, 0.533, 0.200), "#228833"],
    "B_Yellow": [(0.8, 0.733, 0.267), "#CCBB44"],
    "B_Red": [(0.933, 0.4, 0.467), "#EE6677"],
    "B_Purple": [(0.667, 0.2, 0.467), "#AA3377"],
    # High Contrast
    "HC_Yellow": [(0.867, 0.667, 0.2), "#DDAA33"],
    "HC_Red": [(0.733, 0.333, 0.4), "#BB5566"],
    "HC_Blue": [(0.0, 0.267, 0.533), "#004488"],
    # Additional
    "Aqua": [(0.0, 1.0, 1.0), "#00FFFF"],
    "Orange": [(1.0, 0.647, 0.0), "#FFA500"],
}


# ------------------------------------------------
#                  General Service
# ------------------------------------------------


def set_txt_color(txt, col):
    """Set text color using html syntax."""
    if col == "o":
        f_clr = ap_clr['B_Green'][1]
    elif col == "w":
        f_clr = ap_clr['Orange'][1]
    elif col == "e":
        f_clr = ap_clr['B_Red'][1]
    else:
        f_clr = "black"

    return f"<span style='color: {f_clr}'> {txt} </span>"


# ------------------------------------------------
#                   UI functions
# ------------------------------------------------


def msg_box(parent, title, fnt, msg, icon="", head="", hc=""):
    """Create a minimal message box."""
    msg_box = QMessageBox(parent)
    msg_box.setFont(fnt)
    msg_box.setWindowTitle(title)

    if icon == "e":
        m_icon = QMessageBox.Icon.Critical
    elif icon == "w":
        m_icon = QMessageBox.Icon.Warning
    elif icon == "i":
        m_icon = QMessageBox.Icon.Information
    else:
        m_icon = QMessageBox.Icon.NoIcon

    msg_box.setIcon(m_icon)
    if head != "":
        s_msg = f"{set_txt_color(head, hc)}<br><br>" + msg
    else:
        s_msg = msg

    msg_box.setText(s_msg)

    msg_box.exec()


# ------------------------------------------------
#                   Robot Objects
# ------------------------------------------------


class Robot_obj:
    def __init__(self, obj, robot, axis):
        '''Add some custom properties to our box feature'''
        obj.addProperty("App::PropertyLink", "Robot_assembly", "Robot", "Robot_assembly")
        obj.Robot_assembly = robot
        obj.addProperty(
            "App::PropertyLinkListGlobal", "Robot_joints", "Robot", "Robot joints list")
        obj.addProperty(
            "App::PropertyPlacementList", "Robot_links", "Robot", "Robot link lists")
        obj.addProperty(
            "App::PropertyIntegerList", "Robot_joints_dir", "Robot", "Robot joints direction")
        obj.addProperty(
            "App::PropertyLinkListGlobal", "Tools_joints", "Tools", "Tools joints list")
        obj.Proxy = self

    def onChanged(self, fp, prop):
        '''Do something when a property has changed'''
        fcl_msg("Change property: " + str(prop) + "\n")

    def execute(self, fp):
        '''Do something when doing a recomputation, this method is mandatory'''
        fcl_msg("Execute reached\n")
        #
        fp.recompute()


class ViewProviderRBo:

    def __init__(self, obj):
        """
        Set this object to the proxy object of the actual view provider
        """

        obj.Proxy = self

    def attach(self, obj):
        """
        Setup the scene sub-graph of the view provider, this method is mandatory
        """
        self.ViewObject = obj
        self.Object = obj.Object
        self.standard = coin.SoGroup()
        obj.addDisplayMode(self.standard, "Standard")
        return

    def updateData(self, fp, prop):
        """
        If a property of the handled feature has changed we have the chance to handle this here
        """
        return

    def getDisplayModes(self, obj):
        """
        Return a list of display modes.
        """
        return ["Standard"]

    def getDefaultDisplayMode(self):
        """
        Return the name of the default display mode. It must be defined in getDisplayModes.
        """
        return "Standard"

    def onChanged(self, vp, prop):
        """
        Print the name of the property that has changed
        """

        App.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def dumps(self):
        """
        Called during document saving.
        """
        return None

    def loads(self, state):
        """
        Called during document restore.
        """
        return None


def run():
    """Create Robot Object."""
    fnt = QApplication.font("QMessageBox")
    parent = Gui.getMainWindow()
    fcl_msg("Create robot Object reached.\n")  # DBG
    if App.listDocuments() == {}:
        msg_box(
                parent, "Robot Tools", fnt,
                "<b>Create Robot</b><br><br>No document open.")
    else:
        if App.ActiveDocument is not None:
            doc = App.ActiveDocument
            fcl_msg(f"Document: {doc.Name}\n")
            rb_obj = doc.addObject(
                "App::FeaturePython", "Robot_FPO")
            Robot_obj(rb_obj, None, 6)
            if App.GuiUp:
                ViewProviderRBo(rb_obj.ViewObject)

            rb_obj.recompute()
            doc.recompute()
            # TODO: Ask users some data?


# Executed if not imported as module


if __name__ == "__main__":
    run()
