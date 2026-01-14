#!/usr/bin/env python3
# (c) B.Kerler 2025

ISO15693_TAG_MAX_PAGES = 160  # in pages  (0xA0)
ISO15693_TAG_MAX_SIZE = 2048  # in byte (64 pages of 256 bits)
ISO15693_UID_LENGTH = 8
ISO15693_ATQB_LENGTH = 7
class ISO15_TAG_T:
    uid = bytearray(b"\xE0" + b'\x00' * (ISO15693_UID_LENGTH - 1))
    dsfid = 0
    dsfidLock = False
    afi = 0
    afiLock = False
    bytesPerPage = 4
    pagesCount = 128
    ic = 0
    locks = bytearray(b"\x00" * ISO15693_TAG_MAX_PAGES)
    data = bytearray(b"\x00" * ISO15693_TAG_MAX_SIZE)
    random = b"\x00\x00"
    privacyPasswd = b"\x00\x00\x00\x00"
    state = 0
    expectFast = False
    expectFsk = False

    def __init__(self, blocksize: int = 4):
        self.blocksize = blocksize

    def parse(self, data):
        d = data
        self.uid = d[2:2 + 8]
        dCpt = 10
        if d[1] & 0x1:
            self.dsfid = d[dCpt]
        dCpt += 1
        if d[1] & 0x2:
            self.afi = d[dCpt]
        dCpt += 1
        if d[1] & 0x4:
            self.pagesCount = d[dCpt] + 1
            self.bytesPerPage = d[dCpt + 1] + 1
        else:
            self.bytesPerPage = self.blocksize
            self.pagesCount = 128
        dCpt += 2
        if d[1] & 0x8:
            self.ic = d[dCpt]
        dCpt += 1

    def save(self, filename: str = "dump.bin"):
        wd = bytearray()
        wd.extend(self.uid)
        wd.append(self.dsfid)
        wd.append(1 if self.dsfidLock else 0)
        wd.append(self.afi)
        wd.append(1 if self.afiLock else 0)
        wd.append(self.bytesPerPage)
        wd.append(self.pagesCount)
        wd.append(self.ic)
        wd.extend(self.locks)
        wd.extend(self.data)
        wd.extend(self.random)
        wd.extend(self.privacyPasswd)
        wd.extend(int.to_bytes(self.state, 4, 'little'))
        wd.append(1 if self.expectFast else 0)
        wd.append(1 if self.expectFsk else 0)
        with open(filename, "wb") as f:
            f.write(wd)

    def load(self, filename: str = "dump.bin"):
        with open(filename, "rb") as f:
            self.uid = f.read(ISO15693_UID_LENGTH)
            self.dsfid = f.read(1)[0]
            self.dsfidLock = True if f.read(1)[0] == 1 else False
            self.afi = f.read(1)[0]
            self.afiLock = True if f.read(1)[0] == 1 else False
            self.bytesPerPage = f.read(1)[0]
            self.pagesCount = f.read(1)[0]
            self.ic = f.read(1)[0]
            self.locks = f.read(ISO15693_TAG_MAX_PAGES)
            self.data = f.read(ISO15693_TAG_MAX_SIZE)
            self.random = f.read(2)
            self.privacyPasswd = f.read(4)
            self.state = f.read(1)[0]
            self.expectFast = True if f.read(1)[0] == 1 else False
            self.expectFsk = True if f.read(1)[0] == 1 else False
