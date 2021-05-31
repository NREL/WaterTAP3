from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import cost_curves, financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'basic_unit'
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
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

        unit_process_name = unit_params['unit_process_name']
        try:
            case_specific = unit_params['case_specific']
        except:
            case_specific = None

        if case_specific:
            basis, cap_basis, cap_exp, elect, basis_year, kind = cost_curves.basic_unit(unit_process_name, case_specific=case_specific)
        else:
            basis, cap_basis, cap_exp, elect, basis_year, kind = cost_curves.basic_unit(unit_process_name)

        self.chem_dict = {}
        self.costing.basis_year = basis_year
        constituents = self.config.property_package.component_list

        def fixed_cap():
            if kind == 'flow':
                flow_basis = basis * (pyunits.m ** 3 / pyunits.hour)
                flow_factor = flow_in / flow_basis
                basic_cap = cap_basis * flow_factor ** cap_exp
                return basic_cap

            if kind == 'mass':
                mass_basis = basis * (pyunits.kg / pyunits.hour)
                mass_in = 0
                for constituent in constituents:
                    mass_in += self.conc_mass_in[time, constituent]
                density = 0.6312 * mass_in + 997.86  # kg / m3
                total_mass_in = density * flow_in  # kg / hr
                mass_factor = total_mass_in / mass_basis
                basic_cap = cap_basis * mass_factor ** cap_exp
                return basic_cap

        def electricity(flow_in):
            # if unit_process_name in ['mbr_nitrification', 'mbr_denitrification'] and not case_specific:
            #     # Electricity consumption for MBRs from:
            #     # "Assessing Location and Scale of Urban Nonpotable Water Reuse Systems for Life-Cycle Energy Consumption and Greenhouse Gas Emissions" Kavvada et al (2016)
            #     # Equation located in SI
            #     return 9.5 * flow_in ** -0.3
            # else:
            return elect

        self.deltaP_outlet.unfix()
        self.deltaP_waste.unfix()
        self.pressure_out.fix(1)
        self.pressure_waste.fix(1)
        
        
        sys_cost_params = self.parent_block().costing_param
        if unit_process_name == "tramp_oil_tank":
            disposal_cost = 0.000114 # Kiran's disposal cost assumption $/m3
            self.costing.other_var_cost = flow_in * 24 * 365 * 0.00114 * sys_cost_params.plant_cap_utilization


        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)
        
        
        
