"""
Create a new robot from FreeCAD parts
"""

import FreeCAD as App  # type: ignore
import UtilsAssembly   # type: ignore


from freecad.Robot_tools.App.rbt_robot import Robot
from freecad.Robot_tools.App.rbt_creator_asm import (
    create_assembly, add_asm_object, resolve_asm_ref
)
from freecad.Robot_tools.App.rbt_creator_jnt import add_joint


class RobotCreator:
    """
    Builds a new robot from FC Parts
    Create Assm -> Insert Parts -> Insert Joints
    """

    def __init__(self):
        # self context
        self.asm_doc = self.assembly = self.fpo = None

        # insert-stacking state for links in the robot
        self.insertion_stack = []

        self.total_translation = App.Vector()
        self.prev_screen_center = App.Vector()

    def part_count(self):
        """
        Count of linked parts in the working assembly
        """
        asm = self.assembly
        return 0 if asm is None else (
            sum(o.isDerivedFrom('App::Link') for o in asm.Group))

    def link_count(self, obj):
        """
        count many App::Link in the  for the inserted counter
        """
        asm = self.assembly
        if asm is None:
            return 0
        return sum(1 for o in asm.Group
                   if o.isDerivedFrom("App::Link") and
                   o.LinkedObject is obj)

    def grounded_joint(self):
        """The assembly's GroundedJoint object, or None."""
        a = self.assembly
        return a.getObject("GroundedJoint") if a is not None else None

    def is_valid_robot(self):
        """
        Valid Robot : Grounded Base + At least one valid joint
        """
        a, f = self.assembly, self.fpo

        if a is None or f is None:
            return False

        return self.grounded_joint() is not None and \
            len(f.Robot_joints) >= 1

    def bind(self, asm):
        """
        Sets 'asm' as the curr working assembly
        and fixes FPO to Assembly link
        """
        self.assembly = asm
        fpos = asm.Document.getObjectsByLabel('Robot_FPO')
        if len(fpos) == 1:
            self.fpo = fpos[0]
            ra = getattr(self.fpo, 'Robot_assembly', None)
            if ra is not asm:
                self.fpo.Robot_assembly = asm

    def resolve(self):
        """
        resolve the current assembly from doc
        """
        asm, fpo, how = resolve_asm_ref(self.asm_doc)
        if asm is None:
            return None
        self.bind(asm)
        return how

    def insert_parts(self, objs):
        """
        links 'objs' into the curr assembly
        returns parts count or None when no
        assembly is present in current doc
        """
        if self.resolve() is None:
            return None

        return [add_asm_object(o.Document,
                self.assembly,
                o.Name, o.Label, o.Label) for o in objs]

    def build_assembly(self, doc=None):
        """
        Adds Robot_Assembly + Robot_FPO into the
        working document
        """
        self.asm_doc = doc or self.asm_doc or App.ActiveDocument
        asm = create_assembly(self.asm_doc)
        fpo = self.asm_doc.addObject("App::FeaturePython", "Robot_FPO")
        Robot(fpo)
        if App.GuiUp:
            # ^This is needed to nest the Robot_assembly and Toools
            # under the main FPO tree node
            from freecad.Robot_tools.Gui.vp_rbt_robot \
                import ViewProviderRobot
            ViewProviderRobot(fpo.ViewObject)
        fpo.Robot_assembly = asm
        self.asm_doc.recompute()
        self.bind(asm)
        return asm

    def insert_joint(self, jtype, refs, label=""):
        """
        Creates and adds joint of the type 'jtype'
        in the assembly & registers them with FPO
        """
        j = add_joint(self.assembly, jtype, refs, label)
        if jtype != "grounded":
            self.fpo.Robot_joints = list(
                self.fpo.Robot_joints
            ) + [j]
            self.fpo.Robot_joints_dir = list(
                self.fpo.Robot_joints_dir
            ) + [1]
        return j

    def next_joint_index(self):
        """Next free rb_jnt index (max existing + 1)."""
        js = self.fpo.Robot_joints if self.fpo else []
        idxs = [int(j.Label2[6:]) for j in js if j.Label2[6:].isdigit()]
        return max(idxs, default=-1) + 1

    def flip_joint(self, joint):
        """
        re-mate the joint's moving part on the other side of the face
        """
        joint.Proxy.flipOnePart(joint)
        self.assembly.Document.recompute()
        if self.fpo is not None:
            # invalidate and recreate kinematic chain
            # incase the joint dir is flipped
            from freecad.Robot_tools.App import rbt_kine
            rbt_kine.invalidate(self.fpo)

    def delete_joint(self, obj, grounded=False):
        """
        Removes an existing joint & keeps sync
        of robot joints and their directions
        """
        doc = self.assembly.Document
        if not grounded and \
                self.fpo is not None and \
                obj in self.fpo.Robot_joints:

            # read the index of the joint before removal
            idx = list(self.fpo.Robot_joints).index(obj)
            joints = list(self.fpo.Robot_joints)
            dirs = list(self.fpo.Robot_joints_dir)
            joints.pop(idx)
            if idx < len(dirs):
                dirs.pop(idx)
            self.fpo.Robot_joints = joints
            self.fpo.Robot_joints_dir = dirs
        doc.removeObject(obj.Name)
        doc.recompute()

    def stack_translation(self, link, screen_center, screen_corner):
        """
        stack the new added links in the style of assembly wb
        first link at origin
        later ones at 15% of bbox offsets
        """
        translation = App.Vector()
        reset_thresh = (screen_corner - screen_center).Length * 0.1
        if not self.insertion_stack:
            # first insertion: at origin
            pass
        elif (self.prev_screen_center - screen_center).Length > reset_thresh:
            self.total_translation = App.Vector()
        else:
            translation = self.translation_vec(link)

        self.insertion_stack.append(
            {"link": link.Name, "translation": translation}
        )
        self.total_translation += translation
        self.prev_screen_center = screen_center
        return translation

    def translation_vec(self, link):
        """
        offset calculations for adding new part to robot
        when we are first making the assembly
        15% offset from the bbox
        default offset of 10 mm
        """
        shape = getattr(link, "Shape", None)
        bb = shape.BoundBox if shape is not None else None
        t = ((bb.XMax + bb.YMax + bb. ZMax) * 0.15
             if bb is not None and bb.isValid() else 10)
        return App.Vector(t, t, t)

    def curr_last_link(self, obj):
        """
        most recently inserted App::Link
        """
        if self.assembly is None:
            return None
        links = [o for o in self.assembly.Group
                 if o.isDerivedFrom("App::Link") and
                 o.LinkedObject is obj]
        return links[-1] if links else None

    def joints_ref(self, link):
        """
        for each link, get [(joint, is_grounded)] for attached joints
        """
        out = []
        g = self.grounded_joint()
        if (g is not None and
                getattr(g, "ObjectToGround", None) is link):
            out.append((g, True))

        for joint in self.assembly.Joints:

            if hasattr(joint, "ObjectToGround"):
                continue

            refs = (
                getattr(joint, "Reference1", None),
                getattr(joint, "Reference2", None),
            )

            if any(ref and ref[0] is link for ref in refs):
                out.append((joint, False))

        return out

    def remove_link(self, link):
        """
        delete all attached joints to the link
        and then the link itself
        """
        for joint, is_grounded in self.joints_ref(link):
            self.delete_joint(joint, is_grounded)

        doc = link.Document
        self.on_link_removed(link.Name)
        doc.removeObject(link.Name)
        doc.recompute()

    def on_link_removed(self, name):
        """
        remove the link from the stack
        """
        stack_len = len(self.insertion_stack)
        for i in reversed(range(stack_len)):
            if self.insertion_stack[i]["link"] == name:
                self.total_translation -= \
                    self.insertion_stack[i]["translation"]
                del self.insertion_stack[i]
                break

    def track_imported(self, before_names):
        """
        Tracks part names that are added to the assembly
        """
        return {o.Name for o in self.asm_doc.Objects} - set(before_names)

    def resolve_face(self, obj, sub):
        """
        Find the link for the selected face on object in the
        working assembly. Returns (link_obj, face_ref)
        """
        return UtilsAssembly.getComponentReference(self.assembly,
                                                   obj, sub)

    def assembly_owner(self, obj, sub):
        """
        Return the Robot_Assembly that owns the given subelement of `obj`.

        Returns:
            Assembly object if the subelement belongs to a Robot_Assembly,
            otherwise None.
        """
        return next(
            (
                asm
                for asm in self.candidate_assemblies()
                if UtilsAssembly.getComponentReference(asm,
                                                       obj, sub)[0] is not None
            ),
            None)

    def candidate_assemblies(self):
        """
        Return all Robot_Assembly objects in the working document.
        """
        return [
            asm
            for asm in self.asm_doc.getObjectsByLabel("Robot_Assembly")
            if asm.isDerivedFrom("Assembly::AssemblyObject")
        ]
