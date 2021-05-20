import numpy as np
import pandas as pd
from pyomo.environ import Block, units as pyunits
from watertap3.utils import financials, ml_regression
from wt_unit import WT3UnitProcess

## REFERENCE: Texas Water Board

module_name = 'chlorination'
basis_year = 2014
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

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)

        def get_chlorine_dose_cost(flow_in, dose):  # flow in mgd for this cost curve
            df = pd.read_csv('data/chlorine_dose_cost_twb.csv')

            new_dose_list = np.arange(0, 25.1, 0.5)

            cost_list = []
            flow_list = []
            dose_list = []

            for flow in df.Flow_mgd.unique():
                df_hold = df[df.Flow_mgd == flow]
                del df_hold['Flow_mgd']

                if 0 not in df_hold.Cost.values:
                    xs = np.hstack((0, df_hold.Dose.values))  # dont think we need the 0s
                    ys = np.hstack((0, df_hold.Cost.values))  # dont think we need the 0s
                else:
                    xs = df_hold.Dose.values
                    ys = df_hold.Cost.values

                a = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][0]
                b = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][1]

                for new_dose in new_dose_list:
                    if new_dose in df.Dose:
                        if flow in df.Flow_mgd:
                            cost_list.append(df[((df.Dose == new_dose) & (df.Flow_mgd == flow))].Cost.max())
                        else:
                            cost_list.append(a * new_dose ** b)
                    else:
                        cost_list.append(a * new_dose ** b)

                    dose_list.append(new_dose)
                    flow_list.append(flow)

            dose_cost_table = pd.DataFrame()
            dose_cost_table['flow_mgd'] = flow_list
            dose_cost_table['dose'] = dose_list
            dose_cost_table['cost'] = cost_list

            df1 = dose_cost_table[dose_cost_table.dose == dose]
            xs = np.hstack((0, df1.flow_mgd.values))
            ys = np.hstack((0, df1.cost.values))
            a = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][0]
            b = ml_regression.get_cost_curve_coefs(xs=xs, ys=ys)[0][1]

            return (a * flow_in ** b) * 1E-3  # $MM

        contact_time = 1.5  # hours
        contact_time_mins = 1.5 * 60  # min
        ct = 450  # mg/L-min
        chlorine_decay_rate = 3.0  # mg/Lh

        self.applied_cl2_dose = chlorine_decay_rate * contact_time + ct / contact_time_mins
        ## ^^^ The units don't make sense -KAS

        chem_name = unit_params['chemical_name']
        self.chem_dict = {chem_name: self.applied_cl2_dose * 1E-3}

        self.costing.fixed_cap_inv_unadjusted = get_chlorine_dose_cost(flow_in, self.applied_cl2_dose)  # $M

        self.electricity = 0.000005689  # kwh/m3 given in PML tab

        financials.get_complete_costing(self.costing)