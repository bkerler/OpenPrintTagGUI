import unittest
from unittest.mock import patch

from openprinttaggui.Library import device_detector


class DeviceDetectorTests(unittest.TestCase):
    def poll(self, worker):
        with patch.object(device_detector.hid, "enumerate", return_value=[]), \
                patch.object(device_detector.serial.tools.list_ports, "comports", return_value=[]), \
                patch.object(device_detector.QThread, "msleep", side_effect=lambda _: worker.stop()):
            worker.is_running = True
            worker.start_detection()

    def test_pcsc_detection_without_serial_or_hid_and_removal(self):
        worker = device_detector.DeviceDetectorWorker(device_detector.device_list)
        added, removed = [], []
        worker.device_detected.connect(added.append)
        worker.device_removed.connect(removed.append)
        name = "ACS ACR1552 1S CL Reader PICC 00 00"
        with patch.object(device_detector, "pcsc_readers", return_value=[
                name, "ACS ACR1552 SAM 00 01", "Yubico YubiKey 00 00"]):
            self.poll(worker)
        self.assertEqual(added, [{"name": name, "reader": 3, "port": name, "type": "pcsc"}])
        with patch.object(device_detector, "pcsc_readers", return_value=[]):
            self.poll(worker)
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["name"], name)

    def test_unavailable_pcsc_does_not_stop_detection(self):
        worker = device_detector.DeviceDetectorWorker(device_detector.device_list)
        with patch.object(device_detector, "pcsc_readers", side_effect=RuntimeError("unavailable")):
            self.poll(worker)
        self.assertEqual(worker.previous_state, set())
