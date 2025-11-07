import sys
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QCheckBox, QTreeView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont


class CheckableItemDelegate(QStyledItemDelegate):
    """Optional: Custom delegate if you want better checkbox alignment"""
    pass  # Not needed unless custom painting


class PropertyFilterWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        #self.setFixedHeight(self.parent.header_height)

        self.setWindowTitle("Material Properties Filter")
        self.resize(400, 600)

        self.layout = QVBoxLayout(self)

        # Filter checkbox
        self.filter_check = QCheckBox("Show only checked items")
        self.filter_check.stateChanged.connect(self.apply_filter)
        self.layout.addWidget(self.filter_check)

        # Tree view
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setItemsExpandable(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.layout.addWidget(self.tree)


    def load_json(self, json_str):
        # Parse JSON
        try:
            self.data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON Error:", e)
            self.data = {}

        # Model & state tracking
        self.model = QStandardItemModel()
        self.cat_states = {}  # {category_name: 'all' | 'checked' | 'collapsed'}
        self.cat_items = {}  # {category_name: QStandardItem} for fast access

        self.setup_model()
        self.tree.setModel(self.model)
        self.tree.clicked.connect(self.on_clicked)
        self.model.itemChanged.connect(self.on_item_changed)

        # Initial expand
        self.tree.expandAll()

    def setup_model(self):
        for cat_name, items in self.data.items():
            # Category item
            cat_item = QStandardItem(cat_name)
            font = QFont()
            #font.setUnderline(True)
            cat_item.setFont(font)
            cat_item.setEditable(False)
            cat_item.setSelectable(True)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)

            self.model.appendRow(cat_item)
            self.cat_items[cat_name] = cat_item
            self.cat_states[cat_name] = 'all'  # default state

            # Add properties with checkboxes
            for prop in items:
                prop_item = QStandardItem(prop)
                prop_item.setCheckable(True)
                prop_item.setCheckState(Qt.Unchecked)
                prop_item.setEditable(False)
                cat_item.appendRow(prop_item)

            # spacer as last child of the category
            spacer = QStandardItem("")
            spacer.setEditable(False)
            spacer.setSelectable(False)
            spacer.setEnabled(False)
            cat_item.appendRow(spacer)

    def _set_spacer_visibility(self, cat_item: QStandardItem, visible: bool):
        spacer = cat_item.child(cat_item.rowCount() - 1)
        if spacer:
            idx = spacer.index()
            self.tree.setRowHidden(idx.row(), idx.parent(), not visible)
    def on_clicked(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if not item or not item.parent():  # Root-level item → category
            cat_name = item.text()
            if cat_name not in self.cat_states:
                return

            # Cycle: all → checked → collapsed → all
            current = self.cat_states[cat_name]
            if current == 'all':
                new_state = 'checked'
            elif current == 'checked':
                new_state = 'collapsed'
            else:  # collapsed
                new_state = 'all'

            self.cat_states[cat_name] = new_state
            self.update_category_display(cat_name)

    def update_category_display(self, cat_name):
        cat_item = self.cat_items[cat_name]
        cat_index = cat_item.index()
        state = self.cat_states[cat_name]

        if state == 'collapsed':
            self.tree.collapse(cat_index)
            self._set_spacer_visibility(cat_item, False)  # hidden
        else:
            self.tree.expand(cat_index)
            show_all = (state == 'all')  # <-- True only for 'all'
            for r in range(cat_item.rowCount() - 1):  # skip spacer
                child = cat_item.child(r)
                if child:
                    child_index = child.index()
                    hide = not show_all and child.checkState() != Qt.Checked
                    self.tree.setRowHidden(child_index.row(), cat_index, hide)

            self._set_spacer_visibility(cat_item, show_all)

        if self.filter_check.isChecked():
            self.apply_filter()

    def on_item_changed(self, item):
        if item.isCheckable():
            # Find category
            parent = item.parent()
            if parent:
                cat_name = parent.text()
                self.update_category_display(cat_name)
            self.apply_filter()  # refresh filter

    def apply_filter(self):
        filter_on = self.filter_check.isChecked()
        root = self.model.invisibleRootItem()

        for row in range(root.rowCount()):
            cat_item = root.child(row)
            if not cat_item or not cat_item.text():
                continue

            cat_name = cat_item.text()
            has_checked = any(
                cat_item.child(r).checkState() == Qt.Checked
                for r in range(cat_item.rowCount() - 1)  # ignore spacer
            )
            cat_index = cat_item.index()

            if filter_on:
                if has_checked:
                    self.tree.expand(cat_index)
                    # Show only checked children
                    for r in range(cat_item.rowCount() - 1):
                        child = cat_item.child(r)
                        child_index = child.index()
                        hide = child.checkState() != Qt.Checked
                        self.tree.setRowHidden(child_index.row(), cat_index, hide)

                    # SPACER: HIDDEN when global filter is on
                    self._set_spacer_visibility(cat_item, False)
                else:
                    self.tree.collapse(cat_index)
                    self._set_spacer_visibility(cat_item, False)
                    self.tree.setRowHidden(row, QModelIndex(), True)
            else:
                # Filter OFF → restore per-category state (including spacer logic)
                self.tree.setRowHidden(row, QModelIndex(), False)
                self.update_category_display(cat_name)

    def get_checked_items(self):
        """Return dict: {category: [list of checked properties]}"""
        result = {}
        for cat_name, cat_item in self.cat_items.items():
            checked = []
            for r in range(cat_item.rowCount()):
                child = cat_item.child(r)
                if child and child.checkState() == Qt.Checked:
                    checked.append(child.text())
            if checked:
                result[cat_name] = checked
        return result

    def uncheck(self):
        for cat_name, cat_item in self.cat_items.items():
            for r in range(cat_item.rowCount()):
                child = cat_item.child(r)
                if child.checkState() == Qt.Checked:
                    child.setCheckState(Qt.Unchecked)

    def set_property_checked(self, property_name: str, checked: bool = True):
        """
        Check or uncheck a property by its exact name.
        Example: widget.set_property_checked("contains_copper", True)
        """
        found = False
        for cat_name, cat_item in self.cat_items.items():
            for r in range(cat_item.rowCount()):
                child = cat_item.child(r)
                if child and child.text() == property_name:
                    new_state = Qt.Checked if checked else Qt.Unchecked
                    if child.checkState() != new_state:
                        child.setCheckState(new_state)
                    found = True
                    # Update display after change
                    self.update_category_display(cat_name)
                    if self.filter_check.isChecked():
                        self.apply_filter()
                    break
            if found:
                break
        return found  # Return True if property was found and updated

    def get_tag(self, property_name:str):
        for category in self.data:
            fields = self.data[category]
            if property_name in fields:
                return fields[property_name]
        return None

    def get_name(self, tag:str):
        for category in self.data:
            fields = self.data[category]
            for field in fields:
                if tag == fields[field]:
                    return field
        return None