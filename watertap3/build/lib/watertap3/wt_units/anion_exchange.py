from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import cost_curve, financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'anion_exchange'
basis_year = 2017
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

        tds_in = unit_params['tds_in']

        cost_coeffs, elect_coeffs, mats_name, mats_cost, _ = cost_curve(module_name, tds_in=tds_in)

        for k, v in mats_cost.items():
            mats_cost[k] = v * (pyunits.kg / pyunits.m ** 3)

        self.chem_dict = mats_cost

        def fixed_cap(flow_in):
            source_cost = cost_coeffs[0] * flow_in ** cost_coeffs[1]  # $
            return source_cost * 1E-6  # M$

        def electricity(flow_in):  # m3/hr
            electricity = elect_coeffs[0] * flow_in ** elect_coeffs[1]  # kWh/m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)