"""vp_rbt_tool.py — View Provider for Tool & TCP."""
__version__ = "0.01"

# import math
from pivy import coin
import FreeCAD as App
import FreeCADGui as Gui
import UtilsAssembly

fcl_msg = App.Console.PrintMessage
fcl_err = App.Console.PrintError


class ViewProviderTool:
    def __init__(self, vobj):
        vobj.Proxy = self

    # bypass freeCAD's proxy state saving

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def attach(self, vobj):
        self.vobj = vobj
        self.Object = vobj.Object

        self.tx = coin.SoTransform()
        self.axes = self.cm_axes()

        root = coin.SoSeparator()
        root.addChild(self.tx)
        root.addChild(self.axes.Node)

        vobj.addDisplayMode(root, "Standard")
        self.refresh_tx(vobj.Object)

    def claimChildren(self):
        """
        joins the tool CAD as a sub-child in the tree
        """
        obj = self.Object
        return ([obj.Tool_shape]
                if getattr(obj, "Tool_shape", None)
                else [])

    def doubleClicked(self, vobj):
        from freecad.Robot_tools.Gui.define_tool import tool_parent, DefineTCP
        # Find the robot that owns this tool.
        robot = tool_parent(vobj.Object)
        if robot is None:
            fcl_err("No parent robot obj found for selected tool")
            return True

        Gui.Control.showDialog(DefineTCP(robot, tool=vobj.Object))
        return True

    def setEdit(self, vobj, mode=0):
        return self.doubleClicked(vobj)

    def unsetEdit(self, vobj, mode=0):
        Gui.Control.closeDialog()
        return True

    def cm_axes(self):
        """
        Freecad's built in axes triad
        """
        axes = Gui.AxisOrigin()
        axes.AxisLength = 6
        axes.Scale = 1
        return axes

    def cm_dragger(self):
        """
        Draggable axes triad based on legacy roboWB
        """
        pass

    def updateData(self, fp, prop):
        # TODO
        # "TCP_offset", "Tool_offset", "Flange_link"
        if prop in ("TCP_placement"):
            self.refresh_tx(fp)

    def refresh_tx(self, fp):
        """
        update self.tx from curr TCP placement
        """
        if self.tx is None:
            return
        w = getattr(fp, "TCP_placement", None)
        if w is None:
            return
        q = w.Rotation.Q
        self.tx.translation = (w.Base.x, w.Base.y, w.Base.z)
        self.tx.rotation = (q[0], q[1], q[2], q[3])

    def getDisplayModes(self, vobj):
        # TODO: CHECK WHAT THIS FUNCTION IS DOING
        # AND ADD DOCSTRING
        return ["Standard"]

    def getDefaultDisplayMode(self):
        # TODO: CHECK WHAT THIS FUNCTION IS DOING
        # AND ADD DOCSTRING
        return "Standard"

    def getIcon(self):
        import os
        from freecad.Robot_tools import tb_locator
        wb_path = os.path.dirname(tb_locator.__file__)
        return os.path.join(wb_path,
                            "resources/icons/rbt_defineTool.svg")

    # -- event slots --
    def _on_drag(self, dragger, *_):
        """
        # todo -
        reads dragger.trans/rot, gets IK, changes joint angles
        gets called from rbt_kine.ik()
        """
        pass
