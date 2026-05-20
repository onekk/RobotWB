"""rbt_tool.py — Tool / TCP document object."""
__version__ = "0.01"

import FreeCAD as App
import UtilsAssembly
fcl_msg = App.Console.PrintMessage

TOOL_SCHEMA = [
    ("Tool_shape", "App::PropertyLinkGlobal", "Tool", "(optional) CAD for the tool"),
    ("Tool_offset", "App::PropertyPlacement", "Tool", "Flange -> tool body"),
    ("TCP_offset", "App::PropertyPlacement", "Tool", "Tool body -> TCP"),
    ("TCP_placement", "App::PropertyPlacement", "Tool", "(read only) world TCP"),
    ("Tool_mass", "App::PropertyFloat", "Tool", "kg"),
    ("Flange_link", "App::PropertyLinkSubGlobal", "Tool",
        "Face on the Robot where tool's flange mates"),
    ("Tool_flange_link", "App::PropertyLinkSubGlobal", "Tool",
        "Face on the tool that mates to robot's flange"),
    ("TCP_link",   "App::PropertyLinkSubGlobal", "Tool",
        "Reference on tool geom that defines TCP location"),
    ("Source_file", "App::PropertyFile", "Tool", "Tool CAD's .fcstd path")
]


class Tool:
    def __init__(self, obj):
        self.add_properties(obj)
        obj.Proxy = self

    def onDocumentRestored(self, fp):
        self.migrate_flange_link(fp)
        self.add_properties(fp)

    def add_properties(self, fp):
        existing = set(fp.PropertiesList)
        for name, typ, group, doc in TOOL_SCHEMA:
            if name not in existing:
                fp.addProperty(typ, name, group, doc)

    def onChanged(self, fp, prop):
        fcl_msg(f"Tool change: {prop}\n")

    def execute(self, fp):
        """recompute tcp placement & tool body shape"""
        from freecad.Robot_tools.rbt_helpers_math import flip_z_dir

        rob_flange_ref = fp.Flange_link
        if not rob_flange_ref or not rob_flange_ref[0]:
            return

        rob_flange = (UtilsAssembly.getGlobalPlacement(rob_flange_ref)*
                      UtilsAssembly.findPlacement(rob_flange_ref))

        tool_flange_ref = fp.Tool_flange_link
        has_tool = (tool_flange_ref 
                    and tool_flange_ref[0]
                    and fp.Tool_shape)

        if has_tool:
            # when we have tool geom, attach it to rob
            tool_flange_local = UtilsAssembly.findPlacement(tool_flange_ref)

            # add tool flange face antiparallel to rob flange
            tool_shape_placement = (flip_z_dir(rob_flange)
                                    .multiply(fp.Tool_offset)
                                    .multiply(tool_flange_local.inverse()))
            fp.Tool_shape.Placement = tool_shape_placement
            # seated_flange = tool_shape_placement.multiply(tool_flange_local)

            tcp_ref = fp.TCP_link
            tcp_local = UtilsAssembly.findPlacement(
                tcp_ref) if (tcp_ref and tcp_ref[0]) else App.Placement()

            # TCP placement relative to tool body
            fp.TCP_placement = (fp.Tool_shape.Placement
                                .multiply(tcp_local)
                                .multiply(fp.TCP_offset))
        else:
            # TCP placement relative to robot's flange
            fp.TCP_placement = (rob_flange
                                .multiply(fp.Tool_offset)
                                .multiply(fp.TCP_offset))

    def migrate_flange_link(self, fp):
        if "Flange_link" not in fp.PropertiesList:
            return
        if fp.getTypeIdOfProperty(
                "Flange_link") == "App::PropertyLinkSubGlobal":
            return
        old = fp.Flange_link
        fp.removeProperty("Flange_link")
        fp.addProperty("App::PropertyLinkSubGlobal", "Flange_link", "Tool",
                       "Face on the Robot where tool's flange mates")
        if old is not None:
            #  user must re-pick
            fp.Flange_link = (old, [""])


# --------------------------
#         helpers
# --------------------------
def is_tool_fpo(obj):
    """
    True when obj is of the type "Tool"
    ie. it has tool flange and tcp link
    """
    return hasattr(obj, "Tool_flange_link") and hasattr(obj, "TCP_link")


def has_valid_shape(obj):
    """
    True when obj has non null shape 
    with selectable faces
    """
    return (hasattr(obj, "Shape")
            and obj.Shape
            and bool(obj.Shape.Faces))
