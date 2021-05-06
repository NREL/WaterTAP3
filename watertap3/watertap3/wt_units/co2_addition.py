from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for CHLORINE STORAGE AND FEED - FIGURE XXXXX
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:
# No expected energy consumption for CO2 because storage cylinder is at 1000 psig

module_name = 'co2_addition'
basis_year = 2019
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

        base_fixed_cap_cost = 0.464
        cap_scaling_exp = 0.7
        self.chem_dict = {}

        time = self.flowsheet().config.time.first()

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=base_fixed_cap_cost * flow_in ** cap_scaling_exp, doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0.01  # kwh/m3

        financials.get_complete_costing(self.costing)