"""
Geometric helpers for new robot creation & joint placements
"""

import math
import UtilsAssembly  # type: ignore


def find_center(obj, sub):
    """Find center for the mating or flange faces."""
    # TODO: Find center for revolute joint creation more
    # accurately. The edge based selection is more accurate
    # as when we have holes or cuts in face, the
    # center is shifted from the geometrical center currently

    ref = [obj, [sub, sub]]
    elt = UtilsAssembly.getElementName(sub)

    # pass vertex or edge-picks as it is
    if not elt.startswith("Face"):
        return ref

    o = UtilsAssembly.getObject(ref)
    if o is None:
        return ref
    try:
        face = o.Shape.getElement(elt)
    except (ValueError, IndexError):
        # stale or invalid sub-element
        return ref

    # for revolute surfaces: cylinder, cone, torus
    # we already get an on-axis point
    if face.Surface.TypeId != "Part::GeomPlane":
        return ref

    # planar surfaces with COG shift due to holes, cuts etc
    # find the major curved edge and take its center
    edge_i = dominant_circular_edge(face)
    if edge_i is None:
        return ref

    return UtilsAssembly.addVertexToReference(ref, f"Edge{edge_i + 1}")


def dominant_circular_edge(face):
    """
    face edge inedx of dominant boundary circle on it
    or none
    """
    # key(radius, center)
    # -> val([first  edge idx, span sum, raw radius, raw center])
    circles = {}

    for i, e in enumerate(face.Edges):
        c = e.Curve
        if c.TypeId != "Part::GeomCircle":
            continue
        p = c.Location
        key = (round(c.Radius, 6),
               (round(p.x, 6), round(p.y, 6), round(p.z, 6)))
        entry = circles.setdefault(key, [i, 0.0, c.Radius, p])
        entry[1] += abs(e.LastParameter - e.FirstParameter)

    # filter for boundary circles only
    cands = [v for v in circles.values() if (v[1] - math.pi) >= -(1e-6)]
    if not cands:
        return None
    cands.sort(key=lambda v: -v[2])  # sort decreasing raw radius
    idx, _, radius, center = cands[0]

    # do a tie-break check
    for v in cands[1:]:
        # if the curr rad is bigger -> skip
        if radius - v[2] > 1e-6:
            break

        # equal radius but different center
        # ambiguous case -> skip
        if (v[3] - center).Length > 1e-6:
            return None

    return idx
