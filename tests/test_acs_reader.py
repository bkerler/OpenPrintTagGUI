import unittest
from unittest.mock import Mock, patch

from openprinttaggui.Library.acs_nfc.acs_hf15 import ACS_HF15
import acs_generic


PICC_READER = "ACS ACR1552 1S CL Reader [ACR1552 1S CL Reader PICC] 01 00"
SAM_READER = "ACS ACR1552 1S CL Reader [ACR1552 1S CL Reader SAM] 02 00"
YUBIKEY_READER = "Yubico YubiKey OTP+FIDO+CCID 00 00"
CONTACT_READER = "ACS ACR39U 00 00"


class ACSReaderTests(unittest.TestCase):
    def setUp(self):
        reader_patch = patch.object(acs_generic, "readers", return_value=[PICC_READER])
        self.readers = reader_patch.start()
        self.addCleanup(reader_patch.stop)
        request_patch = patch.object(acs_generic, "CardRequest")
        self.request = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.connection = self.request.return_value.waitforcard.return_value.connection
        self.connection.getATR.return_value = [0x3B, 0x00]

    def test_selects_contactless_reader_instead_of_yubikey_or_sam(self):
        self.readers.return_value = [YUBIKEY_READER, CONTACT_READER, SAM_READER, PICC_READER]

        acs_generic.ACS(logger=Mock())

        self.assertEqual(self.request.call_args.kwargs["readers"], [PICC_READER])
        self.connection.connect.assert_called_once()
        self.connection.transmit.assert_not_called()

    def test_preserves_vmware_reader_support(self):
        reader = "VMware Virtual USB CCID 00 00"
        self.readers.return_value = [YUBIKEY_READER, reader]

        acs_generic.ACS(logger=Mock())

        self.assertEqual(self.request.call_args.kwargs["readers"], [reader])

    def test_does_not_fall_back_to_an_unrelated_reader(self):
        for readers in ([], [YUBIKEY_READER], [CONTACT_READER], [SAM_READER]):
            with self.subTest(readers=readers):
                self.readers.return_value = readers
                with self.assertRaisesRegex(RuntimeError, "No ACS contactless"):
                    acs_generic.ACS(logger=Mock())
        self.request.assert_not_called()

    def test_no_tag_returns_empty_uid_without_connecting(self):
        self.request.return_value.waitforcard.side_effect = acs_generic.CardRequestTimeoutException()

        device = ACS_HF15(port=None)

        self.assertIsNone(device.cardservice)
        self.assertEqual(device.getUID(), b"")
        self.connection.connect.assert_not_called()
        self.connection.transmit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
