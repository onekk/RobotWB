"""
Geometric helpers for new robot creation & joint placements
"""


def find_center(jnt_nm, jnt_data, dbg_s=False):
    """Find center from edges of joint mating faces."""
    # TODO: Find center for revolute joint creation more
    # accurately. The edge based selection is more accurate
    # as when we have holes or cuts in face, the
    # center is shifted from the geometrical center currently
    raise NotImplementedError
