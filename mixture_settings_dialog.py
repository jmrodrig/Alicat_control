# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mixture_settings_dialog.ui'
#
# Created: Mon Jul 22 16:30:19 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MixtureSettingsDialog(object):
    def setupUi(self, MixtureSettingsDialog):
        MixtureSettingsDialog.setObjectName(_fromUtf8("MixtureSettingsDialog"))
        MixtureSettingsDialog.resize(393, 190)
        self.label = QtGui.QLabel(MixtureSettingsDialog)
        self.label.setGeometry(QtCore.QRect(40, 40, 71, 21))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(MixtureSettingsDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 80, 91, 21))
        self.label_2.setText(_fromUtf8(""))
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(MixtureSettingsDialog)
        self.label_3.setGeometry(QtCore.QRect(40, 100, 71, 21))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(MixtureSettingsDialog)
        self.label_4.setGeometry(QtCore.QRect(40, 140, 71, 21))
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.inputFlowA = QtGui.QComboBox(MixtureSettingsDialog)
        self.inputFlowA.setGeometry(QtCore.QRect(130, 100, 81, 22))
        self.inputFlowA.setObjectName(_fromUtf8("inputFlowA"))
        self.inputFlowB = QtGui.QComboBox(MixtureSettingsDialog)
        self.inputFlowB.setGeometry(QtCore.QRect(130, 140, 81, 22))
        self.inputFlowB.setObjectName(_fromUtf8("inputFlowB"))
        self.inputMixtureName = QtGui.QLineEdit(MixtureSettingsDialog)
        self.inputMixtureName.setGeometry(QtCore.QRect(130, 40, 113, 20))
        self.inputMixtureName.setText(_fromUtf8(""))
        self.inputMixtureName.setObjectName(_fromUtf8("inputMixtureName"))
        self.inputIsReactingMixture = QtGui.QCheckBox(MixtureSettingsDialog)
        self.inputIsReactingMixture.setGeometry(QtCore.QRect(130, 70, 111, 21))
        self.inputIsReactingMixture.setObjectName(_fromUtf8("inputIsReactingMixture"))
        self.labelFlowA = QtGui.QLabel(MixtureSettingsDialog)
        self.labelFlowA.setGeometry(QtCore.QRect(230, 100, 111, 21))
        self.labelFlowA.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.labelFlowA.setObjectName(_fromUtf8("labelFlowA"))
        self.labelFlowB = QtGui.QLabel(MixtureSettingsDialog)
        self.labelFlowB.setGeometry(QtCore.QRect(230, 140, 111, 21))
        self.labelFlowB.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.labelFlowB.setObjectName(_fromUtf8("labelFlowB"))
        self.buttonValidateAndAccept = QtGui.QPushButton(MixtureSettingsDialog)
        self.buttonValidateAndAccept.setGeometry(QtCore.QRect(300, 30, 75, 23))
        self.buttonValidateAndAccept.setObjectName(_fromUtf8("buttonValidateAndAccept"))
        self.buttonCancel = QtGui.QPushButton(MixtureSettingsDialog)
        self.buttonCancel.setGeometry(QtCore.QRect(300, 60, 75, 23))
        self.buttonCancel.setObjectName(_fromUtf8("buttonCancel"))

        self.retranslateUi(MixtureSettingsDialog)
        QtCore.QMetaObject.connectSlotsByName(MixtureSettingsDialog)

    def retranslateUi(self, MixtureSettingsDialog):
        MixtureSettingsDialog.setWindowTitle(_translate("MixtureSettingsDialog", "Dialog", None))
        self.label.setText(_translate("MixtureSettingsDialog", "Mixture Name", None))
        self.label_3.setText(_translate("MixtureSettingsDialog", "Flow A", None))
        self.label_4.setText(_translate("MixtureSettingsDialog", "Flow B", None))
        self.inputIsReactingMixture.setText(_translate("MixtureSettingsDialog", "Reacting Mixture?", None))
        self.labelFlowA.setText(_translate("MixtureSettingsDialog", "-", None))
        self.labelFlowB.setText(_translate("MixtureSettingsDialog", "-", None))
        self.buttonValidateAndAccept.setText(_translate("MixtureSettingsDialog", "OK", None))
        self.buttonCancel.setText(_translate("MixtureSettingsDialog", "Cancel", None))

