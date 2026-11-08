import threading
import unittest
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication

from openprinttaggui import openprinttag_gui
from openprinttaggui.Library import nfc_handler


class NFCWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["tests", "-platform", "offscreen"])

    def setUp(self):
        with patch.object(openprinttag_gui.QThread, "start"), \
                patch.object(openprinttag_gui.GUI_OpenPrintTag, "cache_filenames"):
            self.window = openprinttag_gui.GUI_OpenPrintTag()
        self.window.reader = 3
        self.window.readers = {3: 1}
        self.window.auto_read_enabled = True
        self.window.auto_read_timer.start(1000)
        self.window.readtagbtn.setEnabled(True)
        self.window.writetagbtn.setEnabled(True)
        self.window.generate_tag_data = Mock(return_value=b"tag data")

    def tearDown(self):
        self.window.auto_read_timer.stop()
        self.window.threadpool.waitForDone(3000)
        self.window.close()
        self.window.deleteLater()

    def test_polling_resumes_after_every_write_outcome(self):
        outcomes = ("success", "rejected", "reset", "no_tag", "connection", "generation")
        for outcome in outcomes:
            with self.subTest(outcome=outcome), \
                    patch.object(self.window.threadpool, "start") as start, \
                    patch.object(nfc_handler, "ACS_HF15") as reader:
                self.window.generate_tag_data.side_effect = None
                device = reader.return_value
                device.getUID.return_value = b"uid"
                device.restore.return_value = outcome != "rejected"
                if outcome == "reset":
                    device.restore.side_effect = RuntimeError("Card was reset")
                elif outcome == "no_tag":
                    device.getUID.return_value = b""
                elif outcome == "connection":
                    reader.side_effect = RuntimeError("Reader disconnected")
                elif outcome == "generation":
                    self.window.generate_tag_data.side_effect = ValueError("Invalid material")

                self.window.on_write_tag()
                self.assertTrue(self.window.is_writing_tag)
                self.assertFalse(self.window.auto_read_timer.isActive())
                self.assertFalse(self.window.readtagbtn.isEnabled())
                self.assertFalse(self.window.writetagbtn.isEnabled())
                worker = start.call_args.args[0]
                worker.run()

                self.assertFalse(self.window.is_writing_tag)
                self.assertTrue(self.window.auto_read_timer.isActive())
                self.assertTrue(self.window.readtagbtn.isEnabled())
                self.assertTrue(self.window.writetagbtn.isEnabled())
                message = self.window.statusbar.currentMessage()
                if outcome == "success":
                    self.assertEqual(message, "Tag written successfully.")
                elif outcome == "reset":
                    self.assertIn("writing NFC tag: Card was reset", message)
                    self.assertNotIn("reading", message)
                elif outcome == "generation":
                    self.assertIn("Invalid material", message)
                else:
                    self.assertNotEqual(message, "Tag written successfully.")

    def test_in_flight_poll_finishes_before_writing_and_late_results_are_ignored(self):
        poll_started = threading.Event()
        release_poll = threading.Event()
        write_started = threading.Event()
        release_write = threading.Event()

        def poll():
            poll_started.set()
            if not release_poll.wait(2):
                raise TimeoutError("Test poll did not finish")
            return b"uid"

        def write(**kwargs):
            write_started.set()
            if not release_write.wait(2):
                raise TimeoutError("Test write did not finish")
            return True

        polling_reader = Mock()
        polling_reader.getUID.side_effect = poll
        writing_reader = Mock()
        writing_reader.getUID.return_value = b"uid"
        writing_reader.restore.side_effect = write
        self.assertEqual(self.window.threadpool.maxThreadCount(), 1)

        with patch.object(nfc_handler, "ACS_HF15", side_effect=[polling_reader, writing_reader]) as reader, \
                patch.object(self.window, "on_read_tag") as read_tag:
            try:
                self.window.try_auto_read_tag()
                self.assertTrue(poll_started.wait(1))
                self.window.on_write_tag()
                self.assertFalse(write_started.is_set())
                release_poll.set()
                self.assertTrue(write_started.wait(1))
                self.app.processEvents()

                read_tag.assert_not_called()
                self.assertTrue(self.window.is_writing_tag)
                self.assertFalse(self.window.auto_read_timer.isActive())
                self.window.try_auto_read_tag()
                self.window.on_write_tag()
                self.window.handle_tag_error("late read error")
                self.window.handle_tag_read_success(Mock())
                self.assertTrue(self.window.is_writing_tag)
                self.assertFalse(self.window.auto_read_timer.isActive())
                self.assertEqual(reader.call_count, 2)

                release_write.set()
                self.assertTrue(self.window.threadpool.waitForDone(1000))
                self.app.processEvents()
                self.assertFalse(self.window.is_writing_tag)
                self.assertTrue(self.window.auto_read_timer.isActive())
            finally:
                release_poll.set()
                release_write.set()
                self.window.threadpool.waitForDone(3000)

    def test_reader_removal_and_reconnection_do_not_restart_polling_during_write(self):
        with patch.object(self.window.threadpool, "start"):
            self.window.on_write_tag()
        self.window.on_device_removed({"reader": 3})
        self.assertFalse(self.window.auto_read_enabled)
        self.window.on_device_detected({"reader": 3, "port": "reader"})
        self.assertFalse(self.window.auto_read_timer.isActive())
        self.assertFalse(self.window.writetagbtn.isEnabled())
        self.window.handle_tag_write_finished("Reader disconnected")
        self.assertTrue(self.window.auto_read_timer.isActive())
        self.assertTrue(self.window.writetagbtn.isEnabled())

    def test_completion_does_not_enable_detection_when_disabled_or_disconnected(self):
        for connected in (True, False):
            with self.subTest(connected=connected):
                self.window.auto_read_enabled = False
                self.window.auto_read_timer.stop()
                self.window.reader = 3 if connected else 0
                self.window.is_writing_tag = True
                self.window.handle_tag_write_finished(None)
                self.assertFalse(self.window.auto_read_timer.isActive())
                self.assertEqual(self.window.readtagbtn.isEnabled(), connected)
                self.assertEqual(self.window.writetagbtn.isEnabled(), connected)


if __name__ == "__main__":
    unittest.main()
