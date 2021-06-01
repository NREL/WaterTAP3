from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for FILTER MEDIA DUAL MEDIA - FIGURE 5.5.27
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
# https://www.lenntech.com/schema-of-an-iron-removal-system.htm
## ELECTRICITY:
# FOR BLOWER
# Loh, H. P., Lyons, Jennifer, and White, Charles W. Process Equipment Cost Estimation, Final Report.
# United States: N. p., 2002. Web. doi:10.2172/797810.


module_name = 'iron_and_manganese_removal'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.cap_scaling_exp = 0.7
        self.cap_scaling_val = 4732 * (pyunits.m ** 3 / pyunits.hour)
        self.number_of_units = 6
        self.filter_surf_area = 580 * pyunits.m ** 2
        self.filter_surf_area = pyunits.convert(self.filter_surf_area, to_units=pyunits.ft ** 2)
        self.air_water_ratio = 0.001 * pyunits.dimensionless  # v / v
        self.air_flow_rate = self.air_water_ratio * self.cap_scaling_val
        self.air_blower_cap = 100000  # fixed cost for air blower that should be changed
        self.chem_dict = {}
        dual_media_filter_cap = 21377 + 38.319 * self.filter_surf_area
        filter_backwash_cap = 92947 + 292.44 * self.filter_surf_area
        total_cap_cost = (((self.air_blower_cap + filter_backwash_cap + (dual_media_filter_cap * self.number_of_units))) * self.tpec_tic) * 1E-6
        cap_scaling_factor = self.flow_in / self.cap_scaling_val
        fe_mn_cap = total_cap_cost * cap_scaling_factor ** self.cap_scaling_exp
        return fe_mn_cap

    def electricity(self):
        self.blower_power = (147.8 * (pyunits.hp / (pyunits.m ** 3 / pyunits.hour)) * self.air_flow_rate)
        self.blower_power = pyunits.convert(self.blower_power, to_units=pyunits.kilowatt)
        electricity = self.blower_power / self.flow_in  # kWh / m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)