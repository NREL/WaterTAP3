from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'microfiltration'
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
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=(pyunits.Mgallons / pyunits.day))

        self.chem_dict = {}
        base_fixed_cap_cost = 2.5

        def fixed_cap(flow_in):
            mf_cap = base_fixed_cap_cost * flow_in
            return mf_cap

        def electricity():
            electricity = 0.307
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity()  # kwh/m3

        financials.get_complete_costing(self.costing)