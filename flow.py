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
