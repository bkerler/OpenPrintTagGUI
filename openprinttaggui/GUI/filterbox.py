from PySide6.QtCore import QSortFilterProxyModel, Qt, QEvent
from PySide6.QtWidgets import QComboBox, QCompleter, QLineEdit


class ClearLineEdit(QLineEdit):
    def focusInEvent(self, event):
        if event.reason() == Qt.MouseFocusReason:
            self.clear()
        super().focusInEvent(event)

class FilterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        completer = self.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        # Set custom line edit
        self.setLineEdit(ClearLineEdit(self))

    def showPopup(self):
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.clear()
        super().showPopup()
