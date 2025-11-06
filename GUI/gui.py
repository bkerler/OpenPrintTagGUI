# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QStatusBar,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget)

from GUI.customcombobox import ClearComboBox
from GUI.property_tree import PropertyFilterWidget

class Ui_OpenPrintTagGui(object):
    def setupUi(self, OpenPrintTagGui):
        if not OpenPrintTagGui.objectName():
            OpenPrintTagGui.setObjectName(u"OpenPrintTagGui")
        OpenPrintTagGui.resize(840, 576)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OpenPrintTagGui.sizePolicy().hasHeightForWidth())
        OpenPrintTagGui.setSizePolicy(sizePolicy)
        OpenPrintTagGui.setMinimumSize(QSize(0, 100))
        self.actionLoad = QAction(OpenPrintTagGui)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionSave = QAction(OpenPrintTagGui)
        self.actionSave.setObjectName(u"actionSave")
        self.centralwidget = QWidget(OpenPrintTagGui)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_8 = QGridLayout(self.centralwidget)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.basictab = QWidget()
        self.basictab.setObjectName(u"basictab")
        self.gridLayout = QGridLayout(self.basictab)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.expdatelabel = QLabel(self.basictab)
        self.expdatelabel.setObjectName(u"expdatelabel")

        self.horizontalLayout_18.addWidget(self.expdatelabel)

        self.expdateedit = QLineEdit(self.basictab)
        self.expdateedit.setObjectName(u"expdateedit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.expdateedit.sizePolicy().hasHeightForWidth())
        self.expdateedit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_18.addWidget(self.expdateedit)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_18, 8, 0, 1, 1)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.datelabel = QLabel(self.basictab)
        self.datelabel.setObjectName(u"datelabel")

        self.horizontalLayout_8.addWidget(self.datelabel)

        self.dateedit = QLineEdit(self.basictab)
        self.dateedit.setObjectName(u"dateedit")
        sizePolicy1.setHeightForWidth(self.dateedit.sizePolicy().hasHeightForWidth())
        self.dateedit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_8.addWidget(self.dateedit)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.horizontalLayout_8, 7, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.materialnamelabel = QLabel(self.basictab)
        self.materialnamelabel.setObjectName(u"materialnamelabel")

        self.horizontalLayout_4.addWidget(self.materialnamelabel)

        self.horizontalSpacer_16 = QSpacerItem(5, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_16)

        self.materialnamebox = ClearComboBox(self.basictab)
        self.materialnamebox.setObjectName(u"materialnamebox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(4)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.materialnamebox.sizePolicy().hasHeightForWidth())
        self.materialnamebox.setSizePolicy(sizePolicy2)

        self.horizontalLayout_4.addWidget(self.materialnamebox)


        self.gridLayout.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.primarycolorlabel = QLabel(self.basictab)
        self.primarycolorlabel.setObjectName(u"primarycolorlabel")

        self.horizontalLayout_5.addWidget(self.primarycolorlabel)

        self.horizontalSpacer_14 = QSpacerItem(10, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_14)

        self.colorlabel = QLabel(self.basictab)
        self.colorlabel.setObjectName(u"colorlabel")

        self.horizontalLayout_5.addWidget(self.colorlabel)

        self.primarycoloredit = QLineEdit(self.basictab)
        self.primarycoloredit.setObjectName(u"primarycoloredit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.primarycoloredit.sizePolicy().hasHeightForWidth())
        self.primarycoloredit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_5.addWidget(self.primarycoloredit)

        self.primarycolorraledit = QLineEdit(self.basictab)
        self.primarycolorraledit.setObjectName(u"primarycolorraledit")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(1)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.primarycolorraledit.sizePolicy().hasHeightForWidth())
        self.primarycolorraledit.setSizePolicy(sizePolicy4)

        self.horizontalLayout_5.addWidget(self.primarycolorraledit)

        self.colornamebox = QComboBox(self.basictab)
        self.colornamebox.setObjectName(u"colornamebox")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(3)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.colornamebox.sizePolicy().hasHeightForWidth())
        self.colornamebox.setSizePolicy(sizePolicy5)

        self.horizontalLayout_5.addWidget(self.colornamebox)

        self.td1sbutton = QPushButton(self.basictab)
        self.td1sbutton.setObjectName(u"td1sbutton")

        self.horizontalLayout_5.addWidget(self.td1sbutton)


        self.gridLayout.addLayout(self.horizontalLayout_5, 2, 0, 1, 1)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.gtinlabel = QLabel(self.basictab)
        self.gtinlabel.setObjectName(u"gtinlabel")

        self.horizontalLayout_7.addWidget(self.gtinlabel)

        self.gtinedit = QLineEdit(self.basictab)
        self.gtinedit.setObjectName(u"gtinedit")
        sizePolicy1.setHeightForWidth(self.gtinedit.sizePolicy().hasHeightForWidth())
        self.gtinedit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_7.addWidget(self.gtinedit)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_17)


        self.gridLayout.addLayout(self.horizontalLayout_7, 6, 0, 1, 1)

        self.readtagbtn = QPushButton(self.basictab)
        self.readtagbtn.setObjectName(u"readtagbtn")

        self.gridLayout.addWidget(self.readtagbtn, 10, 0, 1, 1)

        self.writetagbtn = QPushButton(self.basictab)
        self.writetagbtn.setObjectName(u"writetagbtn")

        self.gridLayout.addWidget(self.writetagbtn, 11, 0, 1, 1)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.transmissiondistancelabel = QLabel(self.basictab)
        self.transmissiondistancelabel.setObjectName(u"transmissiondistancelabel")

        self.horizontalLayout_9.addWidget(self.transmissiondistancelabel)

        self.horizontalSpacer_18 = QSpacerItem(50, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_18)

        self.transmissiondistanceedit = QLineEdit(self.basictab)
        self.transmissiondistanceedit.setObjectName(u"transmissiondistanceedit")
        sizePolicy1.setHeightForWidth(self.transmissiondistanceedit.sizePolicy().hasHeightForWidth())
        self.transmissiondistanceedit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_9.addWidget(self.transmissiondistanceedit)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_12)


        self.gridLayout.addLayout(self.horizontalLayout_9, 4, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.densitylabel = QLabel(self.basictab)
        self.densitylabel.setObjectName(u"densitylabel")

        self.horizontalLayout_6.addWidget(self.densitylabel)

        self.horizontalSpacer_13 = QSpacerItem(50, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_13)

        self.densityedit = QLineEdit(self.basictab)
        self.densityedit.setObjectName(u"densityedit")
        sizePolicy1.setHeightForWidth(self.densityedit.sizePolicy().hasHeightForWidth())
        self.densityedit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_6.addWidget(self.densityedit)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_11)


        self.gridLayout.addLayout(self.horizontalLayout_6, 5, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.brandnamelabel = QLabel(self.basictab)
        self.brandnamelabel.setObjectName(u"brandnamelabel")

        self.horizontalLayout_3.addWidget(self.brandnamelabel)

        self.horizontalSpacer_15 = QSpacerItem(10, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_15)

        self.brandnamebox = ClearComboBox(self.basictab)
        self.brandnamebox.setObjectName(u"brandnamebox")
        sizePolicy2.setHeightForWidth(self.brandnamebox.sizePolicy().hasHeightForWidth())
        self.brandnamebox.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.brandnamebox)


        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.primarycolorlabel_2 = QLabel(self.basictab)
        self.primarycolorlabel_2.setObjectName(u"primarycolorlabel_2")

        self.horizontalLayout_20.addWidget(self.primarycolorlabel_2)

        self.horizontalSpacer_21 = QSpacerItem(10, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_21)

        self.colorlabel_2 = QLabel(self.basictab)
        self.colorlabel_2.setObjectName(u"colorlabel_2")

        self.horizontalLayout_20.addWidget(self.colorlabel_2)

        self.secondary_colorlabel_0 = QLabel(self.basictab)
        self.secondary_colorlabel_0.setObjectName(u"secondary_colorlabel_0")

        self.horizontalLayout_20.addWidget(self.secondary_colorlabel_0)

        self.secondarycolor0edit_0 = QLineEdit(self.basictab)
        self.secondarycolor0edit_0.setObjectName(u"secondarycolor0edit_0")
        sizePolicy4.setHeightForWidth(self.secondarycolor0edit_0.sizePolicy().hasHeightForWidth())
        self.secondarycolor0edit_0.setSizePolicy(sizePolicy4)
        self.secondarycolor0edit_0.setMinimumSize(QSize(0, 0))
        self.secondarycolor0edit_0.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_20.addWidget(self.secondarycolor0edit_0)

        self.secondary_colorlabel_1 = QLabel(self.basictab)
        self.secondary_colorlabel_1.setObjectName(u"secondary_colorlabel_1")

        self.horizontalLayout_20.addWidget(self.secondary_colorlabel_1)

        self.secondarycolor0edit_1 = QLineEdit(self.basictab)
        self.secondarycolor0edit_1.setObjectName(u"secondarycolor0edit_1")
        sizePolicy3.setHeightForWidth(self.secondarycolor0edit_1.sizePolicy().hasHeightForWidth())
        self.secondarycolor0edit_1.setSizePolicy(sizePolicy3)
        self.secondarycolor0edit_1.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_20.addWidget(self.secondarycolor0edit_1)

        self.secondary_colorlabel_2 = QLabel(self.basictab)
        self.secondary_colorlabel_2.setObjectName(u"secondary_colorlabel_2")

        self.horizontalLayout_20.addWidget(self.secondary_colorlabel_2)

        self.secondarycolor0edit_2 = QLineEdit(self.basictab)
        self.secondarycolor0edit_2.setObjectName(u"secondarycolor0edit_2")
        sizePolicy3.setHeightForWidth(self.secondarycolor0edit_2.sizePolicy().hasHeightForWidth())
        self.secondarycolor0edit_2.setSizePolicy(sizePolicy3)
        self.secondarycolor0edit_2.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_20.addWidget(self.secondarycolor0edit_2)

        self.secondary_colorlabel_3 = QLabel(self.basictab)
        self.secondary_colorlabel_3.setObjectName(u"secondary_colorlabel_3")

        self.horizontalLayout_20.addWidget(self.secondary_colorlabel_3)

        self.secondarycolor0edit_3 = QLineEdit(self.basictab)
        self.secondarycolor0edit_3.setObjectName(u"secondarycolor0edit_3")
        sizePolicy3.setHeightForWidth(self.secondarycolor0edit_3.sizePolicy().hasHeightForWidth())
        self.secondarycolor0edit_3.setSizePolicy(sizePolicy3)
        self.secondarycolor0edit_3.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_20.addWidget(self.secondarycolor0edit_3)

        self.secondary_colorlabel_4 = QLabel(self.basictab)
        self.secondary_colorlabel_4.setObjectName(u"secondary_colorlabel_4")

        self.horizontalLayout_20.addWidget(self.secondary_colorlabel_4)

        self.secondarycolor0edit_4 = QLineEdit(self.basictab)
        self.secondarycolor0edit_4.setObjectName(u"secondarycolor0edit_4")
        sizePolicy3.setHeightForWidth(self.secondarycolor0edit_4.sizePolicy().hasHeightForWidth())
        self.secondarycolor0edit_4.setSizePolicy(sizePolicy3)
        self.secondarycolor0edit_4.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_20.addWidget(self.secondarycolor0edit_4)

        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_22)


        self.gridLayout.addLayout(self.horizontalLayout_20, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 9, 0, 1, 1)

        self.tabWidget.addTab(self.basictab, "")
        self.materialtab = QWidget()
        self.materialtab.setObjectName(u"materialtab")
        self.gridLayout_7 = QGridLayout(self.materialtab)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.materialpropgroup = QGroupBox(self.materialtab)
        self.materialpropgroup.setObjectName(u"materialpropgroup")
        self.gridLayout_4 = QGridLayout(self.materialpropgroup)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.matpropwidget = PropertyFilterWidget(self.materialpropgroup)
        self.matpropwidget.setObjectName(u"matpropwidget")

        self.gridLayout_4.addWidget(self.matpropwidget, 0, 0, 1, 1)


        self.gridLayout_7.addWidget(self.materialpropgroup, 1, 0, 1, 1)

        self.groupBox = QGroupBox(self.materialtab)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy6)
        self.groupBox.setMinimumSize(QSize(0, 100))
        self.groupBox.setMaximumSize(QSize(16777215, 100))
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.materialtypelabel = QLabel(self.groupBox)
        self.materialtypelabel.setObjectName(u"materialtypelabel")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy7.setHorizontalStretch(1)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.materialtypelabel.sizePolicy().hasHeightForWidth())
        self.materialtypelabel.setSizePolicy(sizePolicy7)

        self.horizontalLayout_2.addWidget(self.materialtypelabel)

        self.materialtypebox = ClearComboBox(self.groupBox)
        self.materialtypebox.setObjectName(u"materialtypebox")
        sizePolicy2.setHeightForWidth(self.materialtypebox.sizePolicy().hasHeightForWidth())
        self.materialtypebox.setSizePolicy(sizePolicy2)
        self.materialtypebox.setEditable(True)
        self.materialtypebox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.horizontalLayout_2.addWidget(self.materialtypebox)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.materialclasslabel = QLabel(self.groupBox)
        self.materialclasslabel.setObjectName(u"materialclasslabel")
        sizePolicy7.setHeightForWidth(self.materialclasslabel.sizePolicy().hasHeightForWidth())
        self.materialclasslabel.setSizePolicy(sizePolicy7)

        self.horizontalLayout.addWidget(self.materialclasslabel)

        self.materialclassbox = ClearComboBox(self.groupBox)
        self.materialclassbox.addItem("")
        self.materialclassbox.setObjectName(u"materialclassbox")
        sizePolicy2.setHeightForWidth(self.materialclassbox.sizePolicy().hasHeightForWidth())
        self.materialclassbox.setSizePolicy(sizePolicy2)
        self.materialclassbox.setEditable(True)
        self.materialclassbox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.materialclassbox.setFrame(True)

        self.horizontalLayout.addWidget(self.materialclassbox)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)


        self.gridLayout_7.addWidget(self.groupBox, 0, 0, 1, 1)

        self.tabWidget.addTab(self.materialtab, "")
        self.temperaturetab = QWidget()
        self.temperaturetab.setObjectName(u"temperaturetab")
        self.gridLayout_3 = QGridLayout(self.temperaturetab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.groupBox_3 = QGroupBox(self.temperaturetab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.minprinttemplabel = QLabel(self.groupBox_3)
        self.minprinttemplabel.setObjectName(u"minprinttemplabel")

        self.horizontalLayout_10.addWidget(self.minprinttemplabel)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_3)

        self.minprinttempbox = QSpinBox(self.groupBox_3)
        self.minprinttempbox.setObjectName(u"minprinttempbox")
        self.minprinttempbox.setMaximum(1200)
        self.minprinttempbox.setValue(240)

        self.horizontalLayout_10.addWidget(self.minprinttempbox)


        self.verticalLayout.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.maxprinttemplabel = QLabel(self.groupBox_3)
        self.maxprinttemplabel.setObjectName(u"maxprinttemplabel")

        self.horizontalLayout_11.addWidget(self.maxprinttemplabel)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_4)

        self.maxprinttempbox = QSpinBox(self.groupBox_3)
        self.maxprinttempbox.setObjectName(u"maxprinttempbox")
        self.maxprinttempbox.setMaximum(1200)
        self.maxprinttempbox.setValue(260)

        self.horizontalLayout_11.addWidget(self.maxprinttempbox)


        self.verticalLayout.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.preheattemplabel = QLabel(self.groupBox_3)
        self.preheattemplabel.setObjectName(u"preheattemplabel")

        self.horizontalLayout_12.addWidget(self.preheattemplabel)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_5)

        self.preheattempbox = QSpinBox(self.groupBox_3)
        self.preheattempbox.setObjectName(u"preheattempbox")
        self.preheattempbox.setMaximum(1200)
        self.preheattempbox.setValue(170)

        self.horizontalLayout_12.addWidget(self.preheattempbox)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.minbedtemplabel = QLabel(self.groupBox_3)
        self.minbedtemplabel.setObjectName(u"minbedtemplabel")

        self.horizontalLayout_13.addWidget(self.minbedtemplabel)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_6)

        self.minbedtempbox = QSpinBox(self.groupBox_3)
        self.minbedtempbox.setObjectName(u"minbedtempbox")
        self.minbedtempbox.setMaximum(1200)
        self.minbedtempbox.setValue(70)

        self.horizontalLayout_13.addWidget(self.minbedtempbox)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.maxbedtemplabel = QLabel(self.groupBox_3)
        self.maxbedtemplabel.setObjectName(u"maxbedtemplabel")

        self.horizontalLayout_14.addWidget(self.maxbedtemplabel)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_7)

        self.maxbedtempbox = QSpinBox(self.groupBox_3)
        self.maxbedtempbox.setObjectName(u"maxbedtempbox")
        self.maxbedtempbox.setMaximum(1200)
        self.maxbedtempbox.setValue(90)

        self.horizontalLayout_14.addWidget(self.maxbedtempbox)


        self.verticalLayout.addLayout(self.horizontalLayout_14)


        self.gridLayout_3.addWidget(self.groupBox_3, 0, 0, 1, 1)

        self.groupBox_6 = QGroupBox(self.temperaturetab)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.layoutWidget_9 = QWidget(self.groupBox_6)
        self.layoutWidget_9.setObjectName(u"layoutWidget_9")
        self.layoutWidget_9.setGeometry(QRect(10, 30, 337, 34))
        self.horizontalLayout_19 = QHBoxLayout(self.layoutWidget_9)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.diameterlabel = QLabel(self.layoutWidget_9)
        self.diameterlabel.setObjectName(u"diameterlabel")

        self.horizontalLayout_19.addWidget(self.diameterlabel)

        self.horizontalSpacer_20 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_20)

        self.diameteredit = QLineEdit(self.layoutWidget_9)
        self.diameteredit.setObjectName(u"diameteredit")

        self.horizontalLayout_19.addWidget(self.diameteredit)


        self.gridLayout_3.addWidget(self.groupBox_6, 0, 1, 1, 2)

        self.groupBox_4 = QGroupBox(self.temperaturetab)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_9 = QGridLayout(self.groupBox_4)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.nominalweightlabel = QLabel(self.groupBox_4)
        self.nominalweightlabel.setObjectName(u"nominalweightlabel")

        self.horizontalLayout_15.addWidget(self.nominalweightlabel)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_8)

        self.nominalweightbox = QSpinBox(self.groupBox_4)
        self.nominalweightbox.setObjectName(u"nominalweightbox")
        self.nominalweightbox.setMaximum(10000)
        self.nominalweightbox.setValue(1000)

        self.horizontalLayout_15.addWidget(self.nominalweightbox)


        self.gridLayout_9.addLayout(self.horizontalLayout_15, 0, 0, 1, 1)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.actualweightlabel = QLabel(self.groupBox_4)
        self.actualweightlabel.setObjectName(u"actualweightlabel")

        self.horizontalLayout_16.addWidget(self.actualweightlabel)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_9)

        self.actualweightbox = QSpinBox(self.groupBox_4)
        self.actualweightbox.setObjectName(u"actualweightbox")
        self.actualweightbox.setMaximum(10000)
        self.actualweightbox.setValue(1050)

        self.horizontalLayout_16.addWidget(self.actualweightbox)


        self.gridLayout_9.addLayout(self.horizontalLayout_16, 1, 0, 1, 1)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.emptycontainerlabel = QLabel(self.groupBox_4)
        self.emptycontainerlabel.setObjectName(u"emptycontainerlabel")

        self.horizontalLayout_17.addWidget(self.emptycontainerlabel)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_10)

        self.emptycontainerbox = QSpinBox(self.groupBox_4)
        self.emptycontainerbox.setObjectName(u"emptycontainerbox")
        self.emptycontainerbox.setMaximum(10000)
        self.emptycontainerbox.setValue(280)

        self.horizontalLayout_17.addWidget(self.emptycontainerbox)


        self.gridLayout_9.addLayout(self.horizontalLayout_17, 2, 0, 1, 1)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.consumedweightlabel = QLabel(self.groupBox_4)
        self.consumedweightlabel.setObjectName(u"consumedweightlabel")

        self.horizontalLayout_21.addWidget(self.consumedweightlabel)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_23)

        self.consumedweightbox = QSpinBox(self.groupBox_4)
        self.consumedweightbox.setObjectName(u"consumedweightbox")
        self.consumedweightbox.setMaximum(10000)
        self.consumedweightbox.setValue(0)

        self.horizontalLayout_21.addWidget(self.consumedweightbox)


        self.gridLayout_9.addLayout(self.horizontalLayout_21, 3, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_4, 1, 0, 1, 2)

        self.horizontalSpacer_19 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_19, 1, 2, 1, 1)

        self.tabWidget.addTab(self.temperaturetab, "")
        self.nfctab = QWidget()
        self.nfctab.setObjectName(u"nfctab")
        self.gridLayout_5 = QGridLayout(self.nfctab)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.groupBox_5 = QGroupBox(self.nfctab)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_6 = QGridLayout(self.groupBox_5)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.includeurlcheckbox = QCheckBox(self.groupBox_5)
        self.includeurlcheckbox.setObjectName(u"includeurlcheckbox")

        self.gridLayout_6.addWidget(self.includeurlcheckbox, 0, 0, 1, 1)

        self.urledit = QTextEdit(self.groupBox_5)
        self.urledit.setObjectName(u"urledit")

        self.gridLayout_6.addWidget(self.urledit, 1, 0, 1, 1)


        self.gridLayout_5.addWidget(self.groupBox_5, 0, 0, 1, 1)

        self.tabWidget.addTab(self.nfctab, "")

        self.gridLayout_8.addWidget(self.tabWidget, 0, 0, 1, 1)

        OpenPrintTagGui.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(OpenPrintTagGui)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 840, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        OpenPrintTagGui.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(OpenPrintTagGui)
        self.statusbar.setObjectName(u"statusbar")
        OpenPrintTagGui.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addAction(self.actionSave)

        self.retranslateUi(OpenPrintTagGui)

        self.tabWidget.setCurrentIndex(0)
        self.materialtypebox.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(OpenPrintTagGui)
    # setupUi

    def retranslateUi(self, OpenPrintTagGui):
        OpenPrintTagGui.setWindowTitle(QCoreApplication.translate("OpenPrintTagGui", u"OpenPrintTag - GUI", None))
        self.actionLoad.setText(QCoreApplication.translate("OpenPrintTagGui", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("OpenPrintTagGui", u"Save as ...", None))
        self.expdatelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Expiration Date", None))
        self.expdateedit.setPlaceholderText("")
        self.datelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Manufactured Date", None))
        self.dateedit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"04.11.2025", None))
        self.materialnamelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Material name", None))
        self.materialnamebox.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"PETG Jet Black", None))
        self.primarycolorlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Primary color", None))
        self.colorlabel.setText("")
        self.primarycoloredit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"#24292a", None))
        self.primarycolorraledit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"RAL2016", None))
        self.td1sbutton.setText(QCoreApplication.translate("OpenPrintTagGui", u"Detect via TD1S", None))
        self.gtinlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"GTIN (Global Trade Item Number)", None))
        self.gtinedit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"8594173675100", None))
        self.readtagbtn.setText(QCoreApplication.translate("OpenPrintTagGui", u"Read Tag", None))
        self.writetagbtn.setText(QCoreApplication.translate("OpenPrintTagGui", u"Write Tag", None))
        self.transmissiondistancelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Transmission distance / Opacity", None))
        self.transmissiondistanceedit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"0.9", None))
        self.densitylabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Density (g/cm\u00b3)", None))
        self.densityedit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"1,27", None))
        self.brandnamelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Brand name", None))
        self.brandnamebox.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"Prusament", None))
        self.primarycolorlabel_2.setText(QCoreApplication.translate("OpenPrintTagGui", u"Secondary colors", None))
        self.colorlabel_2.setText("")
        self.secondary_colorlabel_0.setText("")
        self.secondarycolor0edit_0.setPlaceholderText("")
        self.secondary_colorlabel_1.setText("")
        self.secondarycolor0edit_1.setPlaceholderText("")
        self.secondary_colorlabel_2.setText("")
        self.secondarycolor0edit_2.setPlaceholderText("")
        self.secondary_colorlabel_3.setText("")
        self.secondarycolor0edit_3.setPlaceholderText("")
        self.secondary_colorlabel_4.setText("")
        self.secondarycolor0edit_4.setPlaceholderText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.basictab), QCoreApplication.translate("OpenPrintTagGui", u"Basic Info", None))
        self.materialpropgroup.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"Material Properties and Tags", None))
        self.groupBox.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"Material classification", None))
        self.materialtypelabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Material type", None))
        self.materialtypebox.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"PLA - Polylactic Acid", None))
        self.materialclasslabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Material class", None))
        self.materialclassbox.setItemText(0, QCoreApplication.translate("OpenPrintTagGui", u"FFF - Filament", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.materialtab), QCoreApplication.translate("OpenPrintTagGui", u"Material", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"Temperature", None))
        self.minprinttemplabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Min Print Temperature (\u00b0C)", None))
        self.maxprinttemplabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Max Print Temperature (\u00b0C)", None))
        self.preheattemplabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Preheat Temperature (\u00b0C)", None))
        self.minbedtemplabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Min Bed Temperature (\u00b0C)", None))
        self.maxbedtemplabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Max Bed Temperature (\u00b0C)", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"Specification", None))
        self.diameterlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Diameter (mm)", None))
        self.diameteredit.setText(QCoreApplication.translate("OpenPrintTagGui", u"1.75", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"Weight Information", None))
        self.nominalweightlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Nominal Weight (g)", None))
        self.actualweightlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Actual Weight (g)", None))
        self.emptycontainerlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Empty Container/Spool (g)", None))
        self.consumedweightlabel.setText(QCoreApplication.translate("OpenPrintTagGui", u"Consumed weight (g)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.temperaturetab), QCoreApplication.translate("OpenPrintTagGui", u"Temperature, Weight, Speed", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"NFC Tag Options", None))
        self.includeurlcheckbox.setText(QCoreApplication.translate("OpenPrintTagGui", u"Include URL Record", None))
        self.urledit.setPlaceholderText(QCoreApplication.translate("OpenPrintTagGui", u"https://www.prusa3d.com/cs/produkt/prusament-petg-jet-black-1kg/", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.nfctab), QCoreApplication.translate("OpenPrintTagGui", u"NFC Tag", None))
        self.menuFile.setTitle(QCoreApplication.translate("OpenPrintTagGui", u"File", None))
    # retranslateUi

