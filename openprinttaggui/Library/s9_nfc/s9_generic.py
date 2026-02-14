import ctypes
from ctypes import *
import time
from binascii import hexlify, unhexlify
import os, sys
import platform

script_path = os.path.dirname(os.path.realpath(__file__))


class S9_GENERIC:
    def __init__(self, port: str = None, logger=print):
        self.szVer = None
        self.lib = None
        self.icdev = None
        self.logger = logger
        self.port = port

    def detect_os(self):
        os_name = platform.system()  # Returns 'Windows', 'Linux', 'Darwin' (for macOS), or others
        if os_name == 'Darwin':
            os_name = 'macOS'  # Optional: human-readable rename
        # Architecture (e.g., 'x86_64', 'AMD64', 'arm64', 'aarch64', etc.)
        arch = platform.machine()  # Most reliable for specific architecture
        # Bitness (32-bit or 64-bit) and support
        bits, linkage = platform.architecture()
        return os_name, bits, arch, linkage

    def init_dll(self, beep: bool = False):
        # Load the DLL and the function
        os_name, bits, arch, linkage = self.detect_os()
        if os_name == "Linux":
            if arch == "x86_64":
                if bits == "64bit":
                    lib = cdll.LoadLibrary(os.path.join(script_path, "Linux", "X86-lib", "64bit", "libS8_64.so"))
                else:
                    lib = cdll.LoadLibrary(os.path.join(script_path, "Linux", "X86-lib", "32bit", "libS8.so"))
            elif arch == "aarch64":
                lib = cdll.LoadLibrary(os.path.join(script_path, "Linux", "arm-lib", bits, "libS8_64.so"))
            elif arch == "arm":
                lib = cdll.LoadLibrary(os.path.join(script_path, "Linux", "arm-lib", "arm-linux-gcc_4.6.3", "libS8.so"))
        elif os_name == "Windows":
            lib = ctypes.WinDLL(os.path.join(script_path, "Windows", "umf.dll"))
        else:
            self.logger(f"{os_name} is currently not supported.")
            return False
        st = -1
        for m_port in range(16):
            if os_name == "Linux":
                szNode = bytes(f"/dev/usb/hiddev{m_port}", 'utf-8')
                icdev = lib.fw_init_ex(2, szNode, 115200)
            else:
                icdev = lib.fw_init(100, 115200)

            if icdev != -1:
                szVer = create_string_buffer(128)
                st = lib.fw_getver(icdev, szVer)
                if st == 0:
                    break
        if st == -1:
            return False
        if beep:
            lib.fw_beep(icdev, 1)
        # set card type
        lib.fw_config_card(icdev, 0x31)
        self.icdev = icdev
        self.lib = lib
        self.szVer = szVer.value
        return True

    def init_nfc(self, uid: bytes = None) -> bytes:
        if uid is None:
            uid = create_string_buffer(256)
        if self.icdev is None:
            return b""
        length = create_string_buffer(8)
        st = self.lib.fw_inventory(self.icdev, 0x36, 0, 0, length, uid)
        if st != 0:
            return b""
        st = self.lib.fw_select_uid(self.icdev, 0x22, uid)  # we got chip, select it
        if st != 0:
            print("Error selecting!")
            return b""

        st = self.lib.fw_reset_to_ready(self.icdev, 0x22, uid)
        if st != 0:
            print("Error resetting!")
            return b""
        secInfo = create_string_buffer(256)
        secInfoLen = create_string_buffer(8)
        st = self.lib.fw_get_securityinfo(self.icdev, 0x22, 0x04, 0x02, uid, secInfoLen, secInfo)
        if st != 0:
            print("Error reading security info!")
            return b""
        return uid.value


if __name__ == "__main__":
    s9 = S9_GENERIC(port=None)
    if s9.init_dll():
        print(s9.szVer.decode('utf-8'))
        uid = s9.init_nfc(uid=None)
        print(f"uid detected: {uid.hex()}")
