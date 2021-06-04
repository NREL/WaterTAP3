from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
# Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis) (2010)
## ELECTRICITY:


module_name = 'sedimentation'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.flow_in = self.flow_vol_in[time] # needs to be in m3/s, so no conversion
        self.chem_dict = {}
        self.base_fixed_cap_cost = 13572
        self.cap_scaling_exp = 0.3182
        self.settling_velocity = unit_params['settling_velocity'] * (pyunits.m / pyunits.second)
        basin_surface_area = self.flow_in / self.settling_velocity
        basin_surface_area = pyunits.convert(basin_surface_area, to_units=pyunits.ft ** 2)
        sed_cap = self.base_fixed_cap_cost * basin_surface_area ** self.cap_scaling_exp * self.tpec_tic * 1E-6
        return sed_cap

    def elect(self):  # m3/hr
        electricity = 0
        return electricity

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