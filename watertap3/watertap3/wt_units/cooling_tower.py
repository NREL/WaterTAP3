from pyomo.environ import Expression, Block, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'cooling_tower'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        atmospheric_pressure = 101325  # Pa
        ambient_temperature = 20
        relative_humidity = 0.5
        self.cp = 4.18  # heat capacity
        self.cycles = 5.0
        self.ci_circ = 0.0  # unset for the ratio, but could be defined in future
        self.ci_makeup = 0.0  # unset for the ratio, but could be defined in future
        self.latent_heat = 2264.76  # latent heat of vaporization MJ/m3
        self.evap_fraction = 0.85  # fraction of total heat rejected by latent heat transfer - 0.9 in EPRI report
        self.approach = 5.55  # see Miara & Vorosmarty 2017 for assumption
        self.wet_bulb_temp = 20  # unless specified
        self.ttd = 4.44  # Celsius based on typical range of 8F from EPRI 2004
        self.range = 11.11  # Celsius based on typical range of 20F from EPRI 2004
        if 'cycles' in unit_params:
            # print('Cycles of concentration are set based on parameters to:', unit_params['cycles'])
            self.cycles = unit_params['cycles'];
        else:
            self.cycles = 5.0;
            print('If cycles are used, assuming cycles of concentration is:', self.cycles)
        ## EVPORATION FRACTION PROVIDED BY USER
        if unit_params['method'] == 'evaporation_fraction':
            self.make_up = self.flow_vol_in[time]
            self.evaporation = unit_params['evaporation_fraction'] * self.flow_vol_in[time]
            self.blowdown = self.make_up - self.evaporation
        ## MASS BALANCE APPROACH
        if unit_params['method'] == 'make_up_mass_balance':
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up / self.cycles
            self.evaporation = self.make_up - self.blowdown  # evaporation assumed to go to waste outlet (out of system) should not go to surface discharge
        ## MASS BALANCE AND PLANT INFO USED TO CALCULATE CYCLES OF CONCENTRATION, BLOWDOWN, EVAPORATION
        if unit_params['method'] == 'plant_info_with_makeup':
            print('Make up is given, cycles of concentration are calculated as a result of assumptions')
            self.set_plant_info(self, unit_params)
            self.nameplate = unit_params['nameplate']
            self.heat_in = self.nameplate / self.eff
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()
            self.unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = unit_params['make_up']
            self.blowdown = self.make_up - self.evaporation
            self.cycles = self.make_up / self.blowdown
        ## MASS BALANCE AND PLANT INFO USED TO CALCULATE CYCLES OF CONCENTRATION, BLOWDOWN, EVAPORATION
        if unit_params['method'] == 'plant_info_without_makeup':
            print('make up not given as a result of assumptions, cycles of concentration are given')
            self.set_plant_info(self, unit_params)
            self.nameplate = unit_params['nameplate']
            self.heat_in = self.nameplate / self.eff
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()
            self.unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up - self.evaporation
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up / self.cycles
            self.evaporation = self.make_up - self.blowdown  # evaporation assumed to go to waste outlet (out of system) should not go to surface discharge
        self.water_recovery.fix(self.blowdown / self.make_up)
        self.chem_dict = {}
        ct_cap = self.flow_vol_in[time] * 1E-9  # $M
        return ct_cap

    def elect(self):
        electricity = 1E-9
        return electricity

    def unfix_inlet_to_train(self):
        if hasattr(self.parent_block(), 'pfd_dict'):
            for key in self.parent_block().pfd_dict:
                if self.parent_block().pfd_dict[key]['type'] == 'intake':
                    print('unfixing intake:', key)
                    getattr(self.parent_block(), key).flow_vol_in.unfix()
        else:
            print('assuming test with source1')
            self.parent_block().source1.flow_vol_in.unfix()

    def set_plant_info(self, unit_params):
        if unit_params['fuel'] == 'nuclear':
            self.heat_sink = 0.0
            self.eff = 0.3
        if unit_params['fuel'] == 'natural_gas_cc':
            self.heat_sink = 0.2
            self.eff = 0.6
        if unit_params['fuel'] == 'coal':
            self.heat_sink = 0.12
            self.eff = 0.35

        if 'efficiency' in unit_params:
            print('Thermal efficiency of plant set based on parameters to:', unit_params['efficiency'])
            self.eff = unit_params['efficiency'];
        else:
            print('Assuming thermal efficiency of plant is:', self.eff)

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)