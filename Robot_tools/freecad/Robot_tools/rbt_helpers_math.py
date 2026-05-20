"""Robot math helper functions.

Name: rbt_helpers_math.py

See Changelog below.

Author: Carlo Dormeletti and Nishendra Singh
Copyright: 2026
Licence:  LGPL 2.1
"""
__version__ = "0.01"
__build__ = "20260507_1255"

import FreeCAD as App

# ------------------------------------------------
#               Service functions
# ------------------------------------------------


def roundvec(r_vec, prec=6):
    """Round value in vectors."""
    vlist = [round(r_vec.x, prec), round(r_vec.y, prec), round(r_vec.z, prec)]
    return vlist


def roundrot(r_rot, prec=6):
    """Round value in vectors."""
    vlist = [round(r_rot[0], prec), round(r_rot[1], prec), round(r_rot[2], prec)]
    return vlist


def rpy_to_rot(rx_deg, ry_deg, rz_deg):
    """ZYX - euler degrees to App.Rotation"""
    return App.Rotation(rz_deg, ry_deg, rx_deg)


def rot_to_rpy(rot):
    """App.Rotation to euler degrees - ZYX format"""
    yaw, pitch, roll = rot.toEuler()
    return roll, pitch, yaw


def flip_z_dir(plc):
    """
    flips placement's z axis
    - [input] plc : App.placement
    - [out] App.placement rotated 180 deg about local X
    """
    flip = App.Placement(App.Vector(), App.Rotation(App.Vector(1, 0, 0), 180))
    return plc.multiply(flip)
