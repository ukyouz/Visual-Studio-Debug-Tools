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
        icon.addPixmap(QtGui.QPixmap(":/action/images/vswin2019/History_16x.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.btnHistory.setIcon(icon)
        self.btnHistory.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btnHistory.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btnHistory.setAutoRaise(False)
        self.btnHistory.setObjectName("btnHistory")
        self.horizontalLayout.addWidget(self.btnHistory)
        self.lineStruct = QtWidgets.QLineEdit(parent=self.frame_2)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        self.lineStruct.setFont(font)
        self.lineStruct.setObjectName("lineStruct")
        self.horizontalLayout.addWidget(self.lineStruct)
        self.btnParse = QtWidgets.QToolButton(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnParse.sizePolicy().hasHeightForWidth())
        self.btnParse.setSizePolicy(sizePolicy)
        self.btnParse.setObjectName("btnParse")
        self.horizontalLayout.addWidget(self.btnParse)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnToggleHex.sizePolicy().hasHeightForWidth())
        self.btnToggleHex.setSizePolicy(sizePolicy)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout_3.addWidget(self.btnToggleHex)
        self.verticalLayout.addWidget(self.frame_2)
        self.treeView = QtWidgets.QTreeView(parent=Form)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        self.treeView.setFont(font)
        self.treeView.setStyleSheet("QHeaderView::section {border: 0; border-right: 1px solid #d8d8d8; border-bottom: 1px solid #d8d8d8; padding: 0px 3px;}\n"
"QTreeView::branch:open:has-children{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:closed:has-children{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:has-siblings:!adjoins-item{border-image:url(:/icon/images/treeview/border-line.png) 0;}\n"
"QTreeView::branch:has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-more.png) 0;}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-end.png) 0;}\n"
"QTreeView::branch:closed:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:closed:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-collapse-more.png) 0;}\n"
"QTreeView::branch:open:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:open:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-expand-more.png) 0;}\n"
"QTreeView::item{  padding: 0px 6px; }")
        self.treeView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIconSize(QtCore.QSize(16, 22))
        self.treeView.setIndentation(16)
        self.treeView.setUniformRowHeights(True)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnHistory.setText(_translate("Form", "History"))
        self.btnHistory.setShortcut(_translate("Form", "Ctrl+S, Ctrl+R, Ctrl+R"))
        self.lineStruct.setPlaceholderText(_translate("Form", "watch expression"))
        self.btnParse.setText(_translate("Form", "Add"))
        self.btnToggleHex.setText(_translate("Form", "0x"))
