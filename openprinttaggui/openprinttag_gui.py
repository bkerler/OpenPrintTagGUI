#!/usr/bin/env python3
# (c) B.Kerler 2025
# GPLv3 License

import os
import sys
from collections import deque

import hid
import yaml
from PySide6.QtCore import Qt, QLocale, QDate, QDateTime, Signal, QObject, QThread, QTimer, Slot, QRunnable, QThreadPool
from PySide6.QtGui import QValidator, QColor, QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QCalendarWidget, QVBoxLayout, QDialog, \
    QColorDialog, QFileDialog, QLabel, QMessageBox, QLineEdit

from openprinttaggui.Library.s9_nfc.s9_hf15 import S9_HF15

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(script_path))
sys.path.insert(1, script_path)
sys.path.insert(2, os.path.join(script_path, "Library", "OpenPrintTag", "utils"))

from GUI.colorconversion import ral_to_hex, hex_to_ral
from GUI.gui import Ui_OpenPrintTagGui
from Library.OpenPrintTag.utils.record import Record
from Library.OpenPrintTag.utils.common import default_config_file
from Library.OpenPrintTag.utils.nfc_initialize import nfc_initialize, Args
from Library.pm3_nfc.pm3_hf15 import PM3_HF15
from Library.td1s import collect_data
import serial.tools.list_ports


class DeviceDetector(QObject):
    """
    A QObject that polls for a specific USB serial device (by VID/PID)
    and emits a signal when it is detected.
    """
    device_detected = Signal(dict)  # Emits the port name when detected
    device_removed = Signal(dict)  # Optional: emitted when device disappears

    def __init__(self, device_list: list, poll_interval_ms: int = 1000):
        """
        :param device_list: Contains usb vid, pid, name and reader param
        :param poll_interval_ms: How often to scan for the device (default 1 second)
        """
        super().__init__()
        self.device_list = device_list
        self.poll_interval = poll_interval_ms

        # QTimer for polling
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_device)
        self.timer.start(self.poll_interval)
        self.reader_state = []

    @Slot()
    def check_device(self):
        curstate = set()
        for dev_template in self.device_list:
            found = False
            target_vid = dev_template["vid"]
            target_pid = dev_template["pid"]
            # Serial check
            for port in serial.tools.list_ports.comports():
                if port.vid == target_vid and port.pid == target_pid:
                    new_dev = dev_template.copy()
                    new_dev["port"] = port.device
                    new_dev["type"] = "serial"
                    curstate.add(tuple(sorted(new_dev.items())))  # Use tuple for hashing
                    found = True
                    break
            if found:
                continue
            # HID check
            for device_info in hid.enumerate(0, 0):
                if target_vid == device_info["vendor_id"] and target_pid == device_info["product_id"]:
                    new_dev = dev_template.copy()
                    new_dev["port"] = device_info["path"].decode('utf-8')
                    new_dev["type"] = "hid"
                    curstate.add(tuple(sorted(new_dev.items())))
                    break

        for device in curstate:
            if device not in self.reader_state:
                # Device just appeared
                self.reader_state.append(device)
                device_dict = dict(device)
                if "reader" in device_dict:
                    reader = device_dict["reader"]
                    if reader not in self.reader_state:
                        self.device_detected.emit(device_dict)
        for device in self.reader_state:
            if device not in curstate:
                device_dict = dict(device)
                # Device was removed
                if "reader" in device_dict:
                    self.reader_state.remove(device)
                    device_dict["port"] = None
                    self.device_removed.emit(device_dict)

    def stop(self):
        """Stop the polling timer (call on application shutdown if needed)."""
        self.timer.stop()


# Worker signals
class TD1S_WorkerSignals(QObject):
    finished = Signal(object, object)  # td, color
    progress = Signal(int)
    error = Signal(Exception)


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
            self.signals.error.emit(f"Failed to generate tag data: {str(e)}")
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


# Worker thread
class DataCollectorThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = TD1S_WorkerSignals()
        self.parent = parent

    def run(self):
        try:
            td, color = collect_data(logger=self.signals.progress.emit)
            # Emit result to main thread
            self.signals.finished.emit(td, color)
        except Exception as e:
            self.signals.error.emit(e)


class DateValidator(QValidator):
    """Validator that only accepts dates in the system locale format."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.locale = QLocale()

    def validate(self, input_text: str, pos: int):
        if not input_text:
            return QValidator.Acceptable, input_text, pos

        # Try to parse the date using system locale
        date = self.locale.toDate(input_text, QLocale.FormatType.ShortFormat)
        if date.isValid():
            return QValidator.Acceptable, input_text, pos
        else:
            # Check intermediate state (e.g. partial input)
            date_long = self.locale.toDate(input_text, QLocale.FormatType.LongFormat)
            if date_long.isValid():
                return QValidator.Acceptable, input_text, pos
            return QValidator.Intermediate, input_text, pos


class GTINValidator(QValidator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.locale = QLocale()

    def validate(self, input_text: str, pos: int):
        if not input_text:
            return QValidator.Acceptable, input_text, pos
        if len(input_text) < 14:
            return QValidator.Acceptable, input_text, pos
        return QValidator.Invalid, input_text, pos


class DatePickerPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)
        self.setModal(False)

        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        # Connect calendar click to close and emit date
        self.calendar.clicked.connect(self.accept_date)

    def accept_date(self, qdate: QDate):
        self.selected_date = qdate
        self.accept()


class GUI_OpenPrintTag(QMainWindow, Ui_OpenPrintTagGui):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.readers = {}
        self.port = None
        self.reader = None
        self.threadpool = QThreadPool()
        self.td1sthread = None
        self.aux_region_size = None
        self.aux_region_offset = None
        self.main_region_size = None
        self.main_region_offset = None
        self.filaments = {}
        self.default_manufacturers = {}
        self.default_filamenttypes = {}
        self.setupUi(self)
        self.add_default_manufacturers()
        self.setup_material()
        self.add_default_material_properties()
        self.add_filaments()

        self.colorlabel.mousePressEvent = self.open_color_picker
        self.secondary_colorlabel_0.mousePressEvent = self.open_secondary0_color_picker
        self.secondary_colorlabel_1.mousePressEvent = self.open_secondary1_color_picker
        self.secondary_colorlabel_2.mousePressEvent = self.open_secondary2_color_picker
        self.secondary_colorlabel_3.mousePressEvent = self.open_secondary3_color_picker
        self.secondary_colorlabel_4.mousePressEvent = self.open_secondary4_color_picker
        for filament in self.default_filamenttypes:
            self.materialtypebox.addItem(filament)

        # Setup manufacturer date calendar widget and edit box
        self.setup_date_view()
        self.actionLoad.triggered.connect(self.on_load_file)
        self.actionSave.triggered.connect(self.on_save_file)
        self.gtinedit.setValidator(GTINValidator(self.gtinedit))

        # Setup nfc reader detection
        self.readtagbtn.clicked.connect(self.on_read_tag)
        self.writetagbtn.clicked.connect(self.on_write_tag)

        self.readtagbtn.setDisabled(True)
        self.writetagbtn.setDisabled(True)
        self.td1sbutton.setDisabled(True)

        device_list = [
            {"vid": 0x9ac4, "pid": 0x4b8f, "reader": 1, "name": "proxmark3"},
            {"vid": 0x0471, "pid": 0xa112, "reader": 2, "name": "s9"},
            {"vid": 0x072F, "pid": 0x2303, "reader": 3, "name": "acr1552u-m1"},
            {"vid": 0x072F, "pid": 0x2308, "reader": 3, "name": "acr1552u-m2"},
            {"vid": 0xe4b2, "pid": 0x0045, "reader": -1, "name": "td1s"},
        ]

        # NFC Reader support
        self.device_detector = DeviceDetector(device_list=device_list, poll_interval_ms=2000)
        self.device_detector.device_detected.connect(self.on_device_detected)
        self.device_detector.device_removed.connect(self.on_device_removed)

        # We default to Prusament here
        self.brandnamebox.setCurrentText("Prusament")
        self.materialnamebox.setCurrentIndex(0)
        self.colornamebox.setCurrentIndex(0)

    def on_td1s_removed(self):
        self.msg("TD1S removed.")
        self.td1sbutton.setDisabled(True)

    def on_device_detected(self, info: dict):
        if "name" in info:
            name = info["name"]
            self.msg(f"{name} detected.")
        if "reader" in info:
            reader = info["reader"]
            if reader in self.readers:
                self.readers[reader] += 1
            else:
                self.readers[reader] = 1
            if reader == -1:
                if not self.td1sbutton.isEnabled():
                    self.td1sbutton.setDisabled(False)
            elif reader > 0:
                self.reader = reader
                if "port" in info:
                    self.port = info["port"]
                if not self.readtagbtn.isEnabled():
                    self.readtagbtn.setDisabled(False)
                if not self.writetagbtn.isEnabled():
                    self.writetagbtn.setDisabled(False)

    def on_device_removed(self, info: dict):
        if "name" in info:
            name = info["name"]
            self.msg(f"{name} removed.")
        if "reader" in info:
            reader = info["reader"]
            if reader == -1:
                if self.td1sbutton.isEnabled():
                    self.td1sbutton.setDisabled(True)
            elif reader > 0:
                if reader in self.readers:
                    self.readers[reader] -= 1
            enabled = False
            for reader in self.readers:
                if self.readers[reader] > 0:
                    enabled = True
            if not enabled:
                self.reader = 0
                self.port = None
                if self.readtagbtn.isEnabled():
                    self.readtagbtn.setDisabled(True)
                if self.writetagbtn.isEnabled():
                    self.writetagbtn.setDisabled(True)

    def msg(self, text, value: int = 0):
        self.statusbar.showMessage(self.tr(text), value)

    def set_progress(self, value: int):
        self.progressBar.setValue(value)
        self.progressBar.update()

    def on_read_tag(self):
        self.progressBar.setValue(0)
        self.msg("Starting...")

        worker = NFC_ReadTagWorker(reader=self.reader, port=self.port)

        # Connect signals to UI updates
        worker.signals.progress.connect(self.set_progress)
        worker.signals.status.connect(self.msg)
        worker.signals.error.connect(lambda msg: self.msg(msg))  # Reuse your existing msg method
        worker.signals.finished.connect(self.handle_tag_read_success)

        # Start the worker in the thread pool
        self.threadpool.start(worker)

    def handle_tag_read_success(self, tag):
        try:
            self.load_data(tag.data)
            self.msg("Tag read and parsed successfully.")
        except Exception as e:
            self.msg(f"Error on parsing nfc tag: {str(e)}")
        finally:
            self.set_progress(0)
            self.msg("")

    def on_write_tag(self):
        self.set_progress(0)
        self.msg("Generating tag data...")

        worker = NFC_WriteTagWorker(parent=self, reader=self.reader, port=self.port)

        # Connect signals to UI updates
        worker.signals.progress.connect(self.set_progress)
        worker.signals.status.connect(self.msg)
        worker.signals.error.connect(lambda msg: self.msg(msg))  # Reuse your existing msg method
        worker.signals.finished.connect(self.handle_tag_write_success)

        # Start the worker in the thread pool
        self.threadpool.start(worker)

    def handle_tag_write_success(self):
        try:
            self.msg("Tag written successfully.")
        except Exception as e:
            self.msg(f"Error on writing nfc tag: {str(e)}")
        finally:
            self.set_progress(0)
            self.msg("")

    def on_td1s_data_ready(self, td, color):
        if td is None and color is None:
            self.show_message_box(self.tr("Error"), self.tr("Couldn't detect td1s"), QMessageBox.Icon.Critical)
            return
        elif td == "" and color == "":
            self.msg("TD1S TD: Please try again, no color detected. Insert filament after button click", 0)
        else:
            self.msg(f"TD1S TD: {td}\nColor: #{color}", 2000)
            self.update_color_label("#" + color, self.colorlabel)
            self.primarycoloredit.setText("#" + color)
            self.transmissiondistanceedit.setText(td)

    def on_td1s_error(self, exc):
        self.show_message_box(self.tr("Error"), self.tr(f"TD1S error: {str(exc)}"), QMessageBox.Icon.Critical)

    def on_td1s_thread_done(self):
        self.td1sbutton.setEnabled(True)

    def readtd1s(self):
        if self.td1sthread and self.td1sthread.isRunning():
            return  # Already running

        self.msg("Collecting td1s data... please insert filament")
        self.td1sbutton.setEnabled(False)

        # Create and start thread
        self.td1sthread = DataCollectorThread(self)
        self.td1sthread.signals.finished.connect(self.on_td1s_data_ready)
        self.td1sthread.signals.error.connect(self.on_td1s_error)
        self.td1sthread.finished.connect(self.on_td1s_thread_done)
        self.td1sthread.start()

    def locale_to_timestamp(self, date_str):
        dt = QLocale().toDate(date_str, QLocale.ShortFormat)
        if not dt.isValid:
            return 0
        # We don't live in the 1925, but 2025 years
        dt = dt.addYears(100)
        date = QDateTime()
        date.setDate(dt)
        return date.toSecsSinceEpoch()

    def show_message_box(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def generate_tag_data(self):
        args = Args(
            size=304,  # 136 for smaller chip
            aux_region=32,  # 16 for smaller chip
            config_file=default_config_file)

        if self.includeurlcheckbox.isChecked():
            args.ndef_uri = self.urledit.toPlainText()

        # Create empty tag
        emptytag_data = nfc_initialize(args)

        # Fill empty tag with data
        record = Record(args.config_file, memoryview(bytearray(emptytag_data)))

        update_data = {}
        consumed_weight = self.consumedweightbox.value()
        if consumed_weight != 0:
            update_data["aux"] = {}
            update_data["aux"]["consumed_weight"] = consumed_weight
        update_data["main"] = dict(
            material_class=self.materialclassbox.currentText().split(" ")[0],
            material_type=self.materialtypebox.currentText().split(" ")[0],
            material_name=self.materialnamebox.currentText(),
            brand_name=self.brandnamebox.currentText(),
            manufactured_date=self.locale_to_timestamp(self.dateedit.text()),
            nominal_netto_full_weight=self.nominalweightbox.value(),
            actual_netto_full_weight=self.actualweightbox.value(),
            empty_container_weight=self.emptycontainerbox.value()
        )
        if self.gtinedit.text() != "":
            update_data["main"]["gtin"] = int(self.gtinedit.text())
        if self.expdateedit.text() != "00.00.00":
            update_data["main"]["expiration_date"] = self.locale_to_timestamp(self.dateedit.text())
        if self.primarycoloredit.text() != "":
            update_data["main"]["primary_color"] = {}
            update_data["main"]["primary_color"]["hex"] = self.primarycoloredit.text().replace("#", "")
        if self.secondarycolor0edit_0.text() != "":
            update_data["main"]["secondary_color_0"] = {}
            update_data["main"]["secondary_color_0"]["hex"] = self.secondarycolor0edit_0.text().replace("#", "")
        if self.secondarycolor0edit_1.text() != "":
            update_data["main"]["secondary_color_1"] = {}
            update_data["main"]["secondary_color_1"]["hex"] = self.secondarycolor0edit_1.text().replace("#", "")
        if self.secondarycolor0edit_2.text() != "":
            update_data["main"]["secondary_color_2"] = {}
            update_data["main"]["secondary_color_2"]["hex"] = self.secondarycolor0edit_2.text().replace("#", "")
        if self.secondarycolor0edit_3.text() != "":
            update_data["main"]["secondary_color_3"] = {}
            update_data["main"]["secondary_color_3"]["hex"] = self.secondarycolor0edit_3.text().replace("#", "")
        if self.secondarycolor0edit_4.text() != "":
            update_data["main"]["secondary_color_4"] = {}
            update_data["main"]["secondary_color_4"]["hex"] = self.secondarycolor0edit_4.text().replace("#", "")
        if self.transmissiondistanceedit.text() != "":
            update_data["main"]["transmission_distance"] = float(self.transmissiondistanceedit.text())
        if self.densityedit.text != "":
            update_data["main"]["density"] = float(self.densityedit.text())
        if self.diameteredit.text() != "1.75":
            update_data["main"]["filament_diameter"] = float(self.diameteredit.text())
        # nominal_full_length
        # actual_full_length
        # shore_hardness_a
        # shore_hardness_d
        # min_nozzle_diameter
        if self.minprinttempbox.value() != 0:
            update_data["main"]["min_print_temperature"] = self.minprinttempbox.value()
        if self.maxprinttempbox.value() != 0:
            update_data["main"]["max_print_temperature"] = self.maxprinttempbox.value()
        if self.minbedtempbox.value() != 0:
            update_data["main"]["min_bed_temperature"] = self.minbedtempbox.value()
        if self.maxbedtempbox.value() != 0:
            update_data["main"]["max_bed_temperature"] = self.maxbedtempbox.value()
        if self.preheattempbox.value() != 0:
            update_data["main"]["preheat_temperature"] = self.preheattempbox.value()
        # min_chamber_temperature
        # max_chamber_temperature
        # chamber_temperature
        # container_width
        # container_outer_diameter
        # container_inner_diameter
        # container_hole_diameter
        # viscosity_18c, viscosity_25c, viscosity_40c, viscoity_60c
        # container_volumetric_capacity
        # cure_wavelength
        update_data["main"]["tags"] = []
        items = self.matpropwidget.get_checked_items()
        for category in items:
            for prop in items[category]:
                update_data["main"]["tags"].append(self.matpropwidget.get_tag(prop))
        for region_name, region in record.regions.items():
            region.update(
                update_fields=update_data.get(region_name, dict())
            )
        return record.data.tobytes()

    def on_save_file(self):
        fn = (self.brandnamebox.currentText().replace(" ", "_").replace("-", "_") + "_" +
              self.materialnamebox.currentText().replace(" ", "_").replace("-", "_") + "_" +
              self.colornamebox.currentText().replace(" ", "_").replace("-", "_")) + ".bin"
        filename, selfilter = QFileDialog.getSaveFileName(self, self.tr("Select Tag data file"), dir=fn)
        if filename != "":
            tagdata = self.generate_tag_data()
            if open(filename, "wb").write(tagdata):
                self.show_message_box(title=self.tr("Info"), message=self.tr(f"Successfully wrote {filename}"))

    def check_tag_implies(self, tag):
        dq = deque()
        dq.append(tag)
        while dq:
            tag = dq.popleft()
            if tag in self.tags:
                if "implies" in self.tags[tag]:
                    for subtag in self.tags[tag]["implies"]:
                        subprop = self.matpropwidget.get_name(subtag)
                        if subprop is not None:
                            self.matpropwidget.set_property_checked(property_name=subprop, checked=True)
                        dq.append(subprop)

    def load_data(self, data):
        self.matpropwidget.uncheck()
        self.matpropwidget.filter_check.setChecked(False)
        fields, uri = self.parse_tag_data(data)
        if "meta" in fields:
            meta = fields["meta"]
            if "aux_region_offset" in meta:
                self.aux_region_offset = meta["aux_region_offset"]
            if "aux_region_size" in meta:
                self.aux_region_size = meta["aux_region_size"]
            if "main_region_offset" in meta:
                self.main_region_offset = meta["main_region_offset"]
            if "main_region_size" in meta:
                self.main_region_size = meta["main_region_size"]
        if "aux" in fields:
            if "consumed_weight" in fields["aux"]:
                self.consumedweightbox.setValue(fields["aux"]["consumed_weight"])
        if "main" in fields:
            main = fields["main"]
            if "brand_name" in main:
                self.brandnamebox.setCurrentText(main["brand_name"])
            if "material_name" in main:
                self.materialnamebox.setCurrentText(main["material_name"])
            elif "material_abbreviation" in main:
                self.materialnamebox.setCurrentText(main["material_abbreviation"])
            if "gtin" in main:
                self.gtinedit.setText(str(main["gtin"]))
            if "material_class" in main:
                found = False
                cur_material_class = main["material_class"]
                for row in range(self.materialclassbox.model().rowCount()):
                    text = self.materialclassbox.itemText(row)
                    if text.split(" ")[0] == cur_material_class:
                        self.materialclassbox.setCurrentIndex(row)
                        found = True
                        break
                if not found:
                    self.materialclassbox.setCurrentText(cur_material_class)
            if "material_type" in main:
                cur_material_type = main["material_type"]
                cf = self.default_filamenttypes.get(cur_material_type)
                if cf is not None:
                    if "name" in cf:
                        self.materialtypebox.setCurrentText(cur_material_type + " - " + cf["name"])
                    else:
                        self.materialtypebox.setCurrentText(cur_material_type)
                else:
                    self.materialtypebox.setCurrentText(cur_material_type)
            if "manufactured_date" in main:
                timestamp = main["manufactured_date"]
                dt = QDateTime()
                dt = dt.toUTC()
                dt.setSecsSinceEpoch(timestamp)
                self.dateedit.setText(QLocale().toString(dt.date(), QLocale.ShortFormat))
            if "expiration_date" in main:
                timestamp = main["expiration_date"]
                dt = QDateTime()
                dt = dt.toUTC()
                dt.setSecsSinceEpoch(timestamp)
                self.expdateedit.setText(QLocale().toString(dt.date(), QLocale.ShortFormat))
            if "nominal_netto_full_weight" in main:
                self.nominalweightbox.setValue(main["nominal_netto_full_weight"])
            if "actual_netto_full_weight" in main:
                self.actualweightbox.setValue(main["actual_netto_full_weight"])
            if "empty_container_weight" in main:
                self.emptycontainerbox.setValue(main["empty_container_weight"])
            if "manufactured_date" in main:
                timestamp = main["manufactured_date"]
                dt = QDateTime()
                dt = dt.toUTC()
                dt.setSecsSinceEpoch(timestamp)
                self.dateedit.setText(QLocale().toString(dt.date(), QLocale.ShortFormat))
            if "expiration_date" in main:
                timestamp = main["expiration_date"]
                dt = QDateTime()
                dt = dt.toUTC()
                dt.setSecsSinceEpoch(timestamp)
                self.expdateedit.setText(QLocale().toString(dt.date(), QLocale.ShortFormat))
            if "primary_color" in main:
                self.colornamebox.clear()
                if "hex" in main["primary_color"]:
                    self.primarycoloredit.setText('#' + main["primary_color"]["hex"])
                    self.update_color_label("#" + main["primary_color"]["hex"], self.colorlabel)
            for i in range(5):
                if f"secondary_color_{i}" in main:
                    if "hex" in main[f"secondary_color_{i}"]:
                        secondarycolor = '#' + main[f"secondary_color_{i}"]["hex"]
                        if i == 0:
                            self.secondarycolor0edit_0.setText(secondarycolor)
                            self.update_color_label(secondarycolor, self.secondarycolor0edit_0)
                        elif i == 1:
                            self.secondarycolor0edit_1.setText(secondarycolor)
                            self.update_color_label(secondarycolor, self.secondarycolor0edit_1)
                        elif i == 2:
                            self.secondarycolor0edit_2.setText(secondarycolor)
                            self.update_color_label(secondarycolor, self.secondarycolor0edit_2)
                        elif i == 3:
                            self.secondarycolor0edit_3.setText(secondarycolor)
                            self.update_color_label(secondarycolor, self.secondarycolor0edit_3)
                        elif i == 4:
                            self.secondarycolor0edit_4.setText(secondarycolor)
                            self.update_color_label(secondarycolor, self.secondarycolor0edit_4)
            if "filament_diameter" in main:
                self.diameteredit.setText("%.02f" % main["filament_diameter"])
            else:
                self.diameteredit.setText("1.75")
            if "density" in main:
                self.densityedit.setText("%.02f" % main["density"])
            if "min_print_temperature" in main:
                self.minprinttempbox.setValue(main["min_print_temperature"])
            if "max_print_temperature" in main:
                self.maxprinttempbox.setValue(main["max_print_temperature"])
            if "preheat_temperature" in main:
                self.preheattempbox.setValue(main["preheat_temperature"])
            if "min_bed_temperature" in main:
                self.minbedtempbox.setValue(main["min_bed_temperature"])
            if "max_bed_temperature" in main:
                self.maxbedtempbox.setValue(main["max_bed_temperature"])
            if "transmission_distance" in main:
                self.transmissiondistanceedit.setText("%0.1f" % main["transmission_distance"])
            self.matpropwidget.filter_check.setChecked(False)
            if "tags" in main:
                for tag in main["tags"]:
                    prop = self.matpropwidget.get_name(tag)
                    if prop is not None:
                        self.matpropwidget.set_property_checked(property_name=prop, checked=True)
                        self.check_tag_implies(tag)
                self.matpropwidget.filter_check.setChecked(True)

            # Make sure uri is read after manufacturer or material change
            if uri != "":
                self.includeurlcheckbox.setChecked(True)
                self.urledit.setText(uri)
            else:
                self.includeurlcheckbox.setChecked(False)
                self.urledit.setText("")

    def on_load_file(self):
        filename, selfilter = QFileDialog.getOpenFileName(self, self.tr("Select Tag data file"))
        if filename != "" and os.path.exists(filename):
            data = open(filename, "rb").read()
            try:
                self.load_data(data)
            except Exception as e:
                self.msg(f"Error on parsing nfc tag: {str(e)}")

    def setup_date_view(self):
        self.dateedit.setPlaceholderText(QLocale().dateFormat(QLocale.ShortFormat))
        self.dateedit.setValidator(DateValidator(self.dateedit))
        self.dateedit.setReadOnly(False)
        self.dateedit.mousePressEvent = self.show_calendar
        # Initial value: today's date in system format
        today = QDate.currentDate()
        self.dateedit.setText(QLocale().toString(today, QLocale.ShortFormat))

        self.expdateedit.setPlaceholderText(QLocale().dateFormat(QLocale.ShortFormat))
        self.expdateedit.setValidator(DateValidator(self.expdateedit))
        self.expdateedit.setReadOnly(False)
        self.expdateedit.mousePressEvent = self.show_exp_calendar
        self.expdateedit.setText("00.00.00")

    def open_color_picker(self, event):
        # Open the native color dialog
        color = QColorDialog.getColor(
            initial=QColor(self.primarycoloredit.text()),  # start with current color
            parent=self,
            title=self.tr("Select a color"),
            options=QColorDialog.ShowAlphaChannel  # remove if you don’t need alpha
        )

        if color.isValid():
            hex_color = color.name(QColor.HexRgb)

            self.primarycoloredit.setText(hex_color)
            self.primarycolorraledit.setText(hex_to_ral(hex_color))
            self.update_color_label(hex_color, self.colorlabel)

    def set_secondary(self, editbox: QLineEdit, labelbox: QLabel):
        # Open the native color dialog
        color = QColorDialog.getColor(
            initial=QColor(editbox.text()),  # start with current color
            parent=self,
            title=self.tr("Select a color"),
            options=QColorDialog.ShowAlphaChannel  # remove if you don’t need alpha
        )

        if color.isValid():
            hex_color = color.name(QColor.HexRgb)

            editbox.setText(hex_color)
            self.update_color_label(hex_color, labelbox)

    def open_secondary0_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycolor0edit_0, self.secondary_colorlabel_0)

    def open_secondary1_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycolor0edit_1, self.secondary_colorlabel_1)

    def open_secondary2_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycolor0edit_2, self.secondary_colorlabel_2)

    def open_secondary3_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycolor0edit_3, self.secondary_colorlabel_3)

    def open_secondary4_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycolor0edit_4, self.secondary_colorlabel_4)

    def show_calendar(self, event):
        # Show popup calendar below the line edit
        popup = DatePickerPopup(self)
        popup.calendar.setSelectedDate(
            QLocale().toDate(self.dateedit.text(), QLocale.ShortFormat)
            or QDate.currentDate()
        )

        # Position popup
        global_pos = self.dateedit.mapToGlobal(self.dateedit.rect().bottomLeft())
        popup.move(global_pos)

        if popup.exec():
            selected = popup.selected_date
            formatted = QLocale().toString(selected, QLocale.ShortFormat)
            self.dateedit.setText(formatted)

    def show_exp_calendar(self, event):
        # Show popup calendar below the line edit
        popup = DatePickerPopup(self)
        popup.calendar.setSelectedDate(
            QLocale().toDate(self.expdateedit.text(), QLocale.ShortFormat)
            or QDate.currentDate()
        )

        # Position popup
        global_pos = self.expdateedit.mapToGlobal(self.expdateedit.rect().bottomLeft())
        popup.move(global_pos)

        if popup.exec():
            selected = popup.selected_date
            formatted = QLocale().toString(selected, QLocale.ShortFormat)
            self.expdateedit.setText(formatted)

    def on_filament_type_changed(self):
        materialtype = self.materialtypebox.currentText()
        if materialtype in self.default_filamenttypes:
            curfilament = self.default_filamenttypes[materialtype]
            if "bed_max_temp" in curfilament:
                self.maxbedtempbox.setValue(curfilament["bed_max_temp"])
            if "bed_min_temp" in curfilament:
                self.minbedtempbox.setValue(curfilament["bed_min_temp"])
            if "max_temp" in curfilament:
                self.maxprinttempbox.setValue(curfilament["max_temp"])
            if "min_temp" in curfilament:
                self.minprinttempbox.setValue(curfilament["min_temp"])
            if "preheat_temp" in curfilament:
                self.preheattempbox.setValue(curfilament["preheat_temp"])

    def add_default_manufacturers(self):
        self.brandnamebox.setStyleSheet("""
                    combobox-popup: 0;
                    QListWidget::item { padding: 4px; }
                    QListWidget { border: 1px solid #999; }
                """)
        self.brandnamebox.setCurrentIndex(0)

    def read_openprinttag_material_class(self) -> dict:
        materialclasses = {}
        mc_filename = os.path.join(script_path, "Library", "OpenPrintTag", "data", "material_class_enum.yaml")
        if not os.path.exists(mc_filename):
            self.show_message_box(title=self.tr("Error"),
                                  message=self.tr(f"Couldn't find material class database at {mc_filename}"),
                                  icon=QMessageBox.Icon.Critical)
        mc = yaml.safe_load(open(mc_filename, encoding="utf8").read())
        for item in mc:
            materialclasses[item["name"]] = item["description"]
        return materialclasses

    def read_openprinttag_tags(self) -> dict:
        tags = {}
        mcc_filename = os.path.join(script_path, "Library", "OpenPrintTag", "data", "tag_categories_enum.yaml")
        if not os.path.exists(mcc_filename):
            self.show_message_box(title=self.tr("Error"),
                                  message=self.tr(f"Couldn't find categories database at {mcc_filename}"),
                                  icon=QMessageBox.Icon.Critical)
        mcc = yaml.safe_load(open(mcc_filename, encoding="utf8").read())

        mc_filename = os.path.join(script_path, "Library", "OpenPrintTag", "data", "tags_enum.yaml")
        if not os.path.exists(mc_filename):
            self.show_message_box(title=self.tr("Error"),
                                  message=self.tr(f"Couldn't find tags database at {mc_filename}"),
                                  icon=QMessageBox.Icon.Critical)
        mc = yaml.safe_load(open(mc_filename, encoding="utf8").read())
        for citem in mcc:
            if "display_name" in citem and "name" in citem:
                category = citem["display_name"]
                tag_category = citem["name"]
                tags[category] = {}
                for item in mc:
                    if "depreciated" in item:
                        if item["depreciated"]:
                            continue
                    if "category" in item:
                        if tag_category == item["category"]:
                            if "display_name" in item:
                                displayname = item["display_name"]
                                tags[category][displayname] = item
        return tags

    def read_openprinttag_material_types(self) -> dict:
        materialtypes = {}
        mt_filename = os.path.join(script_path, "data", "material_temps.yaml")
        if not os.path.exists(mt_filename):
            self.show_message_box(title=self.tr("Error"),
                                  message=self.tr(f"Couldn't find material temp database at {mt_filename}"),
                                  icon=QMessageBox.Icon.Critical)
        default_filamenttypes = yaml.safe_load(open(mt_filename).read())
        mc_filename = os.path.join(script_path, "Library", "OpenPrintTag", "data", "material_type_enum.yaml")
        if not os.path.exists(mc_filename):
            self.show_message_box(title=self.tr("Error"),
                                  message=self.tr(f"Couldn't find material type database at {mc_filename}"),
                                  icon=QMessageBox.Icon.Critical)
        mc = yaml.safe_load(open(mc_filename).read())
        for item in mc:
            abbr = item["abbreviation"]
            materialtypes[abbr] = dict(name=item["name"], desc=item["description"])
            if abbr in default_filamenttypes:
                if "bed_max_temp" in default_filamenttypes[abbr]:
                    materialtypes[abbr]["bed_max_temp"] = default_filamenttypes[abbr]["bed_max_temp"]
                if "bed_min_temp" in default_filamenttypes[abbr]:
                    materialtypes[abbr]["bed_min_temp"] = default_filamenttypes[abbr]["bed_min_temp"]
                if "preheat_temp" in default_filamenttypes[abbr]:
                    materialtypes[abbr]["preheat_temp"] = default_filamenttypes[abbr]["preheat_temp"]
                if "max_temp" in default_filamenttypes[abbr]:
                    materialtypes[abbr]["max_temp"] = default_filamenttypes[abbr]["max_temp"]
                if "min_temp" in default_filamenttypes[abbr]:
                    materialtypes[abbr]["min_temp"] = default_filamenttypes[abbr]["min_temp"]
        return materialtypes

    def setup_material(self):
        self.default_filamenttypes = self.read_openprinttag_material_types()
        materialclasses = self.read_openprinttag_material_class()
        self.materialclassbox.clear()
        idx = 0
        for materialclass in materialclasses:
            self.materialclassbox.addItem(materialclass + " - " + materialclasses[materialclass])
            idx += 1
        for filament in self.default_filamenttypes:
            self.materialtypebox.addItem(filament + " - " + self.default_filamenttypes[filament]["name"])
        self.materialtypebox.setStyleSheet("""
                    combobox-popup: 0;
                    QListWidget::item { padding: 4px; }
                    QListWidget { border: 1px solid #999; }
                """)
        self.materialtypebox.setCurrentIndex(0)
        self.materialtypebox.currentTextChanged.connect(self.on_filament_type_changed)
        self.materialnamebox.currentTextChanged.connect(self.on_materialname_changed)
        self.colorlabel.setFixedSize(20, 20)
        self.colorlabel.setStyleSheet("border: 1px solid #777;")
        self.secondary_colorlabel_0.setFixedSize(20, 20)
        self.secondary_colorlabel_0.setStyleSheet("border: 1px solid #777;")
        self.secondary_colorlabel_1.setFixedSize(20, 20)
        self.secondary_colorlabel_1.setStyleSheet("border: 1px solid #777;")
        self.secondary_colorlabel_2.setFixedSize(20, 20)
        self.secondary_colorlabel_2.setStyleSheet("border: 1px solid #777;")
        self.secondary_colorlabel_3.setFixedSize(20, 20)
        self.secondary_colorlabel_3.setStyleSheet("border: 1px solid #777;")
        self.secondary_colorlabel_4.setFixedSize(20, 20)
        self.secondary_colorlabel_4.setStyleSheet("border: 1px solid #777;")
        self.reset_colors()
        self.colornamebox.currentTextChanged.connect(self.on_colorname_changed)

    def reset_colors(self):
        self.update_color_label("#000000", self.colorlabel)
        self.update_color_label("#000000", self.secondary_colorlabel_0)
        self.update_color_label("#000000", self.secondary_colorlabel_1)
        self.update_color_label("#000000", self.secondary_colorlabel_2)
        self.update_color_label("#000000", self.secondary_colorlabel_3)
        self.update_color_label("#000000", self.secondary_colorlabel_4)
        self.primarycoloredit.setText("")
        self.primarycolorraledit.setText("")
        self.secondarycolor0edit_0.setText("")
        self.secondarycolor0edit_1.setText("")
        self.secondarycolor0edit_2.setText("")
        self.secondarycolor0edit_3.setText("")
        self.secondarycolor0edit_4.setText("")

    def add_default_material_properties(self):
        self.tags = self.read_openprinttag_tags()
        if self.tags is not None:
            self.matpropwidget.load_tags(self.tags)

    def setup_color(self, brandname: str, materialname: str, colorname: str):
        if brandname in self.filaments and materialname in self.filaments[brandname]:
            cm = self.filaments[brandname][materialname]
            self.colornamebox.setCurrentText(colorname)
            if "colors" not in cm:
                return
            color_props = cm["colors"].get(colorname)
            if color_props is None:
                return
            if "primary_color" in color_props:
                color = color_props["primary_color"]
                if "RAL" in color:
                    self.primarycolorraledit.setText(color)
                    color = ral_to_hex(color)
                else:
                    self.primarycolorraledit.setText(hex_to_ral(color))
                self.primarycoloredit.setText(color)
                self.update_color_label(color, self.colorlabel)
            if "transmission_distance" in color_props:
                transmission_distance = color_props["transmission_distance"]
                if transmission_distance is not None:
                    self.transmissiondistanceedit.setText("%.01f" % color_props["transmission_distance"])
            self.includeurlcheckbox.setChecked(False)
            if "uri" in color_props:
                uri = color_props["uri"]
                if uri is not None:
                    self.urledit.setText(uri)
                    self.includeurlcheckbox.setChecked(True)
            else:
                self.includeurlcheckbox.setChecked(False)
                self.urledit.setText("")

            if "tags" in color_props:
                self.add_material_properties(color_props["tags"])

    def setup_default_material(self, brandname, materialname):
        if brandname in self.filaments:
            if materialname in self.filaments[brandname]:
                self.materialnamebox.setCurrentText(materialname)
                cm = self.filaments[brandname][materialname]
                if "material_type" in cm:
                    materialtype = cm["material_type"]
                    cf = self.default_filamenttypes.get(materialtype)
                    if cf is not None and "name" in cf:
                        self.materialtypebox.setCurrentText(materialtype + " - " + cf["name"])
                        if "bed_max_temp" in cf:
                            self.maxbedtempbox.setValue(cf["bed_max_temp"])
                        if "bed_min_temp" in cf:
                            self.minbedtempbox.setValue(cf["bed_min_temp"])
                        if "max_temp" in cf:
                            self.maxprinttempbox.setValue(cf["max_temp"])
                        if "min_temp" in cf:
                            self.minprinttempbox.setValue(cf["min_temp"])
                        if "prehead_temp" in cf:
                            self.preheattempbox.setValue(cf["preheat_temp"])
                    else:
                        self.materialtypebox.setCurrentText(materialtype)
                if "empty_container_weight" in cm:
                    self.emptycontainerbox.setValue(cm["empty_container_weight"])
                if "nominal_netto_full_weight" in cm:
                    self.nominalweightbox.setValue(cm["nominal_netto_full_weight"])
                if "actual_netto_full_weight" in cm:
                    self.actualweightbox.setValue(cm["actual_netto_full_weight"])
                if "density" in cm:
                    self.densityedit.setText("%.02f" % cm["density"])
                if "min_print_temperature" in cm:
                    self.minprinttempbox.setValue(cm["min_print_temperature"])
                if "max_print_temperature" in cm:
                    self.maxprinttempbox.setValue(cm["max_print_temperature"])
                if "min_bed_temperature" in cm:
                    self.minbedtempbox.setValue(cm["min_bed_temperature"])
                if "max_bed_temperature" in cm:
                    self.maxbedtempbox.setValue(cm["max_bed_temperature"])
                if "preheat_temperature" in cm:
                    self.preheattempbox.setValue(cm["preheat_temperature"])
                if "diameter" in cm:
                    diameter = cm["diameter"]
                    self.diameteredit.setText("%.02f" % diameter)
                else:
                    self.diameteredit.setText("1.75")
                self.colornamebox.clear()
                if "colors" in cm:
                    for colorname in cm["colors"]:
                        self.colornamebox.addItem(f"{colorname}")
                    self.colornamebox.setCurrentIndex(0)

    def on_manufacturer_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        manufacturer = self.brandnamebox.currentText()
        found = False
        if manufacturer in self.filaments:
            found = True
            self.materialnamebox.clear()
            for materialname in self.filaments[manufacturer]:
                self.materialnamebox.addItem(materialname)
            self.materialnamebox.model().sort(0, Qt.AscendingOrder)
            self.materialnamebox.setCurrentIndex(0)
        self.matpropwidget.filter_check.setChecked(found)

    def update_color_label(self, hex_color: str, colorlabel: QLabel):
        # Fill a tiny pixmap with the chosen color
        pix = QPixmap(colorlabel.size())
        pix.fill(QColor(hex_color))
        colorlabel.setPixmap(pix)

    def add_material_properties(self, properties):
        self.matpropwidget.uncheck()
        self.matpropwidget.filter_check.setChecked(False)
        for tag in properties:
            self.matpropwidget.set_property_checked(property_name=self.matpropwidget.get_name(tag), checked=True)
            if tag is not None:
                self.check_tag_implies(tag)
        self.matpropwidget.filter_check.setChecked(True)
        self.matpropwidget.repaint()

    def on_colorname_changed(self):
        self.reset_colors()
        brand_name = self.brandnamebox.currentText()
        material_name = self.materialnamebox.currentText()
        color_name = self.colornamebox.currentText()
        if brand_name in self.filaments:
            materialprops = self.filaments[brand_name].get(material_name)
            if materialprops is not None:
                self.setup_color(brand_name, material_name, color_name)

    def on_materialname_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        brandname = self.brandnamebox.currentText()
        materialname = self.materialnamebox.currentText()
        if brandname in self.filaments:
            materialprops = self.filaments[brandname].get(materialname)
            if materialprops is not None:
                self.setup_default_material(brandname, materialname)

    def add_filaments(self):
        self.filaments = {}
        for (root, dirs, files) in os.walk(os.path.join(script_path, "data", "filaments"), topdown=True):
            for file in files:
                filename = os.path.join(root, file)
                if ".yaml" == filename[-5:]:
                    try:
                        filament_dict = yaml.safe_load(open(os.path.join(filename), "r"))
                        if "brand_name" in filament_dict:
                            brand_name = filament_dict["brand_name"]
                            if "material_name" in filament_dict:
                                self.filaments[brand_name] = filament_dict["material_name"]
                    except Exception as e:
                        self.msg(f"YAML Error in {filename}: {str(e)}")
        for brand_name in self.filaments:
            self.brandnamebox.addItem(brand_name)
        self.brandnamebox.setStyleSheet("""
                    combobox-popup: 0;
                    QListWidget::item { padding: 4px; }
                    QListWidget { border: 1px solid #999; }
                """)
        self.brandnamebox.currentTextChanged.connect(self.on_manufacturer_changed)
        self.brandnamebox.model().sort(0, Qt.AscendingOrder)

    def parse_tag_data(self, data):
        uri = ""
        record = Record(config_file=default_config_file, data=memoryview(data))
        fields = {}
        for name, region in record.regions.items():
            unknown_fields = dict()
            try:
                fields[name] = region.read(out_unknown_fields=unknown_fields)
            except Exception as err:
                self.msg(str(err))
        if hasattr(record, "uri"):
            uri = record.uri
        return fields, uri


if __name__ == "__main__":
    app = QApplication(sys.argv)
    info = "OpenPrintTagGUI v1.01 (c) B.Kerler"
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
