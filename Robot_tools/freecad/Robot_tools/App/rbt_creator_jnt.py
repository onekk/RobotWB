"""
Joint creation handling for new robot creation
Current Support: Revolue Jnts, Base Jnt
"""

import JointObject   # type: ignore
import UtilsAssembly  # type: ignore

from freecad.Robot_tools.App.rbt_creator_geom import find_center
from freecad.Robot_tools.App.rbt_kine_types import JOINT_TYPES
from freecad.Robot_tools.App.rbt_global_constants import GROUNDED_JOINT_NAME


def add_joint(asm, jtype, refs, label=""):
    """
    Create a new joint in the assembly & return it
    refs are the objects that make up the joint
    refs = [(obj, elem_ref), ...]
    """
    jg = UtilsAssembly.getJointGroup(asm)
    if jtype == "grounded":
        j = jg.newObject("App::FeaturePython", GROUNDED_JOINT_NAME)
        JointObject.GroundedJoint(j, refs[0][0])
        JointObject.ViewProviderGroundedJoint(j.ViewObject)
        asm.Document.recompute()
        return j

    # other joint types:
    j = jg.newObject("App::FeaturePython", "Joint")
    j.Label2 = label
    proxy = JointObject.Joint(j, JOINT_TYPES[jtype])
    JointObject.ViewProviderJoint(j.ViewObject)
    (o1, r1), (o2, r2) = refs[0], refs[1]
    j.Reference1 = find_center(o1, r1, jtype)
    j.Reference2 = find_center(o2, r2, jtype)
    proxy.preSolve(j, savePlc=False)
    # proxy.matchJCS(j, savePlc=False, reverse=proxy.areJcsSameDir(j))
    asm.Document.recompute()
    return j
