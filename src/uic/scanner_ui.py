# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scanner.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_Scanner(object):
    def setupUi(self, Scanner):
        if not Scanner.objectName():
            Scanner.setObjectName(u"Scanner")
        Scanner.resize(739, 474)
        self.horizontalLayout = QHBoxLayout(Scanner)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame_2 = QFrame(Scanner)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.listWidgetTables = QListWidget(self.frame_2)
        self.listWidgetTables.setObjectName(u"listWidgetTables")

        self.verticalLayout.addWidget(self.listWidgetTables)

        self.btnUpdateTables = QPushButton(self.frame_2)
        self.btnUpdateTables.setObjectName(u"btnUpdateTables")

        self.verticalLayout.addWidget(self.btnUpdateTables)


        self.horizontalLayout.addWidget(self.frame_2)

        self.frame = QFrame(Scanner)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.label_2)

        self.labelIp = QLabel(self.frame)
        self.labelIp.setObjectName(u"labelIp")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelIp)

        self.lineEditIp = QLineEdit(self.frame)
        self.lineEditIp.setObjectName(u"lineEditIp")
        self.lineEditIp.setClearButtonEnabled(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEditIp)

        self.labelPort = QLabel(self.frame)
        self.labelPort.setObjectName(u"labelPort")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.labelPort)

        self.spinPort = QSpinBox(self.frame)
        self.spinPort.setObjectName(u"spinPort")
        self.spinPort.setMinimum(8765)
        self.spinPort.setMaximum(8780)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spinPort)

        self.btnConnect = QPushButton(self.frame)
        self.btnConnect.setObjectName(u"btnConnect")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.btnConnect)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(4, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer)

        self.labelLogin = QLabel(self.frame)
        self.labelLogin.setObjectName(u"labelLogin")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.labelLogin)

        self.lineEditLogin = QLineEdit(self.frame)
        self.lineEditLogin.setObjectName(u"lineEditLogin")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.lineEditLogin)


        self.horizontalLayout.addWidget(self.frame)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)

        self.retranslateUi(Scanner)

        QMetaObject.connectSlotsByName(Scanner)
    # setupUi

    def retranslateUi(self, Scanner):
        Scanner.setWindowTitle(QCoreApplication.translate("Scanner", u"Form", None))
        self.label.setText(QCoreApplication.translate("Scanner", u"\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435  \u0441\u0442\u043e\u043b\u044b \u0432 \u0441\u0435\u0442\u0438 (LAN/VPN)", None))
        self.btnUpdateTables.setText(QCoreApplication.translate("Scanner", u"\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a", None))
        self.label_2.setText(QCoreApplication.translate("Scanner", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u0441\u044f \u043d\u0430 \u043f\u0440\u044f\u043c\u0443\u044e", None))
        self.labelIp.setText(QCoreApplication.translate("Scanner", u"IP", None))
        self.lineEditIp.setPlaceholderText(QCoreApplication.translate("Scanner", u"IP \u0430\u0434\u0440\u0435\u0441 \u043c\u0430\u0441\u0442\u0435\u0440\u0430", None))
        self.labelPort.setText(QCoreApplication.translate("Scanner", u"\u041f\u043e\u0440\u0442", None))
        self.btnConnect.setText(QCoreApplication.translate("Scanner", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u0441\u044f", None))
        self.labelLogin.setText(QCoreApplication.translate("Scanner", u"Login", None))
        self.lineEditLogin.setText(QCoreApplication.translate("Scanner", u"DndGame", None))
    # retranslateUi

