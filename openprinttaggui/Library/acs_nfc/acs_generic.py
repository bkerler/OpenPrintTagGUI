from enum import Enum

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import CardRequestTimeoutException
from smartcard.util import toHexString
from smartcard.ATR import ATR
import os, sys
import platform

script_path = os.path.dirname(os.path.realpath(__file__))

class ReadMode(Enum):
    class dc():
        def __init__(self, mode: int, maxaddr: int, blksize: int):
            self.mode = mode
            self.maxaddr = maxaddr
            self.blksize = blksize
    MIFARE_skip_trailer = dc(mode=0,maxaddr=256,blksize=16)
    MIFARE_with_trailer = dc(mode=8,maxaddr=256,blksize=16)
    MIFARE_Ultralight = dc(mode=0,maxaddr=48,blksize=4)
    MIFARE_UltralightC = dc(mode=0,maxaddr=48,blksize=4)
    SRIX4K = dc(mode=0,maxaddr=0xFFFF,blksize=4)
    SRT512 = dc(mode=0,maxaddr=0xFFFF,blksize=4)
    PICOPASS = dc(mode=0,maxaddr=0xFFFF,blksize=8)
    ISO15693 = dc(mode=0,maxaddr=2048,blksize=4)
    TOPAZ = dc(mode=0, maxaddr=2048, blksize=8)
    CTS = dc(mode=0,maxaddr=32,blksize=4)


class Baudrate(Enum):
    ISO14443_106kbps = 0x98
    ISO14443_212kbps = 0x99
    ISO14443_424kbps = 0x9A
    ISO14443_848kbps = 0x9B
    ISO15693_26kbps = 0x80
    ISO15693_53kbps = 0x08


class Protocol(Enum):
    ISO14443A = 0x00
    ISO14443B = 0x01
    ISO15693 = 0x02
    FeliCa = 0x03
    CurrentRF = 0xFF


class Layer(Enum):
    Layer_Part2 = 0x2
    Layer_Part3 = 0x3
    Layer_Part4 = 0x4

class ACS:
    def __init__(self, port: str = None, logger=print):
        self.sw1 = 0x90
        self.sw2 = 0x00
        self.logger = logger
        cardtype = AnyCardType()
        cardrequest = CardRequest(timeout=1, cardType=cardtype)
        try:
            self.pcsccardrequest = cardrequest.waitforcard()
        except CardRequestTimeoutException:
            logger("Timeout waiting for nfc tag")
            return
        self.cardservice = cardrequest.waitforcard()
        self.cardservice.connection.connect()
        atr = self.cardservice.connection.getATR()
        logger("ATR detected: "+toHexString(atr))
        hb = toHexString(ATR(atr).getHistoricalBytes())
        cardname = hb[-17:-12]
        cardnameMap = {
            "00 01": "MIFARE Classic 1K",
            "00 02": "MIFARE Classic 4K",
            "00 03": "MIFARE Ultralight",
            "00 14": "IC SL2 ICS2602 ( SLIX2 )",
            "00 21": "NTAG203",
            "00 22": "NTAG213",
            "00 23": "NTAG215",
            "00 24": "NTAG216",
            "00 25": "iCode Slix",
            "00 26": "MIFARE Mini",
            "F0 04": "Topaz and Jewel",
            "F0 11": "FeliCa 212K",
            "F0 12": "FeliCa 424K",
            "F0 27": "MIFARE DesFire EV2",
            "F0 20": "iCode Slix2",
            "F0 30": "ISO14443A4",
            "F0 40": "ISO14443A7",
            "F0 50": "ISO14443A10",
            "F0 60": "ISO14443B4",
            "F0 70": "ISO14443B7",

        }
        name = cardnameMap.get(cardname, "unknown")
        logger("Card Name: " + name)
        logger("T0 supported: ", ATR(atr).isT0Supported())
        logger("T1 supported: ", ATR(atr).isT1Supported())
        logger("T15 suppoerted: ", ATR(atr).isT15Supported())



    def hex(self, byte_array):
        return toHexString(list(byte_array))

    def send_apdu(self, apdu):
        response, sw1, sw2 = self.cardservice.connection.transmit(apdu)
        self.sw1=sw1
        self.sw2=sw2
        if sw1 != 0x90 or sw2 != 0x00:
            raise ValueError(f"Bad response! sw1={sw1:02X}, sw2={sw2:02X}, data={self.hex(apdu)}")
        return response

    def transparent_exchange(self, data):
        length = len(data)
        apdu = [0xFF, 0xC2, 0x00, 0x01, length + 2, 0x95, length] + data
        resp = self.send_apdu(apdu)
        return bytes(resp[14:])

    def manage_session(self, cmd):
        ack=self.send_apdu([0xFF, 0xC2, 0x00, 0x00, len(cmd)] + cmd + [0x00])
        res = ack[3]<<8 | ack[4]
        return res

    def switch_protocol(self, cmd):
        ack=self.send_apdu([0xFF, 0xC2, 0x00, 0x02, len(cmd)] + cmd + [0x00])
        res = ack[3]<<8 | ack[4]
        return res

    def set_baudrate(self, baud:Baudrate):
        self.switch_protocol([baud.value])

    def select_protocol(self, protocol:Protocol, layer:Layer):
        res=self.switch_protocol([0x8F, 0x02, protocol.value, layer.value])
        if res!=0x9000:
            raise ValueError(f"Bad response! sw1={(res&0xFF00)>>8:02X}, sw2={res&0xFF:02X}, protocol={protocol.name}, layer={layer.name}")

    def start_transparent(self):
        # Start transparent session
        res=self.manage_session([0x81, 0x00])
        if res!=0x9000:
            raise ValueError(f"Bad response! sw1={(res&0xFF00)>>8:02X}, sw2={res&0xFF:02X} on start_transparent")

    def select_iso14443a(self):
        # Switch protocol to ISO14443-4a
        return self.select_protocol(protocol=Protocol.ISO14443A,layer=Layer.Layer_Part3)==0x9000

    def select_iso14443b(self):
        # Switch protocol to ISO14443-4a
        return self.select_protocol(protocol=Protocol.ISO14443B,layer=Layer.Layer_Part3)==0x9000

    def select_iso15693(self):
        # Switch protocol to ISO15693-3
        return self.select_protocol(protocol=Protocol.ISO15693,layer=Layer.Layer_Part3)==0x9000

    def end_transparent(self):
        return self.manage_session([0x82, 0x00])==0x9000

    def detect_os(self):
        os_name = platform.system()  # Returns 'Windows', 'Linux', 'Darwin' (for macOS), or others
        if os_name == 'Darwin':
            os_name = 'macOS'  # Optional: human-readable rename
        # Architecture (e.g., 'x86_64', 'AMD64', 'arm64', 'aarch64', etc.)
        arch = platform.machine()  # Most reliable for specific architecture
        # Bitness (32-bit or 64-bit) and support
        bits, linkage = platform.architecture()
        return os_name, bits, arch, linkage


if __name__ == "__main__":
    pcsc = ACS(port=None)
    """
    cardtype = ATRCardType(bytes.fromhex("3B 8F 80 01 80 4F 0C A0 00 00 03 06 03 00 3A 00 00 00 00 51"))
    cardrequest = CardRequest(timeout=10, cardType=cardtype)
    cardservice = cardrequest.waitforcard()
    cardservice.connection.connect()
    """
