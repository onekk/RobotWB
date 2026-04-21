"""Robot Test.

Name: study_asm.py

See Changelog before import statements.

Author: Carlo Dormeletti
Copyright: 2026
Licence: All right reserved
"""
__version__ = "0.01"
__build__ = "20260415_1153"


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

        # Robot File groupBox
        gb_rc, gb_rcl = cm_gbx(self, "gb_rc", "Robot FCStd")
        gb_rc.setStyleSheet(self.grb_ss)
        gb_rc.setLayout(gb_rcl)

        brow = 0

        self.flags['rob_fpo'] = True
        #
        self.txt_rbnm = cm_ledit(self, "txt_rbnm", self.fnt, 0)
        gb_rcl.addWidget(self.txt_rbnm, brow, 0, 1, 2)
        #
        self.btn_sel_asm = cm_btn(self, "btn_seldir", "Select", self.fnt, 0)
        gb_rcl.addWidget(self.btn_sel_asm, brow, 2, 1, 2)

        # self.btn_sel_asm.clicked.connect(self.set_working_asm)

        ma_lay.addWidget(gb_rc, row, 0, 1, 4)

        row += 1

        gb_bt, gb_btl = cm_gbx(self, "gb_bt", "Functions")
        gb_bt.setStyleSheet(self.grb_ss)
        gb_bt.setLayout(gb_btl)

        brow = 0

        # btn_jnts_isp = cm_btn(self, "btn_jnts_isp", "Inspect Joints", self.fnt, 0)
        # gb_btl.addWidget(btn_jnts_isp, brow, 0, 1, 2)

        # # btn_jnts_isp.clicked.connect(self.inspect_joints)

        # chb_ast = cm_chb(self, "chb_ast", "Auto scan", self.fnt, True)
        # gb_btl.addWidget(chb_ast, brow, 2, 1, 2)
        # chb_ast.setChecked(True)

        # chb_sara = cm_chb(
        #     self, "chb_sara", "Show JCS on Service doc", self.fnt, True)
        # chb_sara.setToolTip("Show JCS (Joint Coordinate System) on Service doc.")
        # gb_btl.addWidget(chb_sara, brow, 4, 1, 2)
        # chb_sara.setChecked(True)

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

