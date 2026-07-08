"""
rbt_frames.py
jogging and reference frame model for robot wb
"""

from enum import Enum

import FreeCAD as App  # type: ignore


class JogFrame(str, Enum):
    """
    Frame types the TCP can be jogged in
    """

    WORLD = "World"
    TOOL = "Tool"
    # USER = "User"

    @classmethod
    def names(cls):
        """
        values list for App::PropertyEnumeration
        """
        return [f.value for f in cls]


def apply_jog_frames(tool_fp):
    """
    mirror the available jog_frames list into
    TCP_drag_frame's selection dropdown
    """
    tool_fp.TCP_drag_frame = tool_fp.Jog_frames or JogFrame.names()


def jog_rotation(tool_fp) -> App.Rotation:
    """
    World rotation of the tool's active jog frame
    Keeps drag gizmo and rotation constraints in sync
    """
    frame = getattr(tool_fp, "TCP_drag_frame", JogFrame.TOOL)
    if frame == JogFrame.TOOL:
        return tool_fp.TCP_placement.Rotation

    # TODO: add user frames

    return App.Rotation()  # Identity default for JogFrame.WORLD
