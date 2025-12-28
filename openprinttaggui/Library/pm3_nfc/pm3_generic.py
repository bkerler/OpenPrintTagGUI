#!/usr/bin/env python3
# (c) B.Kerler 2025
import time
from typing import Literal
from serial import Serial
from enum import Enum


class PM3CMD(Enum):
    # For the bootloader
    DEVICE_INFO = 0x0000
    SETUP_WRITE = 0x0001
    FINISH_WRITE = 0x0003
    HARDWARE_RESET = 0x0004
    START_FLASH = 0x0005
    CHIP_INFO = 0x0006
    BL_VERSION = 0x0007
    NACK = 0x00fe
    ACK = 0x00ff

    # For general mucking around
    DEBUG_PRINT_STRING = 0x0100
    DEBUG_PRINT_INTEGERS = 0x0101
    DEBUG_PRINT_BYTES = 0x0102
    LCD_RESET = 0x0103
    LCD = 0x0104
    BUFF_CLEAR = 0x0105
    READ_MEM = 0x0106  # legacy
    READ_MEM_DOWNLOAD = 0x010A
    READ_MEM_DOWNLOADED = 0x010B
    VERSION = 0x0107
    STATUS = 0x0108
    PING = 0x0109
    DOWNLOAD_EML_BIGBUF = 0x0110
    DOWNLOADED_EML_BIGBUF = 0x0111
    CAPABILITIES = 0x0112
    QUIT_SESSION = 0x0113
    SET_DBGMODE = 0x0114
    STANDALONE = 0x0115
    WTX = 0x0116
    TIA = 0x0117
    BREAK_LOOP = 0x0118
    SET_TEAROFF = 0x0119
    GET_DBGMODE = 0x0120

    # RDV40, Flash memory operations
    FLASHMEM_WRITE = 0x0121
    FLASHMEM_WIPE = 0x0122
    FLASHMEM_DOWNLOAD = 0x0123
    FLASHMEM_DOWNLOADED = 0x0124
    FLASHMEM_INFO = 0x0125
    FLASHMEM_SET_SPIBAUDRATE = 0x0126
    FLASHMEM_PAGES64K = 0x0127

    # RDV40, High level flashmem SPIFFS Manipulation
    # ALL function will have a lazy or Safe version
    # that will be handled as argument of safety level [0..2] respectiveley normal / lazy / safe
    # However as how design is, MOUNT and UNMOUNT only need/have lazy as
    # safest level so a safe level will still execute a lazy version
    # see spiffs.c for more about the normal/lazy/safety information)
    SPIFFS_MOUNT = 0x0130
    SPIFFS_UNMOUNT = 0x0131
    SPIFFS_WRITE = 0x0132

    FLASHMEM_GET_SIGNATURE = 0x0147
    FLASHMEM_GET_INFO = 0x0148

    # We take +0x1000 when having a variant of similar function (todo : make it an argument!)
    SPIFFS_APPEND = 0x1132

    SPIFFS_READ = 0x0133
    # We use no open/close instruction, as they are handled internally.
    SPIFFS_REMOVE = 0x0134
    SPIFFS_RM = SPIFFS_REMOVE
    SPIFFS_RENAME = 0x0135
    SPIFFS_MV = SPIFFS_RENAME
    SPIFFS_COPY = 0x0136
    SPIFFS_CP = SPIFFS_COPY
    SPIFFS_STAT = 0x0137
    SPIFFS_FSTAT = 0x0138
    SPIFFS_INFO = 0x0139
    SPIFFS_FORMAT = FLASHMEM_WIPE

    SPIFFS_WIPE = 0x013A

    SET_FPGAMODE = 0x013F

    # This take a +0x2000 as they are high level helper and special functions
    # As the others, they may have safety level argument if it makes sense
    SPIFFS_PRINT_TREE = 0x2130
    SPIFFS_GET_TREE = 0x2131
    SPIFFS_TEST = 0x2132
    SPIFFS_PRINT_FSINFO = 0x2133
    SPIFFS_DOWNLOAD = 0x2134
    SPIFFS_DOWNLOADED = 0x2135
    SPIFFS_ELOAD = 0x2136
    SPIFFS_CHECK = 0x3000

    # RDV40,  Smart card operations
    SMART_RAW = 0x0140
    SMART_UPGRADE = 0x0141
    SMART_UPLOAD = 0x0142
    SMART_ATR = 0x0143
    SMART_SETBAUD = 0x0144
    SMART_SETCLOCK = 0x0145

    # RDV40,  FPC USART
    USART_RX = 0x0160
    USART_TX = 0x0161
    USART_TXRX = 0x0162
    USART_CONFIG = 0x0163

    # For low-frequency tags
    LF_TI_READ = 0x0202
    LF_TI_WRITE = 0x0203
    LF_ACQ_RAW_ADC = 0x0205
    LF_MOD_THEN_ACQ_RAW_ADC = 0x0206
    DOWNLOAD_BIGBUF = 0x0207
    DOWNLOADED_BIGBUF = 0x0208
    LF_UPLOAD_SIM_SAMPLES = 0x0209
    LF_SIMULATE = 0x020A
    LF_HID_WATCH = 0x020B
    LF_HID_SIMULATE = 0x020C
    LF_SET_DIVISOR = 0x020D
    LF_SIMULATE_BIDIR = 0x020E
    SET_ADC_MUX = 0x020F
    LF_HID_CLONE = 0x0210
    LF_EM410X_CLONE = 0x0211
    LF_T55XX_READBL = 0x0214
    LF_T55XX_WRITEBL = 0x0215
    LF_T55XX_RESET_READ = 0x0216
    LF_PCF7931_READ = 0x0217
    LF_PCF7931_WRITE = 0x0223
    LF_EM4X_LOGIN = 0x0229
    LF_EM4X_READWORD = 0x0218
    LF_EM4X_WRITEWORD = 0x0219
    LF_EM4X_PROTECTWORD = 0x021B
    LF_EM4X_BF = 0x022A
    LF_IO_WATCH = 0x021A
    LF_EM410X_WATCH = 0x021C
    LF_EM4X50_INFO = 0x0240
    LF_EM4X50_WRITE = 0x0241
    LF_EM4X50_WRITEPWD = 0x0242
    LF_EM4X50_READ = 0x0243
    LF_EM4X50_BRUTE = 0x0245
    LF_EM4X50_LOGIN = 0x0246
    LF_EM4X50_SIM = 0x0250
    LF_EM4X50_READER = 0x0251
    LF_EM4X50_ESET = 0x0252
    LF_EM4X50_CHK = 0x0253
    LF_EM4X70_INFO = 0x0260
    LF_EM4X70_WRITE = 0x0261
    LF_EM4X70_UNLOCK = 0x0262
    LF_EM4X70_AUTH = 0x0263
    LF_EM4X70_SETPIN = 0x0264
    LF_EM4X70_SETKEY = 0x0265
    LF_EM4X70_BRUTE = 0x0266
    # Sampling configuration for LF reader/sniffer
    LF_SAMPLING_SET_CONFIG = 0x021D
    LF_FSK_SIMULATE = 0x021E
    LF_ASK_SIMULATE = 0x021F
    LF_PSK_SIMULATE = 0x0220
    LF_NRZ_SIMULATE = 0x0232
    LF_AWID_WATCH = 0x0221
    LF_VIKING_CLONE = 0x0222
    LF_T55XX_WAKEUP = 0x0224
    LF_COTAG_READ = 0x0225
    LF_T55XX_SET_CONFIG = 0x0226
    LF_SAMPLING_PRINT_CONFIG = 0x0227
    LF_SAMPLING_GET_CONFIG = 0x0228

    LF_T55XX_CHK_PWDS = 0x0230
    LF_T55XX_DANGERRAW = 0x0231

    # ZX8211
    LF_ZX_READ = 0x0270
    LF_ZX_WRITE = 0x0271

    """ *CMD_SET_ADC_MUX: ext1 is 0
    for lopkd, 1 for loraw, 2 for hipkd, 3 for hiraw
    """

    # For the 13.56 MHz tags
    HF_ISO15693_ACQ_RAW_ADC = 0x0300
    HF_ACQ_RAW_ADC = 0x0301
    HF_SRI_READ = 0x0303
    HF_ISO14443B_COMMAND = 0x0305
    HF_ISO15693_READER = 0x0310
    HF_ISO15693_SIMULATE = 0x0311
    HF_ISO15693_SNIFF = 0x0312
    HF_ISO15693_COMMAND = 0x0313
    HF_ISO15693_FINDAFI = 0x0315
    HF_ISO15693_SLIX_ENABLE_PRIVACY = 0x0867
    HF_ISO15693_SLIX_DISABLE_PRIVACY = 0x0317
    HF_ISO15693_SLIX_DISABLE_EAS = 0x0318
    HF_ISO15693_SLIX_ENABLE_EAS = 0x0862
    HF_ISO15693_SLIX_PASS_PROTECT_AFI = 0x0863
    HF_ISO15693_SLIX_PASS_PROTECT_EAS = 0x0864
    HF_ISO15693_SLIX_WRITE_PWD = 0x0865
    HF_ISO15693_SLIX_PROTECT_PAGE = 0x0868
    HF_ISO15693_WRITE_AFI = 0x0866
    HF_TEXKOM_SIMULATE = 0x0320
    HF_ISO15693_EML_CLEAR = 0x0330
    HF_ISO15693_EML_SETMEM = 0x0331
    HF_ISO15693_EML_GETMEM = 0x0332

    HF_ISO15693_CSETUID = 0x0316
    HF_ISO15693_CSETUID_V2 = 0x0333

    LF_SNIFF_RAW_ADC = 0x0360

    # For Hitag 2 transponders
    LF_HITAG_SNIFF = 0x0370
    LF_HITAG_SIMULATE = 0x0371
    LF_HITAG_READER = 0x0372
    LF_HITAG2_WRITE = 0x0377
    LF_HITAG2_CRACK = 0x0378
    LF_HITAG2_CRACK_2 = 0x0379

    # For Hitag S
    LF_HITAGS_TEST_TRACES = 0x0367
    LF_HITAGS_SIMULATE = 0x0368
    LF_HITAGS_READ = 0x0373
    LF_HITAGS_WRITE = 0x0375
    LF_HITAGS_UID = 0x037A

    # For Hitag µ
    LF_HITAGU_READ = 0x037B
    LF_HITAGU_WRITE = 0x037C
    LF_HITAGU_SIMULATE = 0x037D
    LF_HITAGU_UID = 0x037E

    LF_HITAG_ELOAD = 0x0376

    HF_ISO14443A_ANTIFUZZ = 0x0380
    HF_ISO14443B_SIMULATE = 0x0381
    HF_ISO14443B_SNIFF = 0x0382

    HF_ISO14443A_SNIFF = 0x0383
    HF_ISO14443A_SIMULATE = 0x0384
    HF_ISO14443A_SIM_AID = 0x1420

    HF_ISO14443A_READER = 0x0385
    HF_ISO14443A_EMV_SIMULATE = 0x0386

    HF_LEGIC_SIMULATE = 0x0387
    HF_LEGIC_READER = 0x0388
    HF_LEGIC_WRITER = 0x0389

    HF_EPA_COLLECT_NONCE = 0x038A
    HF_EPA_REPLAY = 0x038B
    HF_EPA_PACE_SIMULATE = 0x038C

    HF_LEGIC_INFO = 0x03BC
    HF_LEGIC_ESET = 0x03BD

    # iCLASS / Picopass
    HF_ICLASS_READCHECK = 0x038F
    HF_ICLASS_DUMP = 0x0391
    HF_ICLASS_SNIFF = 0x0392
    HF_ICLASS_SIMULATE = 0x0393
    HF_ICLASS_READER = 0x0394
    HF_ICLASS_READBL = 0x0396
    HF_ICLASS_WRITEBL = 0x0397
    HF_ICLASS_EML_MEMSET = 0x0398
    HF_ICLASS_CHKKEYS = 0x039A
    HF_ICLASS_RESTORE = 0x039B
    HF_ICLASS_CREDIT_EPURSE = 0x039C
    HF_ICLASS_RECOVER = 0x039D
    HF_ICLASS_TEARBL = 0x039E

    # For ISO1092 / FeliCa
    HF_FELICA_SIMULATE = 0x03A0
    HF_FELICA_SNIFF = 0x03A1
    HF_FELICA_COMMAND = 0x03A2
    # temp
    HF_FELICALITE_DUMP = 0x03AA
    HF_FELICALITE_SIMULATE = 0x03AB

    # For 14a config
    HF_ISO14443A_PRINT_CONFIG = 0x03B0
    HF_ISO14443A_GET_CONFIG = 0x03B1
    HF_ISO14443A_SET_CONFIG = 0x03B2

    HF_ISO14443A_SET_THRESHOLDS = 0x03B8

    # For 14b config
    HF_ISO14443B_PRINT_CONFIG = 0x03D0
    HF_ISO14443B_GET_CONFIG = 0x03D1
    HF_ISO14443B_SET_CONFIG = 0x03D2

    # For measurements of the antenna tuning
    MEASURE_ANTENNA_TUNING = 0x0400
    MEASURE_ANTENNA_TUNING_HF = 0x0401
    MEASURE_ANTENNA_TUNING_LF = 0x0402
    LISTEN_READER_FIELD = 0x0420
    HF_DROPFIELD = 0x0430

    # For direct FPGA control
    FPGA_MAJOR_MODE_OFF = 0x0500

    # For mifare commands
    HF_MIFARE_EML_MEMCLR = 0x0601
    HF_MIFARE_EML_MEMSET = 0x0602
    HF_MIFARE_EML_MEMGET = 0x0603
    HF_MIFARE_EML_LOAD = 0x0604

    # magic chinese card commands
    HF_MIFARE_CSETBL = 0x0605
    HF_MIFARE_CGETBL = 0x0606
    HF_MIFARE_CIDENT = 0x0607

    HF_MIFARE_SIMULATE = 0x0610

    HF_MIFARE_READER = 0x0611
    HF_MIFARE_NESTED = 0x0612
    HF_MIFARE_ACQ_ENCRYPTED_NONCES = 0x0613
    HF_MIFARE_ACQ_NONCES = 0x0614
    HF_MIFARE_STATIC_NESTED = 0x0615
    HF_MIFARE_STATIC_ENC = 0x0616
    HF_MIFARE_ACQ_STATIC_ENCRYPTED_NONCES = 0x0617

    HF_MIFARE_READBL = 0x0620
    HF_MIFARE_READBL_EX = 0x0628
    HF_MIFAREU_READBL = 0x0720
    HF_MIFARE_READSC = 0x0621
    HF_MIFAREU_READCARD = 0x0721
    HF_MIFARE_WRITEBL = 0x0622
    HF_MIFARE_WRITEBL_EX = 0x0629
    HF_MIFARE_VALUE = 0x0627
    HF_MIFAREU_WRITEBL = 0x0722
    HF_MIFAREU_WRITEBL_COMPAT = 0x0723

    HF_MIFARE_CHKKEYS = 0x0623
    HF_MIFARE_SETMOD = 0x0624
    HF_MIFARE_CHKKEYS_FAST = 0x0625
    HF_MIFARE_CHKKEYS_FILE = 0x0626

    HF_MIFARE_SNIFF = 0x0630
    HF_MIFARE_MFKEY = 0x0631
    HF_MIFARE_PERSONALIZE_UID = 0x0632

    # ultralight-C
    HF_MIFAREUC_AUTH = 0x0724
    # Ultralight AES
    HF_MIFAREULAES_AUTH = 0x0725
    # 0x0726 no longer used
    HF_MIFAREU_SETKEY = 0x0727

    # mifare desfire
    HF_DESFIRE_READBL = 0x0728
    HF_DESFIRE_WRITEBL = 0x0729
    HF_DESFIRE_AUTH1 = 0x072a
    HF_DESFIRE_AUTH2 = 0x072b
    HF_DESFIRE_READER = 0x072c
    HF_DESFIRE_INFO = 0x072d
    HF_DESFIRE_COMMAND = 0x072e

    HF_MIFARE_NACK_DETECT = 0x0730
    HF_MIFARE_STATIC_NONCE = 0x0731
    HF_MIFARE_STATIC_ENCRYPTED_NONCE = 0x0732

    # MFU OTP TearOff
    HF_MFU_OTP_TEAROFF = 0x0740
    # MFU_Ev1 Counter TearOff
    HF_MFU_COUNTER_TEAROFF = 0x0741
    HF_MFU_ULC_CHKKEYS = 0x0742
    HF_MFU_ULAES_CHKKEYS = 0x0743

    HF_SNIFF = 0x0800
    HF_PLOT = 0x0801

    # Fpga plot download
    FPGAMEM_DOWNLOAD = 0x0802
    FPGAMEM_DOWNLOADED = 0x0803

    # For ThinFilm Kovio
    HF_THINFILM_READ = 0x0810
    HF_THINFILM_SIMULATE = 0x0811

    # For Atmel CryptoRF
    HF_CRYPTORF_SIM = 0x0820

    # Gen 3 magic cards
    HF_MIFARE_GEN3UID = 0x0850
    HF_MIFARE_GEN3BLK = 0x0851
    HF_MIFARE_GEN3FREEZ = 0x0852

    # Gen 4 GTU magic cards
    HF_MIFARE_G4_RDBL = 0x0860
    HF_MIFARE_G4_WRBL = 0x0861

    # Gen 4 GDM magic cards
    HF_MIFARE_G4_GDM_RDBL = 0x0870
    HF_MIFARE_G4_GDM_WRBL = 0x0871

    # HID SAM
    HF_SAM_PICOPASS = 0x0900
    HF_SAM_SEOS = 0x0901
    HF_SAM_MFC = 0x0902

    HF_SEOS_SIMULATE = 0x0903

    UNKNOWN = 0xFFFF


class Packet(bytearray):
    def __str__(self):
        return self.__repr__()

    def __add__(self, other):
        return self.__class__(super().__add__(other))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(super().__getitem__(key))
        return super().__getitem__(key)

    def merge(*items):
        return Packet(b''.join(items))

    def get(self, offset: int, endianness: Literal["little", "big"] = "little", length: int = 1, signed=False) -> int:
        return int.from_bytes(
            bytes=self[offset: offset + length], byteorder=endianness, signed=signed)

    def set(self, offset: int, value: int, endianness: Literal["little", "big"] = "little", length: int = 1,
            signed=False) -> None:
        self[offset: offset + length] = value.to_bytes(length=length, byteorder=endianness, signed=signed)

    def u8(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=2, signed=False)
        else:
            return self.get(offset=offset, endianness=endianness, length=1, signed=False)

    def u16(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=2, signed=False)
        else:
            return self.get(offset=offset, endianness=endianness, length=2, signed=False)

    def u24(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=3, signed=False)
        else:
            return self.get(offset=offset, endianness=endianness, length=3, signed=False)

    def u32(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=4, signed=False)
        else:
            return self.get(offset=offset, endianness=endianness, length=4, signed=False)

    def u64(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=8, signed=False)
        else:
            return self.get(offset=offset, endianness=endianness, length=8, signed=False)

    def i8(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=2, signed=True)
        else:
            return self.get(offset=offset, endianness=endianness, length=1, signed=True)

    def i16(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=2, signed=True)
        else:
            return self.get(offset=offset, endianness=endianness, length=2, signed=True)

    def i24(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=3, signed=True)
        else:
            return self.get(offset=offset, endianness=endianness, length=3, signed=True)

    def i32(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=4, signed=True)
        else:
            return self.get(offset=offset, endianness=endianness, length=4, signed=True)

    def i64(self, offset: int, endianness: Literal["little", "big"] = "little", **kwargs):
        if "value" in kwargs:
            self.set(offset=offset, value=kwargs["value"], endianness=endianness, length=8, signed=True)
        else:
            return self.get(offset=offset, endianness=endianness, length=8, signed=True)


class PacketResponse:
    def __init__(self, packet: Packet):
        if not isinstance(packet, Packet):
            raise ValueError('packet should be Packet')
        self.packet = packet
        self.data = packet[0x20:]

    @property
    def cmd(self):
        return self.packet.u16(offset=0)

    def getArg(self, index):
        return self.packet.u64(offset=8 + (index << 3))


class PacketResponseNG:
    def __init__(self, packet: Packet):
        self.packet = packet
        self.data = packet[10 if self.ng else 34: len(packet) - 2]

    def __len__(self):
        return len(self.packet)

    @property
    def ng(self):
        return (self.packet.u8(offset=5) & 0x80) > 0

    @property
    def status(self):
        return self.packet.i8(offset=6)

    @property
    def reason(self):
        return self.packet.i8(offset=7)

    @property
    def cmd(self):
        return self.packet.u16(offset=8)

    @property
    def crc(self):
        return self.packet.u16(offset=len(self.packet) - 2)

    def getArg(self, index):
        return self.packet.u64(offset=10 + (index << 3))


class ISODEP_STATE_T(Enum):
    ISODEP_INACTIVE = 0
    ISODEP_NFCA = 1
    ISODEP_NFCB = 2
    ISODEP_NFCV = 3


class Proxmark3Handler(Serial):
    def __init__(
            self,
            port: str | None = None,
            baudrate: int = 9600,
            bytesize: int = 8,
            parity: str = "N",
            stopbits: float = 1,
            timeout: float | None = None,
            xonxoff: bool = False,
            rtscts: bool = False,
            write_timeout: float | None = None,
            dsrdtr: bool = False,
            inter_byte_timeout: float | None = None,
            exclusive: bool | None = None,
    ):
        super().__init__(port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts, write_timeout, dsrdtr,
                         inter_byte_timeout, exclusive)
        self.isodep_state = None

    def SendCommandNG(self, cmd: int, data: Packet = None, ng=True):
        self.reset_input_buffer()
        if data and not isinstance(data, Packet):
            raise ValueError("data must be a Packet object")
        if data is not None:
            length = len(data)
            if length > 0x200:
                raise ValueError("data must be less than 0x200 bytes")
        else:
            length = 0
        packet = Packet(length + 0xA)
        packet[:4] = b'PM3a'
        packet.u16(offset=4, value=length + (0x8000 if ng else 0))
        packet.u16(offset=6, value=cmd)
        if data is not None:
            packet[8: length + 8] = data
        packet[-2:] = b"a3"
        if not self.is_open:
            self.open()
        self.write(packet)

    def ping(self):
        pkt = Packet(0x1C)
        pkt.u32(offset=0, value=0x04030201)
        pkt.u32(offset=4, value=0x07060504)
        pkt.u32(offset=8, value=0x0b0a0908)
        pkt.u32(offset=12, value=0x0f0e0d0c)
        pkt.u32(offset=16, value=0x13121110)
        pkt.u32(offset=20, value=0x17161514)
        pkt.u32(offset=24, value=0x1b1a1918)
        pkt.u32(offset=28, value=0x1f1e1d1c)
        self.SendCommandNG(cmd=PM3CMD.PING.value, data=pkt)
        resp = self.waitRespTimeout(PM3CMD.PING.value)
        if resp.status:
            raise Exception('Failed to get ping')
        return resp

    def version(self):
        pkt = Packet()
        self.SendCommandNG(cmd=PM3CMD.VERSION.value, data=pkt)
        resp = self.waitRespTimeout(PM3CMD.VERSION.value)
        if resp.status:
            raise Exception('Failed to get version')
        data = resp.data
        id = int.from_bytes(data[:4], byteorder='little')
        section_size = int.from_bytes(data[4:8], byteorder='little')
        versionstr_len = int.from_bytes(data[8:12], byteorder='little')
        versionstr = data[12:12 + versionstr_len]
        return id, section_size, versionstr

    def sendCommandMix(self, cmd: int, arg: list = None, data: Packet = None):
        if arg is None:
            arg = []
        if data and not isinstance(data, Packet):
            raise ValueError("data must be a Packet object")
        length = len(data)
        if length > 488:
            raise ValueError("data must be less than 488 bytes")
        packet = Packet(length + 0x18)
        if data:
            packet[0x18:] = data
        for i in range(3):
            packet.u64(offset=i << 3, value=arg[i] if i in arg else 0)
        self.SendCommandNG(cmd=cmd, data=packet, ng=False)

    def SetISODEPState(self, state: ISODEP_STATE_T = ISODEP_STATE_T.ISODEP_INACTIVE):
        self.isodep_state = state.value

    def DropField(self):
        self.reset_input_buffer()
        self.SetISODEPState(ISODEP_STATE_T.ISODEP_INACTIVE)
        self.SendCommandNG(cmd=PM3CMD.HF_DROPFIELD.value)

    def readResp(self):
        if not self.is_open:
            self.open()
        pre = Packet(self.read(0xA))
        if pre[0:4] == b'PM3b':
            return PacketResponseNG(Packet(pre + self.read((pre.u16(offset=4) & 0x7fff) + 2)))
        else:
            return PacketResponse(Packet(pre + self.read(0x200 + 0x16)))

    def waitRespTimeout(self, cmd, timeout=2500):
        ts = {
            'backup': self.timeout,
            'end': 0,
            'start': time.time(),
        }
        ts['end'] = ts['start'] + (timeout + 100) // 1000
        try:
            while True:
                self.timeout = ts['end'] - time.time()
                resp = self.readResp()
                if cmd == PM3CMD.UNKNOWN.value or resp.cmd == cmd:
                    return resp
                if resp.cmd == PM3CMD.WTX.value and len(resp.data) == 2:
                    wtx = resp.data.u16(offset=0)
                    if wtx >= 0xffff:
                        continue
                    ts['end'] += wtx / 1000
        except Exception as e:
            print(str(e))
        finally:
            self.timeout = ts['backup']


if __name__ == "__main__":
    pm3 = Proxmark3Handler(port="/dev/ttyACM0", baudrate=115200)
    pm3.ping()
    id, section_size, versionstr = pm3.version()
    print(versionstr.decode('utf-8'))
