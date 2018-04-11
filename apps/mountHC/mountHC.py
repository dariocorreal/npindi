from PyQt5.QtWidgets import QApplication, QMainWindow, QAction

from indi.INDI import *
from indi.client.qt.indicommon import *
from indi.client.qt.drivermanager import DriverManager
from indi.client.qt.guimanager import GUIManager
from indi.client.qt.indilistener import INDIListener
from indi.client.qt.indistd import *
from indi.client.qt.inditelescope import Telescope

from ui_mountHC import *
# still have to wait for every props to be defined there: for can and has* functions
# not simple at all to explicitely wait for their associated props. So wait a while..
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scope = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(1000)
    def initUI(self):
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
            statusTip="Exit the application", triggered=self.quit)
        self.aboutAct = QAction("&About", self,
                    statusTip="Show the application's About box",
                    triggered=self.about)

        self.aboutQtAct = QAction("About &Qt", self,
                    statusTip="Show the Qt library's About box",
                    triggered=QApplication.instance().aboutQt)
        self.testMenu = self.menuBar().addMenu("&Settings")
        self.testMenu.addAction(self.exitAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)
        self.HC = mountHC(self)
        #self.centralFrame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        #self.centralSpacer = QSpacerItem(self.width(), self.height(), QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.HC)
        #self.centrallayout.addStretch(1)
        #self.centrallayout.addSpacerItem(self.centralSpacer)
        INDIListener.Instance().newTelescope.connect(self.addTimedTelescope)
        self.setWindowTitle('Mount Hand Controller Demo')
        self.show()
    def closeEvent(self, event):
        self.quit()
    def quit(self):
        DriverManager.Instance().close()
        GUIManager.Instance().close()
        self.close()
    def about(self):
        QMessageBox.about(self, 'Telescope API Test',
                'This <b>API</b> example demonstrates how to integrate '
                'a Telescope Controller in your Qt application.')
    @QtCore.pyqtSlot(ISD.GDInterface)
    def addTimedTelescope(self, gdi):
        self.timer.timeout.connect(lambda : self.addTelescope(gdi))
        self.timer.start()
    @QtCore.pyqtSlot(ISD.GDInterface)
    def addTelescope(self, gdi):
        if self.scope is not None:
            return
        self.scope = gdi
        self.HC.setTelescope(self.scope)
        self.timer.setInterval(1000)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.HC.update)
        self.timer.start()

import sys
app=QApplication(sys.argv)
mainWin=MainWindow()

DriverManager.Instance().show()
ag = DriverManager.Instance().getActionGroups()
for gkey, ggroup in ag.items():
    mainWin.menuBar().addSeparator()
    gmenu = mainWin.menuBar().addMenu(gkey)
    for a in ggroup.actions():
        gmenu.addAction(a)

rc=app.exec_()
sys.exit(rc)