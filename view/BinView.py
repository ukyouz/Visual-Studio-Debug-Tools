# Form implementation generated from reading ui file '.\view\BinView.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(511, 616)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter_2 = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter_2.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter_2.setObjectName("splitter_2")
        self.layoutWidget = QtWidgets.QWidget(parent=self.splitter_2)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(parent=self.layoutWidget)
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
        self.lineOffset = QtWidgets.QLineEdit(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineOffset.sizePolicy().hasHeightForWidth())
        self.lineOffset.setSizePolicy(sizePolicy)
        self.lineOffset.setObjectName("lineOffset")
        self.gridLayout.addWidget(self.lineOffset, 1, 1, 1, 1)
        self.btnParse = QtWidgets.QPushButton(parent=self.frame)
        self.btnParse.setAutoDefault(True)
        self.btnParse.setDefault(True)
        self.btnParse.setObjectName("btnParse")
        self.gridLayout.addWidget(self.btnParse, 1, 2, 1, 1)
        self.lineStruct = QtWidgets.QLineEdit(parent=self.frame)
        self.lineStruct.setFrame(True)
        self.lineStruct.setObjectName("lineStruct")
        self.gridLayout.addWidget(self.lineStruct, 0, 1, 1, 2)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(parent=self.layoutWidget)
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
        self.label_3 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.btnToggleHex = QtWidgets.QToolButton(parent=self.frame_2)
        self.btnToggleHex.setCheckable(True)
        self.btnToggleHex.setChecked(True)
        self.btnToggleHex.setAutoRaise(True)
        self.btnToggleHex.setObjectName("btnToggleHex")
        self.horizontalLayout.addWidget(self.btnToggleHex)
        self.verticalLayout.addWidget(self.frame_2)
        self.treeView = QtWidgets.QTreeView(parent=self.layoutWidget)
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
        self.treeView.setIndentation(16)
        self.treeView.setObjectName("treeView")
        self.verticalLayout.addWidget(self.treeView)
        self.tableView = QtWidgets.QTableView(parent=self.splitter_2)
        self.tableView.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.tableView.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.tableView.setShowGrid(False)
        self.tableView.setObjectName("tableView")
        self.tableView.verticalHeader().setDefaultSectionSize(24)
        self.verticalLayout_2.addWidget(self.splitter_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 511, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.actionOpen_File = QtGui.QAction(parent=MainWindow)
        self.actionOpen_File.setObjectName("actionOpen_File")
        self.actionQuit = QtGui.QAction(parent=MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionLoad_PDB_file = QtGui.QAction(parent=MainWindow)
        self.actionLoad_PDB_file.setObjectName("actionLoad_PDB_file")
        self.menuFile.addAction(self.actionOpen_File)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.actionQuit.triggered.connect(MainWindow.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.lineStruct, self.lineOffset)
        MainWindow.setTabOrder(self.lineOffset, self.btnParse)
        MainWindow.setTabOrder(self.btnParse, self.treeView)
        MainWindow.setTabOrder(self.treeView, self.tableView)
        MainWindow.setTabOrder(self.tableView, self.btnToggleHex)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_2.setText(_translate("MainWindow", "Struct"))
        self.label.setText(_translate("MainWindow", "Offset"))
        self.btnParse.setText(_translate("MainWindow", "Parse"))
        self.btnHistory.setText(_translate("MainWindow", "History"))
        self.label_3.setText(_translate("MainWindow", "Options:"))
        self.btnToggleHex.setText(_translate("MainWindow", "0x"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen_File.setText(_translate("MainWindow", "Open File..."))
        self.actionOpen_File.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionQuit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.actionLoad_PDB_file.setText(_translate("MainWindow", "Load PDB file..."))
