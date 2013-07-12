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
