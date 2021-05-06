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

        cap_scaling_exp = 0.7
        cap_scaling_val = 4732 * (pyunits.m ** 3 / pyunits.hour)
        number_of_units = 6
        filter_surf_area = 580 * pyunits.m ** 2
        filter_surf_area = pyunits.convert(filter_surf_area, to_units=pyunits.ft ** 2)

        air_water_ratio = 0.001 * pyunits.dimensionless  # v / v
        air_flow_rate = air_water_ratio * cap_scaling_val

        # Assumes 3 stage compressor, 85% efficiency
        blower_power = (147.8 * (pyunits.hp / (pyunits.m ** 3 / pyunits.hour)) * air_flow_rate)
        blower_power = pyunits.convert(blower_power, to_units=pyunits.kilowatt)
        air_blower_cap = 100000  # fixed cost for air blower that should be changed

        self.chem_dict = {}

        def fixed_cap(flow_in):
            dual_media_filter_cap = 21377 + 38.319 * filter_surf_area
            filter_backwash_cap = 92947 + 292.44 * filter_surf_area
            total_cap_cost = (((air_blower_cap + filter_backwash_cap + (dual_media_filter_cap * number_of_units))) * tpec_tic) * 1E-6
            cap_scaling_factor = flow_in / cap_scaling_val
            fe_mn_cap = total_cap_cost * cap_scaling_factor ** cap_scaling_exp
            return fe_mn_cap

        def electricity(flow_in):
            electricity = blower_power / flow_in  # kWh / m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)