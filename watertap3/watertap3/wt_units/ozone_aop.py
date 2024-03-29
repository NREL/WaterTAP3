from pyomo.environ import value, Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

## REFERENCES
## CAPITAL:
# Regression based on Texas Water Board - IT3PR documentation Table 3.24
# https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf
## ELECTRICITY:
# "A Review of Ozone Systems Costs for Municipal Applications. Report by the Municipal Committee – IOA Pan American Group"
# (2018) B. Mundy et al. https://doi.org/10.1080/01919512.2018.1467187
# From source: "5.0–5.5 kWh/lb might be used to include total energy consumption of ozone generator, ozone destruct, nitrogen feed system, cooling water pumps, and other miscellaneous
# energy uses."

module_name = 'ozone_aop'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        Fixed capital for Ozone/Ozone AOP unit.

        :param unit_params: Input parameter dictionary from input sheet
        :type unit_params: dict
        :param toc_in: TOC concentration into unit [mg/L]
        :type toc_in: float
        :param aop: Boolean to indicate if unit is AOP or not.
        :type aop: bool
        :param contact_time: Ozone contact time [min]
        :type contact_time: float
        :param ct: Concentration * time (Ct) target [mg/(L*min)]
        :type ct: float
        :param mass_transfer: Mass transfer coefficient
        :type mass_transfer: float
        :param chemical_name: Name of oxidant used if unit is AOP
        :type chemical_name: str

        :return: Fixed capital cost for Ozone/Ozone AOP  [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        self.toc_in = pyunits.convert(self.conc_mass_in[time, 'toc'], to_units=(pyunits.mg / pyunits.liter))
        try:
            self.aop = unit_params['aop']
        except KeyError as e:
            self.aop = False
        try:
            self.contact_time = unit_params['contact_time'] * pyunits.minutes
            self.ct = unit_params['ct'] * (pyunits.mg / (pyunits.liter * pyunits.minute))
            self.mass_transfer = unit_params['mass_transfer'] * pyunits.dimensionless
        except KeyError as e:
            self.contact_time = 1 * pyunits.minutes
            self.ct = 1 * (pyunits.mg / (pyunits.liter * pyunits.minute))
            self.mass_transfer = 1 * pyunits.dimensionless
        self.ozone_consumption = ((self.toc_in + self.ct * self.contact_time) / self.mass_transfer)
        self.ozone_consumption = pyunits.convert(self.ozone_consumption, to_units=(pyunits.kg / pyunits.m ** 3))
        self.o3_toc_ratio = 1 + ((self.ct * self.contact_time) / self.toc_in)
        if self.aop:
            self.ox_dose = pyunits.convert((0.5 * self.o3_toc_ratio * self.toc_in), to_units=(pyunits.kg / pyunits.m ** 3))
            chem_name = unit_params['chemical_name']
            self.chem_dict = {
                    chem_name: self.ox_dose
                    }
            self.h2o2_base_cap = 1228
            self.h2o2_cap_exp = 0.2277
        else:
            self.chem_dict = {}
        dose = pyunits.convert(self.ozone_consumption, to_units=(pyunits.mg / pyunits.liter))
        flow = self.flow_in
        # ozone_cap = 368.1024498765 * (x0) + 1791.4380214814 * (x1) - 21.1751721133 * (x0 ** 2) + 90.5123958036 * (x0 * x1) - 193.6107786923 * (x1 ** 2) + 0.6038025161 * (
        #         x0 ** 3) + 0.0313834266 * (x0 ** 2 * x1) - 2.4261957652 * (x0 * x1 ** 2) + 5.2214653914 * (x1 ** 3) - 1888.3973953339
        ozone_cap = self.interp_cost_at_dose(dose(), flow())
        if self.aop:
            h2o2_flow = self.solution_vol_flow()
            h2o2_cap = self.h2o2_base_cap * h2o2_flow ** self.h2o2_cap_exp
        else:
            h2o2_cap = 0
        ozone_aop_cap = (ozone_cap + h2o2_cap) * 1E-3
        return ozone_aop_cap

    def interp_cost_at_dose(self, dose, flow):
        '''
        Determine a, b costing parameters as a function of flow and ozone dose
        :param flow: Volumetric flow into unit
        :type flow_in: float
        :param dose: ozone dose
        :return: ozone capital cost
        '''

        def power_curve(flow_mgd, a, b):
            return a * flow_mgd ** b

        df = pd.read_csv('data/ozone_cost.csv', header=0)

        doses = [1, 5, 10, 15, 20, 25]
        flow_interp = []
        cost_interp = []
        for i, k in enumerate(df['flow (mgd)']):
            costs = []
            for d in doses:
                cutal_ox = df[str(d)].to_numpy()
                costs.append(cutal_ox[i])
            flow_interp.append(k)
            cost_interp.append(np.interp(dose, doses, costs))
        (self.a, self.b), _ = curve_fit(power_curve, flow_interp, cost_interp, bounds=[[1E-5, 1E-5], [100000, 5]])
        iterp_cap = power_curve(flow, self.a, self.b)
        return iterp_cap

    def elect(self):
        '''
        Electricity intensity for Ozone/Ozone AOP unit.

        :param ozone_flow: Flow of ozone from ozone generator [lb/day]
        :type ozone_flow: float

        :return: Ozone/Ozone AOP electricity intenstiy [kWh/m3]
        '''
        ozone_flow = self.o3_flow()
        flow_in_m3hr = pyunits.convert(self.flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))
        electricity = (5 * ozone_flow) / flow_in_m3hr
        return electricity

    def solution_vol_flow(self):
        '''
        Determine oxidant solution flow rate [gal/day]

        :return: Oxidant solution flow [gal/day]
        '''
        flow_in_m3hr = pyunits.convert(self.flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))
        chemical_rate = flow_in_m3hr * self.ox_dose  # kg/hr
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
        return chemical_rate

    def o3_flow(self):
        '''
        Determine ozone flow rate [lb/hr]

        :return: Ozone flow [lb/hr]
        '''
        flow_in_m3hr = pyunits.convert(self.flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))
        ozone_flow = flow_in_m3hr * self.ozone_consumption
        ozone_flow = pyunits.convert(ozone_flow, to_units=(pyunits.lb / pyunits.hour))
        return ozone_flow

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)