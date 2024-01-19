# Form implementation generated from reading ui file '.\view\WidgetMemory.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(338, 297)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_2 = QtWidgets.QFrame(parent=Form)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnHistory = QtWidgets.QToolButton(parent=self.frame_2)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/action/images/vscode/history.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.btnHistory.setIcon(icon)
        self.btnHistory.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btnHistory.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btnHistory.setObjectName("btnHistory")
        self.horizontalLayout.addWidget(self.btnHistory)
        self.lineAddress = QtWidgets.QLineEdit(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineAddress.sizePolicy().hasHeightForWidth())
        self.lineAddress.setSizePolicy(sizePolicy)
        self.lineAddress.setObjectName("lineAddress")
        self.horizontalLayout.addWidget(self.lineAddress)
        self.lineSize = QtWidgets.QLineEdit(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineSize.sizePolicy().hasHeightForWidth())
        self.lineSize.setSizePolicy(sizePolicy)
        self.lineSize.setObjectName("lineSize")
        self.horizontalLayout.addWidget(self.lineSize)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.frame_2)
        self.frame_3 = QtWidgets.QFrame(parent=Form)
        self.frame_3.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.labelAddress = QtWidgets.QLabel(parent=self.frame_3)
        self.labelAddress.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.labelAddress.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.labelAddress.setIndent(2)
        self.labelAddress.setObjectName("labelAddress")
        self.verticalLayout.addWidget(self.labelAddress)
        self.tableView = QtWidgets.QTableView(parent=self.frame_3)
        self.tableView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.tableView.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.tableView.setShowGrid(False)
        self.tableView.setObjectName("tableView")
        self.tableView.verticalHeader().setDefaultSectionSize(18)
        self.tableView.verticalHeader().setMinimumSectionSize(18)
        self.verticalLayout.addWidget(self.tableView)
        self.verticalLayout_2.addWidget(self.frame_3)
        self.frame = QtWidgets.QFrame(parent=Form)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 16, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout_2.addWidget(self.btnToggleHex)
        self.verticalLayout_2.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnHistory.setText(_translate("Form", "History"))
        self.lineAddress.setPlaceholderText(_translate("Form", "address"))
        self.lineSize.setToolTip(_translate("Form", "Unit is byte"))
        self.lineSize.setPlaceholderText(_translate("Form", "size"))
        self.labelAddress.setText(_translate("Form", "0x000xxxxx"))
        self.btnToggleHex.setText(_translate("Form", "0x"))
