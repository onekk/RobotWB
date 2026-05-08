""" Robot_tools Custom TB

Name: study_robot.py

See Changelog before import statements.

Author: Carlo Dormeletti
Copyright: 2026
Licence: All right reserved
"""
__version__ = "0.18"
__build__ = "20260507_1307"


import pathlib

from datetime import datetime

import FreeCAD as App
import FreeCADGui as Gui
import Part

# Assembly imports
import UtilsAssembly
import JointObject

import PySide

from PySide import QtGui, QtCore  # noqa  # QtWidgets
from PySide.QtWidgets import (  # noqa
    QApplication, QCheckBox, QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSpinBox, QTabWidget, QTextEdit, QWidget,  # Widgets
    QDialog, QFileDialog, QInputDialog, QMessageBox,  # Dialogs
    QGridLayout, QVBoxLayout)  # Layouts

from PySide.QtCore import QObject, Qt  # noqa

"""
----------------------------------------
Changelog:
----------------------------------------
v0.01 - initial version.
v0.06 - Adds some analysis of the result of the "Service" doc.
v0.07 - Adds some more analysis.
v0.08 - Adds an automatic sorting algorithm.
v0.09 - Adds a check of equlity between automatic found centers.
v0.10 - Adds a report and the visualization of rotation axes.
v0.11 - Adds the rotation centers and pos from assembly file.
v0.12 - Adds rotation axis from the assembly robot joints defs.
v0.13 - Adds the option to copy the Assembly file.
v0.14 - Adds a tabbed layout.
v0.15 - Adds a more rotation axis visualization buttons.
v0.16 - Adds a way to determine incremental rotation centers offset.
v0.17 - Adapt the code to be run in Robot_Tools WB.
v0.18 - Adpt the code to use the new Robot FPO.
"""

fcl_err = App.Console.PrintError
fcl_msg = App.Console.PrintMessage
fcl_warn = App.Console.PrintWarning

mdtsp = "%y%m%d_%H%M"
MODULE_PATH = pathlib.Path(__file__).parent

V3 = App.Vector
Rotation = App.Rotation
Placement = App.Placement


VEC0 = V3(0, 0, 0)
ROT0 = Rotation(0, 0, 0)


ap_clr = {
    "Black": [(0.0, 0.0, 0.0), "#000000"],
    "Grey75": [(0.25, 0.25, 0.25), "#404040"],
    "White": [(1.0, 1.0, 1.0), "#FFFFFF"],
    # Vibrant
    "V_Blue": [(0.0, 0.467, 0.733), "#0077BB"],
    "V_Cyan": [(0.20, 0.733, 0.933), "#33BBEE"],
    "V_Teal": [(0.0, 0.6, 0.533), "#009988"],
    "V_Orange": [(0.933, 0.467, 0.2), "#EE7733"],
    "V_Red": [(0.8, 0.2, 0.67), "#CC3311"],
    "V_Magenta": [(0.933, 0.2, 0.467), "#EE3377"],
    "V_Grey": [(0.733, 0.733, 0.733), "#BBBBBB"],
    # Bright
    "B_Blue": [(0.267, 0.467, 0.667), "#4477AA"],
    "B_Cyan": [(0.4, 0.8, 0.933), "#66CCEE"],
    "B_Green": [(0.133, 0.533, 0.200), "#228833"],
    "B_Yellow": [(0.8, 0.733, 0.267), "#CCBB44"],
    "B_Red": [(0.933, 0.4, 0.467), "#EE6677"],
    "B_Purple": [(0.667, 0.2, 0.467), "#AA3377"],
    # High Contrast
    "HC_Yellow": [(0.867, 0.667, 0.2), "#DDAA33"],
    "HC_Red": [(0.733, 0.333, 0.4), "#BB5566"],
    "HC_Blue": [(0.0, 0.267, 0.533), "#004488"],
    # Additional
    "Aqua": [(0.0, 1.0, 1.0), "#00FFFF"],
    "Orange": [(1.0, 0.647, 0.0), "#FFA500"],
}

msg_log = []  # log message container, used to permit a dump.


def clear_doc(doc_name):
    """Clear the document deleting all the objects.

    Args:
    doc_name  (str): document name
    """
    doc = App.getDocument(doc_name)
    try:
        while len(doc.Objects) > 0:
            doc.removeObject(doc.Objects[0].Name)
    except Exception as e:
        fcl_msg(f"Exception:  {e}\n")


def ensure_document(doc_name, action=0, dbg_l=0):
    """Ensure existence of document with doc_name and clear the doc.

    Args:
        doc_name (string): document name
        action (int): clear action if document exist
              0: do nothing
              1: close and reopen the document with the same name
              2: delete all objects
        dbg_l (int):

    Returns:
        doc_name (string): Document name from obj.Name
    """
    doc_root = App.listDocuments()
    doc_exist = False

    for d_name, doc in doc_root.items():

        if dbg_l > 0:
            fcl_msg(f"ED: doc name = {d_name}\n")

        if d_name == doc_name:
            if dbg_l > 0:
                fcl_msg(f"ED: Match name: {doc_name} action: {action}\n")

            if action == 1:
                # when using clear_doc() is not possible like in Part.Design
                App.closeDocument(doc_name)
                doc_exist = False
            elif action == 2:
                # debug info do not delete
                # print("action 2")  # kp
                doc_exist = True
                clear_doc(doc_name)
                App.setActiveDocument(d_name)
                return App.getDocument(d_name).Name
            else:
                doc_exist = True
                App.setActiveDocument(d_name)
                return App.getDocument(d_name).Name

    if doc_exist is False:
        if dbg_l > 0:
            fcl_msg(f"ED: Create = {doc_name}\n")

        new_doc = App.newDocument(doc_name)
        return new_doc.Name


def setview(doc_name, t_v=0):
    """Set viewport in 3D view."""
    App.setActiveDocument("")
    App.ActiveDocument = None
    Gui.ActiveDocument = None

    switch_document(doc_name)
    VIEW = Gui.ActiveDocument.ActiveView

    if t_v == 0:
        VIEW.viewTop()
    elif t_v == 1:
        VIEW.viewFront()
    elif t_v == 99:
        VIEW.setCameraOrientation(
            Rotation(0.0, 0.0, -0.7071067811865475, 0.7071067811865475))

    else:
        VIEW.viewAxometric()

    VIEW.setAxisCross(True)
    VIEW.fitAll()
    # Gui.updateGui()


def set_txt_color(txt, col):
    """Set text color using html syntax."""
    if col == "o":
        f_clr = ap_clr['B_Green'][1]
    elif col == "w":
        f_clr = ap_clr['Orange'][1]
    elif col == "e":
        f_clr = ap_clr['B_Red'][1]
    else:
        f_clr = "black"

    return f"<span style='color: {f_clr}'> {txt} </span>"


def switch_document(doc_name):
    """Switch a FreeCAD document."""
    App.setActiveDocument(doc_name)
    App.ActiveDocument = App.getDocument(doc_name)
    Gui.ActiveDocument = Gui.getDocument(doc_name)
    #  Trick to swith the Gui to show the document
    gv = Gui.ActiveDocument.ActiveView.graphicsView()
    pw = gv.parentWidget().parentWidget().parentWidget()
    Gui.getMainWindow().centralWidget().setActiveSubWindow(pw)

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


# ------------------------------------------------
#                   UI functions
# ------------------------------------------------


def cm_chb(parent, o_nm, o_txt, l_fnt, enable=True):
    """Create a styled QLabel."""
    chb = QCheckBox(parent)
    chb.setObjectName(o_nm)
    chb.setText(o_txt)

    if enable is True:
        chb.setEnabled(True)
    else:
        chb.setEnabled(False)

    return chb


def cm_gbx(parent, gb_nm, gb_lbl, gbl_nm="", style="bold", blay=0):
    """Create a groupbox container and return it."""
    gpbx = QGroupBox(gb_lbl)
    gpbx.setObjectName(f"{gb_nm}_wd")

    if style == "bold":
        gpbx_style = (
            "QGroupBox{"
            "    font-weight: bold;"
            "    font-style: normal;"
            "    text-decoration: none;"
            "}")
        gpbx.setStyleSheet(gpbx_style)

    if blay == 0:
        gpbxl = QGridLayout()
    else:
        gpbxl = QVBoxLayout()

    if gbl_nm == "":
        gpbxl.setObjectName(f"{gb_nm}_l")
    else:
        gpbxl.setObjectName(gbl_nm)

    return gpbx, gpbxl


def cm_btn(parent, b_nm, b_txt, b_fnt, b_tfm):
    """Create a styled QPushButton."""
    button = QPushButton()
    button.setObjectName(b_nm)
    button.setFont = b_fnt
    button.setAutoDefault(False)

    if b_tfm == 1:
        button.setTextFormat(Qt.RichText)
    else:
        pass

    button.setText(b_txt)

    if parent is None:
        pass
    else:
        button.setParent(parent)

    button.setAutoDefault(False)

    return button


def cm_lbl(parent, l_nm, l_txt, l_fnt, l_tfm, l_aln=0):
    """Create a styled QLabel.

       l_tfm (int): text format 0: Auto 1: RichText 2: bold
       l_aln (int): alignment 0: Standard  1: Center H and V
    """
    #
    label = QLabel()
    label.setObjectName(l_nm)
    label.setFont(l_fnt)
    label.setWordWrap(False)

    lab_txt = l_txt

    if l_tfm in (1, 2):
        label.setTextFormat(Qt.RichText)
        if l_tfm == 2:
            lab_txt = f"<b>{l_txt}</b>"

    if l_aln == 1:
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    elif l_aln == 2:
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    else:
        pass

    label.setText(lab_txt)

    if parent is None:
        pass
    else:
        label.setParent(parent)

    return label


def cm_ledit(parent, t_nm, t_fnt, t_hei):
    """Create a styled QLineEdit.

       t_hei (int): text field height
    """
    #
    text_f = QLineEdit()
    text_f.setObjectName(t_nm)
    text_f.setFont(t_fnt)

    if t_hei > 0:
        text_f.setFixedHeight(t_hei)

    if parent is None:
        pass
    else:
        text_f.setParent(parent)

    return text_f


def cm_txt(parent, t_nm, t_fnt, t_hei, rich=True):
    """Create a styled QTextEdit or QPlainTextEdit.

    Args:
        parent(QObject): parent widget
        t_nm (str): text name
        t_fnt (QFont): text font
        t_hei (int): text field height

    Returns:
        text (QtWidget): text
    """
    #
    if rich is False:
        text_f = QPlainTextEdit()
    else:
        text_f = QTextEdit()

    text_f.setObjectName(t_nm)
    text_f.setFont(t_fnt)
    text_f.setReadOnly(True)

    if t_hei > 0:
        text_f.setFixedHeight(t_hei)

    if parent is None:
        pass
    else:
        text_f.setParent(parent)

    return text_f


def get_dir(parent, fnt, pre_dir=""):
    """Get a directory from a file dialog."""
    f_name = None
    cf_dia = QFileDialog(parent)
    cf_dia.setFileMode(QFileDialog.Directory)
    #
    if pre_dir != "":
        cf_dia.setDirectory(pre_dir)

    if cf_dia.exec():
        f_nms = cf_dia.selectedFiles()
        if len(f_nms) != 1:
            msg_box(
                parent, "You must select only one file.", fnt, "w", 'WARNING:', "w")
            f_name = None
        else:
            f_name = f_nms[0]

    return f_name


def get_file(parent, fnt, ftype="fcstd", pre_dir=""):
    """Get a file from a file dialog."""
    f_name = ""
    cf_dia = QFileDialog(parent)

    if ftype == "wrl":
        cf_dia.setNameFilter("wrl (*.wrl *.WRL)")
    elif ftype == "csv":
        cf_dia.setNameFilter("csv (*.csv *.CSV)")
    elif ftype == "def":
        cf_dia.setNameFilter("json (*_def.json  *_DEF.JSON)")
    else:
        # cf_dia.setNameFilter("")
        # no namefilter
        pass

    cf_dia.setFileMode(QFileDialog.ExistingFile)
    cf_dia.setViewMode(QFileDialog.Detail)  # or List
    if pre_dir != "":
        cf_dia.setDirectory(pre_dir)

    if cf_dia.exec():
        f_nms = cf_dia.selectedFiles()
        if len(f_nms) != 1:
            msg_box(
                parent, "You must select only one file.", fnt, "w", 'WARNING:', "w")
        else:
            f_name = f_nms[0]

    return f_name


def msg_box(parent, title, fnt, msg, icon="", head="", hc=""):
    """Create a minimal message box."""
    msg_box = QMessageBox(parent)
    msg_box.setFont(fnt)
    msg_box.setWindowTitle(title)

    if icon == "e":
        m_icon = QMessageBox.Icon.Critical
    elif icon == "w":
        m_icon = QMessageBox.Icon.Warning
    elif icon == "i":
        m_icon = QMessageBox.Icon.Information
    else:
        m_icon = QMessageBox.Icon.NoIcon

    msg_box.setIcon(m_icon)
    if head != "":
        s_msg = f"{set_txt_color(head, hc)}<br><br>" + msg
    else:
        s_msg = msg

    msg_box.setText(s_msg)

    msg_box.exec()


def getObjByName(parent, btn_nm):
    """Return a button from its name."""
    wid = parent.findChild(QObject, btn_nm)
    if wid is None:
        return None
    else:
        return wid


def set_wd_prop(wid, prop, val):
    """Set Qt Widget property."""
    wid.setProperty(prop, val)
    wid.style().unpolish(wid)
    wid.style().polish(wid)


def set_wid_text(parent, obj_nm, txt):
    """Find an object and set it text."""
    # fcl_msg(parent.children())  # DBG
    wid = parent.findChild(QLineEdit, obj_nm)
    if wid is None:
        return
    else:
        wid.setText(txt)


def set_wid_en(parent, obj_nm, state=True):
    """Find an object by name or a tuple of names and set enabled state."""
    # fcl_msg(parent.children())  # DBG
    if isinstance(obj_nm, tuple):
        obj_tpl = obj_nm
    else:
        obj_tpl = (obj_nm, )

    for elem in obj_tpl:
        wid = parent.findChild(QObject, elem)
        if wid is None:
            pass
        else:
            wid.setEnabled(state)

# ------------------------------------------------
#                 Module functions
# ------------------------------------------------


def dump_log(log_fn):
    """Dump log to a file."""
    fcl_msg(f"Log file name: {log_fn}")


def find_center(jnt_nm, jnt_data, dbg_s=False):
    """Find center from edges of joint mating faces."""
    ptc_f1 = jnt_data['fcc_f1']
    ptc_f2 = jnt_data['fcc_f2']
    #
    if dbg_s:
        dbg_msg = (
            f"-- {jnt_nm}\n"
            f"face1 >> {ptc_f1}\n"
            f"face2 >> {ptc_f2}\n")
        fcl_msg(dbg_msg)
    pts_f1 = sort_centers(ptc_f1)
    pts_f2 = sort_centers(ptc_f2)
    #
    sptf1 = sorted(pts_f1, key=lambda x: x[1])
    sptf2 = sorted(pts_f2, key=lambda x: x[1])
    #
    if dbg_s:
        dbg_msg = (
            f"f1: {sptf1[-1]}\n"
            f"f2: {sptf2[-1]}\n")
        fcl_msg(dbg_msg)
    return sptf1, sptf2


def sort_centers(c_lst):
    """Sort centers data."""
    # fcl_msg(f"list: {c_lst}\n")  # DBG
    tol = 0.001
    pts = []
    n_pts = []
    cnt = 1
    lc = True
    mn = len(c_lst) - 1
    pts.append(V3(*c_lst[0]))
    n_pts.append(1)
    while lc:
        pt_v2 = V3(*c_lst[cnt])
        for v_idx, v in enumerate(pts):
            dt = v.distanceToPoint(pt_v2)
            if dt > tol:
                pts.append(pt_v2)
                n_pts.append(1)
            else:
                n_pts[v_idx] += 1
        # print(f"cnt: {cnt}, {mn} pts: {pts} n_pts: {n_pts}\n")
        cnt += 1
        if cnt >= mn:
            lc = False

    s_list = list(zip(pts, n_pts))

    return s_list


def print_joints(obj):
    """Show joints info on Report View."""
    for joint in obj.Joints:
        # fcl_msg(dir(joint))
        if joint.JointType == "Revolute":
            jref1 = joint.Reference1
            jpl1 = joint.Placement1
            jpl1_b = roundvec(jpl1.Base)
            jpl1_r = roundrot(jpl1.Rotation.toEuler())
            jref2 = joint.Reference2
            jpl2 = joint.Placement2
            jpl2_b = roundvec(jpl2.Base)
            jpl2_r = roundrot(jpl2.Rotation.toEuler())
            msg = (
                f"-- Joint {joint.Name} \n"
                f"- Type = {joint.JointType}\n"
                f"- Reference1 = {jref1}\n"
                f"- Placement1.Base = {jpl1_b}\n"
                f"- Placement1.Rot = {jpl1_r}\n"
                f"- Reference2 = {jref2}\n"
                f"- Placement2.Base = {jpl2_b}\n"
                f"- Placement2.Rot = {jpl2_r}\n"
                "\n"
                )
            fcl_msg(msg)


def show_faces(j_n, jnt_r1, jnt_r2, dsp=Placement(VEC0, ROT0)):
    """Show faces of mating joints."""
    # fcl_msg(f"Joint{j_n + 1}\n")  # DBG
    # Reference1
    obj1 = jnt_r1[0].LinkedObject.Shape.Faces
    o1_fr = jnt_r1[1][0]
    o1_fnr = o1_fr[4:]
    # fcl_msg(f"face number {o1_fr}")  # DBG
    jnt_nm = f"rb_jnt{j_n + 1:02d}"
    o1_fn = int(o1_fnr) - 1
    d_obj1 = Part.show(obj1[o1_fn], f"{jnt_nm}_F1_{o1_fr}")
    d_obj1.Label = f"{jnt_nm}_F1"
    d_obj1.Placement = dsp
    d_obj1.recompute()

    # Reference2
    obj2 = jnt_r2[0].LinkedObject.Shape.Faces
    o2_fr = jnt_r2[1][0]
    o2_fnr = o2_fr[4:]
    # fcl_msg(f"face number {o2_fr}")  # DBG
    o2_fn = int(o2_fnr) - 1
    d_obj2 = Part.show(obj2[o2_fn], f"{jnt_nm}_F2_{o2_fr}")
    d_obj2.Label = f"{jnt_nm}_F2"
    d_obj2.Placement = dsp
    d_obj2.recompute()

    return d_obj1, d_obj2


def set_lcs(d_doc, tupl, fc_nm):
    """Set joint LCS."""
    if tupl == ():
        return None

    # Create an LCS on the joint "center" Hopefully
    obj = d_doc.addObject('Part::LocalCoordinateSystem', 'LCS')
    obj.Label = f"LCS_{fc_nm}"
    # # Object created at document root.
    obj.Visibility = True
    # obj.AttacherEngine = u"Engine 3D"
    obj.AttachmentSupport = tupl
    obj.MapMode = 'Concentric'  # 'InertialCS'
    obj.recompute()
    d_doc.recompute()

    return obj


def show_jcs(d_doc, dbg_s=False):
    """Show Joint coordinate system."""
    jcs_data = []
    for obj in d_doc.Objects:
        if obj.TypeId == "Part::LocalCoordinateSystem":
            jo_lid = obj.Label[4:12]
            jo_nm = obj.Name
            if dbg_s:
                fcl_msg(f"{jo_lid} >> {jo_nm}\n")  # DBG
            if jo_lid[:-2] == "rb_jnt":
                if dbg_s:
                    fcl_msg(f" pos: {obj.Placement.Base}\n")  # DBG


def show_rotaxis(ref_doc, grp_name, jnt_k, jnt_cent, jnt_normal,
                 shp_clr=ap_clr["Orange"][0], c_len=500.0, c_dia=3, dbg_s=False):
    """Show rotation axis on the asm model.

    Args:
    ref_doc (doc_object): FreeCAD document object
    grp_name (str):  Rotation axis group name
    jnt_k (str): Joint identifier usually jointXX
    jnt_cent (list): XYZ values of center
    jnt_normal (list): normal of joint face as XYZ list
    shp_clr (tuple): color as fc (r, g, b) tuple of floats bewtween (0.0 ... 1.0).
    c_len (float): cylinder length (defaults to 500)
    c_rad (int): cylinder radius
    dbg_s (bool): activate debug messages
    """
    # dbg_s = True  # DBG
    if hasattr(ref_doc, grp_name):
        ra_grp_do = ref_doc.getObject(grp_name)
    else:
        ra_grp_do = ref_doc.addObject('App::DocumentObjectGroup', grp_name)
    #
    ra_axs = V3(*jnt_normal)
    ra_ofv = c_len * -0.5 * ra_axs
    ra_cen = V3(*jnt_cent) + ra_ofv
    if dbg_s:
        fcl_msg(f"{grp_name} {jnt_k} >> ax: {ra_axs} cen: {ra_cen}\n")
    cyl = Part.makeCylinder(
        c_dia, c_len, ra_cen, ra_axs)
    # Robot Assembly DO
    jnt_do = ref_doc.addObject(
        "Part::Feature", f"{jnt_k}_ra")
    jnt_do.Shape = cyl
    jnt_do.ViewObject.ShapeColor = shp_clr
    ra_grp_do.addObject(jnt_do)

# ------------------------------------------------
#                    Main Dialog
# ------------------------------------------------


class O2PDialog(QDialog):
    """Show a dialog for RobotAnimator."""
    ui_title = "Study Robot"
    IsInit = False  # flag to avoid unwanted action execution during init.
    # Flags dictionary, place here sane defaults
    flags = {"chb_cpa": False, }
    #
    tab_data = {
        "ma": {"nm": "Main", "cn": 0}, "lg": {"nm": "Log", "cn": 0}}
    #
    wk_asm = None  # Robot model as Assembly DO
    rob_obj = None  # Robot FPO
    # Default values for testing
    s_doc = None  # Assembly service doc
    eus = None   #
    fnt = None  # Font for widgets
    lb_em = 0  #
    # Rotation axis vis data
    as_rashl = 100  # cyl len used on Assembly Service doc
    as_rarad = 3  # cyl rad used on Assembly Service doc
    as_raclr = ap_clr["Orange"][0]  # used for CRC on Assembly Service doc
    rad_rashl = 1000  # cyl len used on Robot Assembly doc
    rad_rarad = 1.5  # cyl rad used on Robot Assembly doc
    rad_raclr = ap_clr["Orange"][0]  # color used for CRC Robot ASM doc
    rad_raoclr = ap_clr["B_Purple"][0]  # color used for JCS on ASM doc
    #
    rbm_dt = {'rb_jnts': 0, }  # Robot model data  dictionary
    # Stylesheets
    grb_ss = (
        ""
        "QGroupBox{"
        "    font-weight: bold;"
        "    font-style: normal;"
        "    text-decoration: none;"
        "}"
    )

    lab_ss = (
        ""
        "QLabel {"
        "    font-weight: normal;"
        "    font-style: normal;"
        "    text-decoration: none;"
        "    border: 0px none;"
        "}"
        ""
        "QLabel[role='tool'] {"
        "    font-weight: bold;"
        "    font-style: normal;"
        "    text-decoration: none;"
        "    border: 0px none;"
        "}"
        ""
        "QLabel[role='done']{"
        "    font-weight: bold;"
        "    font-style: normal;"
        "    text-decoration: none;"
        "    border: 2px outset black;"
        "    border-radius: 5px;"
        "    padding-left: 10px;"
        "}"
        ""
        "QLabel[role='edit'] {"
        "    font-weight: bold;"
        "    font-style: normal;"
        "    text-decoration: none;"
        "    border: 2px outset gray;"
        "    border-radius: 5px;"
        "    padding: 5px;"
        "}"
        "QPushButton[role='step'] {"
        # " text-align: center;"
        # " margin: 2px;"
        " padding: 1px;"
        # " border: 1px solid #111111;"
        # " border-radius: 6px;"
        "}"
        ""
    )

    log_ss = (
        "QTextEdit {"
        "        font-family: monospace;"
        "}"
    )

    def __init__(self, parent=Gui.getMainWindow()):
        """Canonical Init."""
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Init UI."""
        global work_dir
        # get dimensions for available space on screen
        av_wid = QtGui.QGuiApplication.primaryScreen().availableGeometry().width()
        av_hei = QtGui.QGuiApplication.primaryScreen().availableGeometry().height()
        w_wid = av_wid * 0.20
        w_hei = av_hei * 0.33
        x_loc = (av_wid - w_wid) * 0.5
        y_loc = (av_hei - w_hei) * 0.5
        # define window xLoc,yLoc,xDim,yDim
        self.setGeometry(x_loc, y_loc, w_wid, w_hei)
        self.setWindowTitle(self.ui_title)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowStaysOnTopHint
        )

        self.fnt = QApplication.font("QMessageBox")
        lb_fm = QtGui.QFontMetricsF(self.fnt)
        self.lb_em = round(lb_fm.maxWidth())

        # Determine if we are running as a module of Robot Tools WB/TB
        if str(MODULE_PATH.stem) == 'Robot_tools':
            self.isWBcomp = True
        else:
            self.isWBcomp = False

        self.isInit = True
        self.tabw = QTabWidget(self)

        for tb_k in self.tab_data.keys():
            t_dat = self.tab_data[tb_k]
            tab = QWidget()
            tab.setFont = self.fnt
            tab.setObjectName(f"t_{tb_k}")
            lay = QGridLayout(tab)
            lay.setObjectName(f"l_{tb_k}")
            tab.setLayout(lay)
            self.tabw.addTab(tab, t_dat['nm'])

        self.dmw_lay = QGridLayout()

        mcn = 4  # fake number of column to pre adapt panel width
        row = 0
        self.lbl_sw = cm_lbl(self, "lbl_sw", f"Build: {__build__}", self.fnt, 2)
        self.dmw_lay.addWidget(self.lbl_sw, row, 0, 1, mcn)

        row += 1
        self.dmw_lay.addWidget(self.tabw, row, 0, 1, mcn)
        self.setLayout(self.dmw_lay)

        res = self.ma_setui()
        if res is False:
            return

        self.lg_setui()

        self.show()
        self.isInit = False

    def ma_setui(self):
        """Populate main tab."""
        ma_lay = self.tabw.findChild(QObject, "l_ma")
        ma_tab = self.tabw.findChild(QObject, "t_ma")

        fcl_msg(f"isWBcomp {self.isWBcomp}\n ")  # DBG

        row = 0

        # Assembly Model groupBox
        gb_rc, gb_rcl = cm_gbx(self, "gb_rc", "Assembly Model")
        gb_rc.setStyleSheet(self.grb_ss)
        gb_rc.setLayout(gb_rcl)

        brow = 0
        # Robot label
        if self.isWBcomp is True:
            raw_sel = Gui.Selection.getSelection("", 2, True)
            esn = len(raw_sel)

            if esn == 0:
                msg_box(
                    self, "Robot", self.fnt,
                    "<b>Robot Selection</b><br><br>You must select a Robot FPO")
                return False
            elif esn == 1:
                obj = raw_sel[0]
                obj_typ = obj.TypeId
                # fcl_msg(f"Object Name: {obj.Name[:9]}\n")
                if obj_typ == "App::FeaturePython" and obj.Name[:9] == "Robot_FPO":
                    lbl_rob_id = cm_lbl(
                        self, "lbl_rob_id", f"<b>{obj.Name}</b>", self.fnt, 0)
                    gb_rcl.addWidget(lbl_rob_id, brow, 0, 1, 4)
                    row += 1
                    self.rob_obj = obj
                    self.flags['rob_fpo'] = True
                    self.set_working_rbt()
                else:
                    return False
            else:
                return False

        else:
            self.flags['rob_fpo'] = True
            #
            self.txt_rbnm = cm_ledit(self, "txt_rbnm", self.fnt, 0)
            gb_rcl.addWidget(self.txt_rbnm, brow, 0, 1, 2)
            #
            self.btn_sel_asm = cm_btn(self, "btn_seldir", "Select", self.fnt, 0)
            gb_rcl.addWidget(self.btn_sel_asm, brow, 2, 1, 2)

            self.btn_sel_asm.clicked.connect(self.set_working_asm)

            brow += 1
            chb_cpa = cm_chb(self, "chb_cpa", "Copy Assembly", self.fnt, True)
            gb_rcl.addWidget(chb_cpa, brow, 0, 1, 2)
            chb_cpa.setChecked(False)
            chb_cpa.stateChanged.connect(self.chb_mgmt)

        ma_lay.addWidget(gb_rc, row, 0, 1, 4)
        row += 1

        gb_bt, gb_btl = cm_gbx(self, "gb_bt", "Functions")
        gb_bt.setStyleSheet(self.grb_ss)
        gb_bt.setLayout(gb_btl)

        brow = 0

        btn_jnts_isp = cm_btn(self, "btn_jnts_isp", "Inspect Joints", self.fnt, 0)
        gb_btl.addWidget(btn_jnts_isp, brow, 0, 1, 2)

        btn_jnts_isp.clicked.connect(self.inspect_joints)

        chb_ast = cm_chb(self, "chb_ast", "Auto scan", self.fnt, True)
        gb_btl.addWidget(chb_ast, brow, 2, 1, 2)
        chb_ast.setChecked(True)

        chb_sara = cm_chb(
            self, "chb_sara", "Show JCS on Service doc", self.fnt, True)
        chb_sara.setToolTip("Show JCS (Joint Coordinate System) on Service doc.")
        gb_btl.addWidget(chb_sara, brow, 4, 1, 2)
        chb_sara.setChecked(True)

        brow += 1
        btn_jnts_sac = cm_btn(
            self, "btn_jnts_sac", "Show JCS on ASM", self.fnt, 0)
        btn_jnts_sac.setToolTip("Show JCS on assembly doc")
        gb_btl.addWidget(btn_jnts_sac, brow, 0, 1, 2)
        btn_jnts_sac.clicked.connect(self.show_asm_rac)
        btn_jnts_sac.setEnabled(False)

        btn_jnts_crc = cm_btn(
            self, "btn_jnts_crc", "Show CRC on ASM", self.fnt, 0)
        btn_jnts_crc.setToolTip("Show CRC (Calculated Rotation Center) on assembly doc")
        gb_btl.addWidget(btn_jnts_crc, brow, 2, 1, 2)
        btn_jnts_crc.clicked.connect(self.vis_asra_on_asm)
        btn_jnts_crc.setEnabled(False)

        brow += 1
        btn_jnts_ana = cm_btn(self, "btn_jnts_ana", "Analyze Joints", self.fnt, 0)
        gb_btl.addWidget(btn_jnts_ana, brow, 0, 1, 2)
        btn_jnts_ana.clicked.connect(self.analyze_lcs)
        btn_jnts_ana.setEnabled(False)

        ma_lay.addWidget(gb_bt, row, 0, 1, 4)
        row += 1

        tp_gb0, tp_gb0l = cm_gbx(self, "tp_gb0", "GB1")
        tp_gb0.setStyleSheet(self.grb_ss)
        # Empty groupBox
        tp_gb0.setLayout(tp_gb0l)
        ma_lay.addWidget(tp_gb0, row, 0, 1, 4)

        row += 1
        ma_lay.setRowStretch(row, 1)
        return True

    def lg_setui(self):
        """Populate Log Tab."""
        lg_lay = self.tabw.findChild(QObject, "l_lg")
        lg_tab = self.tabw.findChild(QObject, "t_lg")
        self.log_win = cm_txt(lg_tab, "log_win", self.fnt, -1, True)
        self.log_win.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.log_win.setStyleSheet(self.log_ss)

        lg_lay.addWidget(self.log_win, 0, 0)

        btn_log = cm_btn(
            lg_tab, "lg_btnlog", 'Dump Log to File', self.fnt, 0)
        btn_log.clicked.connect(self.act_dump_log)
        btn_log.setToolTip("Not implementd now")
        btn_log.setEnabled(False)

        lg_lay.addWidget(btn_log, 1, 0)

        self.log_win.show()

    def closeEvent(self, event):
        """Called on Close event."""
        Gui.Selection.removeSelectionGate()

    def get_chb_content(self, par_nm, obj_nm):
        """Get QCheckBox Widget state."""
        gb_obj = self.findChild(QObject, par_nm)
        if gb_obj is not None:
            obj = gb_obj.findChild(QCheckBox, obj_nm)
            if obj is not None:
                return obj.isChecked()
            else:
                return None
        else:
            return None

    def inspect_joints(self, dbg_s=False):
        """Inspect joint position."""
        asm_obj = self.wk_asm
        if asm_obj is None:
            return
        if self.flags["chb_cpa"] is True:
            nasm_obj = self.copy_asm(asm_obj)
            asm_obj = nasm_obj
            self.wk_asm = nasm_obj
        #
        sd_name = f"{asm_obj.Label}_Service"
        d_doc_nm = ensure_document(sd_name, 2)
        d_doc = App.getDocument(d_doc_nm)
        #
        self.s_doc = d_doc
        # Add a DocType property to ease the analysis
        if "DocType" not in d_doc.PropertiesList:
            d_doc.addProperty("App::PropertyString", "DocType", "Base", "")
            d_doc.DocType = "JointsData"

        grp_do = d_doc.addObject('App::DocumentObjectGroup', "joints_faces")
        # NOTE: GroundedJoint is a property of the Assembly document
        g_joi = asm_obj.Document.GroundedJoint
        gj_pl = g_joi.ObjectToGround.Placement
        fcl_msg(f"Grounded placement {gj_pl} \n")
        #
        self.face_objs = []
        rb_jnt = 0
        if self.flags["rob_fpo"] is True:
            jnt_obj = self.rob_obj.Robot_joints
        else:
            jnt_obj = asm_obj.Joints

        for j_n, jnt in enumerate(jnt_obj):
            if dbg_s:
                fcl_msg(f"joint_label2 {jnt.Label2} >> {jnt.Label2[:8]}")  # DBG
            if jnt.Label2[:8] == "rb_joint":
                rb_jnt += 1
                d_obj1, d_obj2 = show_faces(j_n, jnt.Reference1, jnt.Reference2, gj_pl)
                grp_do.addObject(d_obj1)
                grp_do.addObject(d_obj2)
                grp_do.recompute()
                self.face_objs.append((j_n, d_obj1.Name, d_obj2.Name))

        if self.face_objs != []:
            self.rbm_dt['rb_jnts'] = rb_jnt
            for n in range(rb_jnt):
                jnt_i = n + 1
                jnt_k = f"joint{jnt_i:02d}"
                if jnt_k not in self.rbm_dt.keys():
                    self.rbm_dt[jnt_k] = {}
                face_obj = self.face_objs[n]
                # fcl_msg(f"face obj: {face_obj}\n")  # DBG
                face1 = self.s_doc.getObject(face_obj[1])
                f1_nm = face1.Shape.Faces[0].normalAt(0.0, 0.0)
                f1_cen = face1.Shape.Faces[0].valueAt(0.0, 0.0)
                face2 = self.s_doc.getObject(face_obj[2])
                f2_nm = face2.Shape.Faces[0].normalAt(0.0, 0.0)
                f2_cen = face2.Shape.Faces[0].valueAt(0.0, 0.0)
                self.rbm_dt[jnt_k]['normals'] = [roundvec(f1_nm), roundvec(f2_nm)]
                self.rbm_dt[jnt_k]['fc_cen'] = [roundvec(f1_cen), roundvec(f2_cen)]

            af_jnt_i = 0
            for j_n, jnt in enumerate(jnt_obj):
                # fcl_msg(f"joint_label2 {jnt.Label2} >> {jnt.Label2[:8]}")  # DBG
                if jnt.Label2[:8] == "rb_joint":
                    af_jnt_i += 1
                    jnt_k = f"joint{af_jnt_i:02d}"
                    if jnt_k not in self.rbm_dt.keys():
                        self.rbm_dt[jnt_k] = {}
                    #
                    jnt_pl = jnt.Reference1[0].Placement * jnt.Placement1
                    jnt_plb = roundvec(jnt_pl.Base)
                    jnt_plr = roundrot(jnt_pl.Rotation.toEuler())
                    if dbg_s:
                        fcl_msg(f"{jnt_k}: Placement.Base {jnt_plb} \n")
                        fcl_msg(f"{jnt_k}: Placement.Rot {jnt_plr} \n")
                    self.rbm_dt[jnt_k]['jcs_pl'] = [jnt_plb, jnt_plr]
            #
            # fcl_msg(f"rbm_dt: {self.rbm_dt}\n")  #  DBG
            #
            if self.get_chb_content("gb_bt_wd", "chb_ast"):
                self.analyze_faces(self.face_objs)
            else:
                # TODO: finish the logic for the non automatic detection.
                self.select_lcs_ui()
        else:
            # TODO: add a message to signal the fail?
            pass
        d_doc.recompute()
        setview(d_doc.Name, 1)
        #

    # --------------------------------------------
    #              Automatic selection
    # --------------------------------------------

    def analyze_faces(self, face_objs, dbg_s=False):
        """Analyze faces."""
        # dbg_s = True  # DBG
        dbg_o = True  # DBG
        jnt_n = self.rbm_dt['rb_jnts']
        #
        for face in face_objs:
            # fcl_msg(f"AF: {face}\n")  # DBG
            face1 = self.s_doc.getObject(face[1])
            face2 = self.s_doc.getObject(face[2])
            #
            res0 = self.scan_edges(face1, False)
            res1 = self.scan_edges(face2, False)
            if res0 is False or res1 is False:
                # TODO: Add a messagebox to signal the failure
                fcl_msg("something has gone wrong!")
                return
        # fcl_msg(f"rbm_dt: {self.rbm_dt}")
        #
        fc_res = []
        for n in range(jnt_n):
            jnt_i = n + 1
            jnt_nm = f"joint{jnt_i:02d}"
            jnt_data = self.rbm_dt[jnt_nm]
            jnt_c = find_center(jnt_nm, jnt_data)
            fc_res.append([jnt_nm, jnt_c[0], jnt_c[1]])
        #
        if dbg_s:
            dbg_msg = (
                "--------------------------------------------------\n"
                "Analysis results: \n"
                )
            fcl_msg(dbg_msg)
            for res in fc_res:
                fcl_msg(f"{res[0]} {res[1][-1]}  {res[2][-1]}\n")
            fcl_msg("--------------------------------------------------\n")

        fl_ok = True
        for res in fc_res:
            cf1 = res[1][-1][0]
            cf2 = res[2][-1][0]
            if cf1.isEqual(cf2, 0.001):
                self.rbm_dt[res[0]]['center'] = roundvec(cf1)
                # delete transient dat from the dictionary
                del self.rbm_dt[res[0]]['fcc_f1']
                del self.rbm_dt[res[0]]['fcc_f2']
                if dbg_s:
                    fcl_msg(f"{res[0]} center: {cf1}\n")
            else:
                fl_ok = False
                fcl_msg(f"{res[0]} centers don't match!\n")

        if fl_ok:
            log_msg = "<b>--------------- Robot Data --------------</b><br>"
            self.log_msg(log_msg)
            for key in self.rbm_dt.keys():
                self.log_msg(f"<b>-- {key}:<b><br>")
                if key not in ('rb_jnts',):
                    for subkey in self.rbm_dt[key].keys():
                        self.log_msg(
                            (f"--- <b> {subkey}:</b><br>"
                             f"{self.rbm_dt[key][subkey]} <br>"))
            self.vis_asra_on_asd()
            set_wid_en(self, ("btn_jnts_sac", "btn_jnts_crc"))
            #
            self.report_offsets()

        else:
            return None

    def report_offsets(self):
        """Report offsets to check on technical data."""
        jnt_data = []
        rb_jnt = self.rbm_dt['rb_jnts']
        for n in range(rb_jnt):
            jnt_i = n + 1
            jnt_k = f"joint{jnt_i:02d}"
            jnt_data.append(self.rbm_dt[jnt_k]['center'])

        loop = True
        cnt = 0
        prev_coord = VEC0
        coord = [["origin", prev_coord],]
        self.log_msg("<b> </b>----- Offsets -----<br>")
        while loop:
            jnt_cdc = V3(*jnt_data[cnt])
            offs = jnt_cdc - prev_coord
            jnt_nm = f"joint{cnt + 1:02d}"
            fcl_msg(f"{cnt} - {jnt_nm}, {offs}\n")
            self.log_msg(f"-- <b>{jnt_nm}</b> {offs}<br>")
            coord.append([jnt_nm, offs])
            prev_coord = jnt_cdc
            cnt +=1
            if cnt >= len(jnt_data):
                loop = False
                break
        #
        fcl_msg(f"Joint_data: {jnt_data}\n")
        fcl_msg(f"Offsets: {coord}\n")

    def scan_edges(self, face, dbg_s=False):
        """Scan edges to find some common center."""
        fc_nm = face.Name
        jnt_n = fc_nm[6:8]
        jnt_k = f"joint{jnt_n}"
        fc_n = fc_nm[10:11]
        if dbg_s:
            fcl_msg(f"---->  joint {jnt_n} >> face {fc_n} {fc_nm}\n")
        face_sh = face.Shape.OuterWire
        # TODO: Add some chek if outerwire is returning a correct wire?
        fcc = []
        for e_idx, edge in enumerate(face_sh.Edges):
            e_c = edge.Curve
            if e_c.TypeId == "Part::GeomCircle":
                ecc = e_c.Center
                if dbg_s:
                    fcl_msg(f"-- Edge {e_idx} Center  {ecc}\n")
                fcc.append(roundvec(ecc))
        if fcc != []:
            self.rbm_dt[jnt_k][f"fcc_f{str(fc_n)}"] = fcc
            return True
        else:
            return False

    # --------------------------------------------
    #               Manual selection
    # --------------------------------------------

    def select_lcs_ui(self, dbg_s=False):
        """Select the correct LCS for a Face."""
        # dbg_s = True  # DBG
        gb_obj = self.findChild(QObject, "tp_gb0_wd")
        gb_objl = self.findChild(QObject, "tp_gb0_l")

        if dbg_s:
            fcl_msg(f"Widget: {gb_obj}\n")
            fcl_msg(f"Layout: {gb_objl}\n")

        gb_obj.setTitle("LCS Selection")

        brow = 0
        for f_data in self.face_objs:
            fcl_msg(f_data)
            j_sn = f_data[0] + 1
            lbl_jname = cm_lbl(
                self, f"lbl_jn{j_sn:02d}gl", f"Joint{j_sn:02d}", self.fnt, 2, 1)
            lbl_jname.setStyleSheet(self.lab_ss)

            gb_objl.addWidget(lbl_jname, brow, 0, 1, 1)

            lbl_jn_f1 = cm_lbl(
                self, f"lbl_jn{j_sn:02d}f1", "F1", self.fnt, 2, 1)
            lbl_jn_f1.setStyleSheet(self.lab_ss)
            # print(f"{lbl_jn_f1.objectName()} created\n")  # DBG

            gb_objl.addWidget(lbl_jn_f1, brow, 1, 1, 1)

            btn_vf1_sel = cm_btn(self, f"btn_vf1_sel{j_sn:02d}", "Vis F1", self.fnt, 0)
            gb_objl.addWidget(btn_vf1_sel, brow, 2, 1, 1)
            btn_vf1_sel.clicked.connect(self.vis_face)

            lbl_jn_f2 = cm_lbl(
                self, f"lbl_jn{j_sn:02d}f2", "F2", self.fnt, 2, 1)
            lbl_jn_f2.setStyleSheet(self.lab_ss)
            # print(f"{lbl_jn_f2.objectName()} created\n")  # DBG

            gb_objl.addWidget(lbl_jn_f2, brow, 3, 1, 1)

            btn_vf2_sel = cm_btn(self, f"btn_vf2_sel{j_sn:02d}", "Vis F2", self.fnt, 0)
            gb_objl.addWidget(btn_vf2_sel, brow, 4, 1, 1)
            btn_vf2_sel.clicked.connect(self.vis_face)

            btn_s_sel = cm_btn(self, f"btn_s_sel{j_sn:02d}", "Select", self.fnt, 0)
            gb_objl.addWidget(btn_s_sel, brow, 5, 1, 1)
            btn_s_sel.clicked.connect(self.sel_face)
            #
            brow += 1

            gb_objl.setColumnMinimumWidth(1, self.lb_em * 1.25)
            gb_objl.setColumnMinimumWidth(3, self.lb_em * 1.25)

        btn_e_sel = cm_btn(self, "btn_end_sel", "End Selection", self.fnt, 0)
        gb_objl.addWidget(btn_e_sel, brow, 0, 1, 2)
        btn_e_sel.clicked.connect(self.end_selection)

    # --------------------------------------------
    #               Actions functions
    # --------------------------------------------

    def chb_mgmt(self):
        """Called when a checkbox is changed."""
        pass

    # --------------------------------------------
    #               Various functions
    # --------------------------------------------

    def copy_asm(self, asm_obj, dbg_s=False):
        """Copy assembly file."""
        file_name = asm_obj.Document.FileName
        asm_name = asm_obj.Name
        if dbg_s:
            fcl_msg(f"Original file name: {file_name}\n")
        fn_obj = pathlib.Path(file_name)
        # NOTE: this to debug path resolution in case of problems, KEEP HERE
        # fcl_msg(f"parent: {fn_obj.parent} stem: {fn_obj.stem} suffix: {fn_obj.suffix}\n")  # DBG
        new_fn = fn_obj.parent.joinpath(f"{str(fn_obj.stem)}_copy{str(fn_obj.suffix)}")
        if dbg_s:
            fcl_msg(f"New file_name: {new_fn}\n")
        #
        # NOTE: it should work prior of python 3.14 introduction of copy()
        new_fn.write_bytes(fn_obj.read_bytes())
        App.closeDocument(asm_obj.Document)
        doc_obj = App.openDocument(str(new_fn))
        asm_nobj = doc_obj.getObject(asm_name)
        return asm_nobj

    def log_msg(self, msg):
        """Write log message in both log tab and msg_log."""
        global msg_log
        self.log_win.append(msg)
        msg_log.append(msg)

    def vis_face(self, dbg_s=False):
        """Visualize selected face."""
        gb_obj = self.findChild(QObject, "tp_gb0_wd")
        Gui.Selection.removeSelectionGate()
        # dbg_s = True  # DBG
        call_id = self.sender().objectName()
        #
        if dbg_s:
            fcl_msg(f"{call_id} button clicked\n")  # DBG

        o_n = call_id[-2:]
        jn_idx = int(o_n) - 1
        fc_idx = int(call_id[6:7])
        if dbg_s:
            fcl_msg(f"jdata index: {jn_idx}\n")
            fcl_msg(f"face index: {fc_idx}\n")
        #
        lbl_nm = f"lbl_jn{o_n}f{fc_idx}"
        self.eus = lbl_nm
        wid = gb_obj.findChild(QLabel, lbl_nm)
        # fcl_msg(f"wid: {wid}")  # DBG
        if wid is not None:
            set_wd_prop(wid, "role", "edit")
        else:
            fcl_msg(f"object: {lbl_nm} not found!\n")

        fc_nm = self.face_objs[jn_idx][fc_idx]
        fc_obj = self.s_doc.getObject(fc_nm)

        # if fc_idx == 1:
        #     obj2 = self.s_doc.getObject(self.face_objs[jn_idx][2])
        # elif fc_idx == 2:
        #     obj2 = self.s_doc.getObject(self.face_objs[jn_idx][1])
        # else:
        #     return
        #
        self.reset_vis_prop(False)
        fc_obj.ViewObject.Transparency = 0
        fc_obj.ViewObject.OnTopWhenSelected = u"Enabled"
        fc_obj.ViewObject.Selectable = True
        #
        if dbg_s:
            fcl_msg(f"Object: {fc_nm}, {fc_obj.Name} \n")

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.s_doc.Name, fc_obj.Name, "")
        Gui.SendMsgToActiveView("ViewSelection")
        Gui.SendMsgToActiveView("AlignToSelection")
        # activate the selection filter
        Gui.Selection.addSelectionGate("SELECT Part::Feature SUBELEMENT Edge")
        Gui.Selection.clearSelection()

    def show_asm_rac(self):
        """Show Robot Assembly rotation centers."""
        jnt_n = self.rbm_dt['rb_jnts']
        asm_doc = self.wk_asm.Document
        for n in range(jnt_n):
            jnt_i = n + 1
            jnt_k = f"joint{jnt_i:02d}"
            ra_pl = self.rbm_dt[jnt_k]['jcs_pl']
            # jnt_normal = ra_pl[1]
            # NOTE: this is cheating as the normal of the assembly is strange
            jnt_normals = self.rbm_dt[jnt_k]['normals']
            show_rotaxis(
                asm_doc, "AS_Orig_Rot_axes", jnt_k, ra_pl[0], jnt_normals[0],
                self.rad_raoclr, self.rad_rashl, self.rad_rarad)

    def vis_asra_on_asd(self):
        """Visualize calculated rotaxis on assembly service doc."""
        rb_jnt = self.rbm_dt['rb_jnts']
        for n in range(rb_jnt):
            jnt_i = n + 1
            jnt_k = f"joint{jnt_i:02d}"
            if ('center' in self.rbm_dt[jnt_k].keys()
                and 'normals' in self.rbm_dt[jnt_k].keys()):
                #
                jnt_cent = self.rbm_dt[jnt_k]['center']
                jnt_normals = self.rbm_dt[jnt_k]['normals']
                show_rotaxis(
                    self.s_doc, "Rot_axes", jnt_k, jnt_cent, jnt_normals[0],
                    self.as_raclr, self.as_rashl, self.as_rarad)
                if self.get_chb_content("gb_bt_wd", "chb_sara"):
                    ra_pl = self.rbm_dt[jnt_k]['jcs_pl']
                    show_rotaxis(
                        self.s_doc, "AS_Orig_Rot_axes",
                        jnt_k, ra_pl[0], jnt_normals[0],
                        self.rad_raoclr, self.as_rashl * 1.15, self.rad_rarad)

    def vis_asra_on_asm(self):
        """Visualize service rota axis on Assembly doc."""
        rb_jnt = self.rbm_dt['rb_jnts']
        asm_doc = self.wk_asm.Document
        for n in range(rb_jnt):
            jnt_i = n + 1
            jnt_k = f"joint{jnt_i:02d}"
            if ('center' in self.rbm_dt[jnt_k].keys()
                and 'normals' in self.rbm_dt[jnt_k].keys()):
                #
                jnt_cent = self.rbm_dt[jnt_k]['center']
                jnt_normals = self.rbm_dt[jnt_k]['normals']
                show_rotaxis(
                    asm_doc, "AS_Rot_axes", jnt_k, jnt_cent, jnt_normals[0],
                    self.as_raclr, self.rad_rashl * 0.75, self.as_rarad)

    def end_selection(self):
        """End selection."""
        Gui.Selection.removeSelectionGate()
        set_wid_en(self, "btn_jnts_ana")

    def analyze_lcs(self, dbg_s=False):
        # dbg_s = True  # DBG
        if self.s_doc is None:
            s_doc = App.ActiveDocument
            if s_doc is None:
                msg_box(
                    self, "RBS", self.fnt,
                    ("<b>Select a document containing Joints LCS</b><br><br>"
                     "And press this button again"))
                return
            else:
                if "DocType" in s_doc.PropertiesList:
                    self.s_doc = s_doc
                else:
                    msg_box(
                        self, "RBS", self.fnt,
                        ("<b>Select a document containing Joints LCS</b><br><br>"
                         "And press this button again"))
                    return

        doc_lcs = []
        has_fcsg = False
        has_lcs = False
        all_good = False
        for dobj in self.s_doc.Objects:
            if dobj.TypeId == "Part::LocalCoordinateSystem":
                if dbg_s:
                    fcl_msg(f"DObj Name: {dobj.Name}\n")
                    fcl_msg(f"- Label: {dobj.Label}\n")
                    fcl_msg(f"- TypeId: {dobj.TypeId}\n")
                if dobj.Label[:10] == "LCS_rb_jnt":
                    doc_lcs.append(dobj)
            elif dobj.TypeId == "App::DocumentObjectGroup" and dobj.Name == "joints_faces":
                has_fcsg = True
        # check the lcs
        if doc_lcs != []:
            has_lcs = True
            lcs_ln = len(doc_lcs)
            fcl_msg(f"There are {lcs_ln} elements in the list\n")
        # Check the number of faces
        if has_fcsg:
            fcs_obj = self.s_doc.getObject("joints_faces")
            fcs_ln = len(fcs_obj.OutList)
            fcl_msg(f"There are {fcs_ln} elements in the face list\n")

        if has_lcs and has_fcsg:
            fcl_msg("Document with all the elements\n")
            if lcs_ln == fcs_ln:
                fcl_msg("Equal number of lcs and faces\n")
                all_good = True
            else:
                fcl_warn("Not Equal number of lcs and faces\n")

        else:
            fcl_warn("Some elements are missing\n")

        if all_good:
            self.validate_joints(doc_lcs)

    def sel_face(self, dbg_s=False):
        """Select entity on face."""
        # dbg_s = True  # DBG
        gb_obj = self.findChild(QObject, "tp_gb0_wd")
        # fcl_msg(f"Sel face: {gb_obj} \n")  # DBG
        call_id = self.sender().objectName()
        # fcl_msg(f"{call_id} button clicked\n")  # DBG
        selx = Gui.Selection.getSelectionEx()
        sel_n = len(selx)
        o_n = int(call_id[-2:])
        #
        if dbg_s:
            fcl_msg(
                (
                    f"calID: {call_id}, num_sel: {sel_n},"
                    f"Obj_n: {o_n} eus {self.eus}\n"
                )
            )
        #
        if sel_n > 0:
            s0 = selx[0]
            obj = s0.Object
            sub_ent = s0.SubElementNames
            if dbg_s:
                fcl_msg(f"obj_name: {obj.Name}\n")
            if len(sub_ent) == 1:
                subname = s0.SubElementNames[0]
                tupl = (obj, subname)
                jnt_nm = obj.Name[:11]
                if dbg_s:
                    fcl_msg(f"Obj_Name: {jnt_nm}\n")
                set_lcs(self.s_doc, tupl, jnt_nm)
                wid = gb_obj.findChild(QLabel, self.eus)
                if dbg_s:
                    fcl_msg(f"wid: {wid}\n")
                if wid is not None:
                    set_wd_prop(wid, "role", "done")
                else:
                    fcl_msg(f"object: {self.eus} not found!\n")
            else:
                msg_box(
                    self, "RBS", self.fnt,
                    (f"<b>Select Face Element for Joint{o_n}</b><br><br>"
                     "You must select one element only"))

        else:
            msg_box(
                self, "RBS", self.fnt,
                (f"<b>Select Face Element for Joint{o_n}</b><br><br>"
                 "You must select something"))
        #
        Gui.Selection.removeSelectionGate()
        self.reset_vis_prop(True)
        return

    def reset_vis_prop(self, state):
        """Reset face visualization properties."""
        if state:
            tval = 0
            otws = u"Enabled"
            sstate = True
        else:
            tval = 95
            otws = u"Disabled"
            sstate = False

        for fobj in self.face_objs:
            obj1 = self.s_doc.getObject(fobj[1])
            obj2 = self.s_doc.getObject(fobj[2])
            obj1.ViewObject.Transparency = tval
            obj1.ViewObject.OnTopWhenSelected = otws
            obj1.ViewObject.Selectable = sstate
            #
            obj2.ViewObject.Transparency = tval
            obj2.ViewObject.OnTopWhenSelected = otws
            obj2.ViewObject.Selectable = sstate

    def set_working_asm(self):
        """Set working asm."""
        raw_sel = Gui.Selection.getSelection("", 2, True)
        esn = len(raw_sel)
        # fcl_msg(raw_sel)

        if esn == 0:
            msg_box(
                self, "Robot", self.fnt,
                "<b>Robot Selection</b><br><br>You must select at least one element")
            return
        elif esn == 1:
            Gui.Selection.clearSelection()
            obj = raw_sel[0]
            obj_typ = obj.TypeId
            if obj_typ == "Assembly::AssemblyObject":
                setview(obj.Document.Name, 1)
                self.wk_asm = obj
                self.txt_rbnm.setText(obj.Label)
                switch_document(obj.Document.Name)
            else:
                msg_box(
                    self, "Robot", self.fnt,
                    ("<b>Robot Selection</b><br><br>"
                     "You must select an Assembly element"))
                return

    def set_working_rbt(self):
        """Load the Assembly specified in Robot FPO as work_asm."""
        self.wk_asm = self.rob_obj.Robot_assembly
        switch_document(self.wk_asm.Document.Name)

    def validate_joints(self, doc_lcs):
        """Validate joints."""
        for elem in doc_lcs:
            elp = elem.Placement.Base
            elpr = roundvec(elp)
            print(f"{elem.Label} >> {elpr}\n")

    # --------------------------------------------
    #                Other functions
    # --------------------------------------------

    def act_dump_log(self):
        """Executed when "Dump Log is pressed."""
        if self.isInit is True:
            return
        tm_st = datetime.strftime(datetime.now(), mdtsp)
        log_fn = f"study_robot_{tm_st}.log"
        self.log_fn = pathlib.Path(MODULE_PATH.joinpath(log_fn))
        dump_log(self.log_fn)


def run():
    dialog = O2PDialog()
    dialog.show()

# Executed if not imported as module


if __name__ == "__main__":
    dialog = O2PDialog()
