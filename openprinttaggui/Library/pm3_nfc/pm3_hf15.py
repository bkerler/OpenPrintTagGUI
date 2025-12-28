#!/usr/bin/env python3
# (c) B.Kerler 2025
import sys
from io import BytesIO
import crcmod
from enum import Enum

from openprinttaggui.Library.pm3_nfc.pm3_generic import Proxmark3Handler, PM3CMD, Packet
from ..iso15693 import ISO15_TAG_T, ISO15693_UID_LENGTH, ISO15693_TAG_MAX_PAGES, ISO15693_TAG_MAX_SIZE, ISO15693_ATQB_LENGTH

class ISO15_COMMAND(Enum):
    ISO15_CONNECT = (1 << 0)
    ISO15_NO_DISCONNECT = (1 << 1)
    ISO15_RAW = (1 << 2)
    ISO15_APPEND_CRC = (1 << 3)
    ISO15_HIGH_SPEED = (1 << 4)
    ISO15_READ_RESPONSE = (1 << 5)
    ISO15_LONG_WAIT = (1 << 6)

ISO15_REQ_SUBCARRIER_SINGLE = 0x00  # Tag should respond using one subcarrier (ASK)
ISO15_REQ_SUBCARRIER_TWO = 0x01  # Tag should respond using two subcarriers (FSK)
ISO15_REQ_DATARATE_LOW = 0x00  # Tag should respond using low data rate
ISO15_REQ_DATARATE_HIGH = 0x02  # Tag should respond using high data rate
ISO15_REQ_NONINVENTORY = 0x00
ISO15_REQ_INVENTORY = 0x04  # This is an inventory request - see inventory flags
ISO15_REQ_PROTOCOL_NONEXT = 0x00
ISO15_REQ_PROTOCOL_EXT = 0x08  # RFU

# REQUEST FLAGS when INVENTORY is not set
ISO15_REQ_SELECT = 0x10  # only selected cards response
ISO15_REQ_ADDRESS = 0x20  # this req contains an address
ISO15_REQ_OPTION = 0x40  # Command specific option selector

# REQUEST FLAGS when INVENTORY is set
ISO15_REQINV_AFI = 0x10  # AFI Field is present
ISO15_REQINV_SLOT1 = 0x20  # 1 Slot
ISO15_REQINV_SLOT16 = 0x00  # 16 Slots
ISO15_REQINV_OPTION = 0x40  # Command specific option selector

# RESPONSE FLAGS
ISO15_RES_ERROR = 0x01
ISO15_RES_EXT = 0x08  # Protocol Extension

# RESPONSE ERROR CODES
ISO15_NOERROR = 0x00
ISO15_ERROR_CMD_NOT_SUP = 0x01  # Command not supported
ISO15_ERROR_CMD_NOT_REC = 0x02  # Command not recognized (eg. parameter error)
ISO15_ERROR_CMD_OPTION = 0x03  # Command option not supported
ISO15_ERROR_GENERIC = 0x0F  # No additional Info about this error
ISO15_ERROR_BLOCK_UNAVAILABLE = 0x10
ISO15_ERROR_BLOCK_LOCKED_ALREADY = 0x11  # cannot lock again
ISO15_ERROR_BLOCK_LOCKED = 0x12  # cannot be changed
ISO15_ERROR_BLOCK_WRITE = 0x13  # Writing was unsuccessful
ISO15_ERROR_BLOCL_WRITELOCK = 0x14  # Locking was unsuccessful

# First byte is 26
ISO15693_INVENTORY = 0x01
ISO15693_STAYQUIET = 0x02
# First byte is 02
ISO15693_READBLOCK = 0x20
ISO15693_WRITEBLOCK = 0x21
ISO15693_LOCKBLOCK = 0x22
ISO15693_READ_MULTI_BLOCK = 0x23
ISO15693_WRITE_MULTI_BLOCK = 0x24
ISO15693_SELECT = 0x25
ISO15693_RESET_TO_READY = 0x26
ISO15693_WRITE_AFI = 0x27
ISO15693_LOCK_AFI = 0x28
ISO15693_WRITE_DSFID = 0x29
ISO15693_LOCK_DSFID = 0x2A
ISO15693_GET_SYSTEM_INFO = 0x2B
ISO15693_READ_MULTI_SECSTATUS = 0x2C
# NXP/Philips custom commands
ISO15693_INVENTORY_READ = 0xA0
ISO15693_FAST_INVENTORY_READ = 0xA1
ISO15693_SET_EAS = 0xA2
ISO15693_RESET_EAS = 0xA3
ISO15693_LOCK_EAS = 0xA4
ISO15693_EAS_ALARM = 0xA5
ISO15693_PASSWORD_PROTECT_EAS = 0xA6
ISO15693_WRITE_EAS_ID = 0xA7
ISO15693_READ_EPC = 0xA8
ISO15693_GET_NXP_SYSTEM_INFO = 0xAB
ISO15693_INVENTORY_PAGE_READ = 0xB0
ISO15693_FAST_INVENTORY_PAGE_READ = 0xB1
ISO15693_GET_RANDOM_NUMBER = 0xB2
ISO15693_SET_PASSWORD = 0xB3
ISO15693_WRITE_PASSWORD = 0xB4
ISO15693_LOCK_PASSWORD = 0xB5
ISO15693_PROTECT_PAGE = 0xB6
ISO15693_LOCK_PAGE_PROTECTION = 0xB7
ISO15693_GET_MULTI_BLOCK_PROTECTION = 0xB8
ISO15693_DESTROY = 0xB9
ISO15693_ENABLE_PRIVACY = 0xBA
ISO15693_64BIT_PASSWORD_PROTECTION = 0xBB
ISO15693_STAYQUIET_PERSISTENT = 0xBC
ISO15693_READ_SIGNATURE = 0xBD
#
ISO15693_MAGIC_WRITE = 0xE0



class ISO15_RAW_CMD_T:
    def __init__(self, flags: int, raw: bytes):
        self.pkt = Packet(1 + 2 + len(raw) + 2)
        self.pkt.u8(offset=0, value=flags)
        self.pkt.u16(offset=1, value=len(raw) + 2)
        crc16 = crcmod.mkCrcFun(0x11021, initCrc=0, xorOut=0xFFFF, rev=True)
        raw += int.to_bytes(crc16(raw), 2, byteorder='little')
        self.pkt[3:] = raw


class PM3_HF15(Proxmark3Handler):

    def __init__(self, port: str, baudrate: int = 115200, logger=print):
        super().__init__(port=port, baudrate=baudrate)
        self.logger = logger

    def iso15_card_select_t(self, data):
        rf = BytesIO(bytearray(data))
        uid = rf.read(ISO15693_UID_LENGTH)
        uidlen = rf.read(1)
        atqb = rf.read(ISO15693_ATQB_LENGTH)
        chipid = rf.read(1)
        cid = rf.read(1)
        return uid, uidlen, atqb, chipid, cid

    def crc_x25(self, data):
        crc16 = crcmod.mkCrcFun(0x11021, initCrc=0, xorOut=0xFFFF, rev=True)
        return crc16(data)

    def arg_get_raw_flag(self, uidlen: int, unaddressed: bool, scan: bool, add_option: bool):
        flags = 0
        if uidlen == 8 or scan or unaddressed:
            flags = ISO15_REQ_SUBCARRIER_SINGLE | ISO15_REQ_DATARATE_HIGH | ISO15_REQ_NONINVENTORY
        if not unaddressed or scan:
            flags |= ISO15_REQ_ADDRESS
        if add_option:
            flags |= ISO15_REQ_OPTION
        return flags

    def getUID(self):
        mask_len = 0
        raw = int.to_bytes(
            ISO15_REQ_SUBCARRIER_SINGLE | ISO15_REQ_DATARATE_HIGH | ISO15_REQ_INVENTORY | ISO15_REQINV_SLOT1, 1,
            'little')
        raw += int.to_bytes(ISO15693_INVENTORY, 1, 'little')
        raw += mask_len.to_bytes(1, 'little')

        flags = (ISO15_COMMAND.ISO15_CONNECT.value |
                 ISO15_COMMAND.ISO15_HIGH_SPEED.value |
                 ISO15_COMMAND.ISO15_READ_RESPONSE.value)
        pkt = ISO15_RAW_CMD_T(flags=flags, raw=raw).pkt
        self.SendCommandNG(cmd=PM3CMD.HF_ISO15693_COMMAND.value, data=pkt)
        resp = self.waitRespTimeout(PM3CMD.HF_ISO15693_COMMAND.value)
        if resp.status:
            raise Exception('Failed to detect tag')
        data = resp.data
        if len(data) != 12:
            raise Exception('Got invalid uid length')
        # 0000bd4aec18090104e0c8af
        gen_crc = self.crc_x25(data[:10])
        if int.to_bytes(gen_crc, 2, 'little') != data[-2:]:
            raise Exception('Got invalid uid crc16')
        uid = resp.data[2:10]
        return uid

    def iso15_error_handling_card_response(self, data):
        gen_crc = self.crc_x25(data[:-2])
        if int.to_bytes(gen_crc, 2, 'little') != data[-2:]:
            print('Got invalid card response crc16')
            return False
        if data[0] & ISO15_RES_ERROR == ISO15_RES_ERROR:
            print('Bad iso15 response')
            return False
        return True

    def iso15_get_system_info(self, fast: bool = False, blocksize: int = 16):
        """
        Get system info : Using scan mode, unaddressed = false
        """
        uid = self.getUID()
        if uid != b"":
            self.logger(f'UID detected: {uid.hex()}')

        add_option = False
        if uid[7] == b"\xE0" and uid[6] == 0x07:
            # Overriding option param, writing to TI tag
            add_option = True
        raw = int.to_bytes(self.arg_get_raw_flag(uidlen=0, unaddressed=False, scan=True, add_option=add_option), 1,
                           byteorder='little') + int.to_bytes(ISO15693_GET_SYSTEM_INFO, 1, byteorder='little')
        if uid[0] != b"\xE0":
            raw += uid

        flags = (ISO15_COMMAND.ISO15_CONNECT.value |
                 ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                 ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
        if fast:
            flags |= ISO15_COMMAND.ISO15_HIGH_SPEED.value

        pkt = ISO15_RAW_CMD_T(flags=flags, raw=raw).pkt
        self.SendCommandNG(cmd=PM3CMD.HF_ISO15693_COMMAND.value, data=pkt)
        resp = self.waitRespTimeout(PM3CMD.HF_ISO15693_COMMAND.value)
        if resp.status:
            raise Exception('Failed to get system info')
        tag = ISO15_TAG_T(blocksize)
        if self.iso15_error_handling_card_response(resp.data):
            # print("All ok")
            tag.parse(resp.data)
        return tag

    def dump(self, filename: str = None, fast: bool = True, blocksize: int = 4, progress=None):
        tag = self.iso15_get_system_info(fast=fast, blocksize=blocksize)

        raw = bytearray(int.to_bytes(self.arg_get_raw_flag(uidlen=0, unaddressed=False, scan=True, add_option=False), 1,
                                     byteorder='little'))
        raw[0] |= ISO15_REQ_OPTION
        raw.append(ISO15693_READBLOCK)
        flags = (ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                 ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
        if fast:
            flags |= ISO15_COMMAND.ISO15_HIGH_SPEED.value
        if tag.uid[0] != b"\xE0":
            raw.extend(tag.uid)
        if progress:
            progress(0)
        for blocknum in range(tag.pagesCount):
            if progress:
                progress(blocknum / tag.pagesCount * 100)
            draw = raw + int.to_bytes(blocknum & 0xFF, 1)
            pkt = ISO15_RAW_CMD_T(flags=flags, raw=draw).pkt
            self.SendCommandNG(cmd=PM3CMD.HF_ISO15693_COMMAND.value, data=pkt)
            resp = self.waitRespTimeout(PM3CMD.HF_ISO15693_COMMAND.value, timeout=2000)
            if resp.status:
                raise Exception('Failed to read block data')
            d = resp.data
            if d[0] & ISO15_RES_ERROR == ISO15_RES_ERROR:
                if d[1] == 0x0F or d[1] == 0x10:
                    break
                raise Exception('Failed to read block data')
            tag.locks[blocknum] = resp.data[1]
            pgdata = resp.data[2:]
            tag.data[blocknum * tag.bytesPerPage:(blocknum * tag.bytesPerPage) + tag.bytesPerPage] = bytearray(
                pgdata[:tag.bytesPerPage])
        if progress:
            progress(100)
        if filename is None:
            return tag
        tag.save(filename)
        self.DropField()
        return tag

    def write_blk(self, pm3flags: int, flags: int, uid: bytes, fast: bool, blockno, data: bytes):
        # 504D3361 1480 1303 73 1100 2221 BD4AEC18090104E0 00 E1402701 C919 6133
        raw = bytearray()
        raw.append(flags)
        raw.append(ISO15693_WRITEBLOCK)
        if uid is not None:
            raw.extend(uid)
        raw.append(blockno)
        if data is not None:
            raw.extend(data)
        if pm3flags is not None:
            flags = pm3flags
        else:
            flags = (ISO15_COMMAND.ISO15_LONG_WAIT.value |
                     ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                     ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
            if fast:
                flags |= ISO15_COMMAND.ISO15_HIGH_SPEED.value
        pkt = ISO15_RAW_CMD_T(flags=flags, raw=raw).pkt
        self.SendCommandNG(cmd=PM3CMD.HF_ISO15693_COMMAND.value, data=pkt)
        resp = self.waitRespTimeout(PM3CMD.HF_ISO15693_COMMAND.value)
        if resp.status:
            raise Exception('Failed to write tag')
        if self.iso15_error_handling_card_response(resp.data):
            return True
        return False

    def restore(self, data_or_filename, fast: bool = False, blocksize: int = 4, progress=None):
        tag = self.iso15_get_system_info(fast=fast, blocksize=blocksize)
        add_option = False
        if isinstance(data_or_filename, str):
            tag.load(data_or_filename)
        else:
            tag.data = data_or_filename
        pm3flags = (ISO15_COMMAND.ISO15_CONNECT.value |
                    ISO15_COMMAND.ISO15_LONG_WAIT.value |
                    ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                    ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
        if fast:
            pm3flags |= ISO15_COMMAND.ISO15_HIGH_SPEED.value

        if tag.uid[7] == b"\xE0" and tag.uid[6] == 0x07:
            # Overriding option param, writing to TI tag
            add_option = True
        flags = self.arg_get_raw_flag(uidlen=0,
                                      unaddressed=False,
                                      scan=True,
                                      add_option=add_option)
        filldata = tag.data
        if len(filldata) % tag.bytesPerPage != 0:
            filldata += b"\x00" * tag.bytesPerPage - (len(filldata) % tag.bytesPerPage)
        blocks = len(filldata) // tag.bytesPerPage
        if progress:
            progress(0)
        blockstowrite = min(blocks, tag.pagesCount)
        for blocknum in range(blockstowrite):
            if progress:
                progress(blocknum / blockstowrite * 100)
            if not self.write_blk(pm3flags=pm3flags, flags=flags,
                                  uid=tag.uid, fast=fast, blockno=blocknum,
                                  data=tag.data[
                                       blocknum * tag.bytesPerPage:(blocknum * tag.bytesPerPage) + tag.bytesPerPage]):
                return False
            if blocknum == 0:
                pm3flags = (ISO15_COMMAND.ISO15_LONG_WAIT.value |
                            ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                            ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
        self.DropField()
        if progress:
            progress(100)
        return True


if __name__ == "__main__":
    pm3 = PM3_HF15(port="/dev/ttyACM0", baudrate=115200)
    """
    tag=ISO15_TAG_T()
    tag.load("dump.bin")
    blocknum=0
    add_option=False
    fast=True
    if tag.uid[7] == b"\xE0" and tag.uid[6] == 0x07:
        # Overriding option param, writing to TI tag
        add_option = True
    pm3flags = (ISO15_COMMAND.ISO15_CONNECT.value |
                ISO15_COMMAND.ISO15_LONG_WAIT.value |
                ISO15_COMMAND.ISO15_READ_RESPONSE.value |
                ISO15_COMMAND.ISO15_NO_DISCONNECT.value)
    if fast:
        pm3flags |= ISO15_COMMAND.ISO15_HIGH_SPEED.value
    flags = pm3.arg_get_raw_flag(uidlen=0,
                                  unaddressed=False,
                                  scan=True,
                                  add_option=add_option)
    pm3.write_blk(pm3flags=pm3flags,flags=flags,uid=tag.uid,
                  fast=fast, blockno=blocknum,
                  data=tag.data[blocknum*tag.bytesPerPage:(blocknum*tag.bytesPerPage)+tag.bytesPerPage])
    """
    id, section_size, versionstr = pm3.version()
    print(versionstr.decode('utf-8') + "\n")
    try:
        tagdata = pm3.dump(filename="dump.bin")
    except Exception as e:
        print("\n" + str(e))
        sys.exit(1)
    print()
    print("OpenPrintTag tag data:\n------------------------\n")
    print(tagdata.hex())
