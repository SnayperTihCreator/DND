# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'launcher.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

from gui.launcher.dm import DmPage
from gui.launcher.scanner import ScannerPage

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.action_update = QAction(MainWindow)
        self.action_update.setObjectName(u"action_update")
        self.action_about = QAction(MainWindow)
        self.action_about.setObjectName(u"action_about")
        self.action_qt = QAction(MainWindow)
        self.action_qt.setObjectName(u"action_qt")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabs = QTabWidget(self.centralwidget)
        self.tabs.setObjectName(u"tabs")
        self.scannerPage = ScannerPage()
        self.scannerPage.setObjectName(u"scannerPage")
        self.tabs.addTab(self.scannerPage, "")
        self.dmPage = DmPage()
        self.dmPage.setObjectName(u"dmPage")
        self.tabs.addTab(self.dmPage, "")

        self.verticalLayout.addWidget(self.tabs)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menu.addAction(self.action_update)
        self.menu.addAction(self.action_about)
        self.menu.addAction(self.action_qt)

        self.retranslateUi(MainWindow)

        self.tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"D&D Launcher", None))
        self.action_update.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", None))
        self.action_about.setText(QCoreApplication.translate("MainWindow", u"\u041e \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0435", None))
        self.action_qt.setText(QCoreApplication.translate("MainWindow", u"\u041e PySide6", None))
        self.tabs.setTabText(self.tabs.indexOf(self.scannerPage), QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0439\u0442\u0438 \u0438\u0433\u0440\u0443", None))
        self.tabs.setTabText(self.tabs.indexOf(self.dmPage), QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0441\u0442\u043e\u043b", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435", None))
    # retranslateUi

