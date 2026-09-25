import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cbor2
import yaml

from openprinttaggui import openprinttag_gui
from openprinttaggui.Library.OpenPrintTag.utils.common import default_config_file
from openprinttaggui.Library.OpenPrintTag.utils.nfc_initialize import Args, nfc_initialize
from openprinttaggui.Library.OpenPrintTag.utils.record import Record


class OpenPrintTagCompatibilityTests(unittest.TestCase):
    def test_reads_legacy_diameter_and_prefers_new_field(self):
        empty_tag = nfc_initialize(Args(size=304, aux_region=32, config_file=default_config_file))
        for fields, expected in (({30: 1.75}, 1750), ({61: 2850, 30: 1.75}, 2850)):
            record = Record(default_config_file, memoryview(bytearray(empty_tag)))
            encoded = cbor2.dumps(fields)
            record.main_region.memory[:] = bytearray(len(record.main_region.memory))
            record.main_region.memory[:len(encoded)] = encoded

            app = SimpleNamespace(msg=self.fail)
            parsed, _ = openprinttag_gui.GUI_OpenPrintTag.parse_tag_data(app, record.data.tobytes())
            self.assertEqual(parsed["main"]["filament_diameter_v2"], expected)

    def test_indexes_packages_by_material_slug_without_optional_diameter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "Library" / "openprinttag-database" / "data"
            (data_dir / "brands").mkdir(parents=True)
            (data_dir / "materials" / "brand").mkdir(parents=True)
            package_dir = data_dir / "material-packages" / "brand"
            package_dir.mkdir(parents=True)
            (data_dir / "brands" / "brand.yaml").write_text(yaml.safe_dump({"slug": "brand", "name": "Brand"}))
            (data_dir / "materials" / "brand" / "material.yaml").write_text(
                yaml.safe_dump({"slug": "material", "name": "Material"})
            )
            package_path = package_dir / "renamed-package-file.yaml"
            package_path.write_text(yaml.safe_dump({
                "slug": "package",
                "material": {"slug": "material"},
                "url": "https://example.com/package",
            }))

            app = SimpleNamespace(filecache={}, msg=self.fail)
            with patch.object(openprinttag_gui, "script_path", temp_dir):
                openprinttag_gui.GUI_OpenPrintTag.cache_filenames(app)
                packages = openprinttag_gui.GUI_OpenPrintTag.read_packages_from_database(app, "brand", "material")

            self.assertEqual(len(packages), 1)
            self.assertEqual(packages[0].url, "https://example.com/package")
            self.assertFalse(hasattr(packages[0], "filament_diameter"))


if __name__ == "__main__":
    unittest.main()
