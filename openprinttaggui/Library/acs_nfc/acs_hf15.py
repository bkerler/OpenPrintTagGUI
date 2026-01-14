import os
import sys
from enum import Enum
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(script_path))
sys.path.insert(1, script_path)
sys.path.insert(2, os.path.join(script_path, "Library", "OpenPrintTag", "utils"))

from acs_generic import ACS, ReadMode
from openprinttaggui.Library.iso15693 import ISO15_TAG_T, ISO15693_UID_LENGTH, ISO15693_TAG_MAX_PAGES, ISO15693_TAG_MAX_SIZE, \
    ISO15693_ATQB_LENGTH

class ISO15693_CMD(Enum):
    INVENTORY = 0x01
    STAY_QUIET = 0x02
    READ_SINGLE_BLOCK = 0x20
    WRITE_SINGLE_BLOCK = 0x21
    LOCK_BLOCK = 0x22
    READ_MULTI_BLOCK = 0x23
    WRITE_MULTI_BLOCK = 0x24
    SELECT = 0x25
    RESET_TO_READY = 0x26
    WRITE_AFI = 0x27
    LOCK_AFI = 0x28
    WRITE_DSFID = 0x29
    LOCK_DSFID = 0x2A
    GET_SYSTEM_INFO = 0x2B
    GET_MULTIPLE_BLOCK_SECURITY_STATUS = 0x2C
    # FAST_READ_MULTIPLE_BLOCKS = 0x2D
    EXTENDED_READ_SINGLE_BLOCK = 0x30
    EXTENDED_WRITE_SINGLE_BLOCK = 0x31
    EXTENDED_LOCK_BLOCK = 0x32
    EXTENDED_READ_MULTI_BLOCKS = 0x33
    EXTENDED_WRITE_MULTI_BLOCKS = 0x34
    AUTHENTICATE = 0x35
    # KEY_UPDATE = 0x36
    # AUTHCOMM_CRYPTO_FORMAT_INDICATOR = 0x37
    # SECURECOMM_CRYPTO_FORMAT_INDICATOR = 0x38
    # CHALLENGE = 0x39
    # READ_BUFFER = 0x3A
    EXTENDED_GET_SYSTEM_INFO = 0x3B
    EXTENDED_GET_MULTIPLE_BLOCK_SECURITY_STATUS = 0x3C
    FAST_EXTENDED_READ_MULTI_BLOCKS = 0x3D
    # CUSTOM: 0xA0 - 0xDF
    # PROPRIETARY: 0xE0 - 0xFF


class ACS_HF15(ACS):

    def __init__(self, port: str, logger=print):
        super().__init__(port=port)
        self.uid = b""
        self.logger = logger


    def pass_through(self, function, data):
        res=self.send_apdu([0xFF,0xFB,0x00,function,len(data)] + data)
        return res

    def end_transparent(self):
        return self.manage_session([0x82, 0x00])==0x9000

    def getUID(self):
        res=self.get_system_info()
        if "uid" in res:
            self.uid=res["uid"]
        else:
            self.uid=b""
        if self.uid != b"":
            self.logger(f'UID detected: {bytearray(self.uid).hex()}')
        return self.uid

    def get_system_info(self):
        self.start_transparent()
        self.select_iso15693()
        resp=self.transparent_exchange(data=[0x02,ISO15693_CMD.GET_SYSTEM_INFO.value])
        #resp2=self.transparent_exchange(data=[0x02,ISO15693_CMD.EXTENDED_GET_SYSTEM_INFO.value])
        self.end_transparent()
        if len(resp)>0:
            flag = resp[0]
            info_flag = resp[1]
            if info_flag == 0xF:
                uid = resp[2:2 + 8]
                dsfid = resp[10]
                afi = resp[11]
                memory = resp[12]
                ic_ref = resp[13:15]
                return dict(uid=uid,dsfid=dsfid,afi=afi,memory=memory, ic_ref=ic_ref)
        return dict()

    def read_block(self, address, length: int = 0):
        mode = ReadMode.ISO15693
        if address > mode.value.maxaddr:
            self.logger(f"Error on reading block {address}: max block address is {mode.value.maxaddr}")
            return b""
        if length == 0:
            length = mode.value.blksize
        mode_val = mode.value.mode
        p1 = (address >> 8) & 7 + (mode_val << 4)
        p2 = address & 0xFF
        try:
            if length == 256:
                return 0, bytes(self.send_apdu([0xFF, 0xB0, p1, p2, 00]))
            elif length < 256:
                return 0, bytes(self.send_apdu([0xFF, 0xB0, p1, p2, length & 0xFF]))
            else:
                return 0, bytes(self.send_apdu([0xFF, 0xB0, p1, p2, (length >> 8) & 0xFF, length & 0xFF]))
        except Exception as e:
            if self.sw1==0x69 and self.sw2==0x82:
                return 0xF, b""
            else:
                self.logger(f"Error on reading block {address}: {e}")
        return -1, b""

    def read_value_block(self, block):
        return bytes(self.send_apdu([0xFF, 0xB1, 00, block, 0x04]))

    def increment_value(self, src_block, dst_block, value):
        return bytes(self.send_apdu([0xFF, 0xD7, src_block&0xFF, dst_block&0xFF, 0x05, 0x01] + [val for val in value.to_bytes(4, byteorder='big')]))

    def decrement_value(self, src_block, dst_block, value):
        return bytes(self.send_apdu([0xFF, 0xD7, src_block&0xFF, dst_block&0xFF, 0x05, 0x02] + [val for val in value.to_bytes(4, byteorder='big')]))

    def copy_value(self, src_block, dst_block):
        return bytes(self.send_apdu([0xFF, 0xD7, src_block & 0xFF, 0x02, 0x03, dst_block & 0xFF]))

    def update_block(self, address, length: int = 0, data:bytearray=b"", mode: ReadMode = ReadMode.ISO15693):
        if address > mode.value.maxaddr:
            self.logger(f"Error on reading block {address}: max block address is {mode.value.maxaddr}")
            return b""
        if length == 0:
            length = mode.value.blksize
        mode_val = mode.value.mode
        p1 = (address >> 8) & 7 + (mode_val << 4)
        p2 = address & 0xFF
        try:
            if length < 256:
                return 0, bytes(self.send_apdu([0xFF, 0xD6, p1, p2, length & 0xFF] + [val for val in bytearray(data)]))
            else:
                return 0, bytes(self.send_apdu([0xFF, 0xD6, p1, p2, (length >> 8) & 0xFF, length & 0xFF] + [val for val in bytearray(data)]))
        except ValueError as err:
            if self.sw1==0x69 and self.sw2==0x82:
                return 0xF, b""
            self.logger(str(err))
            return -1, b""

    def dump(self, filename: str = None, fast: bool = True, blocksize: int = 4, progress=None):
        self.start_transparent()
        self.select_iso15693()
        tag = ISO15_TAG_T(blocksize)
        tag.uid = self.uid
        for blocknum in range(tag.pagesCount):
            if progress:
                progress(blocknum / tag.pagesCount * 100)
            lock, pgdata = self.read_block(address=blocknum, length=blocksize)
            if lock==0xF:
                break
            if pgdata==b"" and self.logger:
                self.logger(f"Error on reading block {blocknum}")
            tag.locks[blocknum] = lock
            if lock==0:
                tag.data[blocknum * tag.bytesPerPage:(blocknum * tag.bytesPerPage) + tag.bytesPerPage] = bytearray(
                    pgdata[:tag.bytesPerPage])
            else:
                break
        self.end_transparent()
        if progress:
            progress(100)
        if filename is not None:
            tag.save(filename=filename)
        return tag

    def restore(self, data_or_filename, fast: bool = False, blocksize: int = 4, progress=None):
        _ = fast
        tag = ISO15_TAG_T(blocksize)
        tag.uid = self.uid
        if isinstance(data_or_filename, str):
            tag.load(data_or_filename)
        else:
            tag.data = data_or_filename
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
            lock, result = self.update_block(address=blocknum, length=blocksize,
                                              data=tag.data[
                                                  blocknum * tag.bytesPerPage:(blocknum * tag.bytesPerPage) +
                                                                              tag.bytesPerPage])
            if not result:
                return False
            if lock!=0x0:
                if lock!=0xF and self.logger:
                    self.logger(f"Error on writing block {blocknum}")
                    break
                else:
                    break
        if progress:
            progress(100)
        return True


if __name__ == "__main__":
    acs = ACS_HF15(port="")
    acs.getUID()
    acs.dump(filename="acs_hf15.dat")
    acs.restore("acs_hf15.dat")