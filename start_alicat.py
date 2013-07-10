import sys
import time
import serial
import math
from PyQt4 import QtCore, QtGui
from alicat_control_ui import Ui_mainWindow
from threading import Thread
from datetime import datetime

class MyForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.timer = QtCore.QTimer()

        #initialize objects
        self.connection = Connection()
        
        self.air_meter = Meter(self.connection)
        self.fuel_meter = Meter(self.connection)       
        self.air = Air()
        self.fuel = Fuel()
        self.burner = Burner()
        self.flow = Flow(self.air_meter, self.fuel_meter, self.air, self.fuel, self.burner)
        self.record = Record(self.flow, self.ui)

        self.update_thread = Update_thread(self.air_meter,self.fuel_meter)

        self.switchedMode = False
        self.Re_setPoint = 0
        self.TotalMass_setPoint = 0
        self.airSLPM_setPoint = 0
        self.fuelSLPM_setPoint = 0
        self.phi_setPoint = 0
        self.Re_step = 5
        self.TotalMass_step = 0.1
        self.phi_step = 0.1
        self.airSLPM_step = 0.1
        self.fuelSLPM_step = 0.1

        self.ui.dial_flowRate_Air_incr.setTracking(False)
        self.ui.dial_flowRate_Fuel_incr.setTracking(False)
        self.signal_from_button = False

        self.control_enabled = False
        self.doneIgniting = False

        self.SI_to_displayUnits = 60000 # Kg/s -> g/min

        # here we connect signals with our slots
        QtCore.QObject.connect(self.ui.Button_flowrate_Air_up,QtCore.SIGNAL("clicked()"), self.Button_A_Up)
        QtCore.QObject.connect(self.ui.Button_flowrate_Air_down,QtCore.SIGNAL("clicked()"), self.Button_A_Down)
        QtCore.QObject.connect(self.ui.Button_flowrate_Fuel_up,QtCore.SIGNAL("clicked()"), self.Button_B_Up)
        QtCore.QObject.connect(self.ui.Button_flowrate_Fuel_down,QtCore.SIGNAL("clicked()"), self.Button_B_Down)
        QtCore.QObject.connect(self.ui.button_openCloseSerial,QtCore.SIGNAL("clicked()"), self.openCloseSerial)
        QtCore.QObject.connect(self.ui.pushButton_apply_all_settings,QtCore.SIGNAL("clicked()"), self.apply_all_settings)
        QtCore.QObject.connect(self.ui.button_reset,QtCore.SIGNAL("clicked()"), self.reset_meters)
        QtCore.QObject.connect(self.ui.button_record_set,QtCore.SIGNAL("clicked()"), self.add_record)
        QtCore.QObject.connect(self.ui.button_new_record_set,QtCore.SIGNAL("clicked()"), self.new_record_set)
        QtCore.QObject.connect(self.ui.delete_record_button,QtCore.SIGNAL("clicked()"), self.delete_record)
        QtCore.QObject.connect(self.ui.pushButton_start,QtCore.SIGNAL("clicked()"), self.start_update)
        QtCore.QObject.connect(self.update_thread,QtCore.SIGNAL("update_ui()"), self.update_meter_data)
        QtCore.QObject.connect(self.ui.pushButton_save_button,QtCore.SIGNAL("clicked()"), self.record.save_to_file)
        QtCore.QObject.connect(self.ui.button_abort,QtCore.SIGNAL("clicked()"), self.abort)
        QtCore.QObject.connect(self.ui.button_ignition,QtCore.SIGNAL("clicked()"), self.ignition_set_point)
        QtCore.QObject.connect(self.ui.pushButton_clear_records,QtCore.SIGNAL("clicked()"), self.record.clear_records)
        
        self.ui.record_list.itemSelectionChanged.connect(self.item_selected)
        self.ui.dial_flowRate_Air_incr.valueChanged.connect(self.SLPM_Air_slide)
        self.ui.dial_flowRate_Fuel_incr.valueChanged.connect(self.SLPM_Fuel_slide)
        self.ui.comboBox_fuel.currentIndexChanged.connect(self.fuel_changed)

        QtCore.QObject.connect(self.ui.radioButton_re_phi,QtCore.SIGNAL("toggled(bool)"),self.switchControlMode)
        QtCore.QObject.connect(self.ui.radioButton_air_fuel_SLPM,QtCore.SIGNAL("toggled(bool)"),self.switchControlMode)
          
        QtCore.QObject.connect(self.ui.flowrate_Air_incr,QtCore.SIGNAL("valueChanged(double)"),self.update_step)
        QtCore.QObject.connect(self.ui.flowrate_Fuel_incr,QtCore.SIGNAL("valueChanged(double)"),self.update_step)


    def fuel_changed(self):
        if self.ui.comboBox_fuel.currentText() == 'CH4':
            #self.ui.lineEdit_fuel_name.setValue('CH4')
            self.ui.lineEdit_fuel_viscosity.setText('1.0997e-5')
            self.ui.lineEdit_fuel_density.setText('0.6569')
            self.ui.lineEdit_fuel_A_F.setText('17.195')
            self.ui.lineEdit_fuel_SCP.setText('55.5')
            self.ui.lineEdit_fuel_molweight.setText('16.044')
            self.ui.lineEdit_fuel_gas_ID.setText('2')
        elif self.ui.comboBox_fuel.currentText() == 'C3H8':
            #self.ui.lineEdit_fuel_name.setValue('C3H8')
            self.ui.lineEdit_fuel_viscosity.setText('8.01e-5')
            self.ui.lineEdit_fuel_density.setText('1.8316')
            self.ui.lineEdit_fuel_A_F.setText('15.246')
            self.ui.lineEdit_fuel_SCP.setText('50.35')
            self.ui.lineEdit_fuel_molweight.setText('44.10')
            self.ui.lineEdit_fuel_gas_ID.setText('12')
            
    def item_selected(self):
        print 'signal'
        self.record.set_current_record()

    def start_update(self):
        if not self.update_thread.isRunning:
            self.update_thread.isRunning = True
            self.update_thread.start()
            self.ui.pushButton_start.setText('Stop')
            #self.ui.pushButton_start.setDown(True)
        else:
            self.update_thread.isRunning = False
            self.ui.pushButton_start.setText('Run')
            #self.ui.pushButton_start.setDown(False)
        
    def add_record(self):
        self.record.add_record()

    def new_record_set(self):
        self.record.new_record_set()

    def delete_record(self):
        self.record.delete_record()

    def apply_all_settings(self):
        if self.ui.pushButton_apply_all_settings.isEnabled():
            self.setMixtureSettings()
            self.set_meters_settings()
            self.set_burner_settings()
            self.ui.button_openCloseSerial.setEnabled(True)
        else:
            message = QtGui.QMessageBox.information(self,'Warning!','Before aplly changes, RESET the meter and CLOSE the connection.') 

    def enable_control_ui(self, state):
        if not self.control_enabled:
            self.control_enabled = state
            self.ui.button_reset.setEnabled(state)
            self.ui.button_ignition.setEnabled(state)
            self.ui.button_abort.setEnabled(state)
            self.ui.pushButton_start.setEnabled(state)
            self.ui.button_record_set.setEnabled(state)
            self.ui.Button_flowrate_Air_up.setEnabled(state)
            self.ui.Button_flowrate_Air_down.setEnabled(state)
            self.ui.dial_flowRate_Air_incr.setEnabled(state)
            self.ui.Button_flowrate_Fuel_up.setEnabled(state)
            self.ui.Button_flowrate_Fuel_down.setEnabled(state)
            self.ui.dial_flowRate_Fuel_incr.setEnabled(state) 

    def setMixtureSettings(self):
        # air
        self.air.din_viscosity = float(self.ui.lineEdit_air_viscosity.text())
        self.air.density = float(self.ui.lineEdit_air_density.text())
        self.air.molecular_weight = float(self.ui.lineEdit_air_molweight.text())

        # fuel
        self.fuel.fuel_name = self.ui.comboBox_fuel.currentText()
        self.fuel.din_viscosity = float(self.ui.lineEdit_fuel_viscosity.text())
        self.fuel.density = float(self.ui.lineEdit_fuel_density.text())
        self.fuel.A_F = float(self.ui.lineEdit_fuel_A_F.text())
        self.fuel.SCP = float(self.ui.lineEdit_fuel_SCP.text())
        self.fuel.molecular_weight = float(self.ui.lineEdit_fuel_molweight.text())
        

    def set_meters_settings(self):
        self.connection.port = str(self.ui.input_connection_port.text())
        self.connection.baudrate = 19200
        self.connection.timeout = 0.1

        fuel_ID = self.ui.input_fuelControllerID.text()
        max_fuel_meter = self.ui.input_fuelControllerMaxCapac.text()
        air_ID = self.ui.input_airControllerID.text()
        max_air_meter = self.ui.input_airControllerMaxCapac.text()

        self.fuel_meter.set_meter_settings(fuel_ID,max_fuel_meter,float(self.ui.lineEdit_fuel_gas_ID.text()))
        self.air_meter.set_meter_settings(air_ID,max_air_meter,0)
        
    def set_burner_settings(self):
        self.burner.dim_a = float(self.ui.input_burnerDim_a.text())
        self.burner.dim_b = float(self.ui.input_burnerDim_b.text())
        self.burner.no_holes = int(self.ui.input_burnerDim_no.text())
        self.burner.isHole = self.ui.radio_button_burnerHoles.isChecked()

    def update_meter_data(self):
        if self.ui.radioButton_re_phi.isChecked():
            self.ui.lcd_flowrate_Air.display(self.flow.get_Reynolds_flow())
            self.ui.lcd_flowrate_Fuel.display(self.flow.get_phi_flow())
        elif self.ui.radioButton_massflow.isChecked():
            self.ui.lcd_flowrate_Air.display(self.flow.get_totalMassFlow() * self.SI_to_displayUnits)
            self.ui.lcd_flowrate_Fuel.display(self.flow.get_phi_flow())
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.ui.lcd_flowrate_Air.display(self.flow.get_airSLPMFlow())
            self.ui.lcd_flowrate_Fuel.display(self.flow.get_fuelSLPMFlow())

        self.ui.lcd_pressure_Air.display(self.air_meter.get_pressure())
##        self.ui.progressBar_pressure
        self.ui.lcd_temperature_Air.display(self.air_meter.get_temperature())
##        self.ui.progressBar_temperature

        self.ui.lcd_mean_velocity.display(self.flow.get_mean_velocity())
        self.ui.lcd_power.display(self.flow.get_power())

    def switchControlMode(self):
        self.switchedMode = True
        self.update_setPoints()
        if self.ui.radioButton_re_phi.isChecked():
            self.ui.label_flowRate_A_mode.setText('Re')
            self.ui.label_18.setText('Re set point')
            self.ui.label_flowRate_B_mode.setText('phi')
            self.ui.label_19.setText('phi set point')
            self.ui.lcd_flowRate_setPoint_Air.display(self.Re_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.phi_setPoint)
            self.ui.flowrate_Air_incr.setDecimals(1)
            self.ui.flowrate_Air_incr.setSingleStep(5)
            self.ui.flowrate_Air_incr.setValue(self.Re_step)
            self.ui.flowrate_Fuel_incr.setDecimals(2)
            self.ui.flowrate_Fuel_incr.setSingleStep(0.1)
            self.ui.flowrate_Fuel_incr.setValue(self.phi_step)

        elif self.ui.radioButton_massflow.isChecked():
            self.ui.label_flowRate_A_mode.setText('total Mass Flow g/min')
            self.ui.label_18.setText('g/min set point')
            self.ui.label_flowRate_B_mode.setText('phi')
            self.ui.label_19.setText('phi set point')
            self.ui.lcd_flowRate_setPoint_Air.display(self.TotalMass_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.phi_setPoint)
            self.ui.flowrate_Air_incr.setDecimals(2)
            self.ui.flowrate_Air_incr.setSingleStep(0.1)
            self.ui.flowrate_Air_incr.setValue(self.TotalMass_step)
            self.ui.flowrate_Fuel_incr.setDecimals(2)
            self.ui.flowrate_Fuel_incr.setSingleStep(0.1)
            self.ui.flowrate_Fuel_incr.setValue(self.phi_step)

        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.ui.label_flowRate_A_mode.setText('air SLPM')
            self.ui.label_18.setText('SLPM set point')
            self.ui.label_flowRate_B_mode.setText('fuel SLPM')
            self.ui.label_19.setText('SLPM set point')
            self.ui.lcd_flowRate_setPoint_Air.display(self.airSLPM_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.fuelSLPM_setPoint)
            self.ui.flowrate_Air_incr.setDecimals(2)
            self.ui.flowrate_Air_incr.setSingleStep(0.1)
            self.ui.flowrate_Air_incr.setValue(self.airSLPM_step)
            self.ui.flowrate_Fuel_incr.setDecimals(2)
            self.ui.flowrate_Fuel_incr.setSingleStep(0.1)
            self.ui.flowrate_Fuel_incr.setValue(self.fuelSLPM_step)

        self.switchedMode = False

    def update_step(self):
        if not self.switchedMode:
            print 'update step'
            A_step = float(self.ui.flowrate_Air_incr.value())
            B_step = float(self.ui.flowrate_Fuel_incr.value())
            if self.ui.radioButton_re_phi.isChecked():
                self.Re_step = A_step
                self.phi_step = B_step
            elif self.ui.radioButton_massflow.isChecked():
                self.TotalMass_step = A_step
                self.phi_step = B_step
            elif self.ui.radioButton_air_fuel_SLPM.isChecked():
                self.airSLPM_step = A_step
                self.fuelSLPM_step = B_step

    def update_setPoints(self):       
        if self.ui.radioButton_re_phi.isChecked():
            self.Re_setPoint = self.flow.convert_massFlow_to_Reynolds(self.flow.get_totalMassFlow_setPoint())
            self.phi_setPoint = self.flow.get_phi_setPoint()
            self.ui.lcd_flowRate_setPoint_Air.display(self.Re_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.phi_setPoint)
        elif self.ui.radioButton_massflow.isChecked():
            self.TotalMass_setPoint = self.flow.get_totalMassFlow_setPoint() * self.SI_to_displayUnits
            self.phi_setPoint = self.flow.get_phi_setPoint()
            self.ui.lcd_flowRate_setPoint_Air.display(self.TotalMass_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.phi_setPoint)
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.airSLPM_setPoint = self.air_meter.get_setPoint_SLPM()
            self.fuelSLPM_setPoint = self.fuel_meter.get_setPoint_SLPM()
            self.ui.lcd_flowRate_setPoint_Air.display(self.airSLPM_setPoint)
            self.ui.lcd_flowRate_setPoint_Fuel.display(self.fuelSLPM_setPoint) 

        air_meter_capacity = self.air_meter.meter_capacity()
        fuel_meter_capacity = self.fuel_meter.meter_capacity()
        self.ui.progressBar_air_meter_scale.setValue(air_meter_capacity)
        self.ui.progressBar_fuel_meter_scale.setValue(fuel_meter_capacity)
        
        if self.signal_from_button:
            self.ui.dial_flowRate_Air_incr.setValue(self.air_meter.get_setPoint_percent())
            self.ui.dial_flowRate_Fuel_incr.setValue(self.fuel_meter.get_setPoint_percent())
            time.sleep(.01)
            self.signal_from_button = False

    def SLPM_Air_slide(self):
        if not self.signal_from_button:
            self.air_meter.set_setPoint_percent(self.ui.dial_flowRate_Air_incr.value())
            self.update_setPoints()

    def SLPM_Fuel_slide(self):
        if not self.signal_from_button:
            self.fuel_meter.set_setPoint_percent(self.ui.dial_flowRate_Fuel_incr.value())
            self.update_setPoints()

    def Button_A_Up(self):
        self.signal_from_button = True
        if self.ui.radioButton_re_phi.isChecked():
            self.Re_Up()
        elif self.ui.radioButton_massflow.isChecked():
            self.TotalMass_Up()
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.airSLPM_Up()        

    def Button_A_Down(self):
        self.signal_from_button = True
        if self.ui.radioButton_re_phi.isChecked():
            self.Re_Down()
        elif self.ui.radioButton_massflow.isChecked():
            self.TotalMass_Down()
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.airSLPM_Down()

    def Button_B_Up(self):
        self.signal_from_button = True       
        if self.ui.radioButton_re_phi.isChecked() or self.ui.radioButton_massflow.isChecked():
            self.phi_Up()
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.fuelSLPM_Up()

    def Button_B_Down(self):
        self.signal_from_button = True
        if self.ui.radioButton_re_phi.isChecked() or self.ui.radioButton_massflow.isChecked():
            self.phi_Down()
        elif self.ui.radioButton_air_fuel_SLPM.isChecked():
            self.fuelSLPM_Down()

    def Re_Up(self):
        if not self.air_meter.at_max:
            self.flow.set_Reynolds_flow(self.Re_setPoint + self.Re_step)
        self.update_setPoints()
        
    def Re_Down(self):
        self.flow.set_Reynolds_flow(self.Re_setPoint - self.Re_step)
        self.update_setPoints()

    def TotalMass_Up(self):
        if not self.air_meter.at_max:
            self.flow.set_totalMassFlow(( self.TotalMass_setPoint + self.TotalMass_step ) / self.SI_to_displayUnits )
        self.update_setPoints()
        
    def TotalMass_Down(self):
        self.flow.set_totalMassFlow(( self.TotalMass_setPoint - self.TotalMass_step ) / self.SI_to_displayUnits )
        self.update_setPoints()

    def phi_Up(self):
        if not self.air_meter.at_max:
            self.flow.set_phi_flow(self.phi_setPoint + self.phi_step)
        self.update_setPoints()

    def phi_Down(self):
        self.flow.set_phi_flow(self.phi_setPoint - self.phi_step)
        self.update_setPoints()

    def airSLPM_Up(self):
        self.flow.set_airSLPMFlow(self.airSLPM_setPoint + self.airSLPM_step)
        self.update_setPoints()
        
    def airSLPM_Down(self):
        self.flow.set_airSLPMFlow(self.airSLPM_setPoint - self.airSLPM_step)
        self.update_setPoints()

    def fuelSLPM_Up(self):
        if not self.air_meter.at_max:
            self.flow.set_fuelSLPMFlow(self.fuelSLPM_setPoint + self.fuelSLPM_step)
        self.update_setPoints()
        
    def fuelSLPM_Down(self):
        self.flow.set_fuelSLPMFlow(self.fuelSLPM_setPoint - self.fuelSLPM_step)
        self.update_setPoints()

    def reset_meters(self):
        print 'Reseting flowmeters'
        # Air
        self.air_meter.set_setPoint_SLPM(0)
        # Fuel
        self.fuel_meter.set_setPoint_SLPM(0)
        self.update_setPoints()
        if not self.update_thread.isRunning:
            self.air_meter.update_meter()
            self.fuel_meter.update_meter()
            self.update_meter_data()

    def closeEvent(self,Event):
        if self.connection.isOpen():
            self.reset_meters()
            time.sleep(.5)
            print 'Exiting GUI and closing all ports and threads'
            self.update_thread.isRunning = False
            self.connection.close()

    def abort(self):
        print 'Abort:: air meter full open and fuel meter closed'
        self.air_meter.set_setPoint_percent(100)
        self.fuel_meter.set_setPoint_percent(0)
        self.update_setPoints()
                                     

    def ignition_set_point(self):
        if not self.doneIgniting:
            self.flow.set_totalMassFlow(float(self.ui.ignition_massflow_set_point.text()) / self.SI_to_displayUnits)
            self.flow.set_phi_flow(float(self.ui.ignition_phi_set_point.text()))
            self.ui.lcd_flowRate_setPoint_Air.display('-')
            self.ui.lcd_flowRate_setPoint_Fuel.display('-')
            self.ui.button_ignition.setText('Stop Igniting')
            self.ui.button_ignition.setDown(True)
            self.doneIgniting = True
        else:
            print 'ignition finished'
            self.ui.button_ignition.setText('Ignition')
            self.ui.button_ignition.setDown(False)
            if self.ui.radioButton_re_phi.isChecked():
                self.flow.set_Reynolds_flow(self.Re_setPoint)
                self.flow.set_phi_flow(self.phi_setPoint)
            elif self.ui.radioButton_massflow.isChecked():
                self.flow.set_totalMassFlow(self.TotalMass_setPoint)
                self.flow.set_phi_flow(self.phi_setPoint)
            elif self.ui.radioButton_air_fuel_SLPM.isChecked():
                self.flow.set_airSLPMFlow(self.airSLPM_setPoint)
                self.flow.set_fuelSLPMFlow(self.fuelSLPM_setPoint)

            self.update_setPoints()
            self.doneIgniting = False
        
        
    def openCloseSerial(self):
        if self.connection.isOpen() == False:
            self.connection.open()
            self.fuel_meter.setup_meter()
            #change button message do "close connection"
            self.ui.button_openCloseSerial.setText("Close connection")
            self.ui.pushButton_apply_all_settings.setEnabled(False)
        else:
            self.reset_meters()
            time.sleep(.1)
            self.connection.close()
            #change button message do "close open"
            self.ui.button_openCloseSerial.setText("Open connection")
            self.ui.pushButton_apply_all_settings.setEnabled(True)
            
        print self.connection

        if not self.control_enabled:
            self.enable_control_ui(True)
        else:
            self.enable_control_ui(False)

#################################### end of class MyForm ####################################

class Air:
    din_viscosity = 1
    density = 1
    molecular_weight = 1

#################################### end of class Air ####################################

class Fuel:
    fuel_name = ' '
    din_viscosity = 1
    density = 1
    A_F = 1
    SCP = 1
    molecular_weight = 1

#################################### end of class Fuel ####################################

class Burner:
    dim_a = 1
    dim_b = 1
    no_holes = 1
    isHole = False
    
    def area(self):
        if self.isHole:
            return math.pi * math.pow(( self.dim_a ) ,2) / 4
        else:
            return self.dim_a * self.dim_b
        

    def D_h(self):
        if self.isHole:
            return self.dim_a
        else:
            return 4 * self.area() / (2 * self.dim_a + 2 + self.dim_b )
        

#################################### end of class Burner ####################################

class Flow:

    SLPM_to_SI_factor = .001/60 # SLPM to Kg/sec
    
    def __init__(self, air_meter, fuel_meter, air, fuel, burner):
        print 'instanciating class flow'
        self.air_meter = air_meter
        self.fuel_meter = fuel_meter
        self.air = air
        self.fuel = fuel
        self.burner = burner
        self.Reynolds_setPoint = 0
        #self.totalSLPM_setPoint = 0
        self.phi_setPoint = 0


    def get_airSLPMFlow(self):
        return self.air_meter.get_massFlow_SLPM()

    def get_fuelSLPMFlow(self):
        return self.fuel_meter.get_massFlow_SLPM()

    def get_airMassFlow(self):
        return self.SLPM_to_SI(self.air_meter.get_massFlow_SLPM(),self.air.density)

    def get_fuelMassFlow(self):
        return self.SLPM_to_SI(self.fuel_meter.get_massFlow_SLPM(),self.fuel.density)

    def get_airMassFlow_setPoint(self):
        return self.SLPM_to_SI(self.air_meter.get_setPoint_SLPM(),self.air.density)

    def get_fuelMassFlow_setPoint(self):
        return self.SLPM_to_SI(self.fuel_meter.get_setPoint_SLPM(),self.fuel.density)

    def get_Y_air(self):
        if self.get_totalMassFlow_setPoint() != 0:
            return self.get_airMassFlow_setPoint() / self.get_totalMassFlow_setPoint()
        else:
            return 0

    def get_Y_fuel(self):
        return 1 - self.get_Y_air()

    def get_mixture_density(self):
        return 1 / (self.get_Y_air() / self.air.density + self.get_Y_fuel() / self.fuel.density)

    def get_X_air(self):
        return self.get_mixture_density() * self.get_Y_air() / self.air.molecular_weight

    def get_X_fuel(self):
        return self.get_mixture_density() * self.get_Y_fuel() / self.fuel.molecular_weight

    def get_mixture_din_viscosity(self):
        return ( self.get_X_air() * self.air.din_viscosity * math.sqrt(self.air.molecular_weight) +
                self.get_X_fuel() * self.fuel.din_viscosity * math.sqrt(self.fuel.molecular_weight) ) / ( self.get_X_air() * math.sqrt(self.air.molecular_weight) + self.get_X_fuel() * math.sqrt(self.fuel.molecular_weight) )

    def get_phi_flow(self):
        if self.get_airMassFlow() != 0:
            return self.get_fuelMassFlow() / self.get_airMassFlow() * self.fuel.A_F
        else:
            return 0

    def get_phi_setPoint(self):
        if self.get_airMassFlow_setPoint() != 0:
            return self.get_fuelMassFlow_setPoint() / self.get_airMassFlow_setPoint() * self.fuel.A_F
        else:
            return 0

    def get_Reynolds_flow(self):
        return self.get_totalMassFlow() * self.burner.D_h() / self.air.din_viscosity / self.burner.area() / self.burner.no_holes

    def get_totalMassFlow(self):
        return self.get_airMassFlow() + self.get_fuelMassFlow()

    def get_totalSLPMflow(self):
        return self.fuel_meter.get_massFlow_SLPM() + self.air_meter.get_massFlow_SLPM()
    
    def get_totalMassFlow_setPoint(self):
        return self.get_fuelMassFlow_setPoint() + self.get_airMassFlow_setPoint()

    def get_air_meter_pressure(self):
        return self.air_meter.get_pressure()

    def get_air_meter_temperature(self):
        return self.air_meter.get_temperature()

    def convert_massFlow_to_Reynolds(self, totalMassFlow):
        return totalMassFlow * self.burner.D_h() / self.air.din_viscosity / self.burner.area() / self.burner.no_holes

    def convert_Reynolds_to_totalMassFlow(self, Re):
        return Re * self.air.din_viscosity * self.burner.area() * self.burner.no_holes / self.burner.D_h()

    def set_Reynolds_flow(self,set_Re):
        #return fuel/air massflow set points for given flow Re
        totalMassFlow = set_Re * self.air.din_viscosity * self.burner.area() * self.burner.no_holes / self.burner.D_h()
        airMassFlow = totalMassFlow / ( 1 + self.get_phi_setPoint() / self.fuel.A_F )
        fuelMassFlow = totalMassFlow - airMassFlow
        air_SLPM = self.SI_to_SLPM(airMassFlow,self.air.density)
        fuel_SLPM = self.SI_to_SLPM(fuelMassFlow,self.fuel.density) 
        self.air_meter.set_setPoint_SLPM(air_SLPM)
        self.fuel_meter.set_setPoint_SLPM(fuel_SLPM)
        
    def set_totalMassFlow(self, set_totalMassFlow):
        #return fuel/air massflow set points for given SLPM massflow
        airMassFlow = set_totalMassFlow / ( 1 + self.get_phi_setPoint() / self.fuel.A_F )
        fuelMassFlow = set_totalMassFlow - airMassFlow
        air_SLPM = self.SI_to_SLPM(airMassFlow,self.air.density)
        fuel_SLPM = self.SI_to_SLPM(fuelMassFlow,self.fuel.density) 
        self.air_meter.set_setPoint_SLPM(air_SLPM)
        self.fuel_meter.set_setPoint_SLPM(fuel_SLPM)

    def set_phi_flow(self,set_phi):
        #return fuel/air massflow set points (reynolds fixed)
        current_totalMassFlow = self.get_totalMassFlow_setPoint()
        airMassFlow = current_totalMassFlow / ( 1 + set_phi / self.fuel.A_F )
        fuelMassFlow = current_totalMassFlow - airMassFlow
        air_SLPM = self.SI_to_SLPM(airMassFlow,self.air.density)
        fuel_SLPM = self.SI_to_SLPM(fuelMassFlow,self.fuel.density)        
        self.air_meter.set_setPoint_SLPM(air_SLPM)
        self.fuel_meter.set_setPoint_SLPM(fuel_SLPM)

##    def set_airMassFlow(self, massflow):
##        air_SLPM = self.SI_to_SLPM(massflow,self.air.density)
##        self.air_meter.set_setPoint_SLPM(air_SLPM)
##
##    def set_fuelMassFlow(self, massflow):
##        fuel_SLPM = self.SI_to_SLPM(massflow,self.fuel.density)
##        self.fuel_meter.set_setPoint_SLPM(fuel_SLPM)

    def set_airSLPMFlow(self, set_SLPM):
        self.air_meter.set_setPoint_SLPM(set_SLPM)

    def set_fuelSLPMFlow(self, set_SLPM):
        self.fuel_meter.set_setPoint_SLPM(set_SLPM)

    def SLPM_to_SI(self, SLPM, gas_density):
        return SLPM * gas_density * self.SLPM_to_SI_factor

    def SI_to_SLPM(self, massflow, gas_density):
        return massflow / gas_density / self.SLPM_to_SI_factor

    def get_power(self):
        return self.fuel.SCP * self.get_fuelMassFlow() * 1e6

    def get_mean_velocity(self):
        return self.get_totalMassFlow() / self.burner.area() / self.burner.no_holes
        
    

#################################### end of class Flow ####################################

class Connection(serial.Serial):

    def set_connection_settings(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def open_serial():
        if not self.isOpen():
            self.open()

    def close_serial():
        if self.isOpen():
            self.close()

#################################### end of class Connection ####################################

class Meter():

    setPoint_value = 0
    meter_data = [1,1,1,1,1,1,1,1,1,1,1]

    def __init__(self,srl_connection):
        self.serial_connection = srl_connection
        self.at_max = False

    def get_volumetricFlow(self):
        return float(self.meter_data[3])
    
    def get_massFlow_SLPM(self):
        return float(self.meter_data[4])

    def set_setPoint_SLPM(self,SLPM_value):
        if SLPM_value >= 0 and SLPM_value <= self.max_meter:
            self.setPoint_value = SLPM_value
            self.at_max = False
        elif SLPM_value < 1e-5:
            self.setPoint_value = 0
            self.at_max = False
        else:
            self.setPoint_value = self.max_meter
            self.at_max = True

    def set_setPoint_percent(self, percent):
        self.setPoint_value = 0.01 * percent * self.max_meter

    def get_setPoint_percent(self):
        return self.setPoint_value / self.max_meter * 100

    def get_setPoint_SLPM(self):
        return self.setPoint_value

    def update_meter(self):
        tries = 0
        in_message = []
        if self.serial_connection.isOpen():
            while not len(in_message) > 8:
                #print len(in_message)
                #print 'talking with controller try ' + str(tries+1)
                out_message = self.meter_ID + str(self.setPointRS232(self.setPoint_value)) + "\r\r"
                #print out_message
                self.serial_connection.write(out_message)
                time.sleep(.1)

                #print 'fetching data from controller'
                in_message = self.serial_connection.read(50).split(' ')
                self.meter_data = in_message
                #print self.meter_data, len(in_message)
                tries += 1
##            if len(in_message) < 11:
##                print 'Message from controller not recieved properly!'
        else:
            print 'serial is closed'

    def set_meter_settings(self,meter_ID,max_meter,gas_ID):
        self.meter_ID = meter_ID
        self.max_meter = float(max_meter)
        self.gas_ID = int(gas_ID)

    def setup_meter(self):
        in_message = []
        if self.serial_connection.isOpen():
            while not len(in_message) > 8:
                out_message = self.meter_ID + '$$' + str(self.gas_ID) + "\r\r"
                self.serial_connection.write(out_message)
                time.sleep(.1)

                in_message = self.serial_connection.read(50).split(' ')

                print in_message, len(in_message)
        else:
            print 'serial is closed'

    def get_temperature(self):
        return self.meter_data[2]

    def get_pressure(self):
        return self.meter_data[1]

    def setPointRS232(self,setPoint):
        return int(( setPoint * 64000 ) / self.max_meter)

    def meter_capacity(self):
        return int( self.setPoint_value / self.max_meter * 100 )

#################################### end of class Meter ####################################
    
class Record():
    
    records = [] #recordID datasetID Re totalSLPM phi airSLPM fuelSLPM pressure temperature time date   
    sets = []

    
    def __init__(self, flow_, ui_):
        self.flow = flow_
        self.ui = ui_
        self.current_record = 0
        self.current_set = 0
        self.record_ID = 0
        self.set_ID = 0
        self.set_counter = 0
        self.record_counter = 0
        self.selected_item = QtGui.QTreeWidgetItem()


    def new_record(self):
        self.record_ID += 1
        self.set_ID = self.current_set
        record_list = [str(self.record_ID),
                        str(self.set_ID),
                        str(self.flow.get_Reynolds_flow()),
                        str(self.flow.get_phi_flow()),
                        str(self.flow.get_totalMassFlow()),
                        str(self.flow.get_airMassFlow()),
                        str(self.flow.get_fuelMassFlow()),
                        str(self.flow.get_power()),
                        str(self.flow.get_mean_velocity()),
                        str(self.flow.get_air_meter_pressure()),
                        str(self.flow.get_air_meter_temperature()),
                        str(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())),
                        self.ui.comments_textBox.toPlainText()]
        self.records.append(record_list)
        return record_list

    def dataset_average_field(self, dataset_id, average_field):
        dataset_records = self.sort_dataset(self.records, 1, str(dataset_id))
        average = 0
        for i in range(len(dataset_records)):
            average = average + float(dataset_records[i][average_field])
        return str(average / len(dataset_records))    

    def add_record(self):
        new_record = self.new_record()
        print self.records
        print self.current_set
        new_list_item = QtGui.QTreeWidgetItem(self.sets[self.current_set-1][1],new_record)
        self.update_dataset_averages(self.current_set)
        self.set_dataset_setText(self.current_set)
        

    def update_dataset_averages(self, dataset_id):
        print 'dataset id ' + str(dataset_id)
        self.sets[dataset_id-1][2] = self.dataset_average_field(dataset_id, 2)
        self.sets[dataset_id-1][3] = self.dataset_average_field(dataset_id, 3)
        self.sets[dataset_id-1][4] = self.dataset_average_field(dataset_id, 4)
        self.sets[dataset_id-1][5] = self.dataset_average_field(dataset_id, 5)
        self.sets[dataset_id-1][6] = self.dataset_average_field(dataset_id, 6)
        self.sets[dataset_id-1][7] = self.dataset_average_field(dataset_id, 7)
        self.sets[dataset_id-1][8] = self.dataset_average_field(dataset_id, 8)
        self.sets[dataset_id-1][9] = self.dataset_average_field(dataset_id, 9)
        self.sets[dataset_id-1][10] = self.dataset_average_field(dataset_id, 10)
        

    def new_record_set(self):
        self.set_counter += 1
        self.current_set = self.set_counter
        new_set_item = QtGui.QTreeWidgetItem(self.ui.record_list)
        set_data = [self.current_set, new_set_item,'-','-','-','-','-','-','-','-','-']
        self.sets.append(set_data)
        self.set_dataset_setText(self.current_set)
        self.ui.record_list.setCurrentItem(new_set_item)

    def set_dataset_setText(self, dataset_id):
        self.sets[dataset_id-1][1].setText(0, 'set ' + str(self.sets[dataset_id-1][0]))
        self.sets[dataset_id-1][1].setText(2, self.sets[dataset_id-1][2]) #Reynolds
        self.sets[dataset_id-1][1].setText(3, self.sets[dataset_id-1][3]) #phi
        self.sets[dataset_id-1][1].setText(4, self.sets[dataset_id-1][4]) #totalMassFlow
        self.sets[dataset_id-1][1].setText(5, self.sets[dataset_id-1][5]) #airSLPM
        self.sets[dataset_id-1][1].setText(6, self.sets[dataset_id-1][6]) #fuelSLPM
        self.sets[dataset_id-1][1].setText(7, self.sets[dataset_id-1][7]) #power
        self.sets[dataset_id-1][1].setText(8, self.sets[dataset_id-1][8]) #mean_velocity
        self.sets[dataset_id-1][1].setText(9, self.sets[dataset_id-1][9]) #pressure
        self.sets[dataset_id-1][1].setText(10, self.sets[dataset_id-1][10]) #temperature    

    def delete_record(self):
        if self.isRecord:
            print 'Item is child. Deleteing selected child.'
            #delete child item
            self.records.pop(self.search_list(self.records,0,self.selected_item.text(0)))
            self.selected_item.removeChild(self.selected_item)
            del self.selected_item
        if self.dataset_isEmpty(self.current_set):
            self.sets[self.current_set-1][2:] = ['-','-','-','-','-','-','-']
            self.set_dataset_setText(self.current_set)          
            
    def set_current_record(self):
        self.selected_item = self.ui.record_list.currentItem()
        if self.selected_item == None:
            self.isRecord = False
        elif self.selected_item.parent() == None:
            print 'Item is a parent.'
            print self.selected_item.text(0)
            dummy = self.selected_item.text(0).split(' ')
            self.current_set = int(dummy[1])
            self.isRecord = False
        else:
            print 'Item is a child.'
            print self.selected_item.text(0) + ' from set ' + self.selected_item.text(1)
            self.current_set = int(self.selected_item.text(1))
            self.current_record = int(self.selected_item.text(0))
            self.isRecord = True 

    def search_list(self, source_list, search_field, search_value):
        index = 0
        for index , s_list in enumerate(source_list):
            if s_list[search_field] == search_value:
                print 'deleting item with index ' + str(index)
                print s_list
                return index
                print 'breaking'
                break

    def sort_dataset(self, source_list, search_field, search_value):
        index = 0
        sorted_list = []
        for index, s_list in enumerate(source_list):
            if s_list[search_field] == search_value:
                sorted_list.append(s_list)
        return sorted_list

    def dataset_isEmpty(self, dataset_id):
        dataset_records = self.sort_dataset(self.records,1,str(dataset_id))
        if len(dataset_records) == 0:
            print 'dataset is empty'
            return True
        else:
            return False


    def save_to_file(self):
        file_date = time.strftime("%a_%d_%b_%Y_%Hh%Mm%Ss", time.localtime())
        #Sets
        file_name = 'sets_ ' + file_date
        file_datasets = open(file_name, 'w')
        file_datasets.write('# datasetID Re phi total_massflow air_massflow fuel_massflow power mean_velocity pressure temperature\n')
        for i in range(len(self.sets)):
            file_datasets.write(str(self.sets[i][0]) + ' ' + self.sets[i][2] + ' ' +
                                self.sets[i][3] + ' ' + self.sets[i][4] + ' ' + self.sets[i][5] + ' ' +
                                self.sets[i][6] + ' ' + self.sets[i][7] + ' ' + self.sets[i][8] + ' ' +
                                self.sets[i][9] + ' ' + self.sets[i][10] + '\n')
        file_datasets.close()
        #Records
        file_name = 'records_ ' + file_date
        file_records = open(file_name, 'w')
        file_records.write('record# Re phi totalSLPM airSLPM fuelSLPM power mean_velocity pressure temperature date comments\n')
        for i in range(len(self.records)):
            file_records.write(str(self.records[i][0]) + self.records[i][1] + ' ' + self.records[i][2] + ' ' +
                                self.records[i][3] + ' ' + self.records[i][4] + ' ' + self.records[i][5] + ' ' +
                                self.records[i][6] + ' ' + self.records[i][7] + ' ' + self.records[i][8] + ' ' +
                                self.records[i][9] + ' ' + self.records[i][10] + ' ' +
                                self.records[i][11] + ' ' + self.records[i][12] + '\n')
        file_records.close()

    def clear_records(self):
        self.sets = []
        self.records =  []
        self.ui.record_list.clear()


#################################### end of class Record ####################################

class Update_thread(QtCore.QThread):

    isRunning = False
    update_ui = QtCore.pyqtSignal()

    def __init__(self,air_meter_,fuel_meter_):
        QtCore.QThread.__init__(self)
        self.air_meter = air_meter_
        self.fuel_meter = fuel_meter_

    def run(self):
        print 'running thread'
        while self.isRunning:
            #print 'fetching serial data\n'
            self.air_meter.update_meter()
            self.update_ui.emit()
            self.fuel_meter.update_meter()
            #time.sleep(.1)
            self.update_ui.emit()
                       
#################################### end of class Update_thread ####################################          
        
##if __name__ == "__main__":
##    app = QtGui.QApplication(sys.argv)
##    myapp = MyForm()
##    myapp.show()
##    sys.exit(app.exec_())

def main():
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main() 
