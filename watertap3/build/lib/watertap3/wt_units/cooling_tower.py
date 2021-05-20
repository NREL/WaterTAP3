from pyomo.environ import Block, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'cooling_tower'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
        self.costing.basis_year = basis_year
        sys_cost_params = self.parent_block().costing_param
        self.tpec_or_tic = tpec_or_tic
        if self.tpec_or_tic == 'TPEC':
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tpec
        else:
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tic

        '''
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        '''

        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

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
            print('Cycles of concentration are set based on parameters to:', unit_params['cycles'])
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
            set_plant_info(self, unit_params)
            self.nameplate = unit_params['nameplate']
            self.heat_in = self.nameplate / self.eff
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()
            unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = unit_params['make_up']
            self.blowdown = self.make_up - self.evaporation
            self.cycles = self.make_up / self.blowdown

        ## MASS BALANCE AND PLANT INFO USED TO CALCULATE CYCLES OF CONCENTRATION, BLOWDOWN, EVAPORATION             
        if unit_params['method'] == 'plant_info_without_makeup':
            print('make up not given as a result of assumptions, cycles of concentration are given')
            set_plant_info(self, unit_params)
            self.nameplate = unit_params['nameplate']
            self.heat_in = self.nameplate / self.eff
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()
            unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up - self.evaporation
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up / self.cycles
            self.evaporation = self.make_up - self.blowdown  # evaporation assumed to go to waste outlet (out of system) should not go to surface discharge  

        self.water_recovery.fix(self.blowdown / self.make_up)
        self.chem_dict = {}

        def fixed_cap(flow_in):
            pass

        def electricity(flow_in):
            pass

        self.costing.fixed_cap_inv_unadjusted = self.flow_vol_in[time] * 1E-9  # $M

        self.electricity = 1E-9  # kwh/m3

        financials.get_complete_costing(self.costing)