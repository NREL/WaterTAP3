from pyomo.environ import Block, Expression, Var, Param, NonNegativeReals, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# McGiveney & Kawamura
## ELECTRICITY:
# 

module_name = 'rapid_mix'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def rapid_mix_setup(self, unit_params):
        time = self.flowsheet().config.time
        t = time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
        self.flow_in_gps = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.gallon / pyunits.second)
        self.chem_dict = {}
        self.residence_time = Var(time, initialize=5, domain=NonNegativeReals, units=pyunits.second, bounds=(5, 60), doc='Rapid mix residence time [sec]')
        
        try:
            self.vel_gradient = unit_params['vel_gradient']
            if self.vel_gradient not in [300, 600, 900]:
                self.vel_gradient = 900
        except (KeyError, TypeError) as e:
            self.vel_gradient = 900
        try:
            self.residence_time.fix(unit_params['residence_time'])
        except (KeyError, TypeError) as e:
            self.residence_time.fix(5)
        try:
            self.motor_eff = unit_params['motor_eff']
        except (KeyError, TypeError) as e:
            self.motor_eff = 0.75
        
        self.mixer_volume_gal = self.flow_in_gps * self.residence_time[t] 

    def fixed_cap(self):
        '''

        :return:
        '''

        if self.vel_gradient == 300:
            self.rapid_mix_cap = (3.2559 * self.mixer_volume_gal + 31023) * 1E-6 * self.tpec_tic
        elif self.vel_gradient == 600:
            self.rapid_mix_cap = (4.0668 * self.mixer_volume_gal + 33040) * 1E-6 * self.tpec_tic
        else:
            self.rapid_mix_cap = (7.0814 * self.mixer_volume_gal + 33269) * 1E-6 * self.tpec_tic

        return self.rapid_mix_cap

    def elect(self):
        '''

        :return:
        '''

        self.g = self.vel_gradient * pyunits.second ** -1
        self.basin_volume_m3 = pyunits.convert(self.mixer_volume_gal, to_units=pyunits.m ** 3)
        self.viscosity = 1E-3 * (pyunits.kilogram / (pyunits.second * pyunits.meter))
        self.power_needed = self.g ** 2 * self.basin_volume_m3 * self.viscosity
        self.power_required = pyunits.convert(self.power_needed, to_units=pyunits.kilowatt) / self.motor_eff

        self.rapid_mix_ei = self.power_required / self.flow_in

        return self.rapid_mix_ei 

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''

        if not isinstance(unit_params, float):
            self.rapid_mix_setup(unit_params)
        else:
            self.rapid_mix_setup({})
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)