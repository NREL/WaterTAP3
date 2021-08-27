from pyomo.environ import Block, Expression, Var, Constraint, NonNegativeReals, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess
from scipy.optimize import curve_fit
import pandas as pd

## REFERENCE
## CAPITAL:
# Development Of A Preliminary Cost Estimation Method For Water Treatment Plants
# Sharma, Jwala Raj - THESIS, 2010
# https://rc.library.uta.edu/uta-ir/handle/10106/4924
## ELECTRICITY:
# Development Of A Preliminary Cost Estimation Method For Water Treatment Plants
# Sharma, Jwala Raj - THESIS, 2010
# https://rc.library.uta.edu/uta-ir/handle/10106/4924
## SIZING
# http://automaticfilterpress.com/filter-press-sizing-calculations/

module_name = 'filter_press'
basis_year = 2010
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fp_setup(self, unit_params):
        try:
            self.filter_press_type = unit_params['type']
        except:
            self.filter_press_type = 'frame'
        try:
            self.slurry_dry_solids = unit_params['slurry_dry_solids']
            self.processing_time = unit_params['processing_time']
        except:
            self.slurry_dry_solids = '5%'
            self.processing_time = 8 * pyunits.hours

        # self.num_cycles = (24 * pyunits.hours / self.processing_time) * pyunits.day ** -1
        self.num_cycles = 3 * pyunits.day ** -1
        self.gal_per_cycle = pyunits.convert(self.flow_vol_in[self.t], to_units=(pyunits.gallons / pyunits.day)) / self.num_cycles
        df = pd.read_csv('data/filter_press.csv')
        x = df.gal_cycle.to_list()
        y = df[self.slurry_dry_solids].to_list()

        def linear(m, x):
            return m * x

        slope, _ = curve_fit(linear, x, y)

        self.press_volume = Var(self.flowsheet().config.time,
                                initialize=0,
                                domain=NonNegativeReals,
                                doc='Filter press volume [ft3]')

        self.press_vol_constr = Constraint(expr=self.press_volume[self.t] == slope[0] * self.gal_per_cycle)
        # self.press_volume = slope[0] * self.gal_per_cycle

    def fixed_cap(self):
        '''

        :return:
        '''

        self.chem_dict = {}
        if self.filter_press_type == 'frame':
            self.fp_cap_unadj = (0.0093 * self.press_volume[self.t] ** 3 - 12.453 * self.press_volume[self.t] ** 2 + 9607.7 * self.press_volume[self.t] + 734176) * 1E-6 # convert to $MM
            self.labor_factor = 0.21 # from source - labor is 21% of cost from this cost curve
            self.fp_cap = self.fp_cap_unadj * (1 - self.labor_factor) # remove labor costs

        if self.filter_press_type == 'belt':
            flow_in_gpm = pyunits.convert(self.flow_in, to_units=(pyunits.gallon / pyunits.minute))
            self.fp_cap_unadj = (-0.0727 * flow_in_gpm ** 3 + 48.326 * flow_in_gpm ** 2 + 13071 * flow_in_gpm + 389081) * 1E-6
            self.labor_factor = 0.24 # from source - labor is 24% of cost from this cost curve
            self.fp_cap = self.fp_cap_unadj * (1 - self.labor_factor) # remove labor costs
        return self.fp_cap

    def elect(self):
        '''

        :return:
        '''
        self.elect_cost = 0.0981  # $/kWh - this is the cost of electricity per kWh from source, used to back out electricity intensity
        if self.filter_press_type == 'frame':
            self.elect_factor = 0.1 # from source - electricity *cost* is 10% of cost from this curve
            self.fp_elect_cost = (-0.0021 * self.press_volume[self.t] ** 3 + 3.288 * self.press_volume[self.t] ** 2 + 340.87 * self.press_volume[self.t] + 353816) * 1E-6 * self.elect_factor
        if self.filter_press_type == 'belt':
            flow_in_gpm = pyunits.convert(self.flow_in, to_units=(pyunits.gallon / pyunits.minute))
            self.elect_factor = 0.3 # from source - electricity *cost* is 10% of cost from this curve
            self.fp_elect_cost = (-0.0727 * flow_in_gpm ** 3 + 48.326 * flow_in_gpm ** 2 + 13071 * flow_in_gpm + 389081) * 1E-6 * self.elect_factor
        self.fp_elect = (self.fp_elect_cost / self.elect_cost) / self.processing_time
        electricity = self.fp_elect / self.flow_in

        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        time = self.flowsheet().config.time
        self.t = time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.fp_setup(unit_params)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)