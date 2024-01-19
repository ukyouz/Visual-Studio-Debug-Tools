# Form implementation generated from reading ui file '.\view\WidgetExpression.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(340, 285)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        Form.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
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
        self.btnHistory.setAutoRaise(False)
        self.btnHistory.setObjectName("btnHistory")
        self.horizontalLayout.addWidget(self.btnHistory)
        self.lineStruct = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineStruct.setObjectName("lineStruct")
        self.horizontalLayout.addWidget(self.lineStruct)
        self.btnParse = QtWidgets.QToolButton(parent=self.frame_2)
        self.btnParse.setObjectName("btnParse")
        self.horizontalLayout.addWidget(self.btnParse)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.frame_2)
        self.treeView = QtWidgets.QTreeView(parent=Form)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        self.treeView.setFont(font)
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
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.frame = QtWidgets.QFrame(parent=Form)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnClear = QtWidgets.QToolButton(parent=self.frame)
        self.btnClear.setObjectName("btnClear")
        self.horizontalLayout_2.addWidget(self.btnClear)
        spacerItem = QtWidgets.QSpacerItem(40, 16, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout_2.addWidget(self.btnToggleHex)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnHistory.setText(_translate("Form", "History"))
        self.btnHistory.setShortcut(_translate("Form", "Ctrl+S, Ctrl+R, Ctrl+R"))
        self.lineStruct.setPlaceholderText(_translate("Form", "watch expression"))
        self.btnParse.setText(_translate("Form", "Parse"))
        self.btnClear.setText(_translate("Form", "Clear"))
        self.btnToggleHex.setText(_translate("Form", "0x"))
