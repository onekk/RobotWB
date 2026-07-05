"""
rbt_kine.py
kinematics module for robot wb
"""

from __future__ import annotations

import traceback
from typing import Dict, List, Optional, Tuple, Type, TypeAlias

import FreeCAD as App  # type: ignore

from freecad.Robot_tools.App.rbt_kine_types import ChainSpec
from freecad.Robot_tools.App.rbt_kine_chain import (
    extract_chain, joint_dirs, doc_limits_deg)
from freecad.Robot_tools.rbt_helpers_math import deg_to_rad, rad_to_deg
from freecad.Robot_tools.backends.base import KinematicsBackend

Placement: TypeAlias = App.Placement
Chain: TypeAlias = ChainSpec

fcl_err = App.Console.PrintError
fcl_warn = App.Console.PrintWarning
fcl_msg = App.Console.PrintMessage

# backend instance : (robot.Name, backend library)
cache: Dict[Tuple[str, str], KinematicsBackend] = {}

# chain cache
chain_cache: Dict[Tuple[str, str], Chain] = {}


# register kinematics backend
def backend_lib(name: str) -> Type[KinematicsBackend]:
    if name == "pinocchio":
        from freecad.Robot_tools.backends.pinocchio import PinocchioBackend
        return PinocchioBackend
    elif name == "tesseract":
        from freecad.Robot_tools.backends.tesseract import TesseractBackend
        return TesseractBackend
    elif name == "ikpy":
        from freecad.Robot_tools.backends.numpy_dls import NumpyDLSBackend
        return NumpyDLSBackend
        # from freecad.Robot_tools.backends.ikpy import IkpyBackend
        # return IkpyBackend
    elif name == "numpy_dls":
        from freecad.Robot_tools.backends.numpy_dls import NumpyDLSBackend
        return NumpyDLSBackend

    # add others

    else:
        raise ValueError(f"unknown kinematics lib: {name}")


def extract_chain_at_zeropos(rbt_obj: "App.DocumentObject"):
    """
        Run extract_chain with every joint forced to q=0
    """
    joints = list(rbt_obj.Robot_joints or [])
    saved = [App.Placement(j.Offset2) for j in joints]  # cache for reset
    try:
        for j in joints:
            j.Offset2 = App.Placement()  # set q=0

        recompute_asm(rbt_obj)
        recompute_tool(rbt_obj)

        return extract_chain(rbt_obj)

    except Exception as e:
        fcl_err(f"Unable to set robot to neutral Q=0 pos: {e}")

    finally:
        for j, plc in zip(joints, saved):
            j.Offset2 = plc  # reset back to original vals

        recompute_asm(rbt_obj)
        recompute_tool(rbt_obj)


def recompute_asm(rbt_obj: "App.DocumentObject") -> None:
    """
        Recomputes robot assembly
    """
    asm = getattr(rbt_obj, "Robot_assembly", None)
    if asm is not None:
        try:
            asm.recompute()
        except Exception as e:
            fcl_err(f"Unable to recompute assembly: {e}")
    else:
        fcl_err("Unable to find attr <Robot_assembly>")


def recompute_tool(rbt_obj: "App.DocumentObject") -> None:
    """
        Recomputes tool object
    """
    tool = getattr(rbt_obj, "Active_tool", None)
    if tool is not None:
        try:
            tool.recompute()
        except Exception as e:
            fcl_err(f"Unable to recompute tool: {e}")
    else:
        fcl_err("Unable to find attr <Active_tool>")


def backend_name(rbt_obj: "App.DocumentObject") -> str:
    return getattr(rbt_obj, "Kinematics_lib", "pinocchio")


def get_backend(rbt_obj: "App.DocumentObject",
                ) -> Optional[KinematicsBackend]:
    """
    Returns the current backend selected for robot object.\n
    If no active B.E exists, it selects one and caches the value.\n
    Inputs:
        - rbt_obj: Robot FC Object
    """
    name = backend_name(rbt_obj)
    key: Tuple[str, str] = (rbt_obj.Name, name)

    # return existing from cache
    if key in cache:
        return cache[key]

    # if no cached BE exists, init new instance & cachce it

    # extract robot kinematic chain at all neutral angles (q=0)
    chain = extract_chain_at_zeropos(rbt_obj)
    if chain is None:
        fcl_err("Cant extract robot kinematics info")
        return None

    # create new backend instance
    def load_lib(lib_name: str):
        lib = backend_lib(lib_name)
        be = lib()
        be.load(chain)
        return be

    # create new backend instance
    # try to load user selection, fallback to ikpy
    libs = [name] if name == "ikpy" else [name, "ikpy"]
    be = None
    for lib in libs:
        try:
            be = load_lib(lib)
            break
        except ImportError:
            fcl_warn(f"Kin Lib '{lib}' is not available.\n")
        except Exception as e:
            fcl_err(f"Failed to load '{lib}': {e}\n")
            return None

    if be is None:
        return None

    # update the UI if we used fallback
    if lib != name:
        try:
            rbt_obj.Kinematics_lib = lib
        except Exception:
            fcl_warn("Unable to update current lib name.\n")

        name = lib

    # cache for future reuse & return
    key = (rbt_obj.Name, name)
    cache[key] = be
    chain_cache[key] = chain
    return be


def invalidate(rbt_obj: "App.DocumentObject") -> None:
    """
        Removes current backend from cache.
        Inputs:
            - rbt_obj: Robot FC Object
    """
    try:
        name = backend_name(rbt_obj)
        cache.pop((rbt_obj.Name, name), None)
        chain_cache.pop((rbt_obj.Name, name), None)
    except Exception as e:
        fcl_err(f"Failed to clear kinematics lib from cache: {e}\n")
        fcl_err(traceback.format_exc())


def current_q_deg(rbt_obj: "App.DocumentObject") -> List[float]:
    """
        Canonical URDF style joint angles
        q = direction * FC Offset2 based yaw
    """
    out: List[float] = []
    for d, j in zip(joint_dirs(rbt_obj), rbt_obj.Robot_joints):
        # offset2 has curr rotation. Z component is what
        # AnimationController writes via Rotation(angle, 0, 0)
        # toEuler() returns (yaw, pitch, roll) in deg
        # TODO: FIX toEuler warp angles to +-180deg
        yaw, _, _ = j.Offset2.Rotation.toEuler()
        out.append(d * float(yaw))
    return out


def set_q_deg(rbt_obj, j_idx: int, q: float) -> None:
    """
    canonical urdf style angle q
    fc's yaw = dir * q
    or canonical q = dir * yaw
    As dir is +-1, above equations are same
    """
    d = joint_dirs(rbt_obj)[j_idx]
    joint = rbt_obj.Robot_joints[j_idx]
    joint.Offset2 = App.Placement(App.Vector(),
                                  App.Rotation(d*q, 0, 0))
    joint.recompute()
    tool = getattr(rbt_obj, "Active_tool", None)
    if tool:
        tool.recompute()


def joint_limits_q_deg(rbt_obj, j_idx: int):
    """
    q-space limits, considering direction into account
    """
    low, high = doc_limits_deg(rbt_obj.Robot_joints[j_idx])
    if joint_dirs(rbt_obj)[j_idx] == -1:
        low, high = -high, -low
    return low, high


def save_home(rbt_obj) -> None:
    """Robot_home_pos in FC yaw convention"""
    rbt_obj.Robot_home_pos = [float(j.Offset2.Rotation.toEuler()[0])
                              for j in rbt_obj.Robot_joints]


def home_q_deg(rbt_obj) -> List[float]:
    """q_home = dir * stored yaw home pos"""
    return [d * float(y) for d, y in zip(joint_dirs(rbt_obj),
                                         rbt_obj.Robot_home_pos or [])]


def get_chain(rbt_obj):
    """
    returns the robot kinematic chain
    """
    key = (rbt_obj.Name, backend_name(rbt_obj))
    if key not in chain_cache:
        get_backend(rbt_obj)  # builds & caches
    return chain_cache.get(key)


def apply_joint_angles(rbt_obj, q_deg):
    """
    Use fk to position the parts
    q_deg is in urdf style q convention
    """
    chain = get_chain(rbt_obj)
    if chain is None:
        return

    doc = rbt_obj.Document
    F = App.Placement(chain.base_world)
    for i, joint in enumerate(chain.joints):
        # forward pass transpose
        F = F.multiply(joint.parent_to_joint)

        if joint.type == "revolute":
            F = F.multiply(App.Placement(App.Vector(),
                                         App.Rotation(joint.axis, q_deg[i])))

        # apply joint to part offset
        part = doc.getObject(chain.links[i+1].name)
        off = chain.links[i+1].joint_to_part

        if part is not None and off is not None:
            part.Placement = F.multiply(off)
            part.purgeTouched()  # prevent assm recompute

    tool = getattr(rbt_obj, "Active_tool", None)
    if tool is not None:
        tool.TCP_placement = F.multiply(chain.flange_local)
        # tool.recompute()


def resolve_offsets(rbt_obj, q_deg):
    """
    write robot pose into offset2 using assembly solver
    """
    if q_deg is None:
        return
    prefs = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly")
    prev = prefs.GetBool("SolveInJointCreation", True)
    prefs.SetBool("SolveInJointCreation", False)  # avoid calculation at start
    try:
        dirs = joint_dirs(rbt_obj)
        for i, joint in enumerate(rbt_obj.Robot_joints):
            joint.Offset2 = App.Placement(App.Vector(),
                                          App.Rotation(dirs[i]*q_deg[i], 0, 0))
    finally:
        prefs.SetBool("SolveInJointCreation", prev)  # reset to original val

    recompute_asm(rbt_obj)
    recompute_tool(rbt_obj)


def fk(
        rbt_obj: "App.DocumentObject",
        q_deg: Optional[List[float]] = None
        ) -> Optional[Placement]:
    """
        Runs a fwd kinematics pass on current joint angles
        and returns the placement of the TCP.
        Input:
            rbt_obj: Robot FC Object
            q_deg  : Current robot joint angles
    """
    be = get_backend(rbt_obj)
    if be is None:
        return None
    if q_deg is None:
        q_deg = current_q_deg(rbt_obj)
    q_rad: List[float] = [deg_to_rad(v) for v in q_deg]
    try:
        return be.fk(q_rad)
    except Exception as e:
        fcl_err(f"FK failed: {e}")
        return None


def ik(
        rbt_obj: "App.DocumentObject",
        target: Placement,
        q_seed_deg: Optional[List[float]] = None,
        pos_tol_mm: float = 0.01,
        rot_tol_deg: float = 0.5,
        ) -> Optional[List[float]]:
    """
        Runs inverse kinematic pass and returns
        the list of joint angles.
        Inputs:
            - rbt_obj: Robot FC Object
            - target: Target TCP placement
            - q_seed_deg: Initial joint angles for IK solver
            - pos_tol_mm: Accuracy tolerance in position (millimeters)
            - rot_tol_deg: Accuracy tolerance in orientaion (degrees)
    """
    be = get_backend(rbt_obj)
    if be is None:
        return None

    # take last valid joint angles or current angles when
    # no initial values are provided in input
    if q_seed_deg is None:
        q_seed_deg = current_q_deg(rbt_obj)

    # filter out fixed/active joints & convert deg -> rad
    mask = [j.type == "revolute" for j in get_chain(rbt_obj).joints]
    q_seed_rad: List[float] = [deg_to_rad(q) for q, m in zip(q_seed_deg,
                                                             mask) if m]
    # q_seed_rad: List[float] = [deg_to_rad(v) for v in q_seed_deg]

    # ik pass
    try:
        # fcl_msg(f"Length of seed: {len(q_seed_deg)}\n")
        q_rad: Optional[List[float]] = be.ik(
            target, q_seed_rad,
            pos_tol=pos_tol_mm / 1000.0,
            rot_tol=deg_to_rad(rot_tol_deg),
        )
    except Exception as e:
        fcl_err(f"IK failed: {e}\n")
        return None
    if q_rad is None:
        return None

    # apply back the fixed joints & convert back rad -> deg
    dof = iter(rad_to_deg(v) for v in q_rad)
    q_deg: List[float] = [next(dof) if m else q for q, m in zip(q_seed_deg,
                                                                mask)]

    return q_deg
