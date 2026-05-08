"""Robot Objects.

Name: rbt_objects.py

See Changelog below.

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence: LGPL 2.1
"""
__version__ = "0.03"
__build__ = "20260508_1337"

import FreeCADGui as Gui
import FreeCAD as App

# Coin3d import
from pivy import coin

"""
----------------------------------------
Changelog:
----------------------------------------
v0.01 - Initial version.
v0.02 - Added the STEPFile property.
"""

fcl_err = App.Console.PrintError
fcl_msg = App.Console.PrintMessage
fcl_warn = App.Console.PrintWarning

# ------------------------------------------------
#                   Robot Objects
# ------------------------------------------------


class Robot_obj:
    def __init__(self, obj):
        '''Add some custom properties to our box feature'''
        obj.addProperty(
            "App::PropertyLink", "Robot_assembly", "Robot", "Robot_assembly")
        obj.addProperty(
            "App::PropertyLinkListGlobal", "Robot_joints", "Robot", "Robot joints list")
        obj.addProperty(
            "App::PropertyPlacementList", "Robot_links", "Robot", "Robot link lists")
        obj.addProperty(
            "App::PropertyIntegerList", "Robot_joints_dir", "Robot",
            "Robot joints direction")
        obj.addProperty(
            "App::PropertyLinkListGlobal", "Tools_joints", "Tools", "Tools joints list")
        # TODO: this is useful in case of unfinished editing
        obj.addProperty(
            "App::PropertyFile", "STEPFile", "General",
            "File from where elements have been loaded.")
        # Added a Version property
        obj.addProperty(
            "App::PropertyString", "Version", "Base",
            "Object version")
        obj.Version = "0.01"

        obj.addProperty(
            "App::PropertyFloatList", "Robot_home_pos", "Robot",
            "Robot home position angles")

        obj.Proxy = self

    def _migrate_from_001(self, obj):
        """Migrate from version 0.01"""
        fcl_msg("Migrating FPO to v0.02\n")  # DBG

    def _migrate_from_002(self, obj):
        """Migrate from version 0.02"""
        fcl_msg("Migrating FPO to v0.03\n")  # DBG

    def onChanged(self, fp, prop):
        '''Do something when a property has changed'''
        fcl_msg("Change property: " + str(prop) + "\n")

    def onDocumentRestored(self, obj):
        if hasattr(obj, "Version") and obj.Version:
            fcl_msg("FPO version check\n")  # DBG
            if obj.Version == "0.01":
                fcl_msg("FPO is already at v0.01\n")  # DBG
                pass  # do nothing
            if obj.Version == "0.02":
                self._migrate_from_001(obj)
            elif obj.Version == "0.03":
                self._migrate_from_002(obj)
        else:
            fcl_msg("FPO has no version bumping to v0.01\n")  # DBG
            obj.addProperty(
                "App::PropertyString", "Version", "Base",
                "Object version")
            obj.Version = "0.01"

            if not hasattr(obj, "Robot_home_pos"):
                obj.addProperty(
                    "App::PropertyFloatList", "Robot_home_pos", "Robot",
                    "Robot home position angles")

    def execute(self, fp):
        '''Do something when doing a recomputation, this method is mandatory'''
        fcl_msg("Execute reached\n")  # DBG
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
        If a property of the handled feature has changed.
          we have the chance to handle this here
        """
        return

    def getDisplayModes(self, obj):
        """
        Return a list of display modes.
        """
        return ["Standard"]

    def getDefaultDisplayMode(self):
        """
        Return the name of the default display mode.
          It must be defined in getDisplayModes.
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
