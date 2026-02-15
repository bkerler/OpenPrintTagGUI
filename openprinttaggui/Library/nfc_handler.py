from PySide6.QtCore import QObject, Signal, QRunnable, Slot

from openprinttaggui.Library.acs_nfc.acs_hf15 import ACS_HF15
from openprinttaggui.Library.pm3_nfc.pm3_hf15 import PM3_HF15
from openprinttaggui.Library.s9_nfc.s9_hf15 import S9_HF15


class NFC_WorkerSignals(QObject):
    progress = Signal(int)  # Progress percentage (0-100)
    status = Signal(str)  # Status message updates
    finished = Signal(object)  # Emits the tag object on success (or None)
    error = Signal(str)  # Emits error message on failure


class NFC_WriteTagWorker(QRunnable):
    def __init__(self, parent, reader: int, port: str = None):
        super().__init__()
        self.signals = NFC_WorkerSignals()
        self.parent = parent
        self.reader = reader
        self.port = port

    @Slot()
    def run(self):
        self.signals.status.emit("Generating tag data...")
        try:
            tagdata = self.parent.generate_tag_data()
        except Exception as e:
            self.signals.error.emit(f"Failed to generate tag data: {str(e.__notes__)}")
            return

        try:
            if self.reader == 1:
                self.signals.status.emit("Connecting to Proxmark3...")
                dev = PM3_HF15(port=self.port, baudrate=115200, logger=self.signals.status.emit)
            elif self.reader == 2:
                self.signals.status.emit("Connecting to S9...")
                dev = S9_HF15(port=self.port, logger=self.signals.status.emit)
                if dev.getUID() == b"":
                    self.signals.error.emit(f"Couldn't detect nfc tag.")
                    return
            elif self.reader == 3:
                self.signals.status.emit("Connecting to ACS...")
                dev = ACS_HF15(port=self.port, logger=self.signals.status.emit)
                if dev.getUID() == b"":
                    self.signals.error.emit(f"Couldn't detect nfc tag.")
                    return
            else:
                self.signals.error.emit(f"Unknown nfc reader: {str(self.reader)}")
                return
        except Exception as e:
            self.signals.error.emit(f"Failed to connect to reader: {str(e)}")
            return

        self.signals.status.emit("Writing to NFC tag ...")
        try:
            if dev.restore(data_or_filename=tagdata, fast=True, progress=self.signals.progress.emit):
                self.signals.status.emit("Succeeded writing nfc tag")
            else:
                self.signals.error.emit("Error on writing nfc tag")
        except Exception as e:
            self.signals.error.emit(f"Error on reading nfc tag: {str(e)}")
            return
        pass


class NFC_ReadTagWorker(QRunnable):
    def __init__(self, reader: int, port: str):
        super().__init__()
        self.reader = reader
        self.signals = NFC_WorkerSignals()
        self.port = port

    @Slot()
    def run(self):
        try:
            if self.reader == 1:
                self.signals.status.emit("Connecting to Proxmark3...")
                dev = PM3_HF15(port=self.port, baudrate=115200, logger=self.signals.status.emit)
            elif self.reader == 2:
                self.signals.status.emit("Connecting to S9...")
                dev = S9_HF15(port=self.port, logger=self.signals.status.emit)
                if dev.getUID() == b"":
                    self.signals.error.emit(f"Couldn't detect nfc tag.")
                    return
            elif self.reader == 3:
                self.signals.status.emit("Connecting to ACS...")
                dev = ACS_HF15(port=self.port, logger=self.signals.status.emit)
                if dev.getUID() == b"":
                    self.signals.error.emit(f"Couldn't detect nfc tag.")
                    return
            else:
                self.signals.error.emit(f"Unknown nfc reader: {str(self.reader)}")
                return
        except Exception as e:
            self.signals.error.emit(f"Failed to connect to reader: {str(e)}")
            return

        self.signals.status.emit("Reading NFC tag ...")
        try:
            # Assuming the progress callback expects a percentage (0-100)
            tag = dev.dump(filename=None, progress=self.signals.progress.emit)
        except Exception as e:
            self.signals.error.emit(f"Error reading NFC tag: {str(e)}")
            return

        self.signals.status.emit("Parsing tag data...")
        try:
            # If load_data is a method on your main window/class, you'll need to pass the data back
            # and handle parsing in the main thread if it touches UI elements.
            self.signals.finished.emit(tag)  # tag should have .data attribute
        except Exception as e:
            self.signals.error.emit(f"Error parsing NFC tag: {str(e)}")

class NFC_ReadTagDetect(QRunnable):
    def __init__(self, reader: int, port: str):
        super().__init__()
        self.reader = reader
        self.signals = NFC_WorkerSignals()
        self.port = port

    @Slot()
    def run(self):
        try:
            uid = b""
            if self.reader == 1:
                dev = PM3_HF15(port=self.port, baudrate=115200, logger=self.signals.status.emit)
            elif self.reader == 2:
                dev = S9_HF15(port=self.port, logger=self.signals.status.emit)
            elif self.reader == 3:
                dev = ACS_HF15(port=self.port, logger=self.signals.status.emit)
                uid = dev.getUID()
                self.signals.finished.emit(uid)
                return
            self.signals.finished.emit(uid)
        except Exception as e:
            self.signals.finished.emit(b"")

