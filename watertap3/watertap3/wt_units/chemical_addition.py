import pandas as pd
from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: Voutchkov (2018) figures 4.2 and 4.4

module_name = 'chemical_addition'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'dose': 10}**

        Fixed capital for chemical addition is a function of chemical dose, chemical solution flow, and the number of units.

        :param chemical_name: Chemical name to be used.
        :type chemical_name: str
        :param dose: Dose of chemical [mg/L]
        :type dose: float
        :return: Chemical addition fixed capital cost [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        def chem_addition(chem_name):
            df = pd.read_csv('data/chemical_addition.csv', index_col='chem_name')
            df = df.loc[chem_name].copy()
            return df.base, df.exp, df.ratio, df.density

        self.number_of_units = 2
        self.base_fixed_cap_cost = 900.97
        self.cap_scaling_exp = 0.6179
        chem_name = unit_params['chemical_name']
        self.base_fixed_cap_cost, self.cap_scaling_exp, self.ratio, self.solution_density = chem_addition(chem_name)
        self.dose = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.chem_dict = {chem_name: self.dose}
        source_cost = self.base_fixed_cap_cost * self.solution_vol_flow() ** self.cap_scaling_exp
        chem_cap = (source_cost * self.tpec_tic * self.number_of_units) * 1E-6
        return chem_cap

    def elect(self, unit_params):
        '''
        Electricity intensity.

        :param lift_height: Lift height for pump [ft]
        :type lift_height: float
        :param pump_eff: Pump efficiency
        :type pump_eff: float
        :param motor_eff: Motor efficiency
        :type motor_eff: float
        :return: Electricity intensity [kWh/m3]
        '''
        if 'lift_height' in unit_params.keys():
            self.lift_height = unit_params['lift_height'] * pyunits.ft
        else:
            self.lift_height = 100 * pyunits.ft
        if 'pump_eff' in unit_params.keys() and 'motor_eff' in unit_params.keys():
            self.pump_eff = unit_params['pump_eff'] * pyunits.dimensionless
            self.motor_eff = unit_params['motor_eff'] * pyunits.dimensionless
        else:
            self.pump_eff = 0.9 * pyunits.dimensionless
            self.motor_eff = 0.9 * pyunits.dimensionless
        soln_vol_flow = pyunits.convert(self.solution_vol_flow(), to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * soln_vol_flow * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in
        return electricity

    def solution_vol_flow(self):
        '''
        Chemical solution flow in gal/day

        :param solution_density: Solution density [kg/m3]
        :type solution_density: float

        :return: Chemical solution flow [gal/day]
        '''
        # self.solution_density = 1000 * (pyunits.kg / pyunits.m ** 3)
        chemical_rate = self.flow_in * self.dose
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
        soln_vol_flow = chemical_rate / self.solution_density / self.ratio
        soln_vol_flow = pyunits.convert(soln_vol_flow, to_units=(pyunits.gallon / pyunits.day))
        return soln_vol_flow

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(unit_params),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)