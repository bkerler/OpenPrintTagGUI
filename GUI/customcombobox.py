from PySide6.QtWidgets import QComboBox


class ClearComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self._le = self.lineEdit()
        self._le.installEventFilter(self)

    def eventFilter(self, obj, event):
        # We only care about mouse clicks inside the line-edit
        if obj is self._le and event.type() == event.Type.MouseButtonRelease:
            # Clear the text (and the current index)
            self.setEditText("")
            # Put the cursor back so the user can type immediately
            self._le.setFocus()
            return True  # event handled
        return super().eventFilter(obj, event)