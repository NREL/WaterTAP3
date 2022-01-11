from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for LIQUID ALUM FEED - FIGURE 5.5.6
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:

module_name = 'alum_addition'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'dose': 10}**

        :param dose: Alum dose [mg/L]
        :type dose: float
        :return: Alum addition fixed capital cost [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.number_of_units = 2
        self.base_fixed_cap_cost = 15408
        self.cap_scaling_exp = 0.5479
        chem_name = 'Aluminum_Al2_SO4_3'
        self.chemical_dosage = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.chem_dict = {chem_name: self.chemical_dosage}
        source_cost = self.base_fixed_cap_cost * self.solution_vol_flow() ** self.cap_scaling_exp
        alum_cap = (source_cost * self.tpec_tic * self.number_of_units) * 1E-6
        return alum_cap

    def elect(self):
        '''
        Electricity intensity.

        :return: Electricity intensity [kWh/m3]
        '''
        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless
        soln_vol_flow = pyunits.convert(self.solution_vol_flow(), to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * soln_vol_flow * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in
        return electricity

    def solution_vol_flow(self):
        '''
        Chemical solution flow in gal/day

        :param solution_density: Alum solution density [kg/m3]
        :type solution_density: float
        :param ratio_in_solution: Ratio of alum in solution
        :type ratio_in_solution: float
        :return: Alum solution flow [gal/day]
        '''
        self.solution_density = 1360 * (pyunits.kg / pyunits.m ** 3)
        self.ratio_in_solution = 0.50
        chemical_rate = self.flow_in * self.chemical_dosage
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
        soln_vol_flow = chemical_rate / self.solution_density / self.ratio_in_solution
        soln_vol_flow = pyunits.convert(soln_vol_flow, to_units=(pyunits.gallon / pyunits.day))
        return soln_vol_flow

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