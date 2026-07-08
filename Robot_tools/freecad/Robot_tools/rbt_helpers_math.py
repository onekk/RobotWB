"""Robot math helper functions.

Name: rbt_helpers_math.py

See Changelog below.

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence:  LGPL 2.1
"""
from __future__ import annotations

import math

from typing import Union, TypeAlias

import FreeCAD as App  # type: ignore

V3: TypeAlias = App.Vector
Number: TypeAlias = Union[int, float]
RAD_PER_DEG: float = math.pi / 180.0
DEG_PER_RAD: float = 180.0 / math.pi

# ------------------------------------------------
#               Service functions
# ------------------------------------------------


def flip_z_dir(plc):
    """
    flips placement's z axis
    - [input] plc : App.placement
    - [out] App.placement rotated 180 deg about local X
    """
    flip = App.Placement(V3(), App.Rotation(V3(1, 0, 0), 180))
    return plc.multiply(flip)


def deg_to_rad(d: Number) -> float:
    """
        converts deg to rad
    """
    return float(d) * RAD_PER_DEG


def rad_to_deg(d: Number) -> float:
    """
        converts rad to deg
    """
    return float(d) * DEG_PER_RAD
