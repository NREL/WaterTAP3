from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for FILTER MEDIA DUAL MEDIA - FIGURE 5.5.27
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:
# An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant
# Water 2020, 12, 28; doi:10.3390/w12010028

module_name = 'media_filtration'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.chem_dict = {}
        media_filt_cap = self.tpec_tic * (self.dual_media_filter() + self.filter_backwash()) * 1E-6
        return media_filt_cap

    def elect(self):
        electricity = 0.00015
        return electricity

    def base_filter_surface_area(self):
        self.filtration_rate = 10 * (pyunits.meter / pyunits.hour)
        surface_area = pyunits.convert((self.flow_in / self.filtration_rate), to_units=pyunits.ft ** 2)
        return surface_area

    def dual_media_filter(self):
        self.number_of_units = 6
        dual_cost = (38.319 * self.base_filter_surface_area() + 21377) * self.number_of_units
        return dual_cost

    def filter_backwash(self):
        filter_backwash_cost = 292.44 * self.base_filter_surface_area() + 92497
        return filter_backwash_cost

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)