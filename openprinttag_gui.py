#!/usr/bin/env python3
import json
import os
import sys
from collections import deque
from PySide6.QtCore import Qt, QLocale, QDate, QDateTime
from PySide6.QtGui import QValidator, QColor, QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QCalendarWidget, QVBoxLayout, QDialog, \
    QColorDialog, QFileDialog, QLabel, QMessageBox, QLineEdit

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(script_path))
sys.path.insert(1, script_path)
sys.path.insert(2, os.path.join(script_path, "Library", "OpenPrintTag", "utils"))

from GUI.colorconversion import ral_to_hex, hex_to_ral
from GUI.gui import Ui_OpenPrintTagGui
from Library.OpenPrintTag.utils.record import Record
from Library.OpenPrintTag.utils.common import default_config_file
from Library.OpenPrintTag.utils.nfc_initialize import nfc_initialize, Args


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
        self.aux_region_size = None
        self.aux_region_offset = None
        self.main_region_size = None
        self.main_region_offset = None
        self.filaments = {}
        self.default_manufacturers = {}
        self.default_filamenttypes = {}
        self.setupUi(self)
        self.add_default_manufacturers()
        self.add_default_filaments()
        self.add_material_properties()
        self.add_filaments()
        # We default to Prusament here
        self.brandnamebox.setCurrentText("Prusament")
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

        # toDo implement
        self.readtagbtn.setDisabled(True)
        self.writetagbtn.setDisabled(True)
        self.td1sbutton.setDisabled(True)
        # end ToDo

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
        result = msg.exec()

    def on_save_file(self):
        fn = (self.brandnamebox.currentText().replace(" ", "_").replace("-", "_") + "_" +
              self.materialnamebox.currentText().replace(" ", "_").replace("-", "_") + "_" +
              self.colornamebox.currentText().replace(" ", "_").replace("-", "_")) + ".bin"
        filename, selfilter = QFileDialog.getSaveFileName(self, "Select Tag data file", dir=fn)
        if filename != "":
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
            if open(filename, "wb").write(record.data.tobytes()):
                self.show_message_box(title="Info", message=f"Successfully wrote {filename}")

    def load_file(self, filename):
        self.matpropwidget.uncheck()
        self.matpropwidget.filter_check.setChecked(False)
        data = open(filename, "rb").read()
        fields, uri = self.parse_tag_data(data)
        if uri != "":
            self.includeurlcheckbox.setChecked(True)
            self.urledit.setText(uri)
        else:
            self.includeurlcheckbox.setChecked(False)
            self.urledit.setText("")
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
                found = False
                for filament in self.default_filamenttypes:
                    cf = filament.split(" ")[0]
                    if cf == cur_material_type:
                        found = True
                        self.materialtypebox.setCurrentText(filament)
                if not found:
                    self.materialtypebox.setCurrentText(cur_material_type)
            if "brand_name" in main:
                self.brandnamebox.setCurrentText(main["brand_name"])
            if "material_name" in main:
                self.materialnamebox.setCurrentText(main["material_name"])
            elif "material_abbreviation" in main:
                self.materialnamebox.setCurrentText(main["material_abbreviation"])
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
            if "primary_color" in main:
                if "hex" in main["primary_color"]:
                    self.primarycoloredit.setText('#' + main["primary_color"]["hex"])
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
            if "tags" in main:
                for tag in main["tags"]:
                    prop = self.matpropwidget.get_name(tag)
                    if prop is not None:
                        self.matpropwidget.set_property_checked(property_name=prop, checked=True)
                        dq = deque()
                        dq.append(tag)
                        while dq:
                            tag = dq.popleft()
                            if tag in self.matpropwidget.implication_data:
                                for subtag in self.matpropwidget.implication_data[tag]:
                                    subprop = self.matpropwidget.get_name(subtag)
                                    if subprop is not None:
                                        self.matpropwidget.set_property_checked(property_name=subprop, checked=True)
                                    dq.append(subprop)
        self.matpropwidget.filter_check.setChecked(True)

    def on_load_file(self):
        filename, selfilter = QFileDialog.getOpenFileName(self, "Select Tag data file")
        if filename != "":
            self.load_file(filename)

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
            title="Select a color",
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
            title="Select a color",
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

    def add_default_filaments(self):
        self.default_filamenttypes = json.loads(open(os.path.join(script_path, "data", "material_types.json")).read())
        materialclasses = json.loads(open(os.path.join(script_path, "data", "material_classes.json")).read())
        self.materialclassbox.clear()
        idx = 0
        for materialclass in materialclasses:
            self.materialclassbox.addItem(materialclass + " - " + materialclasses[materialclass])
            idx += 1
        for filament in self.default_filamenttypes:
            self.materialtypebox.addItem(filament)
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

    def add_material_properties(self):
        matprop_filename = os.path.join(script_path, "data", "material_properties.json")
        if os.path.exists(matprop_filename):
            matprop = open(matprop_filename).read()
            matprop_imp_filename = os.path.join(script_path, "data", "material_properties_implication.json")
            if os.path.exists(matprop_imp_filename):
                matprop_implication = open(matprop_imp_filename).read()
                self.matpropwidget.load_json(matprop, matprop_implication)

    def on_manufacturer_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        manufacturer = self.brandnamebox.currentText()
        found = False
        if manufacturer in self.filaments:
            found = True
            self.materialnamebox.clear()
            for material in self.filaments[manufacturer]:
                if "weight" in self.filaments[manufacturer][material]:
                    emptycontainer, nominalweight, actualweight = self.filaments[manufacturer][material]["weight"]
                    self.emptycontainerbox.setValue(emptycontainer)
                    self.nominalweightbox.setValue(nominalweight)
                    self.actualweightbox.setValue(actualweight)
                self.materialnamebox.addItem(material)
            self.materialnamebox.model().sort(0, Qt.AscendingOrder)
            self.materialnamebox.setCurrentIndex(0)
        self.matpropwidget.filter_check.setChecked(found)

    def update_color_label(self, hex_color: str, colorlabel: QLabel):
        # Fill a tiny pixmap with the chosen color
        pix = QPixmap(colorlabel.size())
        pix.fill(QColor(hex_color))
        colorlabel.setPixmap(pix)

    def add_material_property(self, materialprops):
        self.matpropwidget.uncheck()
        self.matpropwidget.filter_check.setChecked(False)
        properties = materialprops["properties"]
        for tag in properties:
            self.matpropwidget.set_property_checked(property_name=self.matpropwidget.get_name(tag), checked=True)
            if tag is not None:
                dq = deque()
                dq.append(tag)
                while dq:
                    tag = dq.popleft()
                    if tag in self.matpropwidget.implication_data:
                        for subtag in self.matpropwidget.implication_data[tag]:
                            subprop = self.matpropwidget.get_name(subtag)
                            if subprop is not None:
                                self.matpropwidget.set_property_checked(property_name=subprop, checked=True)
                            dq.append(subprop)
        self.matpropwidget.filter_check.setChecked(True)
        self.matpropwidget.repaint()

    def on_colorname_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        current_manufacturer = self.brandnamebox.currentText()
        current_material = self.materialnamebox.currentText()
        current_colorname = self.colornamebox.currentText()
        if current_manufacturer in self.filaments:
            for material in self.filaments[current_manufacturer]:
                if current_material == material:
                    materialprops = self.filaments[current_manufacturer][material]
                    if "diameter" in materialprops:
                        diameter = materialprops["diameter"]
                        self.diameteredit.setText("%.02f" % diameter)
                    else:
                        self.diameteredit.setText("1.75")
                    if "color" in materialprops:
                        hexcolor = materialprops["color"]
                        if isinstance(hexcolor, list):
                            if len(hexcolor) == 2:
                                hexcolor, transmission_distance = materialprops["color"]
                                self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                            elif len(hexcolor) == 3:
                                hexcolor, transmission_distance, uri = materialprops["color"]
                                self.urledit.setText(uri)
                                self.includeurlcheckbox.setChecked(True)
                                self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                        self.primarycoloredit.setText(hexcolor)
                        self.primarycolorraledit.setText(hex_to_ral(hexcolor))
                    elif "colors" in materialprops:
                        for colorname in materialprops["colors"]:
                            if colorname == current_colorname:
                                hexcolor = materialprops["colors"][colorname]
                                if isinstance(hexcolor, list):
                                    uri = ""
                                    if len(materialprops["colors"][colorname]) == 2:
                                        hexcolor, transmission_distance = materialprops["colors"][colorname]
                                        self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                                    elif len(materialprops["colors"][colorname]) == 3:
                                        hexcolor, transmission_distance, uri = materialprops["colors"][colorname]
                                        self.urledit.setText(uri)
                                        self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                                    self.includeurlcheckbox.setChecked(True) \
                                        if uri != "" else self.includeurlcheckbox.setChecked(False)
                                    self.urledit.setText(uri)

                                if "RAL" in hexcolor:
                                    self.primarycolorraledit.setText(hexcolor)
                                    hexcolor = ral_to_hex(hexcolor)
                                else:
                                    self.primarycolorraledit.setText(hex_to_ral(hexcolor))
                                self.primarycoloredit.setText(hexcolor)
                                self.update_color_label(hexcolor, self.colorlabel)
                                return
                    if "properties" in materialprops:
                        self.add_material_property(materialprops)

    def on_materialname_changed(self):
        self.includeurlcheckbox.setChecked(False)
        self.urledit.clear()
        self.reset_colors()
        current_manufacturer = self.brandnamebox.currentText()
        current_material = self.materialnamebox.currentText()
        if current_manufacturer in self.filaments:
            for material in self.filaments[current_manufacturer]:
                if current_material == material:
                    materialprops = self.filaments[current_manufacturer][material]
                    self.colornamebox.clear()
                    if "diameter" in materialprops:
                        diameter = materialprops["diameter"]
                        self.diameteredit.setText("%.02f" % diameter)
                    else:
                        self.diameteredit.setText("1.75")
                    if "colors" in materialprops:
                        for colorname in materialprops["colors"]:
                            if "RAL" in colorname:
                                colorname = ral_to_hex(colorname)
                            self.colornamebox.addItem(f"{colorname}")
                    elif "color" in materialprops:
                        color = materialprops["color"]
                        if isinstance(color, list):
                            if len(color) == 2:
                                color, transmission_distance = materialprops["color"]
                                self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                            elif len(color) == 3:
                                color, transmission_distance, uri = materialprops["color"]
                                self.transmissiondistanceedit.setText("%.01f" % transmission_distance)
                                self.urledit.setText(uri)
                                self.includeurlcheckbox.setChecked(True)
                        self.primarycoloredit.setText(color)
                        self.primarycolorraledit.setText(hex_to_ral(color))
                        self.update_color_label(color, self.colorlabel)
                    if "density" in materialprops:
                        density = materialprops["density"]
                        self.densityedit.setText("%.02f" % density)
                    if "bed" in materialprops:
                        bed_temps = materialprops["bed"]
                        self.minbedtempbox.setValue(bed_temps[0])
                        self.maxbedtempbox.setValue(bed_temps[1])
                    if "nozzle" in materialprops:
                        nozzle_temps = materialprops["nozzle"]
                        self.minprinttempbox.setValue(nozzle_temps[0])
                        self.maxprinttempbox.setValue(nozzle_temps[1])
                    if "material" in materialprops:
                        material = materialprops["material"]
                        for filament in self.default_filamenttypes:
                            cf = filament.split(" ")[0]
                            if cf == material:
                                self.materialtypebox.setCurrentText(filament)
                    if "properties" in materialprops:
                        self.add_material_property(materialprops)
                    self.colornamebox.model().sort(0, Qt.AscendingOrder)
                    self.colornamebox.setCurrentIndex(0)
                    break

    def add_filaments(self):
        self.filaments = {}
        for (root, dirs, files) in os.walk(os.path.join(script_path, "data", "filaments"), topdown=True):
            for file in files:
                filename = os.path.join(root, file)
                try:
                    filament_dict = json.loads(open(filename).read())
                    for manufacturer in filament_dict:
                        self.filaments[manufacturer] = filament_dict[manufacturer]
                except json.JSONDecodeError as e:
                    print(f"JSON Error in {filename}", e)
        for manufacturer in self.filaments:
            self.brandnamebox.addItem(manufacturer)
        self.brandnamebox.setStyleSheet("""
                    combobox-popup: 0;
                    QListWidget::item { padding: 4px; }
                    QListWidget { border: 1px solid #999; }
                """)
        self.brandnamebox.currentTextChanged.connect(self.on_manufacturer_changed)
        self.brandnamebox.model().sort(0, Qt.AscendingOrder)
        self.brandnamebox.setCurrentIndex(0)

    def parse_tag_data(self, data):
        uri = ""
        record = Record(config_file=default_config_file, data=memoryview(data))
        fields = {}
        for name, region in record.regions.items():
            unknown_fields = dict()
            fields[name] = region.read(out_unknown_fields=unknown_fields)
        if hasattr(record, "uri"):
            uri = record.uri
        return fields, uri


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GUI_OpenPrintTag()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if os.path.exists(filename):
            widget.load_file(filename)
        else:
            print(f"Filename {filename} doesn't exist ! Aborting ...")
            sys.exit(1)
    widget.show()
    sys.exit(app.exec())
