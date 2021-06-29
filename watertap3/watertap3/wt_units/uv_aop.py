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

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'aop': True, 'uv_dose': 350, 'dose': 5, 'chemical_name': 'Hydrogen Peroxide'}**

        :param aop: (**required**) Boolean that determines if UV is used with AOP. Must be either True or False
        :type aop: bool
        :param uvt_in: (**optional**, default is 0.9) UV transmission (UVT) into unit
        :type uvt_in: float
        :param uv_dose: (**optional**, default is 100) Reduction Equivalent Dose (RED)  [mJ/cm2]
        :type uv_dose: float
        :param dose: (**optional**, no default) Dose for oxidant (if AOP) [mg/L]
        :type dose: float
        :param chemical_name: (**optional**, default is ``'Hydrogen_Peroxide'``) Name of oxidant used for AOP.
        :type chemical_name: str


        :return: Fixed capital for UV or UV+AOP unit [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.aop = unit_params['aop']
        try:
            self.uvt_in = unit_params['uvt_in']
            self.uv_dose = unit_params['uv_dose']
            chem_name = unit_params['chemical_name']
        except:
            self.uvt_in = 0.9
            self.uv_dose = 100
            chem_name = 'Hydrogen_Peroxide'
        if self.aop:
            self.ox_dose = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
            self.chem_dict = {chem_name: self.ox_dose}
            self.h2o2_base_cap = 1228
            self.h2o2_cap_exp = 0.2277
        else:
            self.chem_dict = {}
        self.a, self.b = self.uv_regress()
        flow_in_mgd = pyunits.convert(self.flow_in, to_units=(pyunits.Mgallons / pyunits.day))
        uv_cap = (self.a * flow_in_mgd ** self.b) * 1E-3
        if self.aop:
            h2o2_cap = (self.h2o2_base_cap * self.solution_vol_flow() ** self.h2o2_cap_exp) * 1E-3
        else:
            h2o2_cap = 0
        uv_aop_cap = h2o2_cap + uv_cap
        return uv_aop_cap

    def elect(self):  # m3/hr
        electricity = 0.1  # kWh / m3
        return electricity

    def uv_regress(self):
        '''
        Determine a, b costing parameters as a function of flow, UVT, and UV dose for unit.

        :param flow_in: Volumetric flow into unit [MGD]
        :type flow_in: float
        :param uvt_in: UV transmission (UVT) into unit
        :type uvt_in: float
        :param uv_dose: UV dose used by the unit [mg/L]
        :type uv_dose: float
        :return: a, b
        '''

        def power_curve(x, a, b):
            '''
            Return power curve. Used for fitting cost data to determine a, b.
            '''
            return a * x ** b

        self.df = pd.read_csv('data/uv_cost_interp.csv', index_col='flow')
        self.flow_points = [1E-8]
        self.flow_list = [1E-8, 1, 3, 5, 10, 25]  # flow in mgd
        for flow in self.flow_list[1:]:
            temp = self.df.loc[flow]
            cost = temp[((temp.dose == self.uv_dose) & (temp.uvt == self.uvt_in))]
            cost = cost.iloc[0]['cost']
            self.flow_points.append(cost)
        coeffs, cov = curve_fit(power_curve, self.flow_list, self.flow_points)
        self.a, self.b = coeffs[0], coeffs[1]
        return self.a, self.b

    def solution_vol_flow(self):  # m3/hr
        '''
        Determine oxidant solution flow rate in gal / day

        :return: Oxidant solution flow [gal/day]
        '''
        chemical_rate = self.flow_in * self.ox_dose  # kg/hr
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
        soln_vol_flow = chemical_rate
        return soln_vol_flow  # lb / day

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)