# Form implementation generated from reading ui file '.\view\WidgetBinParser.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(563, 570)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        Form.setFont(font)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(parent=Form)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.frame_3 = QtWidgets.QFrame(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.frame = QtWidgets.QFrame(parent=self.frame_3)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(parent=self.frame)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.frame)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.lineStruct = QtWidgets.QLineEdit(parent=self.frame)
        self.lineStruct.setFrame(True)
        self.lineStruct.setObjectName("lineStruct")
        self.gridLayout.addWidget(self.lineStruct, 0, 1, 1, 2)
        self.lineOffset = QtWidgets.QLineEdit(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineOffset.sizePolicy().hasHeightForWidth())
        self.lineOffset.setSizePolicy(sizePolicy)
        self.lineOffset.setObjectName("lineOffset")
        self.gridLayout.addWidget(self.lineOffset, 1, 1, 1, 2)
        self.verticalLayout_3.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(parent=self.frame_3)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnHistory = QtWidgets.QToolButton(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnHistory.sizePolicy().hasHeightForWidth())
        self.btnHistory.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/action/images/vswin2019/History_16x.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.btnHistory.setIcon(icon)
        self.btnHistory.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btnHistory.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btnHistory.setObjectName("btnHistory")
        self.horizontalLayout.addWidget(self.btnHistory)
        spacerItem = QtWidgets.QSpacerItem(410, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnToggleHex.sizePolicy().hasHeightForWidth())
        self.btnToggleHex.setSizePolicy(sizePolicy)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout.addWidget(self.btnToggleHex)
        self.label_3 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.spinParseCount = QtWidgets.QSpinBox(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinParseCount.sizePolicy().hasHeightForWidth())
        self.spinParseCount.setSizePolicy(sizePolicy)
        self.spinParseCount.setMinimumSize(QtCore.QSize(40, 0))
        self.spinParseCount.setSuffix("")
        self.spinParseCount.setPrefix("")
        self.spinParseCount.setMaximum(999999999)
        self.spinParseCount.setProperty("value", 1)
        self.spinParseCount.setObjectName("spinParseCount")
        self.horizontalLayout.addWidget(self.spinParseCount)
        self.checkParseTable = QtWidgets.QCheckBox(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkParseTable.sizePolicy().hasHeightForWidth())
        self.checkParseTable.setSizePolicy(sizePolicy)
        self.checkParseTable.setMinimumSize(QtCore.QSize(0, 0))
        self.checkParseTable.setObjectName("checkParseTable")
        self.horizontalLayout.addWidget(self.checkParseTable)
        self.btnParse = QtWidgets.QPushButton(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnParse.sizePolicy().hasHeightForWidth())
        self.btnParse.setSizePolicy(sizePolicy)
        self.btnParse.setAutoDefault(True)
        self.btnParse.setDefault(True)
        self.btnParse.setObjectName("btnParse")
        self.horizontalLayout.addWidget(self.btnParse)
        self.verticalLayout_3.addWidget(self.frame_2)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setObjectName("stackedWidget")
        self.pageTree = QtWidgets.QWidget()
        self.pageTree.setObjectName("pageTree")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.pageTree)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeView = QtWidgets.QTreeView(parent=self.pageTree)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        self.treeView.setFont(font)
        self.treeView.setStyleSheet("QHeaderView::section {border: 0; border-right: 1px solid #d8d8d8; border-bottom: 1px solid #d8d8d8;}\n"
"QTreeView::branch:open:has-children{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:closed:has-children{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:has-siblings:!adjoins-item{border-image:url(:/icon/images/treeview/border-line.png) 0;}\n"
"QTreeView::branch:has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-more.png) 0;}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-end.png) 0;}\n"
"QTreeView::branch:closed:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:closed:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-collapse-more.png) 0;}\n"
"QTreeView::branch:open:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:open:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-expand-more.png) 0;}\n"
"")
        self.treeView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIconSize(QtCore.QSize(16, 22))
        self.treeView.setIndentation(16)
        self.treeView.setUniformRowHeights(True)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.stackedWidget.addWidget(self.pageTree)
        self.pageTable = QtWidgets.QWidget()
        self.pageTable.setObjectName("pageTable")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.pageTable)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tableView = QtWidgets.QTableView(parent=self.pageTable)
        self.tableView.setStyleSheet("QHeaderView::section {border: 0; border-right: 1px solid #d8d8d8; border-bottom: 1px solid #d8d8d8;}")
        self.tableView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setWordWrap(False)
        self.tableView.setObjectName("tableView")
        self.tableView.verticalHeader().setDefaultSectionSize(22)
        self.verticalLayout_4.addWidget(self.tableView)
        self.stackedWidget.addWidget(self.pageTable)
        self.verticalLayout_3.addWidget(self.stackedWidget)
        self.tableMemory = QtWidgets.QTableView(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableMemory.sizePolicy().hasHeightForWidth())
        self.tableMemory.setSizePolicy(sizePolicy)
        self.tableMemory.setStyleSheet("QHeaderView::section {border: 0; border-right: 1px solid #d8d8d8; border-bottom: 1px solid #d8d8d8;}")
        self.tableMemory.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.tableMemory.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.tableMemory.setShowGrid(False)
        self.tableMemory.setWordWrap(False)
        self.tableMemory.setObjectName("tableMemory")
        self.tableMemory.horizontalHeader().setStretchLastSection(True)
        self.tableMemory.verticalHeader().setDefaultSectionSize(25)
        self.verticalLayout_2.addWidget(self.splitter)

        self.retranslateUi(Form)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_2.setText(_translate("Form", "Struct"))
        self.label.setText(_translate("Form", "Offset"))
        self.btnHistory.setText(_translate("Form", "History"))
        self.btnToggleHex.setText(_translate("Form", "0x"))
        self.label_3.setText(_translate("Form", "Count"))
        self.spinParseCount.setToolTip(_translate("Form", "Parse Option: Count"))
        self.checkParseTable.setText(_translate("Form", "Table"))
        self.btnParse.setText(_translate("Form", "Parse"))
