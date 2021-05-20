from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'media_filtration'
basis_year = 2007
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

        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        self.chem_dict = {}

        filtration_rate = 10 * (pyunits.meter / pyunits.hour)
        number_of_units = 6

        def base_filter_surface_area(flow_in):
            surface_area = pyunits.convert((flow_in / filtration_rate), to_units=pyunits.ft ** 2)  # conversion to ft2
            return surface_area  # total surface area of the filter, in ft2

        def dual_media_filter(flow_in):
            dual_cost = (38.319 * base_filter_surface_area(flow_in) + 21377) * number_of_units  # calculations done based on ft2
            return dual_cost

        def filter_backwash(flow_in):
            filter_backwash_cost = 292.44 * base_filter_surface_area(flow_in) + 92497  # calculations done based on ft2
            return filter_backwash_cost

        def fixed_cap(flow_in):
            media_filt_cap = (dual_media_filter(flow_in) + filter_backwash(flow_in)) * 1E-6
            return media_filt_cap * tpec_tic

        def electricity(flow_in):  # m3/hr
            electricity = 0
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)