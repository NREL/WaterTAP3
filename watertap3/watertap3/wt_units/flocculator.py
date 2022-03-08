from pyomo.environ import Block, Expression, Var, Param, NonNegativeReals, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# McGiveney & Kawamura
## ELECTRICITY:
# 

module_name = 'flocculator'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def floc_setup(self, unit_params):
        '''

        :return:
        '''
        time = self.flowsheet().config.time
        t = time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
        self.flow_in_Mgpm = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.Mgallon / pyunits.minute)
        self.chem_dict = {}
        self.residence_time = Var(time, initialize=10, domain=NonNegativeReals, units=pyunits.minute, bounds=(5,45), doc='Flocculator residence time [min]')

        try:
            self.terminal_floc = unit_params['terminal_floc']
        except:
            self.terminal_floc = False
        
        if self.terminal_floc:
            self.water_recovery.fix(0.9999)
            self.removal_fraction[0, 'toc'].fix(0.40)
        else:
            self.water_recovery.fix(0.9999)
        try:
            self.vel_gradient = unit_params['vel_gradient']
            if self.vel_gradient not in [20, 50, 80]:
                self.vel_gradient = 80
        except (KeyError, TypeError) as e:
            self.vel_gradient = 80
        try:
            self.residence_time.fix(unit_params['residence_time'])
        except (KeyError, TypeError) as e:
            self.residence_time.fix(10)

        try:
            self.motor_eff = unit_params['motor_eff']
        except (KeyError, TypeError) as e:
            self.motor_eff = 0.75
        
        try:
            self.num_mixers = unit_params['num_mixers']
        except KeyError as e:
            self.num_mixers = 3

        self.basin_volume_Mgal = self.flow_in_Mgpm * self.residence_time[t] 
    
    def fixed_cap(self):
        '''

        :return:
        '''
        if self.vel_gradient == 20:
            self.floc_cap = (566045 * self.basin_volume_Mgal + 224745) * 1E-6 * self.tpec_tic
        elif self.vel_gradient == 50:
            self.floc_cap = (673894 * self.basin_volume_Mgal + 217222) * 1E-6 * self.tpec_tic
        else:
            self.floc_cap = (952902 * self.basin_volume_Mgal + 177335) * 1E-6 * self.tpec_tic

        return self.floc_cap

    def elect(self):
        '''

        :return:
        '''
        self.g = self.vel_gradient * pyunits.second ** -1
        self.basin_volume_m3 = pyunits.convert(self.basin_volume_Mgal, to_units=pyunits.m ** 3)
        self.viscosity = 1E-3 * (pyunits.kilogram / (pyunits.second * pyunits.meter))
        self.power_needed = (self.g ** 2 * self.basin_volume_m3 * self.viscosity) * self.num_mixers
        self.power_required = pyunits.convert(self.power_needed, to_units=pyunits.kilowatt) / self.motor_eff
        self.floc_ei = self.power_required / self.flow_in

        return self.floc_ei

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        if not isinstance(unit_params, float):
            self.floc_setup(unit_params)
        else:
            self.floc_setup({})
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)