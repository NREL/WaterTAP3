from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

module_name = 'static_mixer'
basis_year = 2010
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

        number_of_units = 2
        lift_height = 100 * pyunits.ft
        pump_eff = 0.9 * pyunits.dimensionless
        motor_eff = 0.9 * pyunits.dimensionless

        self.chem_dict = {}

        # a, b, c generated with the following code:
        # Data from ______________________
        # from scipy.optimize import curve_fit
        # import numpy as np
        # flow_cc = np.array([3.6, 18, 36, 72, 108, 144, 180])  # m3/hr
        # cost_cc = np.array([5916, 9511, 11930, 15123, 17444, 19336, 20960])  ## $$
        #
        # def func(x, a, b, c):
        #     return a + b * x ** c
        #
        # cc_params, _ = curve_fit(func, flow_cc, cost_cc)
        # a, b, c = cc_params[0], cc_params[1], cc_params[2]

        a = 14317.142
        b = 389.454
        c = -57.342

        def fixed_cap(flow_in):
            source_cost = a + b * flow_in ** c
            mix_cap = (source_cost * tpec_tic * number_of_units) * 1E-6
            return mix_cap

        def electricity(flow_in):  # m3/hr
            electricity = 0 * flow_in  # kWh/m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)