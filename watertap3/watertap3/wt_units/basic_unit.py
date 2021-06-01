from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import cost_curves, financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'basic_unit'
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        if self.kind == 'flow':
            flow_basis = self.basis * (pyunits.m ** 3 / pyunits.hour)
            flow_factor = self.flow_in / flow_basis
            basic_cap = self.cap_basis * flow_factor ** self.cap_exp
            return basic_cap

        if kind == 'mass':
            mass_basis = self.basis * (pyunits.kg / pyunits.hour)
            mass_in = 0
            for constituent in self.constituents:
                mass_in += self.conc_mass_in[time, constituent]
            density = 0.6312 * mass_in + 997.86  # kg / m3
            total_mass_in = density * self.flow_in  # kg / hr
            mass_factor = total_mass_in / mass_basis
            basic_cap = self.cap_basis * mass_factor ** self.cap_exp
            return basic_cap

    def elect(self):
        if self.unit_process_name in ['mbr_nitrification', 'mbr_denitrification'] and not self.case_specific:
            # Electricity consumption for MBRs from:
            # "Assessing Location and Scale of Urban Nonpotable Water Reuse Systems for Life-Cycle Energy Consumption and Greenhouse Gas Emissions" Kavvada et al (2016)
            # Equation located in SI
            return 9.5 * self.flow_in ** -0.3
        else:
            return self.elect_intensity

    def get_costing(self, unit_params=None, year=None):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.unit_process_name = unit_params['unit_process_name']
        if 'case_specific' in unit_params.keys():
            self.case_specific = unit_params['case_specific']
            self.basis, self.cap_basis, self.cap_exp, self.elect_intensity, self.basis_year, self.kind = cost_curves.basic_unit(self.unit_process_name, case_specific=self.case_specific)
        else:
            self.case_specific = None
            self.basis, self.cap_basis, self.cap_exp, self.elect_intensity, self.basis_year, self.kind = cost_curves.basic_unit(self.unit_process_name)
        self.chem_dict = {}
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.constituents = self.config.property_package.component_list
        self.deltaP_outlet.unfix()
        self.deltaP_waste.unfix()
        self.pressure_out.fix(1)
        self.pressure_waste.fix(1)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)