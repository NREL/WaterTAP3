from pyomo.environ import Block, Expression, Var, Constraint, NonNegativeReals, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# McGivney & Kawamura (2008) 
## ELECTRICITY:
# Biosolids Treatment Processes (2007)
# https://doi.org/10.1007/978-1-59259-996-7

## FACT SHEETS
# https://www.epa.gov/sites/default/files/2018-11/documents/recessed-plate-filter-press-factsheet.pdf
# https://www.epa.gov/sites/default/files/2018-11/documents/belt-filter-press-factsheet.pdf


module_name = 'filter_press'
basis_year = 2007
tpec_or_tic = 'TPEC'



class UnitProcess(WT3UnitProcess):

    def fp_setup(self, unit_params):

        time = self.flowsheet().config.time
        t = time.first()
        self.flow_in_ft3_d = pyunits.convert(self.flow_vol_in[t], to_units=(pyunits.ft ** 3 / pyunits.day))

        try:
            self.filter_press_type = unit_params['type']
            if self.filter_press_type not in ['belt', 'pressure']:
                self.filter_press_type = 'belt'
        except KeyError as e:
            self.filter_press_type = 'belt'
        try:
            self.hours_per_day_operation = unit_params['hours_per_day_operation'] * (pyunits.hours / pyunits.day)
            self.cycle_time = unit_params['cycle_time'] * pyunits.hours
            self.cycles_per_day = self.hours_per_day_operation / self.cycle_time
        except KeyError as e:
            self.hours_per_day_operation = 24 * (pyunits.hours / pyunits.day)
            self.cycle_time = 3 * pyunits.hours
            self.cycles_per_day = self.hours_per_day_operation / self.cycle_time

        self.press_capacity = self.flow_in_ft3_d / self.cycles_per_day

    def fixed_cap(self):
        '''

        :return:
        '''
        
        t = self.flowsheet().config.time.first()
        self.flow_in_gal_hr = pyunits.convert(self.flow_vol_in[t], to_units=(pyunits.gallon / pyunits.hour))
        self.chem_dict = {}
        if self.filter_press_type == 'belt':
            self.fp_cap = 146.29 * self.flow_in_gal_hr + 433972

        if self.filter_press_type == 'pressure':
            self.fp_cap = 102794 * self.flow_in_gal_hr ** 0.4216

        return self.fp_cap * 1E-6

    def elect(self):
        '''

        :return:
        '''
        t = self.flowsheet().config.time.first()
        self.flow_in_m3_yr = pyunits.convert(self.flow_vol_in[t], to_units=(pyunits.m ** 3 / pyunits.year))

        if self.filter_press_type == 'belt':
            ## kWh/yr, Assumes 6% solids
            self.fp_annual_energy = 16.285 * self.press_capacity ** 1.2434

        if self.filter_press_type == 'pressure':
            ## kWh/yr, Assumes 6% solids
            self.fp_annual_energy = 16.612 * self.press_capacity ** 1.2195
        
        self.fp_elect_intens = self.fp_annual_energy / self.flow_in_m3_yr

        electricity = self.fp_elect_intens

        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        if not isinstance(unit_params, float):
            self.fp_setup(unit_params)
        else:
            self.fp_setup({})
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)
