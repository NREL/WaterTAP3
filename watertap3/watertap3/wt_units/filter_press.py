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
## FACT SHEETS
# https://www.epa.gov/sites/default/files/2018-11/documents/recessed-plate-filter-press-factsheet.pdf
# https://www.epa.gov/sites/default/files/2018-11/documents/belt-filter-press-factsheet.pdf


module_name = 'filter_press'
basis_year = 2010
tpec_or_tic = 'TPEC'

data = {
        'gal_per_cycle': [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        '1%': [0.0, 0.49, 0.98, 1.47, 1.96, 2.46, 2.95, 3.44, 3.93, 4.42, 4.91],
        '2%': [0.0, 0.98, 1.96, 2.95, 3.92, 4.91, 5.89, 6.88, 7.86, 8.84, 9.82],
        '3%': [0.0, 1.47, 2.95, 4.42, 5.89, 7.37, 8.84, 10.31, 11.79, 13.26, 14.73],
        '4%': [0.0, 1.95, 3.93, 5.89, 7.86, 9.82, 11.79, 13.75, 15.72, 17.68, 19.64],
        '5%': [0.0, 2.45, 4.91, 7.37, 9.82, 12.28, 14.73, 17.19, 19.64, 22.1, 24.5],
        '6%': [0.0, 3.64, 5.89, 8.84, 11.79, 14.73, 17.68, 20.63, 23.57, 26.52, 19.47],
        '7%': [0.0, 3.93, 6.88, 10.31, 13.75, 17.19, 20.63, 24.06, 27.5, 30.94, 34.38],
        '8%': [0.0, 4.11, 7.66, 11.79, 15.72, 19.64, 23.57, 27.5, 31.43, 35.36, 39.29],
        '9%': [0.0, 4.42, 8.84, 13.26, 17.68, 22.1, 26.52, 30.94, 35.36, 39.78, 44.2],
        '10%': [0.0, 4.91, 9.82, 14.73, 19.64, 24.56, 29.47, 34.38, 39.29, 44.2, 49.11]
        }


class UnitProcess(WT3UnitProcess):

    def fp_setup(self, unit_params):
        time = self.flowsheet().config.time
        try:
            self.filter_press_type = unit_params['type']
        except:
            self.filter_press_type = 'frame'
        try:
            self.slurry_dry_solids = unit_params['slurry_dry_solids']
            self.processing_time = unit_params['processing_time'] * pyunits.hours
            self.cycles_per_day = unit_params['cycles_per_day'] * pyunits.dimensionless
        except:
            self.slurry_dry_solids = '5%'
            self.processing_time = 8 * pyunits.hours
            self.cycles_per_day = 3 * pyunits.dimensionless

        self.num_cycles = (24 * pyunits.hours / self.processing_time) * pyunits.day ** -1
        # self.num_cycles = 3 * pyunits.day ** -1
        self.gal_per_cycle = pyunits.convert(self.flow_vol_out[self.t], to_units=(pyunits.gallons / pyunits.day)) / self.num_cycles
        self.data = data
        x = self.data['gal_per_cycle']
        y = self.data[self.slurry_dry_solids]

        self.slope, _ = curve_fit(lambda m, x: m * x, x, y)

        self.press_volume = Var(time,
                                initialize=0,
                                domain=NonNegativeReals,
                                bounds=(0, 1000),
                                doc='Filter press volume [ft3]')

        self.num_press = Var(time,
                             initialize=0,
                             domain=NonNegativeReals,
                             doc='Number of filter presses')

        self.press_vol_constr = Constraint(expr=self.press_volume[self.t] == self.slope[0] * self.gal_per_cycle)

        self.num_press_constr = Constraint(expr=self.num_press[self.t] == self.flow_vol_out[self.t] / self.press_volume[self.t])
        # self.press_volume = slope[0] * self.gal_per_cycle

    def fixed_cap(self):
        '''

        :return:
        '''

        self.chem_dict = {}
        if self.filter_press_type == 'frame':
            self.fp_cap_unadj = (0.0093 * self.press_volume[self.t] ** 3 - 12.453 * self.press_volume[self.t] ** 2 + 9607.7 * self.press_volume[self.t] + 734176) * 1E-6  # convert to $MM
            self.labor_factor = 0.21  # from source - labor is 21% of cost from this cost curve
            self.fp_cap = self.fp_cap_unadj * (1 - self.labor_factor)  # remove labor costs

        if self.filter_press_type == 'belt':
            flow_in_gpm = pyunits.convert(self.flow_in, to_units=(pyunits.gallon / pyunits.minute))
            self.fp_cap_unadj = (-0.0727 * flow_in_gpm ** 3 + 48.326 * flow_in_gpm ** 2 + 13071 * flow_in_gpm + 389081) * 1E-6
            self.labor_factor = 0.24  # from source - labor is 24% of cost from this cost curve
            self.fp_cap = self.fp_cap_unadj * (1 - self.labor_factor)  # remove labor costs
        return self.fp_cap

    def elect(self):
        '''

        :return:
        '''
        self.elect_cost = 0.0981  # $/kWh - this is the cost of electricity per kWh from source, used to back out electricity intensity
        if self.filter_press_type == 'frame':
            self.elect_factor = 0.1  # from source - electricity *cost* is 10% of cost from this curve
            self.fp_elect_cost = (-0.0021 * self.press_volume[self.t] ** 3 + 3.288 * self.press_volume[self.t] ** 2 +
                                  340.87 * self.press_volume[self.t] + 353816) * 1E-6 * self.elect_factor
        if self.filter_press_type == 'belt':
            flow_in_gpm = pyunits.convert(self.flow_in, to_units=(pyunits.gallon / pyunits.minute))
            self.elect_factor = 0.3  # from source - electricity *cost* is 30% of cost from this curve
            self.fp_elect_cost = (-0.0727 * flow_in_gpm ** 3 + 48.326 * flow_in_gpm ** 2 +
                                  13071 * flow_in_gpm + 389081) * 1E-6 * self.elect_factor
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