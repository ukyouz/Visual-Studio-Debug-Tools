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
        MainWindow.resize(800, 600)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mdiArea = QtWidgets.QMdiArea(parent=self.centralwidget)
        self.mdiArea.setObjectName("mdiArea")
        self.verticalLayout.addWidget(self.mdiArea)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dockWidget = QtWidgets.QDockWidget(parent=MainWindow)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame = QtWidgets.QFrame(parent=self.dockWidgetContents)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(1, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnOpenFiles = QtWidgets.QToolButton(parent=self.frame)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/action/images/vswin2019/OpenFile_16x.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.btnOpenFiles.setIcon(icon)
        self.btnOpenFiles.setIconSize(QtCore.QSize(16, 16))
        self.btnOpenFiles.setAutoRaise(True)
        self.btnOpenFiles.setObjectName("btnOpenFiles")
        self.horizontalLayout.addWidget(self.btnOpenFiles)
        spacerItem = QtWidgets.QSpacerItem(63, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.checkOpenedOnly = QtWidgets.QCheckBox(parent=self.frame)
        self.checkOpenedOnly.setObjectName("checkOpenedOnly")
        self.horizontalLayout.addWidget(self.checkOpenedOnly)
        self.verticalLayout_2.addWidget(self.frame)
        self.treeExplorer = QtWidgets.QTreeView(parent=self.dockWidgetContents)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        palette.setBrush(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Base, brush)
        self.treeExplorer.setPalette(palette)
        self.treeExplorer.setAutoFillBackground(False)
        self.treeExplorer.setStyleSheet("QTreeView::branch:open:has-children{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:closed:has-children{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:has-siblings:!adjoins-item{border-image:url(:/icon/images/treeview/border-line.png) 0;}\n"
"QTreeView::branch:has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-more.png) 0;}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item{border-image:url(:/icon/images/treeview/border-end.png) 0;}\n"
"QTreeView::branch:closed:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-collapse.png) 0;}\n"
"QTreeView::branch:closed:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-collapse-more.png) 0;}\n"
"QTreeView::branch:open:has-children:!has-siblings{border-image: url(:/icon/images/treeview/border-expand.png) 0;}\n"
"QTreeView::branch:open:has-children:has-siblings{border-image: url(:/icon/images/treeview/border-expand-more.png) 0;}\n"
"")
        self.treeExplorer.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.treeExplorer.setIconSize(QtCore.QSize(16, 22))
        self.treeExplorer.setIndentation(16)
        self.treeExplorer.setObjectName("treeExplorer")
        self.treeExplorer.header().setVisible(False)
        self.treeExplorer.header().setMinimumSectionSize(16)
        self.verticalLayout_2.addWidget(self.treeExplorer)
        self.dockWidget.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget)
        self.actionOpen_File = QtGui.QAction(parent=MainWindow)
        self.actionOpen_File.setObjectName("actionOpen_File")
        self.actionQuit = QtGui.QAction(parent=MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.menuFile.addAction(self.actionOpen_File)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.actionQuit.triggered.connect(MainWindow.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.dockWidget.setWindowTitle(_translate("MainWindow", "Explorer"))
        self.btnOpenFiles.setText(_translate("MainWindow", "Open File"))
        self.btnOpenFiles.setShortcut(_translate("MainWindow", "Ctrl+S, Ctrl+R"))
        self.checkOpenedOnly.setText(_translate("MainWindow", "Opened Only"))
        self.actionOpen_File.setText(_translate("MainWindow", "Open File..."))
        self.actionOpen_File.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionQuit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
