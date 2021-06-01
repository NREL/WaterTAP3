import pandas as pd
from pyomo.environ import Block, Expression, units as pyunits
from scipy.optimize import curve_fit
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE:
## CAPITAL
# Interpolated values for UV cost based on Texas Water Board - IT3PR documentation Table 3.22
# https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf
## ELECTRICITY

module_name = 'uv_aop'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def uv_regress(self):

        def power_curve(x, a, b):
            return a * x ** b

        self.df = pd.read_csv('data/uv_cost_interp.csv', index_col='flow')
        self.flow_points = [1E-8]
        self.flow_list = [1E-8, 1, 3, 5, 10, 25]  # flow in mgd
        for flow in self.flow_list[1:]:
            temp = self.df.loc[flow]
            cost = temp[((temp.dose == self.uv_dose) & (temp.uvt == self.uvt_in))]
            cost = cost.iloc[0]['cost']
            self.flow_points.append(cost)
        self.coeffs, self.cov = curve_fit(power_curve, self.flow_list, self.flow_points)
        self.a, self.b = coeffs[0], coeffs[1]

    def solution_vol_flow(self):  # m3/hr
        chemical_rate = self.flow_in * self.ox_dose  # kg/hr
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
        soln_vol_flow = chemical_rate
        return soln_vol_flow  # lb / day

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.uvt_in = unit_params['uvt_in']
        self.uv_dose = unit_params['uv_dose']
        self.aop = unit_params['aop']
        if self.aop:
            self.ox_dose = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
            chem_name = unit_params['chemical_name']
            self.chem_dict = {chem_name: self.ox_dose}
            self.h2o2_base_cap = 1228
            self.h2o2_cap_exp = 0.2277
        else:
            self.chem_dict = {}
        uv_regress()
        flow_in_mgd = pyunits.convert(self.flow_in, to_units=(pyunits.Mgallons / pyunits.day))
        uv_cap = (self.a * flow_in_mgd ** self.b) * 1E-3
        if aop:
            h2o2_cap = (self.h2o2_base_cap * self.solution_vol_flow() ** self.h2o2_cap_exp) * 1E-3
        else:
            h2o2_cap = 0
        uv_aop_cap = h2o2_cap + uv_cap
        return uv_aop_cap

    def elect(self):  # m3/hr
        electricity = 0.1  # kWh / m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)