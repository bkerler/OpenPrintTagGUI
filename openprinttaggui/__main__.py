#!/usr/bin/env python3
import os
import sys
from PySide6.QtWidgets import QApplication
from openprinttaggui.openprinttag_gui import GUI_OpenPrintTag

if __name__ == "__main__":
    app = QApplication(sys.argv)
    info = "OpenPrintTagGUI v1.02 (c) B.Kerler"
    app.setApplicationName(info)
    widget = GUI_OpenPrintTag()
    widget.setWindowTitle(info)
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if os.path.exists(filename):
            data = open(filename, "rb").read()
            widget.load_data(data)
        else:
            print(f"Filename {filename} doesn't exist ! Aborting ...")
            sys.exit(1)
    widget.show()
    sys.exit(app.exec())
