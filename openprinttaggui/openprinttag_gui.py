#!/usr/bin/env python3
# (c) B.Kerler 2025
# GPLv3 License

import os
import sys
from collections import deque
from types import SimpleNamespace

import requests
import yaml
from PySide6.QtCore import Qt, QLocale, QDate, QDateTime, Signal, QObject, QThread, QTimer, Slot, QRunnable, QThreadPool
from PySide6.QtGui import QValidator, QColor, QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QCalendarWidget, QVBoxLayout, QDialog, \
    QColorDialog, QFileDialog, QLabel, QMessageBox, QLineEdit

from openprinttaggui.Library.device_detector import DeviceDetectorWorker, device_list
from openprinttaggui.Library.nfc_handler import NFC_ReadTagWorker, NFC_WriteTagWorker, NFC_ReadTagDetect

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(script_path))
sys.path.insert(1, script_path)
sys.path.insert(2, os.path.join(script_path, "Library", "OpenPrintTag", "utils"))

from GUI.colorconversion import ral_to_hex, hex_to_ral
from GUI.gui import Ui_OpenPrintTagGui
from Library.OpenPrintTag.utils.record import Record
from Library.OpenPrintTag.utils.common import default_config_file
from Library.OpenPrintTag.utils.nfc_initialize import nfc_initialize, Args
from Library.td1s import collect_data, DataCollectorThread

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
        self.filecache = {}
        self.packages = {}
        self.vendors = {}
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
        self.select_first_brandname()
        self.setup_material()
        self.add_default_material_properties()
        self.cache_filenames()
        self.read_vendors_from_database()
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
        self.td1sbutton.clicked.connect(self.on_readtd1s)
        self.readtagbtn.setDisabled(True)
        self.writetagbtn.setDisabled(True)
        self.td1sbutton.setDisabled(True)

        # NFC Reader support
        self.detector_thread = QThread()
        self.detector_worker = DeviceDetectorWorker(device_list=device_list, poll_interval_ms=1000)
        self.detector_worker.moveToThread(self.detector_thread)
        self.detector_thread.started.connect(self.detector_worker.start_detection)
        # Connect signals
        self.detector_worker.device_detected.connect(self.on_device_detected,Qt.QueuedConnection)
        self.detector_worker.device_removed.connect(self.on_device_removed,Qt.QueuedConnection)
        # Clean up
        self.detector_thread.finished.connect(self.detector_thread.deleteLater,Qt.QueuedConnection)
        self.detector_worker.finished.connect(self.detector_worker.deleteLater,Qt.QueuedConnection)
        self.detector_thread.start()

        # Auto-read polling
        self.auto_read_timer = QTimer(self)
        self.auto_read_timer.timeout.connect(self.try_auto_read_tag)
        self.last_read_uid = None          # to avoid reading the same tag repeatedly
        self.auto_read_enabled = False

        # We default to Prusament here
        self.brandnamebox.setCurrentText("Prusament")
        self.materialnamebox.setCurrentIndex(0)

        self.countryoforiginedit.textChanged.connect(self.on_country_change)


    def on_country_change(self):
        try:
            self.country_to_flag(self.countryoforiginedit.text())
        except Exception:
            pass

    def cache_filenames(self):
        for (root, dirs, files) in os.walk(os.path.join(script_path, "Library", "openprinttag-database", "data", "brands"), topdown=True):
            for file in files:
                filename = os.path.join(root, file)
                if ".yaml" == filename[-5:]:
                    vendorname = os.path.basename(filename).replace(".yaml", "")
                    vendorpath = os.path.join(script_path, "Library", "openprinttag-database", "data", "materials", vendorname)
                    for (root, dirs, files) in os.walk(vendorpath, topdown=True):
                        for file in files:
                            filename = os.path.join(root, file)
                            if ".yaml" == filename[-5:]:
                                if vendorname not in self.filecache:
                                    self.filecache[vendorname] = {}
                                materialname = os.path.basename(filename).replace(".yaml", "")
                                materialpackagepath = os.path.join(script_path, "Library", "openprinttag-database", "data",
                                                          "material-packages", vendorname)
                                if materialname not in self.filecache[vendorname]:
                                    self.filecache[vendorname][materialname] = []
                                for (root, dirs, files) in os.walk(materialpackagepath, topdown=True):
                                    for file in files:
                                        filename = os.path.join(root, file)
                                        if ".yaml" == filename[-5:] and materialname in file:
                                            self.filecache[vendorname][materialname].append(filename)

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
                    if not self.auto_read_enabled:
                        self.auto_read_timer.start(1000)
                        self.auto_read_enabled = True
                if not self.writetagbtn.isEnabled():
                    self.writetagbtn.setDisabled(False)

    def on_tag_detected(self, uid):
        if self.last_read_uid != uid and uid != b"":
            self.on_read_tag()
        self.last_read_uid = uid

    def try_auto_read_tag(self):
        if not self.auto_read_enabled:
            return
        if self.reader is None or self.reader <= 0:
            return  # no reader connected
        try:
            worker = NFC_ReadTagDetect(reader=self.reader, port=self.port)

            # Connect signals to UI updates
            worker.signals.finished.connect(self.on_tag_detected)
            self.threadpool.start(worker)

        except Exception as e:
            pass

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
                    if self.auto_read_enabled:
                        self.auto_read_timer.stop()
                        self.auto_read_enabled = False
                if self.writetagbtn.isEnabled():
                    self.writetagbtn.setDisabled(True)

    def msg(self, text, value: int = 0):
        self.statusbar.showMessage(self.tr(text), value)

    def set_progress(self, value: int):
        self.progressBar.setValue(value)
        self.progressBar.update()

    def on_read_tag(self):
        self.auto_read_timer.stop()
        self.progressBar.setValue(0)
        self.msg("Starting...")

        worker = NFC_ReadTagWorker(reader=self.reader, port=self.port)

        # Connect signals to UI updates
        worker.signals.progress.connect(self.set_progress)
        worker.signals.status.connect(self.msg)
        worker.signals.error.connect(self.handle_tag_error)  # Reuse your existing msg method
        worker.signals.finished.connect(self.handle_tag_read_success)
        # Start the worker in the thread pool
        self.threadpool.start(worker)

    def handle_tag_error(self, msg):
        self.msg(str(msg))
        self.auto_read_timer.start(1000)

    def handle_tag_read_success(self, tag):
        try:
            self.load_tag_data(tag.data)
            self.msg("Tag read and parsed successfully.")
        except Exception as e:
            self.msg(f"Error on parsing nfc tag: {str(e)}")
        finally:
            self.set_progress(0)
            self.msg("")
        self.auto_read_timer.start(1000)

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
            alpha = "%02x" % (int(((100-float(td))/100)*255)&0xFF)
            self.update_color_label("#" + color + alpha, self.colorlabel)
            self.primarycoloredit.setText("#" + color + alpha)
            self.transmissiondistanceedit.setText(td)

    def on_td1s_error(self, exc):
        self.show_message_box(self.tr("Error"), self.tr(f"TD1S error: {str(exc)}"), QMessageBox.Icon.Critical)

    def on_td1s_thread_done(self):
        self.td1sbutton.setEnabled(True)

    def on_readtd1s(self):
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
        material_name = self.materialnamebox.currentText()
        idx = material_name.rfind(" [")
        if idx != -1:
            material_name = material_name[:idx]
        update_data["main"] = dict(
            material_class=self.materialclassbox.currentText().split(" ")[0],
            material_type=self.materialtypebox.currentText().split(" ")[0],
            material_name=material_name[:31],
            brand_name=self.brandnamebox.currentText()[:31],
            manufactured_date=self.locale_to_timestamp(self.dateedit.text()),
            nominal_netto_full_weight=self.nominalweightbox.value(),
            actual_netto_full_weight=self.actualweightbox.value(),
            empty_container_weight=self.emptycontainerbox.value()
        )
        if self.materialabbredit.text() != "":
            update_data["main"]["material_abbreviation"] = self.materialabbredit.text()[:7]
        if self.countryoforiginedit.text() != "":
            update_data["main"]["country_of_origin"] = self.countryoforiginedit.text()[:2]
        if self.gtinedit.text() != "":
            update_data["main"]["gtin"] = int(self.gtinedit.text())
        if self.expdateedit.text() != "00.00.00":
            update_data["main"]["expiration_date"] = self.locale_to_timestamp(self.dateedit.text())
        if self.primarycoloredit.text() != "":
            update_data["main"]["primary_color"] = self.primarycoloredit.text()
        if self.secondarycoloredit_0.text() != "":
            update_data["main"]["secondary_color_0"] = self.secondarycoloredit_0.text()
        if self.secondarycoloredit_1.text() != "":
            update_data["main"]["secondary_color_1"] = self.secondarycoloredit_1.text()
        if self.secondarycoloredit_2.text() != "":
            update_data["main"]["secondary_color_2"] = self.secondarycoloredit_2.text()
        if self.secondarycoloredit_3.text() != "":
            update_data["main"]["secondary_color_3"] = self.secondarycoloredit_3.text()
        if self.secondarycoloredit_4.text() != "":
            update_data["main"]["secondary_color_4"] = self.secondarycoloredit_4.text()
        if self.transmissiondistanceedit.text() != "":
            update_data["main"]["transmission_distance"] = float(self.transmissiondistanceedit.text())
        if self.densityedit.text != "":
            update_data["main"]["density"] = float(self.densityedit.text())
        if self.diameteredit.text() != "":
            update_data["main"]["filament_diameter"] = float(self.diameteredit.text())
        # nominal_full_length
        # actual_full_length
        if self.hardnessshoreabox.value() != 0:
            update_data["main"]["shore_hardness_a"] = self.hardnessshoreabox.value()
        if self.hardnessshoredbox.value() != 0:
            update_data["main"]["shore_hardness_d"] = self.hardnessshoredbox.value()
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
        if self.minchambertempbox.value() != 0:
            update_data["main"]["min_chamber_temperature"] = self.minchambertempbox.value()
        if self.maxchambertempbox.value() != 0:
            update_data["main"]["max_chamber_temperature"] = self.maxchambertempbox.value()
        if self.chambertempbox.value() != 0:
            update_data["main"]["chamber_temperature"] = self.chambertempbox.value()
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
              self.materialnamebox.currentText().replace(" ", "_").replace("-", "_")) + ".bin"
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

    def load_tag_data(self, data):
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
            if "material_abbreviation" in main:
                self.materialabbredit.setText(main["material_abbreviation"])
            if "country_of_origin" in main:
                self.countryoforiginedit.setText(main["country_of_origin"])
                self.country_to_flag(main["country_of_origin"])
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
            if "material_abbreviation" in main:
                materialabbr = main["material_abbreviation"][:7]
                self.materialabbredit.setText(materialabbr)
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
            else:
                self.nominalweightbox.setValue(1000)
            if "actual_netto_full_weight" in main:
                self.actualweightbox.setValue(main["actual_netto_full_weight"])
            else:
                self.actualweightbox.setValue(min(self.nominalweightbox.value(),1000))
            if "empty_container_weight" in main:
                self.emptycontainerbox.setValue(main["empty_container_weight"])
            else:
                self.emptycontainerbox.setValue(0)
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
                self.primarycoloredit.setText(main["primary_color"])
                self.update_color_label(main["primary_color"], self.colorlabel)
            self.picturelabel.setPixmap(QPixmap())
            colors = []
            for i in range(5):
                if f"secondary_color_{i}" in main:
                    colors.append(main[f"secondary_color_{i}"])
            self.set_secondary_colors(colors)

            if "filament_diameter" in main:
                self.diameteredit.setText("%.02f" % main["filament_diameter"])
            else:
                self.diameteredit.setText("1.75")
            if "density" in main:
                self.densityedit.setText("%.02f" % main["density"])
            if "min_print_temperature" in main:
                self.minprinttempbox.setValue(main["min_print_temperature"])
            else:
                self.minprinttempbox.setValue(0)
            if "max_print_temperature" in main:
                self.maxprinttempbox.setValue(main["max_print_temperature"])
            else:
                self.maxprinttempbox.setValue(0)
            if "preheat_temperature" in main:
                self.preheattempbox.setValue(main["preheat_temperature"])
            else:
                self.preheattempbox.setValue(0)
            if "min_bed_temperature" in main:
                self.minbedtempbox.setValue(main["min_bed_temperature"])
            else:
                self.minbedtempbox.setValue(0)
            if "min_chamber_temperature" in main:
                self.minchambertempbox.setValue(main["min_chamber_temperature"])
            else:
                self.minchambertempbox.setValue(0)
            if "max_chamber_temperature" in main:
                self.maxchambertempbox.setValue(main["max_chamber_temperature"])
            else:
                self.maxchambertempbox.setValue(0)
            if "chamber_temperature" in main:
                self.chambertempbox.setValue(main["chamber_temperature"])
            else:
                self.chambertempbox.setValue(0)
            if "max_bed_temperature" in main:
                self.maxbedtempbox.setValue(main["max_bed_temperature"])
            else:
                self.maxbedtempbox.setValue(0)
            if "transmission_distance" in main:
                self.transmissiondistanceedit.setText("%0.1f" % main["transmission_distance"])
            if "shore_hardness_d" in main:
                self.hardnessshoredbox.setValue(main["shore_hardness_d"])
            else:
                self.hardnessshoredbox.setValue(0)
            if "shore_hardness_a" in main:
                self.hardnessshoreabox.setValue(main["shore_hardness_a"])
            else:
                self.hardnessshoreabox.setValue(0)
            self.matpropwidget.filter_check.setChecked(False)
            if "tags" in main:
                for tag in main["tags"]:
                    prop = self.matpropwidget.get_name(tag)
                    if prop is not None:
                        self.matpropwidget.set_property_checked(property_name=prop, checked=True)
                        self.check_tag_implies(tag)
                self.matpropwidget.filter_check.setChecked(True)

            # Make sure uri is read after manufacturer or material change
            if uri is not None and uri != "":
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
                self.load_tag_data(data)
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
            hex_color = self.argb_to_rgba(color.name(QColor.HexArgb))

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
            hex_color = self.argb_to_rgba(color.name(QColor.HexRgb))

            editbox.setText(hex_color)
            self.update_color_label(hex_color, labelbox)

    def open_secondary0_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycoloredit_0, self.secondary_colorlabel_0)

    def open_secondary1_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycoloredit_1, self.secondary_colorlabel_1)

    def open_secondary2_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycoloredit_2, self.secondary_colorlabel_2)

    def open_secondary3_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycoloredit_3, self.secondary_colorlabel_3)

    def open_secondary4_color_picker(self, event):
        _ = event
        self.set_secondary(self.secondarycoloredit_4, self.secondary_colorlabel_4)

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

    def select_first_brandname(self):
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
        mt_filename = os.path.join(script_path, "database", "material_temps.yaml")
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

    def reset_colors(self):
        self.update_color_label("#000000ff", self.colorlabel)
        self.set_secondary_colors([])
        self.primarycoloredit.setText("")
        self.primarycolorraledit.setText("")

    def add_default_material_properties(self):
        self.tags = self.read_openprinttag_tags()
        if self.tags is not None:
            self.matpropwidget.load_tags(self.tags)

    def setup_color(self, brandname: str, materialname: str, colorname: str):
        if brandname in self.filaments and materialname in self.filaments[brandname]:
            cm = self.filaments[brandname][materialname]
            if "colors" not in cm:
                return
            color_props = cm["colors"].get(colorname)
            if color_props is None:
                return
            if "primary_color" in color_props:
                color = color_props["primary_color"]
                if "RAL" in color:
                    self.primarycolorraledit.setText(color.lower())
                    color = ral_to_hex(color)
                else:
                    self.primarycolorraledit.setText(hex_to_ral(color))
                self.primarycoloredit.setText(color.lower())
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

    def set_secondary_colors(self, colors):
        if colors == []:
            colors = ["#000000ff","#000000ff","#000000ff","#000000ff","#000000ff"]
        i = 0
        for argb in colors:
            if i == 0:
                if argb == "#000000ff":
                    self.secondarycoloredit_0.setText("")
                else:
                    self.secondarycoloredit_0.setText(argb)
                self.update_color_label(argb, self.secondary_colorlabel_0)
            elif i == 1:
                if argb == "#000000ff":
                    self.secondarycoloredit_1.setText("")
                else:
                    self.secondarycoloredit_1.setText(argb)
                self.update_color_label(argb, self.secondary_colorlabel_1)
            elif i == 2:
                if argb == "#000000ff":
                    self.secondarycoloredit_2.setText("")
                else:
                    self.secondarycoloredit_2.setText(argb)
                self.update_color_label(argb, self.secondary_colorlabel_2)
            elif i == 3:
                if argb == "#000000ff":
                    self.secondarycoloredit_3.setText("")
                else:
                    self.secondarycoloredit_3.setText(argb)

                self.update_color_label(argb, self.secondary_colorlabel_3)
            elif i == 4:
                if argb == "#000000ff":
                    self.secondarycoloredit_4.setText("")
                else:
                    self.secondarycoloredit_4.setText(argb)
                self.update_color_label(argb, self.secondary_colorlabel_4)
            i += 1

    def rgba_to_argb(self, rgba:str):
        argb = "#" + rgba[7:9] + rgba[1:7]
        return argb

    def argb_to_rgba(self, rgba:str):
        if len(rgba) > 7:
            argb = "#" + rgba[3:9] + rgba[1:3]
        else:
            argb = rgba + "ff"
        return argb


    def setup_default_material(self, brandname, materialname):
        if materialname in self.filaments:
            cm = self.filaments[materialname]
            if hasattr(cm, "abbreviation"):
                self.materialabbredit.setText(cm.abbreviation)
            if brandname in self.vendors:
                curbrand = self.vendors[brandname]
                if hasattr(curbrand, "countries_of_origin"):
                    country_of_origin = curbrand.countries_of_origin
                    if len(country_of_origin) > 0:
                        self.countryoforiginedit.setText(country_of_origin[0])
                        self.country_to_flag(country_of_origin[0])
            if hasattr(cm, "type"):
                materialtype = cm.type
                self.materialtypebox.setCurrentText(materialtype)
                cf = self.default_filamenttypes.get(materialtype)
                if hasattr(cm, "properties") and "min_bed_temperature" in cm.properties:
                    self.minbedtempbox.setValue(cm.properties["min_bed_temperature"])
                elif "bed_min_temp" in cf:
                    self.minbedtempbox.setValue(cf["bed_min_temp"])
                if hasattr(cm, "properties") and "max_bed_temperature" in cm.properties:
                    self.maxbedtempbox.setValue(cm.properties["max_bed_temperature"])
                elif "bed_max_temp" in cf:
                    self.maxbedtempbox.setValue(cf["bed_max_temp"])
                if hasattr(cm, "properties") and "min_print_temperature" in cm.properties:
                    self.minprinttempbox.setValue(cm.properties["min_print_temperature"])
                elif "min_temp" in cf:
                    self.minprinttempbox.setValue(cf["min_temp"])
                if hasattr(cm, "properties") and "max_print_temperature" in cm.properties:
                    self.maxprinttempbox.setValue(cm.properties["max_print_temperature"])
                elif "min_temp" in cf:
                    self.maxprinttempbox.setValue(cf["max_temp"])
                if hasattr(cm, "properties") and "preheat_temperature" in cm.properties:
                    self.preheattempbox.setValue(cm.properties["preheat_temperature"])
                elif "preheat_temp" in cf:
                    self.preheattempbox.setValue(cf["preheat_temp"])
                if hasattr(cm, "properties") and "chamber_temperature" in cm.properties:
                    self.chambertempbox.setValue(cm.properties["chamber_temperature"])
                elif "chamber_temp" in cf:
                    self.chambertempbox.setValue(cf["chamber_temp"])
                else:
                    self.chambertempbox.setValue(0)
                if hasattr(cm, "properties") and "max_chamber_temperature" in cm.properties:
                    self.maxchambertempbox.setValue(cm.properties["max_chamber_temperature"])
                elif "max_chamber_temp" in cf:
                    self.maxchambertempbox.setValue(cf["max_chamber_temp"])
                else:
                    self.maxchambertempbox.setValue(0)
                if hasattr(cm, "properties") and "min_chamber_temperature" in cm.properties:
                    self.minchambertempbox.setValue(cm.properties["min_chamber_temperature"])
                elif "min_chamber_temp" in cf:
                    self.minchambertempbox.setValue(cf["min_chamber_temp"])
                else:
                    self.minchambertempbox.setValue(0)
            if hasattr(cm, "properties"):
                properties = cm.properties
                if "density" in properties:
                    self.densityedit.setText("%.02f" % properties["density"])
                else:
                    self.densityedit.setText("")
                if "hardness_shore_d" in properties:
                    self.hardnessshoredbox.setValue(properties["hardness_shore_d"])
                else:
                    self.hardnessshoredbox.setValue(0)
                if "hardness_shore_a" in properties:
                    self.hardnessshoreabox.setValue(properties["hardness_shore_a"])
                else:
                    self.hardnessshoreabox.setValue(0)
            if hasattr(cm,"primary_color"):
                if "color_rgba" in cm.primary_color:
                    hex_color = cm.primary_color["color_rgba"]
                    # We need to convert rgba to argb
                    self.primarycoloredit.setText(hex_color)
                    self.primarycolorraledit.setText(hex_to_ral(hex_color))
                    self.update_color_label(hex_color, self.colorlabel)
            else:
                argb = "#000000ff"
                self.primarycoloredit.setText(argb)
                self.primarycolorraledit.setText(hex_to_ral(argb))
                self.update_color_label(argb, self.colorlabel)

            colors = []
            if hasattr(cm,"secondary_colors"):
                for color in cm.secondary_colors:
                    if "color_rgba" in color:
                        hex_color = color["color_rgba"]
                        colors.append(hex_color)
            self.set_secondary_colors(colors)

            # toDo: photos
            if hasattr(cm,"photos"):
                for photoitem in cm.photos:
                    if "url" in photoitem:
                        url = photoitem["url"]
                        try:
                            response = requests.get(url,timeout=1)
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            self.picturelabel.setPixmap(pixmap.scaled(self.picturelabel.frameSize(),Qt.KeepAspectRatio))
                        except Exception as e:
                            self.picturelabel.setPixmap(QPixmap())
                        break
            else:
                self.picturelabel.setPixmap(QPixmap())
            if hasattr(cm, "url"):
                self.urledit.setText(cm.url)
                self.includeurlcheckbox.setChecked(True)
            else:
                self.urledit.setText("")
                self.includeurlcheckbox.setChecked(False)

            if hasattr(cm,"transmission_distance"):
                self.transmissiondistanceedit.setText("%.02f" % cm.transmission_distance)
            else:
                self.transmissiondistanceedit.setText("")

            # toDo: uuid
            if hasattr(cm, "uuid"):
                uuid = cm.uuid

            if hasattr(cm, "class"):
                self.materialclassbox.setCurrentText(getattr(cm,"class"))

            if hasattr(cm, "tags"):
                self.add_material_properties(cm.tags)

    def on_manufacturer_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        manufacturername = self.brandnamebox.currentText()
        if manufacturername in self.vendors:
            if hasattr(self.vendors[manufacturername], "slug"):
                manufacturer = self.vendors[manufacturername].slug
                self.filaments = self.read_filaments_from_database(manufacturer)
                if manufacturer not in self.filaments:
                    self.filaments[manufacturer] = self.read_filaments_from_database(manufacturer)
                filaments = self.filaments[manufacturer]
                if not filaments:
                    return
                self.materialnamebox.clear()
                for entry in filaments:
                    prefs = filaments[entry]
                    if hasattr(prefs, "slug"):
                        if prefs.slug not in self.packages:
                            packages = self.read_packages_from_database(vendorname=manufacturer,materialname=prefs.slug)
                            if packages:
                                self.packages[prefs.slug] = packages
                                for package in packages:
                                    if hasattr(package, "nominal_netto_full_weight"):
                                        nominal_netto_full_weight = "%.02fKg" % (package.nominal_netto_full_weight/1000)
                                    else:
                                        nominal_netto_full_weight = ""

                                    # toDo: filament_diameter is in mm, but database has incorrect format
                                    package.filament_diameter = package.filament_diameter/1000
                                    # End of change

                                    diameter = "%.02fmm" % (package.filament_diameter)
                                    class info:
                                        materialname=prefs.slug
                                        if hasattr(package, "nominal_netto_full_weight"):
                                            nominal_netto_full_weight=package.nominal_netto_full_weight
                                        if hasattr(package, "filament_diameter"):
                                            diameter=package.filament_diameter
                                        if hasattr(package, "empty_container_weight"):
                                            empty_container_weight=package.empty_container_weight
                                    if hasattr(prefs,"name"):
                                        name = prefs.name
                                        self.materialnamebox.addItem(f"{name} [{nominal_netto_full_weight} {diameter}]",info())
                            else:
                                if hasattr(prefs,"name"):
                                    name = prefs.name
                                    class info:
                                        materialname=prefs.slug
                                        diameter=1750
                                        nominal_netto_full_weight=1000
                                        empty_container_weight=0
                                    self.materialnamebox.addItem(f"{name}", info())
                    else:
                        self.materialnamebox.addItem(entry)
                self.materialnamebox.model().sort(0, Qt.AscendingOrder)
                self.materialnamebox.setCurrentIndex(0)
                self.matpropwidget.filter_check.setChecked(False)

    def update_color_label(self, hex_color: str, colorlabel: QLabel):
        # Fill a tiny pixmap with the chosen color
        pix = QPixmap(colorlabel.size())
        pix.fill(QColor(self.rgba_to_argb(hex_color)))
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

    def country_to_flag(self, code: str):
        code = code.upper()
        if len(code) != 2 or not code.isalpha():
            txt="🏳️"  # invalid input fallback
            self.countryflaglabel.setText(txt)
            return
        # Regional Indicator Symbol Letters start at U+1F1E6 = ord('🇦')
        offset = 0x1F1E6 - ord('A')
        txt=chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)
        self.countryflaglabel.setText(txt)

    def on_materialname_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        brandname = self.brandnamebox.currentText()
        vendorslug=""
        if brandname in self.vendors:
            if hasattr(self.vendors[brandname], "slug"):
                vendorslug = self.vendors[brandname].slug
        itemdata = self.materialnamebox.currentData()
        if itemdata and hasattr(itemdata,"materialname"):
            materialslug = itemdata.materialname
            self.packages = self.read_packages_from_database(vendorname=vendorslug,materialname=materialslug)
            if hasattr(itemdata,"diameter") and hasattr(itemdata,"nominal_netto_full_weight"):
                nominal_netto_full_weight = itemdata.nominal_netto_full_weight
                diameter = itemdata.diameter
                for package in self.packages:
                    if (package.nominal_netto_full_weight == nominal_netto_full_weight and
                        package.filament_diameter/1000 == diameter):
                        if hasattr(package,"gtin"):
                            self.gtinedit.setText("%d" % package.gtin)
                        break
            if hasattr(itemdata, "diameter"):
                self.diameteredit.setText(str(itemdata.diameter))
            if hasattr(itemdata, "nominal_netto_full_weight"):
                self.nominalweightbox.setValue(itemdata.nominal_netto_full_weight)
                self.actualweightbox.setValue(itemdata.nominal_netto_full_weight)
            else:
                self.nominalweightbox.setValue(1000)
                self.actualweightbox.setValue(1000)

            if hasattr(itemdata, "empty_container_weight"):
                self.emptycontainerbox.setValue(itemdata.empty_container_weight)
            else:
                self.emptycontainerbox.setValue(0)
            materialprops = self.filaments.get(materialslug)
            if materialprops is not None:
                self.setup_default_material(brandname, materialslug)

    """ 
    def add_filaments(self):
        self.filaments = {}
        for (root, dirs, files) in os.walk(os.path.join(script_path, "database", "filaments"), topdown=True):
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
#                    combobox-popup: 0;
#                    QListWidget::item { padding: 4px; }
#                    QListWidget { border: 1px solid #999; }
#                """)
#        self.brandnamebox.currentTextChanged.connect(self.on_manufacturer_changed)
#        self.brandnamebox.model().sort(0, Qt.AscendingOrder)
#    """

    def read_vendors_from_database(self):
        self.vendors = {}
        for vendorname in self.filecache:
            fn = os.path.join(script_path, "Library", "openprinttag-database", "data", "brands", vendorname+".yaml")
            if os.path.exists(fn):
                vendor_dict = yaml.safe_load(open(fn, "r"))
                if "name" in vendor_dict and "slug" in vendor_dict:
                    class Vendor_T:
                        slug = vendor_dict["slug"]
                        countries_of_origin = vendor_dict["countries_of_origin"]

                    self.vendors[vendor_dict["name"]] = Vendor_T()

        for brand_name in self.vendors:
            self.brandnamebox.addItem(brand_name)
        self.brandnamebox.setStyleSheet("""
                    combobox-popup: 0;
                    QListWidget::item { padding: 4px; }
                    QListWidget { border: 1px solid #999; }
                """)
        self.brandnamebox.currentTextChanged.connect(self.on_manufacturer_changed)
        self.brandnamebox.model().sort(0, Qt.AscendingOrder)

    def read_filaments_from_database(self, vendorname:str):
        # self.filecache[vendorname][materialname]
        filaments = {}
        if not vendorname in self.filecache:
            return filaments
        for material in self.filecache[vendorname]:
            fn = os.path.join(script_path, "Library", "openprinttag-database", "data", "materials", vendorname, material + ".yaml")
            if os.path.exists(fn):
                try:
                    filament_dict = yaml.safe_load(open(os.path.join(fn), "r"))
                    fd = SimpleNamespace(**filament_dict)
                    if hasattr(fd, "slug"):
                        filaments[fd.slug] = fd
                except Exception as e:
                    self.msg(f"YAML Error in {fn}: {str(e)}")
        return filaments

    def read_packages_from_database(self, vendorname:str, materialname:str) -> list:
        packages = []
        if vendorname not in self.filecache or materialname not in self.filecache[vendorname]:
            return packages

        for fn in self.filecache[vendorname][materialname]:
            try:
                package_dict = yaml.safe_load(open(os.path.join(fn), "r"))
                fd = SimpleNamespace(**package_dict)
                if hasattr(fd,"material") and "slug" in fd.material:
                    material_name = fd.material["slug"]
                    if material_name == materialname:
                        packages.append(fd)
            except Exception as e:
                self.msg(f"YAML Error in {fn}: {str(e)}")
        return packages

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

def main():
    app = QApplication(sys.argv)
    info = "OpenPrintTagGUI v1.03 (c) B.Kerler"
    app.setApplicationName(info)
    widget = GUI_OpenPrintTag()
    widget.setWindowTitle(info)
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if os.path.exists(filename):
            data = open(filename, "rb").read()
            widget.load_tag_data(data)
        else:
            print(f"Filename {filename} doesn't exist ! Aborting ...")
            sys.exit(1)
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()