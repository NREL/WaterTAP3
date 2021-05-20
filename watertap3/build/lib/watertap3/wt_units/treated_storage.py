from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'treated_storage'
basis_year = 2002
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

        a = 0.00344
        b = 0.72093
        self.storage_duration = unit_params['hours'] * pyunits.hours  # hours
        capacity_needed = flow_in * self.storage_duration

        def fixed_cap(flow_in):
            storage_cap = a * capacity_needed ** b
            return storage_cap  # $MM

        self.chem_dict = {}

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0  # kwh/m3

        financials.get_complete_costing(self.costing)