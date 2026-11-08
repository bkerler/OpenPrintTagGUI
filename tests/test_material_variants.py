import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication, QMainWindow

from openprinttaggui import openprinttag_gui


MATERIAL = "prusament-petg-clear"
CURRENT = "1.00Kg,1.75mm,Current NFC Spool"


class MaterialVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["tests", "-platform", "offscreen"])
        previous_locale = QLocale()
        QLocale.setDefault(QLocale.c())
        cls.addClassCleanup(QLocale.setDefault, previous_locale)

    def setUp(self):
        self.window = openprinttag_gui.GUI_OpenPrintTag.__new__(openprinttag_gui.GUI_OpenPrintTag)
        QMainWindow.__init__(self.window)
        self.window.setupUi(self.window)
        self.addCleanup(self.window.deleteLater)
        self.window.packages = {}
        self.window.filaments = {}
        self.window.tags = {}
        self.window.matpropwidget.load_tags({})
        self.window.vendors = {
            "Prusament": SimpleNamespace(slug="prusament"),
            "Empty brand": SimpleNamespace(slug="empty"),
        }
        materials = {
            MATERIAL: SimpleNamespace(slug=MATERIAL, name="PETG Clear"),
            "single": SimpleNamespace(slug="single", name="Single"),
            "unpackaged": SimpleNamespace(slug="unpackaged", name="Unpackaged"),
        }
        self.packages = {
            MATERIAL: [
                SimpleNamespace(slug=MATERIAL + "-1000-old-refill", material={"slug": MATERIAL},
                                nominal_netto_full_weight=1000, filament_diameter=1750,
                                gtin=8594173676169),
                SimpleNamespace(slug=MATERIAL + "-1000-old-spool", material={"slug": MATERIAL},
                                nominal_netto_full_weight=1000, filament_diameter=1750,
                                gtin=8594173675315, container={"slug": "old-prusament-spool-1kg"}),
                SimpleNamespace(slug=MATERIAL + "-1000-spool", material={"slug": MATERIAL},
                                nominal_netto_full_weight=1000, filament_diameter=1750,
                                gtin=8594173675315, container={"slug": "prusament-spool-1kg"},
                                url="https://example.com/petg-clear-1kg-nfc/"),
            ],
            "single": [SimpleNamespace(slug="single-500-spool", material={"slug": "single"},
                                       nominal_netto_full_weight=500, filament_diameter=2850)],
            "unpackaged": [],
        }
        self.window.read_filaments_from_database = Mock(
            side_effect=lambda vendor: materials if vendor == "prusament" else {})
        self.window.read_packages_from_database = Mock(
            side_effect=lambda vendor, material: self.packages[material])
        self.window.setup_default_material = Mock()
        self.window.setup_material()
        self.window.setup_date_view()
        self.window.brandnamebox.currentTextChanged.connect(self.window.on_manufacturer_changed)
        self.window.brandnamebox.addItems(self.window.vendors)
        self.window.brandnamebox.setCurrentText("Prusament")
        self.window.materialnamebox.setCurrentText("PETG Clear")
        self.window.materialtypebox.setCurrentText("PETG")

    def test_material_names_are_separate_from_read_only_variants(self):
        window = self.window
        self.assertEqual(window.materialnamebox.count(), 3)
        self.assertEqual(window.materialnamebox.currentText(), "PETG Clear")
        self.assertTrue(window.materialnamebox.isEditable())
        self.assertFalse(window.materialvariantbox.isEditable())
        self.assertFalse(window.materialvariantbox.isHidden())
        self.assertEqual(
            [window.materialvariantbox.itemText(i) for i in range(window.materialvariantbox.count())],
            [CURRENT, "1.00Kg,1.75mm,Old Refill", "1.00Kg,1.75mm,Old Spool"],
        )
        layout = window.horizontalLayout_4
        self.assertGreater(layout.indexOf(window.materialvariantbox), layout.indexOf(window.materialnamebox))

    def test_variant_selection_updates_package_fields(self):
        window = self.window
        window.materialvariantbox.setCurrentIndex(window.materialvariantbox.findText("1.00Kg,1.75mm,Old Refill"))
        self.assertEqual(window.gtinedit.text(), "8594173676169")
        self.assertFalse(window.includeurlcheckbox.isChecked())
        window.materialvariantbox.setCurrentIndex(window.materialvariantbox.findText(CURRENT))
        self.assertEqual(window.materialnamebox.currentText(), "PETG Clear")
        self.assertEqual(window.diameteredit.text(), "1.75")
        self.assertEqual(window.nominalweightbox.value(), 1000)
        self.assertEqual(window.gtinedit.text(), "8594173675315")
        self.assertTrue(window.includeurlcheckbox.isChecked())

    def test_hides_selector_for_one_or_no_packages(self):
        window = self.window
        window.materialnamebox.setCurrentText("Single")
        self.assertTrue(window.materialvariantbox.isHidden())
        self.assertEqual(window.materialvariantbox.count(), 1)
        self.assertEqual(window.nominalweightbox.value(), 500)
        self.assertEqual(window.diameteredit.text(), "2.85")
        window.materialnamebox.setCurrentText("Unpackaged")
        self.assertTrue(window.materialvariantbox.isHidden())
        self.assertEqual(window.materialvariantbox.count(), 0)

        self.assertEqual(window.nominalweightbox.value(), 1000)
        self.assertEqual(window.diameteredit.text(), "1.75")

    def test_switching_brands_repopulates_cached_materials(self):
        window = self.window
        window.brandnamebox.setCurrentText("Empty brand")
        self.assertEqual(window.materialnamebox.count(), 0)
        self.assertTrue(window.materialvariantbox.isHidden())
        window.brandnamebox.setCurrentText("Prusament")
        window.materialnamebox.setCurrentText("PETG Clear")
        self.assertEqual(window.materialnamebox.count(), 3)
        self.assertEqual(window.materialvariantbox.count(), 3)

    def test_missing_diameter_and_custom_material_names(self):
        del self.packages["single"][0].filament_diameter
        window = self.window
        window.materialnamebox.setCurrentText("Single")
        self.assertEqual(window.materialvariantbox.currentText(), "0.50Kg,Spool")
        self.assertEqual(window.diameteredit.text(), "")
        window.materialnamebox.setCurrentText("My PETG [custom]")
        self.assertEqual(window.materialnamebox.currentText(), "My PETG [custom]")
        self.assertTrue(window.materialvariantbox.isHidden())
        self.assertEqual(window.materialvariantbox.count(), 0)
        fields, _ = window.parse_tag_data(window.generate_tag_data())
        self.assertEqual(fields["main"]["material_name"], "My PETG [custom]")

    def test_tag_round_trip_preserves_name_variant_and_actual_weight(self):
        window = self.window
        window.materialvariantbox.setCurrentIndex(window.materialvariantbox.findText(CURRENT))
        window.actualweightbox.setValue(700)
        tag = window.generate_tag_data()
        fields, _ = window.parse_tag_data(tag)
        self.assertEqual(fields["main"]["material_name"], "PETG Clear")
        window.materialnamebox.setCurrentText("Single")
        window.load_tag_data(tag)
        self.assertEqual(window.materialnamebox.currentText(), "PETG Clear")
        self.assertEqual(window.materialvariantbox.currentText(), CURRENT)
        self.assertEqual(window.actualweightbox.value(), 700)
        window.includeurlcheckbox.setChecked(False)
        tag_without_url = window.generate_tag_data()
        window.load_tag_data(tag_without_url)
        self.assertEqual(window.materialvariantbox.currentIndex(), -1)
        self.assertEqual(window.actualweightbox.value(), 700)


if __name__ == "__main__":
    unittest.main()
