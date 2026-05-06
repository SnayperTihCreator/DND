# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_create_token.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

from views.awidgets import AdvancedTextEdit

class Ui_CreateToken(object):
    def setupUi(self, CreateToken):
        if not CreateToken.objectName():
            CreateToken.setObjectName(u"CreateToken")
        CreateToken.resize(400, 300)
        self.formLayout = QFormLayout(CreateToken)
        self.formLayout.setObjectName(u"formLayout")
        self.labelName = QLabel(CreateToken)
        self.labelName.setObjectName(u"labelName")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.labelName)

        self.lineEditName = QLineEdit(CreateToken)
        self.lineEditName.setObjectName(u"lineEditName")
        self.lineEditName.setClearButtonEnabled(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEditName)

        self.labelUnique = QLabel(CreateToken)
        self.labelUnique.setObjectName(u"labelUnique")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.labelUnique)

        self.labelSize = QLabel(CreateToken)
        self.labelSize.setObjectName(u"labelSize")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.labelSize)

        self.comboBoxScale = QComboBox(CreateToken)
        self.comboBoxScale.addItem("")
        self.comboBoxScale.addItem(u"\u041c\u0430\u043b\u0435\u043d\u044c\u043a\u0438\u0439")
        self.comboBoxScale.addItem("")
        self.comboBoxScale.addItem("")
        self.comboBoxScale.addItem("")
        self.comboBoxScale.addItem("")
        self.comboBoxScale.setObjectName(u"comboBoxScale")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.comboBoxScale)

        self.checkBoxUnique = QCheckBox(CreateToken)
        self.checkBoxUnique.setObjectName(u"checkBoxUnique")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.checkBoxUnique)

        self.textEditDescription = AdvancedTextEdit(CreateToken)
        self.textEditDescription.setObjectName(u"textEditDescription")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.textEditDescription)

        self.btnBox = QDialogButtonBox(CreateToken)
        self.btnBox.setObjectName(u"btnBox")
        self.btnBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.SpanningRole, self.btnBox)

        self.btnSelectAvatar = QPushButton(CreateToken)
        self.btnSelectAvatar.setObjectName(u"btnSelectAvatar")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.btnSelectAvatar)

        self.label = QLabel(CreateToken)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(6, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer)


        self.retranslateUi(CreateToken)

        self.comboBoxScale.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(CreateToken)
    # setupUi

    def retranslateUi(self, CreateToken):
        CreateToken.setWindowTitle(QCoreApplication.translate("CreateToken", u"\u0421\u043e\u0437\u0434\u0430\u043d\u0438\u0435 \u0442\u043e\u043a\u0435\u043d\u0430", None))
        self.labelName.setText(QCoreApplication.translate("CreateToken", u"\u0418\u043c\u044f \u0442\u043e\u043a\u0435\u043d\u0430", None))
        self.labelUnique.setText(QCoreApplication.translate("CreateToken", u"\u0423\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0439", None))
        self.labelSize.setText(QCoreApplication.translate("CreateToken", u"\u0420\u0430\u0437\u043c\u0435\u0440", None))
        self.comboBoxScale.setItemText(0, QCoreApplication.translate("CreateToken", u"\u041c\u0435\u043b\u043a\u0438\u0439", None))
        self.comboBoxScale.setItemText(2, QCoreApplication.translate("CreateToken", u"\u041e\u0431\u044b\u0447\u043d\u044b\u0439", None))
        self.comboBoxScale.setItemText(3, QCoreApplication.translate("CreateToken", u"\u0411\u043e\u043b\u044c\u0448\u043e\u0439", None))
        self.comboBoxScale.setItemText(4, QCoreApplication.translate("CreateToken", u"\u041e\u0433\u0440\u043e\u043c\u043d\u044b\u0439", None))
        self.comboBoxScale.setItemText(5, QCoreApplication.translate("CreateToken", u"\u0413\u0438\u0433\u0430\u043d\u0441\u043a\u0438\u0439", None))

        self.checkBoxUnique.setText("")
        self.btnSelectAvatar.setText(QCoreApplication.translate("CreateToken", u"Select Avatar", None))
        self.label.setText(QCoreApplication.translate("CreateToken", u"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u0434\u043b\u044f {}", None))
    # retranslateUi

