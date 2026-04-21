import os
import FreeCADGui as Gui
import FreeCAD as App
from . import tb_commands

from freecad.Robot_tools.rbt_objects import Robot_obj, ViewProviderRBo

fc_log_msg = App.Console.PrintMessage

tb_pstr = "User parameter:BaseApp/Workbench/Global/Toolbar"
tb_vers = 1.04
tb_name = "Robot Tools Toolbar"
pg_name = "Robot_tools"

tb_cmds = [("RBT_defrob", "RBT"), ("RBT_crob", "RBT"), ("RBT_strob", "RBT"),
           ("RBT_anrob", "RBT")]

gtb_grp = App.ParamGet(tb_pstr)


def check_tb(tb_grp):
    """Check the toolbar existence."""
    grp_nm = tb_grp.GetGroupName()
    if tb_grp.GetString('Name') == tb_name:
        fc_log_msg(f"RBT group: {grp_nm}\n")
        if check_vers(tb_grp) is True:
            return True
        else:
            create_tb(tb_grp)
    else:
        return False


def check_vers(tb_grp):
    """Check toolbar version."""
    vers = tb_grp.GetFloat('Vers')
    fc_log_msg(f"RBT version: {vers}\n")
    if vers < tb_vers:
        fc_log_msg("RBT version outdated\n")
        fc_log_msg(f"new version {tb_vers}\n Recreating the ToolBar")
        tb_grp.Clear()
        return False
    fc_log_msg("RBT version OK")
    return True


def create_tb(tb_grp):
    """Create the Toolbar."""
    tb_grp.SetString("Name", tb_name)
    tb_grp.SetBool("Active", True)
    tb_grp.SetFloat("Vers", tb_vers)
    # add commands
    for tb_cmd in tb_cmds:
        tb_grp.SetString(tb_cmd[0], tb_cmd[1])


# ------------------------------------------------
#                   init_toolbar
# ------------------------------------------------


tb_is_cust1 = False

if gtb_grp.HasGroup("Custom_1"):
    # print("Custom_1 group exists!")
    cust_grp = App.ParamGet(tb_pstr + "/Custom_1")
    # print(dir(cust_grp))
    if check_tb(cust_grp) is True:
        tb_is_cust1 = True
    else:
        print("Custom_1 is not our tb")

if tb_is_cust1 is False:
    if gtb_grp.HasGroup(pg_name):
        tb_grp = App.ParamGet(tb_pstr + "/" + pg_name)
        if check_tb(tb_grp) is True:
            pass
    else:
        tb_grp = App.ParamGet(tb_pstr + "/" + pg_name)
        create_tb(tb_grp)
