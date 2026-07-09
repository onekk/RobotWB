"""
Assembly document handling for creation of new robot
Builds the Robot_Assembly & links part instances to it
"""

import FreeCAD as App  # type: ignore
import UtilsAssembly   # type: ignore

from freecad.Robot_tools.App.rbt_global_constants import (
    ROBOT_ASSEMBLY_LABEL, ROBOT_FPO_NAME, GROUNDED_JOINT_NAME
)


def create_assembly(doc):
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    asm.Label = ROBOT_ASSEMBLY_LABEL
    asm.Type = "Assembly"
    asm.newObject("Assembly::JointGroup", "Joints")
    asm.recompute()
    return asm


def add_asm_object(obj_doc, asm, feat_nm, link_nm, glbl):
    """
    Adds objects/links to assembly document
    - Inputs:
      - obj_doc: Document containinng the part to be added
      - asm: Assembly instance where the part has to be added
      - feat_nm: Name of the object in obj_doc
      - link_nm: Name of the new link being created
    """
    item = asm.newObject("App::Link", link_nm)
    item.LinkedObject = obj_doc.getObject(feat_nm)
    item.Label = glbl
    item.recompute()
    asm.recompute()
    return item


def resolve_asm_ref(asm_doc):
    """Resolve the robot assembly for the given document."""

    fpos = asm_doc.getObjectsByLabel(ROBOT_FPO_NAME)
    fpo = fpos[0] if len(fpos) == 1 else None

    # try preferred sources
    candidates = [
        ("fpo", getattr(fpo, "Robot_assembly", None)),
        ("active", UtilsAssembly.activeAssembly()),
    ]

    # first valid match wins
    for source, asm in candidates:
        if asm and asm.Document is asm_doc:
            return asm, fpo, source

    # fallback: search by label
    objs = find_assemblies(asm_doc)

    # unique match only
    if len(objs) == 1:
        return objs[0], fpo, "label"

    # nothing found
    return None, fpo, "none"


def find_assemblies(doc):
    """
    All Robot_Assembly objects in doc
    """
    return [obj for obj in
            doc.getObjectsByLabel(ROBOT_ASSEMBLY_LABEL)
            if obj.isDerivedFrom("Assembly::AssemblyObject")]
