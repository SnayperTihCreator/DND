# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dm.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.formLayout = QFormLayout(Form)
        self.formLayout.setObjectName(u"formLayout")
        self.labelLogin = QLabel(Form)
        self.labelLogin.setObjectName(u"labelLogin")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.labelLogin)

        self.lineEditLogin = QLineEdit(Form)
        self.lineEditLogin.setObjectName(u"lineEditLogin")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEditLogin)

        self.labelRemote = QLabel(Form)
        self.labelRemote.setObjectName(u"labelRemote")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelRemote)

        self.checkBoxRemote = QCheckBox(Form)
        self.checkBoxRemote.setObjectName(u"checkBoxRemote")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.checkBoxRemote)

        self.directPanel = QFrame(Form)
        self.directPanel.setObjectName(u"directPanel")
        self.directPanel.setFrameShape(QFrame.Shape.NoFrame)
        self.directPanel.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout = QVBoxLayout(self.directPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.directPanel)

        self.pages = QStackedWidget(Form)
        self.pages.setObjectName(u"pages")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.verticalLayout_2 = QVBoxLayout(self.page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.btnCreate = QPushButton(self.page)
        self.btnCreate.setObjectName(u"btnCreate")

        self.verticalLayout_2.addWidget(self.btnCreate)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.pages.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.formLayout_3 = QFormLayout(self.page_2)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.labelIp = QLabel(self.page_2)
        self.labelIp.setObjectName(u"labelIp")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.labelIp)

        self.lineEditIp = QLineEdit(self.page_2)
        self.lineEditIp.setObjectName(u"lineEditIp")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEditIp)

        self.labelMasterToken = QLabel(self.page_2)
        self.labelMasterToken.setObjectName(u"labelMasterToken")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelMasterToken)

        self.lineEditMasterToken = QLineEdit(self.page_2)
        self.lineEditMasterToken.setObjectName(u"lineEditMasterToken")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEditMasterToken)

        self.btnConnect = QPushButton(self.page_2)
        self.btnConnect.setObjectName(u"btnConnect")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.btnConnect)

        self.pages.addWidget(self.page_2)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.pages)


        self.retranslateUi(Form)

        self.pages.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelLogin.setText(QCoreApplication.translate("Form", u"Login", None))
        self.lineEditLogin.setText(QCoreApplication.translate("Form", u"DungeonMaster", None))
        self.labelRemote.setText(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0435\u043d\u043d\u044b\u0439 \u0441\u0435\u0440\u0432\u0435\u0440", None))
        self.btnCreate.setText(QCoreApplication.translate("Form", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.labelIp.setText(QCoreApplication.translate("Form", u"IP", None))
        self.lineEditIp.setText(QCoreApplication.translate("Form", u"127.0.0.1", None))
        self.lineEditIp.setPlaceholderText(QCoreApplication.translate("Form", u"x.x.x.x", None))
        self.labelMasterToken.setText(QCoreApplication.translate("Form", u"MASTER Token", None))
        self.lineEditMasterToken.setPlaceholderText(QCoreApplication.translate("Form", u"MASTER TOKEN", None))
        self.btnConnect.setText(QCoreApplication.translate("Form", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u0441\u044f", None))
    # retranslateUi

