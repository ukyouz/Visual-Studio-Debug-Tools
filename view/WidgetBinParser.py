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
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
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
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(parent=self.frame_3)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnHistory = QtWidgets.QToolButton(parent=self.frame_2)
        self.btnHistory.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btnHistory.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btnHistory.setObjectName("btnHistory")
        self.horizontalLayout.addWidget(self.btnHistory)
        spacerItem = QtWidgets.QSpacerItem(410, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame_2)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout.addWidget(self.btnToggleHex)
        self.label_3 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.spinParseCount = QtWidgets.QSpinBox(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
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
        self.btnParse = QtWidgets.QPushButton(parent=self.frame_2)
        self.btnParse.setAutoDefault(True)
        self.btnParse.setDefault(True)
        self.btnParse.setObjectName("btnParse")
        self.horizontalLayout.addWidget(self.btnParse)
        self.verticalLayout.addWidget(self.frame_2)
        self.treeView = QtWidgets.QTreeView(parent=self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.treeView.sizePolicy().hasHeightForWidth())
        self.treeView.setSizePolicy(sizePolicy)
        self.treeView.setStyleSheet("QTreeView::branch:open:has-children{border-image: url(:/icon/images/treeview/border-expand.png);}\n"
"QTreeView::branch:closed:has-children{border-image: url(:/icon/images/treeview/border-collapse.png);}\n"
"QTreeView::branch:has-siblings:!adjoins-item{border-image:url(:/icon/images/treeview/border-line.png);}\n"
"QTreeView::branch:has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-more.png);}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-end.png);}\n"
"QTreeView::branch:closed:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-collapse.png);}\n"
"QTreeView::branch:closed:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-collapse-more.png);}\n"
"QTreeView::branch:open:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-expand.png);}\n"
"QTreeView::branch:open:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-expand-more.png);}")
        self.treeView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.treeView.setAutoScroll(False)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.treeView.setIndentation(16)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.tableView = QtWidgets.QTableView(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.tableView.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.tableView.setShowGrid(False)
        self.tableView.setObjectName("tableView")
        self.tableView.verticalHeader().setDefaultSectionSize(24)
        self.verticalLayout_2.addWidget(self.splitter)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_2.setText(_translate("Form", "Struct"))
        self.label.setText(_translate("Form", "Offset"))
        self.btnHistory.setText(_translate("Form", "History"))
        self.btnToggleHex.setText(_translate("Form", "0x"))
        self.label_3.setText(_translate("Form", "Array"))
        self.spinParseCount.setToolTip(_translate("Form", "Parse Option: Count"))
        self.btnParse.setText(_translate("Form", "Parse"))
