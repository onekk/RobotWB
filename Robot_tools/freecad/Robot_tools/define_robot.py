"""Robot Test.

Name: study_asm.py

See Changelog below.

Author: Carlo Dormeletti
Copyright: 2026
Licence: All right reserved
"""
__version__ = "0.06"
__build__ = "20260421_1903"


import sys
if sys.version_info.major >= 3:
    from importlib import reload

import pathlib

from datetime import datetime

import FreeCAD as App
import FreeCADGui as Gui
import Part

# Assembly imports
import UtilsAssembly
import JointObject

# Coin3d import
from pivy import coin

import PySide

from PySide import QtGui, QtCore  # noqa  # QtWidgets
from PySide.QtWidgets import (  # noqa
    QApplication, QCheckBox,  QFrame, QGroupBox, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QSpinBox, QTabWidget, QTextEdit, QWidget,  # Widgets
    QDialog, QFileDialog, QInputDialog, QMessageBox,  # Dialogs
    QGridLayout, QVBoxLayout, QSizePolicy)  # Layouts and Policy

from PySide.QtCore import QObject, Qt  # noqa

from freecad.Robot_tools.rbt_constants import ap_clr

from freecad.Robot_tools.rbt_helpers_ui import (
    cm_chb, cm_gbx, cm_btn,
    cm_lbl, cm_ledit, cm_txt,
    getObjByName,set_wid_text, set_wid_en,
    msg_box, get_file, get_dir
)

from freecad.Robot_tools.rbt_helpers_doc import (
    clear_doc, ensure_document, setview, switch_document
)

from freecad.Robot_tools.rbt_helpers_math import roundrot, roundvec

from freecad.Robot_tools.rbt_objects import Robot_obj, ViewProviderRBo

"""
----------------------------------------
Changelog:
----------------------------------------
v0.01 - Initial version.
v0.02 - Added create_asm code.
v0.03 - Added add joint action (unfinished).
v0.04 - Added some refinement in UI and various.
v0.05 - Added actions needed when loading an asm doc:
         - check the asm document for "big errors" like the absence of Robot_FPO
           and Robot_Assembly object.
         - check for empty joints and signal it with a messagebox.
v0.06 - added code to add joints (grounded).
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

msg_log = []  # log message container, used to permit a dump.

# ------------------------------------------------
#                 Module functions
# ------------------------------------------------


def dump_log(log_fn):
    """Dump log to a file."""
    fcl_msg(f"Log file name: {log_fn}")

# ------------------------------------------------
#                Assembly functions
# ------------------------------------------------


def add_asm_object(obj_doc, asm, feat_nm, link_nm, glbl):
    item = asm.newObject("App::Link", link_nm)
    item.LinkedObject = obj_doc.getObject(feat_nm)
    item.Label = glbl
    item.recompute()
    asm.recompute()
    return item


def add_grounded(asm, obj):
    """Add the grounded object."""
    joint_group = UtilsAssembly.getJointGroup(asm)
    ground = joint_group.newObject("App::FeaturePython", "GroundedJoint")
    JointObject.GroundedJoint(ground, obj)
    JointObject.ViewProviderGroundedJoint(ground.ViewObject)
    asm.recompute()


def add_revolute(asm, j_lbl, plt1, plr1, plt2, plr2, ref1, ref2,
                 ofs1=Placement(VEC0, ROT0), ofs2=Placement(VEC0, ROT0)):
    """Add the grounded object."""
    joint_group = UtilsAssembly.getJointGroup(asm)
    rev_j = joint_group.newObject("App::FeaturePython", "RevoluteJoint")
    JointObject.Joint(rev_j, 1)
    JointObject.ViewProviderJoint(rev_j.ViewObject)
    rev_j.recompute()
    rev_j.Detach1 = False
    rev_j.Detach2 = False
    rev_j.EnableAngleMax = False
    rev_j.EnableAngleMin = False
    rev_j.EnableLengthMax = False
    rev_j.EnableLengthMin = False
    rev_j.JointType = "Revolute"
    rev_j.Label = j_lbl
    rev_j.Label2 = ""
    rev_j.Offset1 = ofs1
    rev_j.Offset2 = ofs2
    rev_j.Placement1 = Placement(plt1, plr1)
    rev_j.Placement2 = Placement(plt2, plr2)
    rev_j.Reference1 = ref1
    rev_j.Reference2 = ref2
    rev_j.Suppressed = False
    rev_j.Visibility = False
    rev_j.recompute()
    return rev_j


def create_assembly(doc):
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    asm.Label = "Robot_Assembly"
    asm.Type = "Assembly"
    asm.newObject("Assembly::JointGroup", "Joints")
    asm.recompute()
    return asm


# ------------------------------------------------
#            Assembly helpers functions
# ------------------------------------------------

def set_pose(asm_obj):
    """Set pose to the standard one."""
    for j_n, jnt in enumerate(asm_obj.Joints):
        jnt_o2 = jnt.Offset2
        fcl_msg(f"{j_n} {jnt.Label}\n")
        fcl_msg(f"OF2:  {jnt_o2}\n")
        jnt.Offset2 = Placement(VEC0, Rotation(1, 0, 0)).multiply(jnt_o2)
        asm_obj.recompute()
        jnt.Offset2 = jnt_o2
        asm_obj.recompute()

# ------------------------------------------------
#                    Main Dialog
# ------------------------------------------------


class O2PDialog(QDialog):
    """Show a dialog for RobotAnimator."""

    ui_title = "Define Robot"
    IsInit = False  # flag to avoid unwanted action execution during init.
    # Flags dictionary, place here sane defaults
    flags = {"chb_cpa": False, }
    #
    tab_data = {
        "ma": {"nm": "Main", "cn": 0}, "lg": {"nm": "Log", "cn": 0}}
    #
    wk_mod = None  # Working model
    wk_asm = None  # Robot model as Assembly DO
    wk_asm_d = None  # Robot Assembly Document
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
    # --- Joint sequence control ---
    jnt_ec = 0  # joint edit counter, indicate what joint we are editing.
    jnt_fc = 1  # joint face counter it will be reset by add_jnt_asm code
    jnt_meta = {}  # joint metadata it will be reset by add_jnt_asm code
    #
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
        av_geom = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        av_wid = av_geom.width()
        av_hei = av_geom.height()
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
        # ma_tab = self.tabw.findChild(QObject, "t_ma")

        fcl_msg(f"isWBcomp {self.isWBcomp}\n ")  # DBG

        row = 0

        # groupBox helper
        def _make_gbx(name, desc):
            gb, gbl = cm_gbx(self, name, desc)
            gb.setStyleSheet(self.grb_ss)
            gb.setLayout(gbl)
            return gb, gbl

        # -- Robot Files --
        gb_rc, gb_rcl = _make_gbx("gb_rc", "Robot Files")
        self.flags['rob_fpo'] = True

        selection_rows = [
            # rob components file selection
            ("txt_rbnm", "btn_selrbf", "btn_sel_rbf", "Select 'Component' file",
             "Select the FCStd file that contains the robot components.", self.set_working_model),

            # rob assembly file selection
             ("txt_asnm", "btn_selasm", "btn_sel_asm", "Select 'Assembly' file",
             "Select the FCStd file that contains Robot_Assembly and the Robot_FPO.", self.set_working_asm),
        ]
        brow = 0
        for txt_name, btn_name, btn_attr, btn_lbl, tool_tip, callback in selection_rows:
            txt = cm_ledit(self, txt_name, self.fnt, 0)
            gb_rcl.addWidget(txt, brow, 0, 1, 4)
            setattr(self, txt_name, txt)
            brow += 1

            btn = cm_btn(self, btn_name, btn_lbl, self.fnt, 0)
            btn.setToolTip(tool_tip)
            btn.clicked.connect(callback)
            gb_rcl.addWidget(btn, brow, 0, 1, 2)
            setattr(self, btn_attr, btn)
            brow += 1
        
        ma_lay.addWidget(gb_rc, row, 0, 1, 4)
        row += 1

        # -- Functions --
        gb_bt, gb_btl = _make_gbx("gb_bt", "Functions")
        func_btns = [
            ("btn_cre_asm", "Create ASM", self.create_asm),
            ("btn_load_step", "Load STEP", self.act_load_step),
            ("btn_add_jnt", "Add Joints", self.act_add_joint),
        ]

        brow = 0
        for btn_name, btn_lbl, callback in func_btns:
            btn = cm_btn(self, btn_name, btn_lbl, self.fnt, 0)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            gb_btl.addWidget(btn, brow, 0, 1, 2)
            brow += 1

        ma_lay.addWidget(gb_bt, row, 0, 1, 4)
        row += 1
        
        # -- Empty Spacer --
        tp_gb0, _ = _make_gbx("tp_gb0", "")

        ma_lay.addWidget(tp_gb0, row, 0, 1, 4)
        row += 1

        # -- Joints --
        jn_gb0, jn_gb0l = _make_gbx("jn_gb0", "Joints")
        headers = ["Joint", "Type", "Face1", "Face2"]
        brow = 0
        for header in headers:
            lbl = cm_lbl(self, f"lbl_jnspc{brow}", f"<b>{header}</b>", self.fnt, 0)
            jn_gb0l.addWidget(lbl, 0, brow, 1, 1)
            brow += 1
        
        ma_lay.addWidget(jn_gb0, row, 0, 1, 4)
        row += 1

        ma_lay.setRowStretch(row, 1)
        return True

    def jnt_setui(self):
        """Create the add joint UI."""
        wid = self.findChild(QObject, "tp_gb0_wd")
        wid.setTitle("Set Joints")
        lay = self.findChild(QObject, "tp_gb0_l")
        row = 0
        js_gb0, js_gb0l = cm_gbx(self, "js_gb0", "Add Joint")
        js_gb0.setStyleSheet(self.grb_ss)
        # Empty groupBox
        js_gb0.setLayout(js_gb0l)
        brow = 0
        btn_jnt_s1 = cm_btn(self, "btn_jnt_s1", "Select Face1", self.fnt, 0)
        btn_jnt_s1.setEnabled(True)
        js_gb0l.addWidget(btn_jnt_s1, brow, 0, 1, 2)

        btn_jnt_s1.clicked.connect(self.select_face)

        btn_jnt_s2 = cm_btn(self, "btn_jnt_s2", "Select Face2", self.fnt, 0)
        btn_jnt_s2.setEnabled(False)
        js_gb0l.addWidget(btn_jnt_s2, brow, 2, 1, 2)

        btn_jnt_s2.clicked.connect(self.select_face)

        brow += 1
        chb_sgj = cm_chb(self, "chb_sgj", "Grounded Joint", self.fnt, True)
        js_gb0l.addWidget(chb_sgj, brow, 0, 1, 2)
        chb_sgj.setChecked(True)

        brow += 1
        btn_jnt_add = cm_btn(self, "btn_jnt_add", "Add Joint", self.fnt, 0)
        btn_jnt_add.setEnabled(False)
        js_gb0l.addWidget(btn_jnt_add, brow, 0, 1, 2)

        btn_jnt_add.clicked.connect(self.add_jnt2asm)

        lay.addWidget(js_gb0, row, 0, 1, 4)

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

    def add_joint2ui(self, jpr, j_data):
        """Add a joint to the panel.

        Parameters:
          jpr (int):  row number
          j_data (list): joint column data (see in the code)

        """
        wid = self.findChild(QObject, "jn_gb0_wd")
        lay = self.findChild(QObject, "jn_gb0_l")
        #
        # Data: [number, type, face1, face2]
        names = ("lbl_jnt", "lbl_jt", "lbl_jf1", "lbl_jf2")

        for idx, (name,val) in enumerate(zip(names, j_data)):
            lbl = cm_lbl(self, f"{name}{jpr}", str(val), self.fnt, 0)
            lbl.setFrameShape(QFrame.Shape.Panel)
            lbl.setFrameShadow(QFrame.Shadow.Sunken)
            lbl.setStyleSheet("QLabel {background-color: white;}")
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
            lay.addWidget(lbl, jpr, idx, 1, 1)

    # --------------------------------------------
    #                Model functions
    # --------------------------------------------

    def _open_doc(self, doc_name, attr):
        """helper for setting robot/assm. models"""
        f_name = get_file(self, self.fnt, ftype="fcstd", pre_dir="")
        # fcl_msg(f"Set working model: {f_name}\n")
        if not f_name: 
            return None
        o_doc = App.openDocument(f_name)
        fcl_msg(f"open doc: {o_doc}\n")
        setattr(self, attr, o_doc)
        wid = getObjByName(self, doc_name)
        if wid is None:
            return None
        wid.setText(str(f_name))
        return o_doc

    def set_working_model(self):
        """Set robot working model."""
        if self._open_doc("txt_rbnm", "wk_mod"):
            set_wid_en(self, ("btn_cre_asm",), True)

    def set_working_asm(self):
        """Set robot assembly file."""
        o_doc = self._open_doc("txt_asnm", "wk_asm_d")
        if o_doc:
            self.check_asm()
            setview(o_doc.Name)

    # --------------------------------------------
    #                Assembly functions
    # --------------------------------------------

    def create_asm(self):
        """Add Joint to assembly."""
        # dbg_s = False
        dbg_s = True

        # Step1: ask for a name?
        asm_doc_name = "Asm_doc_test"

        # Step2: create the ASM doc (and save it)
        doc_name = self.wk_mod.FileName
        if dbg_s:
            fcl_msg(f"Robot file folder: {doc_name}\n")
        #
        file_dir = pathlib.Path(doc_name).parent
        if dbg_s:
            fcl_msg(f"Assembly file folder: {file_dir}\n")
        #
        doc_rname = ensure_document(asm_doc_name, 1)
        asm_doc = App.getDocument(doc_rname)
        gui_doc = Gui.getDocument(doc_rname)

        asm_doc.saveAs(str(pathlib.Path(file_dir, doc_rname)))

        asm = create_assembly(asm_doc)
        gui_doc.ActiveView.setActiveObject('assembly', asm)

        asm_doc.recompute()

        # Step3: create the FPO in the ASM doc

        rb_obj = asm_doc.addObject(
            "App::FeaturePython", "Robot_FPO")

        Robot_obj(rb_obj)
        # if App.GuiUp:
        ViewProviderRBo(rb_obj.ViewObject)

        rb_obj.Robot_assembly = asm

        rb_obj.recompute()
        asm_doc.recompute()
        # Disable "Create ASM" button
        set_wid_en(self, ("btn_cre_asm",), False)
        # Enable "Add joint" button
        set_wid_en(self, ("btn_add_jnt",), True)

    def act_add_joint(self):
        """Add Joint panel assembly."""
        self.jnt_setui()
        self.jnt_ec = 0
        return

    def act_load_step(self):
        """Load Step file."""
        sf = self.rob_obj.STEPFile
        # fcl_msg(f"STEPFile: {sf}\n")
        App.openDocument(sf)

    def check_asm(self):
        """Check the correctness of the asm file."""
        asm_objs = self.wk_asm_d.getObjectsByLabel("Robot_Assembly")
        ran = len(asm_objs)
        if ran > 0:
            pass
        else:
            msg_box(
                self, "Robot_tools", self.fnt,
                ("<b>There are no Robot Assembly definitions in the document</b>"
                 "<br><br> You must select a correct document or create one"))
            # FIXME: See if the activation of Create ASM button is correct here.
            set_wid_en(self, ("btn_cre_asm",), True)
            return

        if ran == 1:
            self.wk_asm = asm_objs[0]
        else:
            msg_box(
                self, "Robot_tools", self.fnt,
                (f"<b>There are: [{ran}] Robot Assembly objects "
                 "in the document</b><br><br>"
                 "You must select one"))
            # TODO: add the corresponding selection dialog.
            return

        rob_objs = self.wk_asm_d.getObjectsByLabel("Robot_FPO")
        ron = len(rob_objs)
        if ron > 0:
            if ron == 1:
                self.rob_obj = rob_objs[0]
            else:
                msg_box(
                    self, "Robot_tools", self.fnt,
                    (f"<b>There are: [{ron}] FPO in the assembly</b><br><br>"
                     "You must select the working one"))
                # TODO: create the selection dialog
                return
        else:
            msg_box(
                self, "Robot_tools", self.fnt,
                ("<b>There are no Robot FPO in the assembly</b><br><br>"
                 "You must select a valid Assembly Robot document"))
            return
        #
        ojl = len(self.wk_asm.Joints)
        if ojl == 0:
            msg_box(
                self, "Robot_tools", self.fnt,
                ("<b>There are no Joints in the assembly</b><br><br>"
                 "You must assign them"))

        # deactivate appropriate buttons
        # TODO: we could deactivate also the "Select Asembly File" button too?
        set_wid_en(self, ("btn_cre_asm", "btn_selrbf"), False)

        # Check if assembly object has only a Joint group on it
        # checking Group property length > 1 will tell if there are other
        # objects
        # FIXME: it is rough guess see if there are alternatives.
        if len(self.wk_asm.Group) > 1:
            set_wid_en(self, ("btn_add_jnt",), True)
            # NOTE: no need to activate the "Load STEP" button as the Document
            # with robot components will be opened by FreeCAD for us.
        else:
            set_wid_en(self, ("btn_add_jnt", "btn_load_step"), True)

        if ojl > 0:
            print(f"obj: {ojl}")

        # TODO: In case of already present joints, we must:
        # 1) alter here jnt_ec value
        # 2) populate the already defined joints
        # 3) if grounded joint is already defined, we must disbale the checkbox?

        return

    # --------------------------------------------
    #                   Add joint
    # --------------------------------------------

    def add_jnt2asm(self):
        """Add a joint to the assembly and the FPO."""
        fcl_msg(f"Joint meta: {self.jnt_meta}\n")
        # NOTE: correct sequence:
        # 1) validate the sequence
        # 2) reset the face counter to 1
        # 3) reset the jnt_meta dic to empty
        # 4) advance jnt_ec by 1
        # 5) set buttons Select Face1 and Select Face2 state
        dks = list(self.jnt_meta)
        jn = int(dks[0][5:7])
        jf = int(dks[0][7:9])
        jid0 = self.jnt_meta[dks[0]]
        if len(dks) == 1:
            fcl_msg(f"Joint number {jn} Face {jf} jid: {jid0}\n")
            # one face selected, so the joint is probably the grounded one.
            if jn == 0:
                # This is probably a grounded joint as it is logically the first
                # to be set.
                jnt_fc1_onm = jid0['ob_nm']
                jnt_fc1_se = jid0['sub_el'][0]
                jnt_obj = self.wk_asm.getObject(jnt_fc1_onm)
                add_grounded(self.wk_asm, jnt_obj)
                self.wk_asm.recompute()
                # Reset the interface
                set_wid_en(self, ("btn_jnt_s1",), True)
                set_wid_en(self, ("chb_sgj",), False)
                # TODO: populate the joint frame with a joint type.
                self.add_joint2ui(jn + 2, [0, "grounded", jnt_fc1_se, "--"])
                # advance joint counter and reset face counter and data dict
                self.jnt_ec += 1
                self.jnt_fc = 1
                self.jnt_meta = {}
            else:
                # Emit an error as two faces are needed
                return

        # NOTE: following code is to add the joint to the ASM
        # add_grounded(asm, base_obj)
        # base_obj.recompute()

        # rev1 = add_revolute(
        #     asm, "Revolute001",
        #     V3(0.0, 317.0, 0.0), Rotation(*[0.0, 0.0, -90.0]),
        #     V3(0.0, 317.0, 0.0), Rotation(*[180.0, 0.0, 90.0]),
        #     [jnt1_obj, ['Face1977', 'Face1977']],
        #     [base_obj, ['Face792', 'Face792']],
        #     Placement(VEC0, Rotation(180, 0, 0)),
        #     Placement(VEC0, ROT0)
        # )

        # rev1.recompute()

    def select_face(self):
        """Select Face."""
        fcl_msg(f"Select Face{self.jnt_fc}\n")
        raw_sel = Gui.Selection.getSelectionEx()
        esn = len(raw_sel)

        if esn == 0:
            msg_box(
                self, "Robot_tools", self.fnt,
                "<b>Joint Face Selection</b><br><br>You must select a Face")
            return False
        elif esn == 1:
            s0 = raw_sel[0]
            obj = s0.Object
            sub_ent = s0.SubElementNames
            obj_typ = obj.TypeId
            fcl_msg((
                f"Obj Name: {obj.Name}\n"
                f"Obj Label: {obj.Label}\n"
                f"Obj Type: {obj_typ}\n"
                f"Obj SubElements: {sub_ent}\n"
            )
            )
            jnt_elnm = f"joint{self.jnt_ec:02d}{self.jnt_fc:02d}"
            self.jnt_meta[jnt_elnm] = {}
            self.jnt_meta[jnt_elnm]["ob_nm"] = obj.Name
            self.jnt_meta[jnt_elnm]["sub_el"] = sub_ent
            #
            if self.jnt_fc == 1:
                self.jnt_fc = 2
                set_wid_en(self, ("btn_jnt_s1",), False)
                set_wid_en(self, ("btn_jnt_s2", "btn_jnt_add"), True)
            else:
                pass

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