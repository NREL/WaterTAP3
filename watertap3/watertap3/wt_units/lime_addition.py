from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for LIME FEED - FIGURE 5.5.9
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:

module_name = 'lime_addition'
basis_year = 2007
tpec_or_tic = 'TPEC'

class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'lime': 10}**

        Fixed capital for lime addition is a function of lime dose, lime solution flow, and the number of units.

        :param lime: Lime dose [mg/L]
        :type lime: float

        :return: Lime addition fixed capital cost [$MM]
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.number_of_units = 2
        # self.base_fixed_cap_cost = 16972
        # self.cap_scaling_exp = 0.5435
        self.base_fixed_cap_cost = 12985
        self.cap_scaling_exp = 0.5901
        chem_name = 'Lime_Suspension_CaOH_2'
        self.chemical_dosage = pyunits.convert(unit_params['lime'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.chem_dict = {chem_name: self.chemical_dosage}
        soln_vol_flow, self.chemical_rate = self.solution_vol_flow()
        source_cost = self.base_fixed_cap_cost * self.chemical_rate ** self.cap_scaling_exp
        lime_cap = (source_cost * self.tpec_tic * self.number_of_units) * 1E-6
        return lime_cap

    def elect(self):
        '''
        Electricity intensity.

        :return: Electricity intensity [kWh/m3]
        '''
        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless
        self.soln_vol_flow, chemical_rate = self.solution_vol_flow()
        self.soln_vol_flow = pyunits.convert(self.soln_vol_flow, to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * self.soln_vol_flow * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in
        return electricity

    def solution_vol_flow(self):
        '''
        Chemical solution flow in gal/day

        :param solution_density: Solution density [kg/m3]
        :type solution_density: float

        :return: Lime solution vol. flow [gal/day], Lime solution mass flow [lb/day]
        '''
        self.solution_density = 1250 * (pyunits.kg / pyunits.m ** 3)
        chemical_rate = self.flow_in * self.chemical_dosage
        soln_vol_flow = chemical_rate / self.solution_density
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
        soln_vol_flow = pyunits.convert(soln_vol_flow, to_units=(pyunits.gallon / pyunits.min))
        return soln_vol_flow, chemical_rate

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