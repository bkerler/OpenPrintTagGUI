from enum import Enum
from acs_generic import ACS, ReadMode

class ACS_HF14(ACS):

    def __init__(self, port: str, logger=print):
        super().__init__(port=port)
        self.logger = logger

    def dump(self):
        self.start_transparent()
        self.select_iso14443a()
        data = bytearray()
        blksize = 4
        for block in range(0, ReadMode.ISO15693.value.maxaddr, blksize // ReadMode.ISO15693.value.blksize):
            tmp = self.read_block(address=block, length=blksize, mode=ReadMode.ISO15693)
            if tmp == b"":
                break
            data.extend(tmp)
        self.end_transparent()
        return data

    def read_block(self, address, length: int = 0, mode: ReadMode = ReadMode.ISO15693):
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
                return bytes(self.send_apdu([0xFF, 0xB0, p1, p2, 00]))
            elif length < 256:
                return bytes(self.send_apdu([0xFF, 0xB0, p1, p2, length & 0xFF]))
            else:
                return bytes(self.send_apdu([0xFF, 0xB0, p1, p2, (length >> 8) & 0xFF, length & 0xFF]))
        except ValueError as err:
            self.logger(f"Error on reading block {address}: {str(err)}")
            return b""


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
                return bytes(self.send_apdu([0xFF, 0xD6, p1, p2, length & 0xFF] + list(data)))
            else:
                return bytes(self.send_apdu([0xFF, 0xD6, p1, p2, (length >> 8) & 0xFF, length & 0xFF] + list(data)))
        except ValueError as err:
            self.logger(f"Error on reading block {address}: {str(err)}")
            return b""

    def pass_through_cmd(self, data):
        return self.send_apdu([0xFF, 0x00, 0x00, 0x00, len(data)] + data)