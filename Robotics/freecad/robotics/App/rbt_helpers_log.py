"""Console logging to FreeCAD's Report Viewer Panel"""

import FreeCAD as App  # type: ignore

fcl_msg = App.Console.PrintMessage
fcl_warn = App.Console.PrintWarning
fcl_err = App.Console.PrintError
