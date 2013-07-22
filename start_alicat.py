import sys
import time
import serial
import math

import burner
import flow
import meter
import record

from PyQt4 import QtCore, QtGui
from alicat_control_ui import Ui_MainWindow
from new_setup_ui import Ui_NewSetupWindow
from mixture_settings_dialog import Ui_MixtureSettingsDialog
from threading import Thread
from datetime import datetime

class MainForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.timer = QtCore.QTimer()

        QtCore.QObject.connect(self.ui.buttonNewSetup,QtCore.SIGNAL("clicked()"), self.new_setup)

    def new_setup(self):
        print "open create new setup window"
        new_setup_window = NewSetupWindow()
        new_setup_window.exec_()

        params = new_setup_window.getSetupParams()
        print "passing values to main window"
        print params
        

##    def new_setup(self):
##        new_setup_window = QtGui.QDialog()
##        new_setup_window.ui = Ui_NewSetupWindow()
##        new_setup_window.ui.setupUi(new_setup_window)
##        new_setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
##        new_setup_window.exec_()

class NewSetupWindow(QtGui.QDialog,Ui_NewSetupWindow):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)

        # Reads the gasfile
        self.gasList = self.readGasFile()
        # populates the UI with the available gases in the file
        self.inputGasName.clear()
        gasIndexes = range(len(self.gasList))
        for gas in gasIndexes:
            self.inputGasName.addItem(self.gasList[gas][1])
        self.updateGasSettings()

        #Validators
        self.inputGeometryA.setValidator(QtGui.QDoubleValidator())
        self.inputGeometryB.setValidator(QtGui.QDoubleValidator())
        self.inputGeometryArea.setValidator(QtGui.QDoubleValidator())
        self.inputGeometryL.setValidator(QtGui.QDoubleValidator())
        self.inputGeometryL.setMaxLength(5)
        self.inputGeometryPerimeter.setValidator(QtGui.QDoubleValidator())
        self.inputGeometryNumber.setValidator(QtGui.QDoubleValidator())

        #Signals
        QtCore.QObject.connect(self.buttonCancel,QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.buttonCreate,QtCore.SIGNAL("clicked()"), self.createSetup)

        # -> Burner Geometry Tab
        QtCore.QObject.connect(self.rButtonHoles,QtCore.SIGNAL("toggled(bool)"),self.switchGeometry)
        QtCore.QObject.connect(self.rButtonSlits,QtCore.SIGNAL("toggled(bool)"),self.switchGeometry)
        QtCore.QObject.connect(self.rButtonOther,QtCore.SIGNAL("toggled(bool)"),self.switchGeometry)

        QtCore.QObject.connect(self.inputGeometryA,QtCore.SIGNAL("editingFinished()"),self.updateGeometryParams)
        QtCore.QObject.connect(self.inputGeometryB,QtCore.SIGNAL("editingFinished()"),self.updateGeometryParams)
        QtCore.QObject.connect(self.inputGeometryArea,QtCore.SIGNAL("editingFinished()"),self.updateGeometryParams)
        QtCore.QObject.connect(self.inputGeometryPerimeter,QtCore.SIGNAL("editingFinished()"),self.updateGeometryParams)
        QtCore.QObject.connect(self.inputGeometryNumber,QtCore.SIGNAL("editingFinished()"),self.updateGeometryParams)

        # -> Flowmeters Tab
        QtCore.QObject.connect(self.buttonAddFlowmeter,QtCore.SIGNAL("clicked()"), self.addFlowmeterToView)
        QtCore.QObject.connect(self.buttonRemoveFlowmeter,QtCore.SIGNAL("clicked()"), self.removeFlowmetersFromView)
        QtCore.QObject.connect(self.buttonMixFlowmeter,QtCore.SIGNAL("clicked()"), self.mixSelectedStreams)
        QtCore.QObject.connect(self.inputGasName,QtCore.SIGNAL("currentIndexChanged(int)"), self.updateGasSettings)
        

    def createSetup(self):
        self.getGeometryParams()

    def getSetupParams(self):
        return 1
    
    #################################
    #####                       #####
    #####       GEOMETRY        #####  ##########################################################################################################################################################################
    #####                       #####
    #################################
    
    def updateGeometryParams(self):
        # Circular Holes
        if self.rButtonHoles.isChecked():
            if not self.inputGeometryA.text().isEmpty():
                self.inputGeometryArea.setText(str(self.calculateAreaCircle(float(self.inputGeometryA.text()))))
                self.inputGeometryPerimeter.setText(str(self.calculatePerimeterCircle(float(self.inputGeometryA.text()))))
                self.inputGeometryL.setText(str(self.calculateHydraulicDiameter(float(self.inputGeometryArea.text()),float(self.inputGeometryPerimeter.text()))))
            if not self.inputGeometryNumber.text().isEmpty():
                self.inputGeometryTotal.setText(str(self.calculateTotalArea(float(self.inputGeometryArea.text()), float(self.inputGeometryNumber.text()))))
                

        # Slit Holes
        elif self.rButtonSlits.isChecked():
            if not self.inputGeometryA.text().isEmpty() and not self.inputGeometryB.text().isEmpty():
                self.inputGeometryArea.setText(str(self.calculateAreaSlit(float(self.inputGeometryA.text()),float(self.inputGeometryB.text()))))
                self.inputGeometryPerimeter.setText(str(self.calculatePerimeterSlit(float(self.inputGeometryA.text()),float(self.inputGeometryB.text()))))
                self.inputGeometryL.setText(str(self.calculateHydraulicDiameter(float(self.inputGeometryArea.text()),float(self.inputGeometryPerimeter.text()))))
            if not self.inputGeometryNumber.text().isEmpty():
                self.inputGeometryTotal.setText(str(self.calculateTotalArea(float(self.inputGeometryArea.text()), float(self.inputGeometryNumber.text()))))
            

        # Other Geometries
        elif self.rButtonOther.isChecked():
            if not self.inputGeometryArea.text().isEmpty() and not self.inputGeometryPerimeter.text().isEmpty():
                self.inputGeometryL.setText(str(self.calculateHydraulicDiameter(float(self.inputGeometryArea.text()),float(self.inputGeometryPerimeter.text()))))
            if not self.inputGeometryNumber.text().isEmpty():
                self.inputGeometryTotal.setText(str(self.calculateTotalArea(float(self.inputGeometryArea.text()), float(self.inputGeometryNumber.text()))))
            

    def switchGeometry(self):
        #Clear inputs
        self.inputGeometryA.clear()
        self.inputGeometryB.clear()
        self.inputGeometryArea.clear()
        self.inputGeometryL.clear()
        self.inputGeometryPerimeter.clear()
        self.inputGeometryNumber.clear()
        self.inputGeometryTotal.clear()
        
        # Circular Holes
        if self.rButtonHoles.isChecked():
            self.inputGeometryA.setEnabled(True)
            self.inputGeometryB.setEnabled(False)
            self.inputGeometryArea.setEnabled(False)
            self.inputGeometryL.setEnabled(False)
            self.inputGeometryPerimeter.setEnabled(False)

        # Slit Holes
        elif self.rButtonSlits.isChecked():
            self.inputGeometryA.setEnabled(True)
            self.inputGeometryB.setEnabled(True)
            self.inputGeometryArea.setEnabled(False)
            self.inputGeometryL.setEnabled(False)
            self.inputGeometryPerimeter.setEnabled(False)

        # Other Geometries
        elif self.rButtonOther.isChecked():
            self.inputGeometryA.setEnabled(False)
            self.inputGeometryB.setEnabled(False)
            self.inputGeometryArea.setEnabled(True)
            self.inputGeometryL.setEnabled(False)
            self.inputGeometryPerimeter.setEnabled(True)

    def calculateAreaCircle(self,diameter):
        return math.pow(diameter,2) * math.pi / 4

    def calculateAreaSlit(self,a,b):
        return a * b

    def calculatePerimeterCircle(self,diameter):
        return diameter * math.pi

    def calculatePerimeterSlit(self,a,b):
        return 2 * a + 2 * b

    def calculateHydraulicDiameter(self,area,perimeter):
        return 4 * area / perimeter

    def calculateTotalArea(self,hole_area,number_holes):
        return hole_area * number_holes

    def getGeometryParams(self):
        print [ float(self.inputGeometryArea.text()),
                 float(self.inputGeometryPerimeter.text()),
                 float(self.inputGeometryNumber.text()),
                 float(self.inputGeometryTotal.text()) ]

    ##################################
    #####                        #####
    #####       FLOWMETER        #####  ##########################################################################################################################################################################
    #####                        #####
    ##################################

    flowmeterList = [] # ID, GasName, GasID, MaxCapacity, SerialPort, MixID
    mixtureList = [] # ID, mixtureName, isReactingMixture, flowA, flowB

    def addFlowmeterToView(self):
        flowmeterParams = [ str(self.inputFlowmeterID.currentText()),
                            str(self.inputGasName.currentText()),
                            str(self.inputGasID.text()),
                            str(self.inputMaxCapacity.text()),
                            str(self.inputSerialPort.currentText()),
                            0 ] # MixID is used to define a mixture stream (default: 0 - none)
        
        if self.addFlowmeterToList(flowmeterParams):            
            # add new flowmeter item to tree view list
            flowmeterTreeViewItem = QtGui.QTreeWidgetItem(self.treeViewFlowmeters,flowmeterParams[:-1])

    def addFlowmeterToList(self,flowmeterParams):
        # validate if flowmeter ID does not exist in the list before adding to the list
        if not self.flowmeterIdIsUsed(self.inputFlowmeterID.currentText()):            
            self.flowmeterList.append(flowmeterParams)
            return True

    def removeFlowmetersFromList(self,FM_id):
        for index, fList in enumerate(self.flowmeterList):
            if FM_id == fList[0]:
                self.flowmeterList.pop(index)
                break

    def findMixtureNameFromList(self,mixName):
        for index, mList in enumerate(self.mixtureList):
            if mixName == mList[0]:
                return index
        return False

    def findMixtureFlowMetersFromList(self,FM):
        for index, mList in enumerate(self.mixtureList):
            if FM == mList[2] or FM == mList[3]:
                return index
        return False
                            
    def removeFlowmetersFromView(self):
        selectedFlowmeters = self.treeViewFlowmeters.selectedItems()
        if not selectedFlowmeters == None:
            for SL in selectedFlowmeters:
                if SL.childCount() == 0 and SL.parent() == None:          # select non-mixture flowmeter items only (items have no children and no parents)
                    # remove from QTreeWidget
                    self.treeViewFlowmeters.takeTopLevelItem(self.treeViewFlowmeters.indexOfTopLevelItem(SL))
                    # remove from flowmeterList
                    self.removeFlowmetersFromList(SL.text(0))
                elif SL.parent() == None:                                 # select mixture items (items have no parents)
                    # remove from QTreeWidget
                    self.treeViewFlowmeters.takeTopLevelItem(self.treeViewFlowmeters.indexOfTopLevelItem(SL))
                    # remove mixture flowmeters from flowmeters list
                    mix = self.mixtureList[self.findMixtureNameFromList(SL.text(0))]
                    self.removeFlowmetersFromList(mix[2])
                    self.removeFlowmetersFromList(mix[3])
                    # remove from mixture list
                    self.mixtureList.pop(self.findMixtureNameFromList(SL.text(0)))
                    
        
    def mixSelectedStreams(self):
        # get selected items
        selectedFlowmeters = self.treeViewFlowmeters.selectedItems()

        # VALIDATE SELECTION
        # check if selected items are not mixtures
        for SL in selectedFlowmeters:
            if not SL.childCount() == 0:
                return 0

        # check if any of the flowmeters is already in use in a mixture
        for SL in selectedFlowmeters:
            if not SL.parent() == None:
                message = QtGui.QMessageBox.information(self,'Warning!','Flowmeter(s) already in use in another mixture.')
                return 0
            
        # check if 2 flowmeters are selected
        if not len(selectedFlowmeters) == 2:
            message = QtGui.QMessageBox.information(self,'Warning!','Select 2 Flowmeters')
            return 0


        # open mixture settings dialog and get new mixture params 
        mixtureParams = self.getMixtureSettings(selectedFlowmeters) # [ mixtureName, isReactingMixture, flowA, flowB ]

        if mixtureParams == False:
            return 0   # cancel button was pressed
        
        #remove selected items from top-level treeView
        for SF in selectedFlowmeters:
            self.treeViewFlowmeters.takeTopLevelItem(self.treeViewFlowmeters.indexOfTopLevelItem(SF))

        #add Mix top-level item to list
        mixName = mixtureParams[0]
        mixtureTreeViewItem = QtGui.QTreeWidgetItem(self.treeViewFlowmeters)
        mixtureTreeViewItem.setText(0,mixName)

        #add selected items to Mix top-level item
        mixtureTreeViewItem.addChildren(selectedFlowmeters)
        mixtureTreeViewItem.setExpanded(True)

        #update mixtureList
        self.mixtureList.append(mixtureParams)
        print self.mixtureList
        
    def getMixtureSettings(self,selectedFlowmeters):
        MSDDialog = MixtureSettingsDialog(selectedFlowmeters,self.mixtureList)
        MSDResult = MSDDialog.exec_()
        if MSDResult == 1:
            mixtureName = MSDDialog.inputMixtureName.text()
            isReactingMixture = MSDDialog.inputIsReactingMixture.isChecked()
            flowA = MSDDialog.inputFlowA.currentText()
            flowB = MSDDialog.inputFlowB.currentText()
            return [ mixtureName, isReactingMixture, flowA, flowB ]
        else:
            return False


    def flowmeterIdIsUsed(self,flometerId):
        for index, fList in enumerate(self.flowmeterList):
            if flometerId == fList[0]:
                return True
        return False

    def readGasFile(self):
        with open("gasfile") as f:
            content = f.readlines()
        content.pop(0)
        lineIndex = range(len(content))
        for index in lineIndex:
            content[index] = content[index][:-2].split('\t')
        return content

    def findFlowmeterFromList(self,flometerId):
        for index, fList in enumerate(self.flowmeterList):
            if flometerId == fList[0]:
                return self.flowmeterList[index]
        return False

    def updateGasSettings(self):
        gasIndex = self.inputGasName.currentIndex()
        self.inputGasID.setText(self.gasList[gasIndex][0])
        self.inputAirFuelRatio.setText(self.gasList[gasIndex][2])
        self.inputFuelHHF.setText(self.gasList[gasIndex][3])
        self.inputGasDensity.setText(self.gasList[gasIndex][4])
        self.inputGasViscosity.setText(self.gasList[gasIndex][5])
        self.inputGasMolecularWeight.setText(self.gasList[gasIndex][6])

##    def newGas(self):
##
##    def updateGasFile(self):
##
##    def validateGasID(self):
##
##    def getFlowmeterParams(self):


class MixtureSettingsDialog(QtGui.QDialog,Ui_MixtureSettingsDialog):

    def __init__(self,SL,mixList):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.selectedFlowmeters = SL
        self.mixtureList = mixList

        self.inputMixtureName.setText('Mix' + str(len(self.mixtureList) + 1))
        for item in self.selectedFlowmeters:
            self.inputFlowA.addItem(item.text(0))
            self.inputFlowB.addItem(item.text(0))

        self.inputFlowA.setCurrentIndex(0)
        self.labelFlowA.setText(self.selectedFlowmeters[0].text(1))
        self.inputFlowB.setCurrentIndex(1)
        self.labelFlowB.setText(self.selectedFlowmeters[1].text(1))
        
        QtCore.QObject.connect(self.inputFlowA,QtCore.SIGNAL("currentIndexChanged(int)"), self.updateLabels)
        QtCore.QObject.connect(self.inputFlowB,QtCore.SIGNAL("currentIndexChanged(int)"), self.updateLabels)

        QtCore.QObject.connect(self.buttonValidateAndAccept,QtCore.SIGNAL("clicked()"), self.validateAndAccept)
        QtCore.QObject.connect(self.buttonCancel,QtCore.SIGNAL("clicked()"), self.reject)

    def updateLabels(self):
        self.labelFlowA.setText(self.selectedFlowmeters[self.inputFlowA.currentIndex()].text(1))
        self.labelFlowB.setText(self.selectedFlowmeters[self.inputFlowB.currentIndex()].text(1))
        
    def validateMixtureName(self):
        for index, mList in enumerate(self.mixtureList):
            if self.inputMixtureName.text() == mList[0]:
                return False
        return True

    def validateAndAccept(self):
        if self.inputFlowA.currentIndex() == self.inputFlowB.currentIndex():
            message = QtGui.QMessageBox.information(self,'Warning!','Flow A and Flow B must not have the same values!')
        elif not self.validateMixtureName():
            message = QtGui.QMessageBox.information(self,'Warning!','Mixture name must be unique! ' + self.inputMixtureName.text() + ' is already in use.')
        else:
            self.accept()
        

def main():
    app = QtGui.QApplication(sys.argv)
    myapp = MainForm()
    myapp.show()
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main() 
