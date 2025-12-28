#!/usr/bin/env python3
# (c) B.Kerler 2025
import ctypes
from ctypes import create_string_buffer
from openprinttaggui.Library.iso15693 import ISO15_TAG_T, ISO15693_UID_LENGTH, ISO15693_TAG_MAX_PAGES, ISO15693_TAG_MAX_SIZE, \
    ISO15693_ATQB_LENGTH
from openprinttaggui.Library.s9_nfc.s9_generic import S9_GENERIC


class S9_HF15(S9_GENERIC):

    def __init__(self, port: str = None, logger=print):
        super().__init__(port=port, logger=logger)
        self.logger = logger
        self.uid = None
        self.port = port

    def getUID(self, uid: bytes = None):
        if self.init_dll():
            self.logger(self.szVer.decode('utf-8'))
        self.uid = self.init_nfc(uid=uid)
        if self.uid != b"":
            self.logger(f'UID detected: {bytearray(self.uid).hex()}')
        return self.uid

    def read_block(self, blocknum, blocksize: int = 4):
        dataLen = create_string_buffer(blocksize)
        databuffer = create_string_buffer(4)
        bnum = ctypes.c_ubyte(blocknum)
        flags = ctypes.c_ubyte(0x22)
        uid_ptr = ctypes.cast(self.uid, ctypes.POINTER(ctypes.c_ubyte))
        res = self.lib.fw_readblock(self.icdev, flags, bnum, 1, uid_ptr, dataLen, databuffer)
        if res != 0:
            return b"", res
        return bytearray(databuffer.raw), res

    def write_block(self, blocknum: int, blocksize: int = 4, data: bytes = None):
        uid_ptr = ctypes.cast(self.uid, ctypes.POINTER(ctypes.c_ubyte))
        flags = ctypes.c_ubyte(0x22)
        wlen = ctypes.c_ubyte(blocksize)
        wbuffer = (ctypes.c_ubyte * len(data))(*data)
        bnum = ctypes.c_ubyte(blocknum)
        res = self.lib.fw_writeblock(self.icdev, flags, bnum, 1, uid_ptr, wlen, wbuffer)
        if res not in [0, 0x7d]:
            return res, False
        return res, True

    def dump(self, filename: str = None, fast: bool = True, blocksize: int = 4, progress=None):
        _ = fast
        if progress:
            progress(0)
        tag = ISO15_TAG_T(blocksize)
        tag.uid = self.uid
        maxblocks = ISO15693_TAG_MAX_SIZE // blocksize
        for blocknum in range(tag.pagesCount):
            if progress:
                progress(blocknum / tag.pagesCount * 100)
            pgdata, res = self.read_block(blocknum=blocknum, blocksize=blocksize)
            if res == 0 and pgdata == b"":
                pgdata, res = self.read_block(blocknum=blocknum, blocksize=blocksize)
            if pgdata is None and self.logger:
                self.logger(f"Error on reading block {blocknum}")
            if progress:
                progress(blocknum / maxblocks * 100)
            tag.locks[blocknum] = res
            tag.data[blocknum * tag.bytesPerPage:(blocknum * tag.bytesPerPage) + tag.bytesPerPage] = bytearray(
                pgdata[:tag.bytesPerPage])
        if progress:
            progress(100)
        if filename is not None:
            open(filename, "wb").write(data)
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
            result, value = self.write_block(blocknum=blocknum, blocksize=blocksize,
                                             data=tag.data[
                                                  blocknum * tag.bytesPerPage:(
                                                                                          blocknum * tag.bytesPerPage) + tag.bytesPerPage])
            if not value:
                return False
            if value and result == 0x7D:
                break
        if progress:
            progress(100)
        return True


if __name__ == "__main__":
    s9 = S9_HF15()
    uid = s9.getUID()
    if uid != b"":
        print(f"uid detected: {uid.hex()}")
        data = s9.dump()
        print(data.hex())
