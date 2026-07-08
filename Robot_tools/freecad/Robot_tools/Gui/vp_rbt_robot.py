"""
vp_rbt_robot.py - view provider for Robot FreeCAD python object (FPO)
"""

from pivy import coin  # type: ignore


class ViewProviderRobot:

    def __init__(self, obj):
        """
        Set this object to the proxy object of the actual view provider
        """
        obj.Proxy = self

    def attach(self, obj):
        """
        Setup the scene sub-graph of the view provider,
        this method is mandatory
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

    def claimChildren(self):
        """
        populates the sub-elements (links, tools etc)
        under the robot fpo
        """
        obj = self.Object
        kids = []
        if getattr(obj, "Robot_assembly", None):
            kids.append(obj.Robot_assembly)
        kids.extend(getattr(obj, "Tools", []) or [])
        return kids

    def onChanged(self, vp, prop):
        """

        """
        pass

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
