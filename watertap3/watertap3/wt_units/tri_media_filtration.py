from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE:
# from IT3PR, section 3.5.6 figure 3.3
# from IT3PR, section 3.5.6 figure 3.3

module_name = 'tri_media_filtration'
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

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        
        self.chem_dict = {}
        self.base_fixed_cap_cost = 0.72557
        self.cap_scaling_exp = 0.5862

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.base_fixed_cap_cost *
                                                                flow_in ** self.cap_scaling_exp,
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0.19813  # kwh/m3

        financials.get_complete_costing(self.costing)