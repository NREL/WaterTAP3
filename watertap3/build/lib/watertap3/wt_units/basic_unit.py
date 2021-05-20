from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import basic_unit, financials
from wt_unit import WT3UnitProcess

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
            basis, cap_basis, cap_exp, elect, basis_year, kind = basic_unit(unit_process_name, case_specific=case_specific)
        else:
            basis, cap_basis, cap_exp, elect, basis_year, kind = basic_unit(unit_process_name)

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

        self.deltaP_outlet.unfix()
        self.deltaP_waste.unfix()
        self.pressure_out.fix(1)
        self.pressure_waste.fix(1)

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = elect  # kwh/m3

        financials.get_complete_costing(self.costing)