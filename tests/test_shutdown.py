import os
from pathlib import Path
import subprocess
import sys
import unittest


class ShutdownTests(unittest.TestCase):
    def test_close_and_quit_stop_detector_before_python_cleanup(self):
        for action in ("window.close()", "app.quit()"):
            with self.subTest(action=action):
                result = subprocess.run(
                    [sys.executable, "-c", f"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from openprinttaggui.openprinttag_gui import GUI_OpenPrintTag
app = QApplication([])
window = GUI_OpenPrintTag()
window.show()
QTimer.singleShot(100, lambda: {action})
app.exec()
assert not window.detector_thread.isRunning()
window.shutdown()
"""],
                    cwd=Path(__file__).resolve().parents[1],
                    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
