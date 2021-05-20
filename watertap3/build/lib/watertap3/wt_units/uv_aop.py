import pandas as pd
from pyomo.environ import Block, Expression, units as pyunits
from scipy.optimize import curve_fit
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE:
# TEXAS WATER BOARD

module_name = 'uv_aop'
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

        # FIRST TIME POINT FOR STEADY-STATE ASSUMPTION
        time = self.flowsheet().config.time.first()
        # UNITS = m3/hr
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        try:
            uvt_in = unit_params['uvt_in']
            uv_dose = unit_params['uv_dose']
        except:
            uvt_in = 0.9
            uv_dose = 100

        aop = unit_params['aop']

        if aop:
            ox_dose = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
            chem_name = unit_params['chemical_name']
            self.chem_dict = {chem_name: ox_dose}
            h2o2_base_cap = 1228
            h2o2_cap_exp = 0.2277
        else:
            self.chem_dict = {}

        def power_curve(x, a, b):
            return a * x ** b

        df = pd.read_csv('data/uv_cost_interp.csv', index_col='flow')
        flow_points = [1E-8]
        flow_list = [1E-8, 1, 3, 5, 10, 25]  # flow in mgd

        for flow in flow_list[1:]:
            temp = df.loc[flow]
            cost = temp[((temp.dose == uv_dose) & (temp.uvt == uvt_in))]
            cost = cost.iloc[0]['cost']
            flow_points.append(cost)

        coeffs, cov = curve_fit(power_curve, flow_list, flow_points)
        a, b = coeffs[0], coeffs[1]

        def solution_vol_flow(flow_in):  # m3/hr
            chemical_rate = flow_in * ox_dose  # kg/hr
            chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
            soln_vol_flow = chemical_rate
            return soln_vol_flow  # lb / day

        def fixed_cap(flow_in):
            flow_in_mgd = pyunits.convert(flow_in, to_units=(pyunits.Mgallons / pyunits.day))

            uv_cap = (a * flow_in_mgd ** b) * 1E-3

            if aop:
                h2o2_cap = (h2o2_base_cap * solution_vol_flow(flow_in) ** h2o2_cap_exp) * 1E-3
            else:
                h2o2_cap = 0

            uv_aop_cap = h2o2_cap + uv_cap
            return uv_aop_cap

        def electricity():  # m3/hr
            electricity = 0.1  # kWh / m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity()  # kwh/m3

        financials.get_complete_costing(self.costing)