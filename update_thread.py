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
