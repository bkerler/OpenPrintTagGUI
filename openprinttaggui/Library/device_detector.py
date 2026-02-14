import hid
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal, QObject, Slot

device_list = [
    {"vid": 0x9ac4, "pid": 0x4b8f, "reader": 1, "name": "proxmark3"},
    {"vid": 0x0471, "pid": 0xa112, "reader": 2, "name": "s9"},
    {"vid": 0x072F, "pid": 0x2303, "reader": 3, "name": "acr1552u-m1"},
    {"vid": 0x072F, "pid": 0x2308, "reader": 3, "name": "acr1552u-m2"},
    {"vid": 0x0e0f, "pid": 0x0003, "reader": 3, "name": "VMWARE-ccid"},
    {"vid": 0xe4b2, "pid": 0x0045, "reader": -1, "name": "td1s"},
]


class DeviceDetectorWorker(QObject):
    device_detected = Signal(dict)
    device_removed = Signal(dict)
    finished = Signal()   # optional

    def __init__(self, device_list, poll_interval_ms=1500):
        super().__init__()
        self.device_list = device_list
        self.poll_interval = poll_interval_ms
        self.is_running = True
        self.previous_state = set()

    def stop(self):
        self.is_running = False

    @Slot()
    def start_detection(self):
        while self.is_running:
            current_state = set()

            for dev_tpl in self.device_list:
                # --- Serial check ---
                try:
                    for port in serial.tools.list_ports.comports():
                        if port.vid == dev_tpl["vid"] and port.pid == dev_tpl["pid"]:
                            d = dev_tpl.copy()
                            d["port"] = port.device
                            d["type"] = "serial"
                            current_state.add(tuple(sorted(d.items())))
                except Exception:
                    pass  # very important - never let exception kill thread

                # --- HID check ---
                try:
                    for info in hid.enumerate(0, 0):
                        if info["vendor_id"] == dev_tpl["vid"] and info["product_id"] == dev_tpl["pid"]:
                            d = dev_tpl.copy()
                            d["port"] = info["path"].decode(errors='replace')
                            d["type"] = "hid"
                            current_state.add(tuple(sorted(d.items())))
                except Exception:
                    pass

            # Detect added / removed
            for dev_tuple in current_state - self.previous_state:
                self.device_detected.emit(dict(dev_tuple))

            for dev_tuple in self.previous_state - current_state:
                d = dict(dev_tuple)
                d["port"] = None
                self.device_removed.emit(d)

            self.previous_state = current_state.copy()

            # Sleep – do NOT use QTimer here
            QThread.msleep(self.poll_interval)

        self.finished.emit()
