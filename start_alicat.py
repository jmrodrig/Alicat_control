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
        QtCore.QObject.connect(self.buttonAddFlowmeter,QtCore.SIGNAL("clicked()"), self.addFlowmeterToList)
        QtCore.QObject.connect(self.buttonRemoveFlowmeter,QtCore.SIGNAL("clicked()"), self.removeFlowmeterFromList)
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
    mixtureList = [] # ID, mixtureType, flowA, flowB

    def addFlowmeterToView(self):
        flowmeterParams = [ str(self.inputFlowmeterID.currentText()),
                            str(self.inputGasName.currentText()),
                            str(self.inputGasID.text()),
                            str(self.inputMaxCapacity.text()),
                            str(self.inputSerialPort.currentText()),
                            0 ] # MixID is used to define a mixture stream (default for 0 - none)
        
        if self.addFlowmeterToList(flowmeterParams):            
            #add new flowmeter item to tree view list
            flowmeterTreeView = QtGui.QTreeWidgetItem(self.listFlowmeter,flowmeterParams)

    def addFlowmeterToList(self,flowmeterParams):
        #validate if flowmeter ID does not exist in the list before adding to the list
        if not self.flowmeterIdIsUsed(self.inputFlowmeterID.currentText()):            
            self.flowmeterList.append(flowmeterParams)
            return True

    def removeFlowmeterFromList(self,FM_id):
        for index, fList in enumerate(self.flowmeterList):
            if FM_id == fList[0]:
                self.flowmeterList.pop(index)
                break
                            
    def removeFlowmeterFromView(self):
        selectedFlowmeter = self.listFlowmeter.currentItem()
        if not selectedFlowmeter == None:
            #remove from QTreeWidget
            self.listFlowmeter.takeTopLevelItem(self.listFlowmeter.indexOfTopLevelItem(selectedFlowmeter))
            #remove from flowmeterList
            self.removeFlowmeterFromList(selectedFlowmeter.text(0))
            
        
    def mixSelectedStreams(self):
        #get selected items
        selectedFlowmeters = self.listFlowmeter.selectedItems()

        #remove selected items from top-level treeView
        for SF in selectedFlowmeters:
            self.listFlowmeter.takeTopLevelItem(self.listFlowmeter.indexOfTopLevelItem(SF))

        #open mixture settings dialog 


        #add Mix top-level item to list
        

        #add selected items to Mix top-level item

        #update MixID in the flowmeterList of both items 
        
        



    def flowmeterIdIsUsed(self,id):
        for index, fList in enumerate(self.flowmeterList):
            if id == fList[0]:
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

    
        

def main():
    app = QtGui.QApplication(sys.argv)
    myapp = MainForm()
    myapp.show()
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main() 
