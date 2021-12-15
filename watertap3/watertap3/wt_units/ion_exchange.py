import pandas as pd
from pyomo.environ import *
from pyomo.environ import units as pyunits
from pyomo.repn.plugins.baron_writer import NonNegativeReals

from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'ion_exchange'
basis_year = 2016 # 2016 is costing year for EPA component costing data
tpec_or_tic = 'TIC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        Docstrings go here.
        
        :return:
        '''
        time = self.flowsheet().config.time

        self.total_ix_cap = Var(time,
                                initialize=25,
                                domain=NonNegativeReals,
                                doc='Total ion exchange FCI [$MM]')

        self.cap_per_column = Var(time,
                                  initialize=1,
                                  domain=NonNegativeReals,
                                  doc='Capital per column [$MM]')

        self.column_total_cap = Var(time,
                                    initialize=1,
                                    domain=NonNegativeReals,
                                    doc='Total column capital [$MM]')

        self.resin_unit_cap = Var(time,
                                  initialize=4000,
                                  domain=NonNegativeReals,
                                  doc='Resin cap per m3 [$/m3]')

        self.resin_cap = Var(time,
                             initialize=1E4,
                             domain=NonNegativeReals,
                             doc='Resin capital [$MM]')

        self.regen_pump_cap = Var(time,
                                  initialize=100,
                                  domain=NonNegativeReals,
                                  doc='Pump capital for regen cycle [$MM]')

        self.bw_pump_cap = Var(time,
                               initialize=100,
                               domain=NonNegativeReals,
                               doc='Pump capital for backwash cycle [$MM]')

        self.rinse_pump_cap = Var(time,
                                  initialize=100,
                                  domain=NonNegativeReals,
                                  doc='Pump capital for rinse cycle [$MM]')

        self.boost_pump_cap = Var(time,
                                  initialize=100,
                                  domain=NonNegativeReals,
                                  doc='Pump capital for booster pump [#MM]')

        if self.pv_material == 'carbon_w_stainless_internals':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column[self.t] ==
                                                         (16504 * self.column_vol[self.t] ** 0.43) * 1E-6)
        if self.pv_material == 'carbon_w_plastic_internals':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column[self.t] ==
                                                         (9120 * self.column_vol[self.t] ** 0.49) * 1E-6)
        if self.pv_material == 'fiberglass':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column[self.t] ==
                                                         (5637 * self.column_vol[self.t] ** 0.9) * 1E-6)

        self.col_total_cap_constr = Constraint(expr=self.column_total_cap[self.t] == self.cap_per_column[self.t] * (self.num_columns[self.t] + 1))

        self.resin_unit_cap.fix(self.resin_dict[self.resin_type])

        self.resin_cap_constr = Constraint(expr=self.resin_cap[self.t] == ((self.resin_vol[self.t] + self.resin_per_column[self.t]) * self.resin_unit_cap[self.t]) * 1E-6)  # include an additional resin vol per column to account for the extra column

        self.regen_pump_cap_constr = Constraint(expr=self.regen_pump_cap[self.t] == (-24.257 * self.regen_flow[self.t] ** 2 + 2803.7 * self.regen_flow[self.t] + 7495.7) *
                                                     (self.num_columns[self.t] + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column

        self.bw_pump_cap_constr = Constraint(expr=self.bw_pump_cap[self.t] == (-24.257 * self.bw_flow[self.t] ** 2 + 2803.7 * self.bw_flow[self.t] + 7495.7) *
                                                  (self.num_columns[self.t] + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column

        self.rinse_pump_cap_constr = Constraint(expr=self.rinse_pump_cap[self.t] == (-24.257 * self.rinse_flow[self.t] ** 2 + 2803.7 * self.rinse_flow[self.t] + 7495.7) *
                                                     (self.num_columns[self.t] + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column

        self.flow_per_col_m3_min = pyunits.convert(self.flow_per_column[self.t], to_units=pyunits.m ** 3 / pyunits.min)

        self.boost_pump_cap_constr = Constraint(expr=self.boost_pump_cap[self.t] == (-24.257 * self.flow_per_col_m3_min ** 2 + 2803.7 * self.flow_per_col_m3_min + 7495.7) *
                                                     (self.num_columns[self.t] + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column

        self.total_ix_cap_constr = Constraint(expr=self.total_ix_cap[self.t] ==
                                                   self.column_total_cap[self.t] + self.resin_cap[self.t] + self.regen_pump_cap[self.t] + self.bw_pump_cap[self.t] + self.rinse_pump_cap[self.t] + self.boost_pump_cap[self.t])
        return self.total_ix_cap[self.t] * self.tpec_tic

    def elect(self):

        '''
        Electricity intensity for ion exchange

        :return:
        '''
        time = self.flowsheet().config.time

        self.main_pump_ei = Var(time,
                                initialize=4E-6,
                                domain=NonNegativeReals,
                                doc='Electricity intensity for main pump [kWh/m3]')

        self.regen_pump_ei = Var(time,
                                 initialize=4E-6,
                                 domain=NonNegativeReals,
                                 doc='Electricity intensity for regen pump [kWh/m3]')

        self.bw_pump_ei = Var(time,
                              initialize=4E-6,
                              domain=NonNegativeReals,
                              doc='Electricity intensity for backwash pump [kWh/m3]')

        self.rinse_pump_ei = Var(time,
                                 initialize=4E-6,
                                 domain=NonNegativeReals,
                                 doc='Electricity intensity for rinse pump [kWh/m3]')

        self.total_pump_ei = Var(time,
                                 initialize=4E-5,
                                 domain=NonNegativeReals,
                                 doc='Total pumping electricity intensity [kWh/m3]')

        flow_out_m3_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_waste_m3_hr = pyunits.convert(self.flow_vol_waste[self.t], to_units=pyunits.m ** 3 / pyunits.hr)

        self.main_pump_ei_constr = Constraint(expr=self.main_pump_ei[self.t] == ((1000 * 9.81 * self.pressure_drop[self.t] * 0.703249) / (3.6E6 * 0.7)) / flow_out_m3_hr)

        self.regen_pump_ei_constr = Constraint(expr=self.regen_pump_ei[self.t] == ((1000 * 9.81) / (3.6E6 * 0.7)) / flow_waste_m3_hr)

        self.bw_pump_ei_constr = Constraint(expr=self.bw_pump_ei[self.t] == ((1000 * 9.81) / (3.6E6 * 0.7)) / flow_waste_m3_hr)

        self.rinse_pump_ei_constr = Constraint(expr=self.rinse_pump_ei[self.t] == ((1000 * 9.81) / (3.6E6 * 0.7)) / flow_waste_m3_hr)

        self.total_pump_ei_constr = Constraint(expr=self.total_pump_ei[self.t] == self.main_pump_ei[self.t] + self.regen_pump_ei[self.t] + self.bw_pump_ei[self.t] + self.rinse_pump_ei[self.t])

        return self.total_pump_ei[self.t] * self.tpec_tic

    def sba(self, unit_params):
        '''
        Function for Strong-Base Anion Exchange Model

        :param unit_params:
        :return:
        '''

        time = self.flowsheet().config.time

        ### REGEN VARIABLES

        self.regen_dose = Var(time,
                              initialize=300,
                              domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              bounds=(80, 500),
                              doc='NaCl dose required for regeneration [kg/m3]')

        self.regen_rate = Var(time,
                              initialize=4,
                              domain=NonNegativeReals,
                              bounds=(2, 5),
                              doc='Regeneration rate [BV/hr]')

        self.regen_density = Var(time,
                                 initialize=1000,
                                 domain=NonNegativeReals,
                                 units=pyunits.kg / pyunits.m ** 3,
                                 bounds=(990, 1200),
                                 doc='Density of NaCl regen solution [kg/m3]')

        self.regen_ww = Var(time,
                            initialize=0.1,
                            domain=NonNegativeReals,
                            bounds=(0.015, 0.26),
                            doc='Strength of NaCl solution w/w [kg NaCl/kg soln]')

        self.regen_conc = Var(time,
                              initialize=110,
                              domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              doc='Concentration of regen solution [kg/m3]')

        self.regen_vol = Var(time,
                             initialize=2,
                             domain=NonNegativeReals,
                             doc='m3 of regen solution per m3 resin')

        self.regen_soln_per_column = Var(time,
                                         initialize=50,
                                         domain=NonNegativeReals,
                                         units=pyunits.m ** 3,
                                         doc='Regen solution used per column [m3/column]')

        self.regen_soln_per_column_annual = Var(time,
                                                initialize=1E3,
                                                domain=NonNegativeReals,
                                                units=pyunits.m ** 3 / pyunits.year,
                                                doc='Annual regen used per column [m3/year]')

        self.regen_soln_annual = Var(time,
                                     initialize=1E5,
                                     domain=NonNegativeReals,
                                     units=pyunits.m ** 3 / pyunits.year,
                                     doc='Total volume regen solution used [m3/year]')

        self.regen_time_per_column = Var(time,
                                         initialize=5,
                                         domain=NonNegativeReals,
                                         units=pyunits.min,
                                         doc='Regen time per column [min]')

        self.regen_flow = Var(time,
                              initialize=10,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 3 / pyunits.min,
                              doc='Regeneration flow rate [m3/min]')

        self.num_regen_per_column_annual = Var(time,
                                               initialize=200,
                                               domain=NonNegativeReals,
                                               doc='Number of regen cycles per year')

        self.salt_per_regen_per_column = Var(time,
                                             initialize=5E3,
                                             domain=NonNegativeReals,
                                             doc='Number of regen cycles per year')

        self.salt_per_column_annual = Var(time,
                                          initialize=1E5,
                                          domain=NonNegativeReals,
                                          units=pyunits.kg / pyunits.year,
                                          doc='Mass of salt per column per year [kg/yr]')

        self.salt_total_annual = Var(time,
                                     initialize=1E6,
                                     domain=NonNegativeReals,
                                     units=pyunits.kg / pyunits.year,
                                     doc='Mass of salt per year [kg/yr]')

        self.salt_dose = Var(time,
                             initialize=0.1,
                             domain=NonNegativeReals,
                             units=pyunits.kg / pyunits.m ** 3,
                             doc='Salt dose for system [kg/m3]')

        self.total_regen_time = Var(time,
                                    initialize=30,
                                    units=pyunits.min,
                                    domain=NonNegativeReals,
                                    doc='Total regeneration cycle time [min]')

        self.regen_dose.fix(300)

        try:
            self.regen_ww.fix(unit_params['regen_ww'])
        except KeyError:
            self.regen_ww.fix(0.1)

        ### BACKWASH VARIABLES

        self.bw_rate = Var(time,
                           initialize=6,
                           domain=NonNegativeReals,
                           units=pyunits.m / pyunits.hour,
                           bounds=(4.5, 8),
                           doc='Backwash rate [m/hr]')

        self.bw_time = Var(time,
                           initialize=6,
                           domain=NonNegativeReals,
                           units=pyunits.minute,
                           bounds=(4, 20),
                           doc='Backwash time [min]')

        self.bw_flow = Var(time,
                           initialize=5,
                           domain=NonNegativeReals,
                           units=pyunits.m ** 3 / pyunits.minute,
                           doc='Backwash flow rate [m3/min]')

        self.bed_expansion = Var(time,
                                 initialize=0.5,
                                 domain=NonNegativeReals,
                                 units=pyunits.dimensionless,
                                 bounds=(0.4, 0.8),
                                 doc='Resin bed expansion during backwash [%]')

        self.bed_expansion_h = Var(time,
                                   # initialize=0.5,
                                   domain=NonNegativeReals,
                                   units=pyunits.m,
                                   bounds=(0.5, 3),
                                   doc='Resin bed expansion during backwash [m]')

        # self.bw_time.fix(6)
        self.bw_time.fix(12)

        ### RINSE VARIABLES

        self.rinse_bv = Var(time,
                            initialize=5,
                            domain=NonNegativeReals,
                            bounds=(2, 10),
                            doc='Number of bed volumes for rinse step [BV]')

        self.rinse_vol_per_column = Var(time,
                                        initialize=150,
                                        domain=NonNegativeReals,
                                        units=pyunits.m ** 3,
                                        doc='Rinse volume per column [m3/col]')

        self.rinse_vol_per_column_annual = Var(time,
                                               initialize=5E3,
                                               domain=NonNegativeReals,
                                               units=pyunits.m ** 3 / pyunits.year,
                                               doc='Rinse volume per column [m3/yr]')

        self.rinse_time_per_column = Var(time,
                                         initialize=4,
                                         domain=NonNegativeReals,
                                         units=pyunits.min,
                                         doc='Rinse time per column [min]')

        self.rinse_flow = Var(time,
                              initialize=2,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 3 / pyunits.min,
                              doc='Rinse step flow rate [m3/min]')

        self.rinse_bv.fix(5)

        ### RESIN AND FLOW VARIABLES

        ix_df = self.ix_df = pd.read_csv('data/ix_sba.csv', index_col='constituent')
        self.cons = [c for c in self.config.property_package.component_list if c in ix_df.index]
        ix_df = self.ix_df = ix_df.loc[self.cons].copy()
        self.sep_factor_dict = ix_df.to_dict()['sep_factor']
        self.meq_conv_dict = ix_df.to_dict()['meq']

        try:
            self.target = unit_params['target']
        except:
            self.cons_df = self.source_df.loc[[c for c in self.cons if c != 'chloride']].copy()
            self.cons_df['meq_L'] = [(self.cons_df.loc[c].value * 1E3) / self.meq_conv_dict[c] for c in self.cons if c != 'chloride']
            self.target = self.cons_df.meq_L.idxmax()

        for k, v in self.sep_factor_dict.items():
            if v > self.sep_factor_dict[self.target]:
                self.sep_factor_dict[k] = 0.99 * self.sep_factor_dict[self.target]

        self.sep_factor = Param(self.cons,
                                initialize=self.sep_factor_dict)

        self.meq_conv = Param(self.cons,
                              initialize=self.meq_conv_dict)

        self.target_removal = Var(time,
                                  initialize=1,
                                  domain=NonNegativeReals,
                                  bounds=(0.0001, 1),
                                  doc='Removal fraction for target compound')

        self.sfr = Var(time,
                       initialize=30,
                       domain=NonNegativeReals,
                       bounds=(6, 50),
                       doc='Service flow rate [BV/hr]')

        self.loading_rate = Var(time,
                                initialize=20,
                                domain=NonNegativeReals,
                                bounds=(10, 40),
                                units=pyunits.m / pyunits.hr,
                                doc='Column loading rate (superficial velocity) [m/hr]')

        self.cycle_time = Var(time,
                              initialize=100,
                              domain=NonNegativeReals,
                              units=pyunits.hr,
                              doc='Service cycle time [hr]')

        self.ebct = Var(time,
                        initialize=1.1,
                        domain=NonNegativeReals,
                        units=pyunits.min,
                        doc='Empty Bed Contact Time [min]')

        self.mg_L = Var(time,
                        self.cons,
                        initialize=1,
                        domain=NonNegativeReals,
                        doc='Influent concentration in mg/L')

        self.meq_L = Var(time,
                         self.cons,
                         initialize=0.1,
                         domain=NonNegativeReals,
                         doc='Influent concentration in meq/L')

        self.mass_in = Var(time,
                           self.cons,
                           initialize=200,
                           domain=NonNegativeReals,
                           doc='Influent mass [eq]')

        self.mass_removed = Var(time,
                                self.cons,
                                initialize=10,
                                domain=NonNegativeReals,
                                doc='Mass removed [eq]')

        self.frac_removed = Var(time,
                                self.cons,
                                initialize=0.8,
                                domain=NonNegativeReals,
                                doc='Fraction removed [%]')

        self.denom_resin = Var(time,
                               initialize=1,
                               domain=NonNegativeReals)

        self.denom_aq = Var(time,
                            initialize=1,
                            domain=NonNegativeReals)

        self.resin_conc = Var(time,
                              self.cons,
                              initialize=0.1,
                              domain=NonNegativeReals,
                              doc='Resin phase concentration of each ion [eq/L resin]')

        self.max_vol_treated = Var(time,
                                   initialize=5E3,
                                   domain=NonNegativeReals,
                                   bounds=(100, 1E6),
                                   units=pyunits.L / pyunits.L,
                                   doc='Max volume of water treated before breakthrough [L water/L resin]')

        self.resin_capacity = Var(time,
                                  initialize=1.2,
                                  domain=NonNegativeReals,
                                  bounds=(0.9, 1.5),
                                  doc='Resin capacity [eq/L]')

        self.resin_vol = Var(time,
                             # initialize=100,
                             domain=NonNegativeReals,
                             units=pyunits.m ** 3,
                             doc='Resin volume needed [m3]')

        self.resin_area = Var(time,
                              initialize=100,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 2,
                              doc='Resin cross-sectional area needed [m2]')

        self.resin_depth = Var(time,
                               initialize=1.5,
                               domain=NonNegativeReals,
                               bounds=(0.75, 3),
                               units=pyunits.m,
                               doc='Resin bed depth [m]')

        self.resin_depth_to_column_diam_ratio = Var(time,
                                                    initialize=1,
                                                    domain=NonNegativeReals,
                                                    bounds=(0.6, 1.6),
                                                    units=pyunits.dimensionless,
                                                    doc='Ratio of resin depth to column height')

        self.resin_per_column = Var(time,
                                    initialize=15,
                                    domain=NonNegativeReals,
                                    units=pyunits.m ** 3,
                                    doc='Resin per column [m3]')

        self.resin_loss_frac_annual = Var(time,
                                          initialize=0.045,
                                          domain=NonNegativeReals,
                                          bounds=(3.75, 5.25),
                                          doc='Fraction of resin replaced per year [%]')

        self.resin_loss_annual = Var(time,
                                     initialize=20,
                                     domain=NonNegativeReals,
                                     units=pyunits.m ** 3,
                                     doc='Resin replaced per year [m3]')

        #### COLUMN VARIABLES

        self.column_h = Var(time,
                            initialize=2,
                            domain=NonNegativeReals,
                            units=pyunits.m,
                            bounds=(1, 16),
                            doc='Column height [m]')

        self.column_diam = Var(time,
                               initialize=2,
                               domain=NonNegativeReals,
                               units=pyunits.m,
                               bounds=(1, 4),
                               doc='Column diameter [m]')

        self.column_area = Var(time,
                               initialize=15,
                               domain=NonNegativeReals,
                               units=pyunits.m ** 2,
                               doc='Column cross-sectional area [m2]')

        if self.pv_material == 'fiberglass':
            self.column_vol = Var(time,
                                  initialize=2,
                                  domain=NonNegativeReals,
                                  bounds=(0.5, 4),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        else:
            self.column_vol = Var(time,
                                  initialize=35,
                                  domain=NonNegativeReals,
                                  bounds=(0.5, 25),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        self.num_columns = Var(time,
                               initialize=2,
                               domain=NonNegativeReals,
                               bounds=(1, 1E5),
                               units=pyunits.dimensionless,
                               doc='Number of columns in parallel')

        self.underdrain_h = Var(time,
                                initialize=0.5,
                                domain=NonNegativeReals,
                                units=pyunits.m,
                                doc='Underdrain height [m]')

        self.distributor_h = Var(time,
                                 initialize=1,
                                 domain=NonNegativeReals,
                                 units=pyunits.m,
                                 doc='Distributor height [m]')

        self.flow_per_column = Var(time,
                                   initialize=250,
                                   domain=NonNegativeReals,
                                   units=pyunits.m ** 3 / pyunits.hr,
                                   doc='Flow per column [m3/hr]')

        self.pressure_drop = Var(time,
                                 initialize=14,
                                 domain=NonNegativeReals,
                                 units=pyunits.psi,
                                 bounds=(0, 25),
                                 doc='Pressure drop across column [psi]')

        self.resin_capacity.fix(1.2)
        # self.resin_capacity.fix(0.9435)
        # self.sfr.fix(30)
        self.loading_rate.fix(20)
        self.underdrain_h.fix(0.5)
        self.distributor_h.fix(1)
        self.resin_loss_frac_annual.fix(0.045)
        # self.column_diam.fix(3)

        try:
            self.target_removal = unit_params['target_removal']
        except KeyError:
            self.target_removal.fix(1)

        flow_out_m3_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_out_m3_yr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.year)
        flow_out_L_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.L / pyunits.hr)

        ############################# CONSTRAINTS START
        #### RESIN AND PERFORMANCE CONSTRAINTS

        self.mg_L_constr = ConstraintList()
        self.meq_L_constr = ConstraintList()
        self.resin_conc_constr = ConstraintList()
        self.mass_in_constr = ConstraintList()
        self.mass_removed_constr = ConstraintList()
        self.frac_removed_constr = ConstraintList()

        for c in self.cons:
            self.mg_L_constr.add(self.mg_L[self.t, c] == (self.conc_mass_in[self.t, c] * 1E3))
            self.meq_L_constr.add(self.meq_L[self.t, c] == self.mg_L[self.t, c] / self.meq_conv[c])
            self.resin_conc_constr.add(self.resin_conc[self.t, c] == (self.resin_capacity[self.t] * self.sep_factor[c] * self.meq_L[self.t, c]) /
                                       self.denom_resin[self.t])
            self.mass_in_constr.add(self.mass_in[self.t, c] == self.meq_L[self.t, c] * flow_out_m3_hr * self.cycle_time[self.t] * 1E-3)
            self.mass_removed_constr.add(self.mass_removed[self.t, c] == (self.resin_conc[self.t, c] / self.max_vol_treated[self.t]) * flow_out_m3_hr * self.cycle_time[self.t])
            self.frac_removed_constr.add(self.frac_removed[self.t, c] == 0.99 * (self.mass_removed[self.t, c] / self.mass_in[self.t, c]))

        self.denom_resin_constr = Constraint(expr=self.denom_resin[self.t] == sum(self.meq_L[self.t, c] * self.sep_factor[c] for c in self.cons))
        self.denom_aq_constr = Constraint(expr=self.denom_aq[self.t] == sum(self.resin_conc[self.t, c] / self.sep_factor[c] for c in self.cons))

        self.max_vol_treated_constr = Constraint(expr=self.max_vol_treated[self.t] == (self.resin_conc[self.t, self.target] * 1E3) /
                                                      (self.meq_L[self.t, self.target] * self.target_removal[self.t]))

        self.resin_vol_constr = Constraint(expr=self.resin_vol[self.t] == flow_out_m3_hr / self.sfr[self.t])
        resin_vol_L = pyunits.convert(self.resin_vol[self.t], to_units=pyunits.L)

        self.resin_depth_to_column_diam_ratio_constr = Constraint(expr=self.resin_depth_to_column_diam_ratio[self.t] == self.resin_depth[self.t] / self.column_diam[self.t])

        self.resin_loss_annual_constr = Constraint(expr=self.resin_loss_annual[self.t] == self.resin_vol[self.t] * self.resin_loss_frac_annual[self.t])

        self.cycle_time_constr = Constraint(expr=self.cycle_time[self.t] == (self.max_vol_treated[self.t] * resin_vol_L) / flow_out_L_hr)

        self.resin_area_constr = Constraint(expr=self.resin_area[self.t] == self.resin_vol[self.t] / self.resin_depth[self.t])

        self.column_area_constr = Constraint(expr=self.column_area[self.t] == 3.141592 * (self.column_diam[self.t] / 2) ** 2)

        self.num_columns_constr = Constraint(expr=self.num_columns[self.t] == self.resin_area[self.t] / self.column_area[self.t])

        self.flow_per_col_constr = Constraint(expr=self.flow_per_column[self.t] == flow_out_m3_hr / self.num_columns[self.t])

        self.resin_per_col_constr = Constraint(expr=self.resin_per_column[self.t] == self.resin_vol[self.t] / self.num_columns[self.t])

        self.loading_rate_constr1 = Constraint(expr=self.loading_rate[self.t] == self.flow_per_column[self.t] / self.column_area[self.t])
        self.loading_rate_constr2 = Constraint(expr=self.loading_rate[self.t] == self.sfr[self.t] * self.resin_depth[self.t])

        self.pressure_drop_constr = Constraint(expr=self.pressure_drop[self.t] == (8.28E-04 * self.loading_rate[self.t] ** 2 + 0.173 * self.loading_rate[self.t] + 0.609) * self.resin_depth[self.t])  # Curve for 20C temperatuer

        self.column_h_constr = Constraint(expr=self.column_h[self.t] == self.resin_depth[self.t] + self.bed_expansion_h[self.t] + self.distributor_h[self.t] + self.underdrain_h[self.t])

        self.column_vol_constr = Constraint(expr=self.column_vol[self.t] == 3.14159 * (self.column_diam[self.t] / 2) ** 2 * self.column_h[self.t])

        self.ebct_constr = Constraint(expr=self.ebct[self.t] == (self.resin_depth[self.t] / self.loading_rate[self.t]) * 60)

        #### REGEN CONSTRAINTS

        self.regen_density_constr = Constraint(expr=self.regen_density[self.t] == 994.34 + 761.65 * self.regen_ww[self.t])  # kg Nacl / m3 resin

        self.regen_conc_constr = Constraint(expr=self.regen_conc[self.t] == self.regen_ww[self.t] * self.regen_density[self.t])

        self.regen_vol_constr = Constraint(expr=self.regen_vol[self.t] == self.regen_dose[self.t] / self.regen_conc[self.t])  # m3 regen soln / m3 resin

        self.num_regen_per_column_annual_constr = Constraint(expr=self.num_regen_per_column_annual[self.t] == 8760 / self.cycle_time[self.t])  # numerator is hours per year

        self.salt_per_regen_per_column_constr = Constraint(expr=self.salt_per_regen_per_column[self.t] == self.resin_per_column[self.t] * self.regen_dose[self.t])

        self.salt_per_col_annual_constr = Constraint(expr=self.salt_per_column_annual[self.t] == self.num_regen_per_column_annual[self.t] * self.salt_per_regen_per_column[self.t])  # kg / year per column

        self.salt_total_annual_constr = Constraint(expr=self.salt_total_annual[self.t] == self.salt_per_column_annual[self.t] * self.num_columns[self.t])  # kg / year

        self.salt_dose_constr = Constraint(expr=self.salt_dose[self.t] == self.salt_total_annual[self.t] / flow_out_m3_yr)

        self.regen_soln_per_col_constr = Constraint(expr=self.regen_soln_per_column[self.t] == self.resin_per_column[self.t] * self.regen_vol[self.t])

        self.regen_soln_per_col_annual_constr = Constraint(expr=self.regen_soln_per_column_annual[self.t] == self.regen_soln_per_column[self.t] * self.num_regen_per_column_annual[self.t])

        self.regen_soln_annual_constr = Constraint(expr=self.regen_soln_annual[self.t] == self.regen_soln_per_column_annual[self.t] * self.num_columns[self.t])

        self.regen_time_per_col_constr = Constraint(expr=self.regen_time_per_column[self.t] == self.ebct[self.t] * self.regen_vol[self.t])

        self.total_regen_time_constr = Constraint(expr=self.total_regen_time[self.t] == self.regen_time_per_column[self.t] + self.rinse_time_per_column[self.t] + self.bw_time[self.t])

        self.regen_flow_constr = Constraint(expr=self.regen_flow[self.t] == self.column_vol[self.t] / self.regen_time_per_column[self.t])

        ##### BW CONSTRAINTS

        self.bed_exp_constr = Constraint(expr=self.bed_expansion[self.t] == -1.35E-3 * self.bw_rate[self.t] ** 2 + 1.02E-1 * self.bw_rate[self.t] - 1.23E-2)

        self.bed_exp_h_constr = Constraint(expr=self.bed_expansion_h[self.t] == self.resin_depth[self.t] * self.bed_expansion[self.t])

        self.bw_flow_constr = Constraint(expr=self.bw_flow[self.t] == self.column_vol[self.t] / self.bw_time[self.t])

        ##### RINSE CONSTRAINTS

        self.rinse_vol_per_column_constr = Constraint(expr=self.rinse_vol_per_column[self.t] == self.resin_per_column[self.t] * self.rinse_bv[self.t])

        self.rinse_vol_per_col_annual_constr = Constraint(expr=self.rinse_vol_per_column_annual[self.t] == self.rinse_vol_per_column[self.t] * self.num_regen_per_column_annual[self.t])

        self.rinse_time_per_col_constr = Constraint(expr=self.rinse_time_per_column[self.t] == self.ebct[self.t] * self.rinse_bv[self.t])

        self.rinse_flow_constr = Constraint(expr=self.rinse_flow[self.t] == self.column_vol[self.t] / self.rinse_time_per_column[self.t])

        ##### WATER RECOVERY, CHEM DICT, AND CONSTITUENT REMOVAL

        self.wr_constr = Constraint(expr=self.water_recovery[self.t] == 1 - (self.total_regen_time[self.t] / ((self.cycle_time[self.t] * 60) + self.total_regen_time[self.t])))

        self.chem_dict = {
                'Sodium_Chloride': self.salt_dose[self.t]
                }

        self.del_component(self.component_removal_equation)

        self.ix_component_removal = ConstraintList()
        for c in self.config.property_package.component_list:
            if c in self.cons:
                self.ix_component_removal.add(self.frac_removed[self.t, c] * self.flow_vol_in[self.t] * self.conc_mass_in[self.t, c] ==
                                              self.flow_vol_waste[self.t] * self.conc_mass_waste[self.t, c])
            else:
                self.ix_component_removal.add(self.removal_fraction[self.t, c] * self.flow_vol_in[self.t] * self.conc_mass_in[self.t, c] ==
                                              self.flow_vol_waste[self.t] * self.conc_mass_waste[self.t, c])

    def sac(self, unit_params):
        '''
        Function for Strong-Acid Cation Exchange Model
        :param unit_params:
        :return:
        '''

        ### REGEN VARIABLES

        time = self.flowsheet().config.time

        ### REGEN VARIABLES

        self.regen_dose = Var(time,
                              initialize=300,
                              domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              bounds=(80, 500),\
                              doc='NaCl dose required for regeneration [kg/m3]')

        self.regen_rate = Var(time,
                              initialize=4,
                              domain=NonNegativeReals,
                              bounds=(2, 5),
                              doc='Regeneration rate [BV/hr]')

        self.regen_density = Var(time,
                                 initialize=1000,
                                 domain=NonNegativeReals,
                                 units=pyunits.kg / pyunits.m ** 3,
                                 bounds=(990, 1200),
                                 doc='Density of NaCl regen solution [kg/m3]')

        self.regen_ww = Var(time,
                            initialize=0.1,
                            domain=NonNegativeReals,
                            bounds=(0.015, 0.26),
                            doc='Strength of NaCl solution w/w [kg NaCl/kg soln]')

        self.regen_conc = Var(time,
                              initialize=110,
                              domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              doc='Concentration of regen solution [kg/m3]')

        self.regen_vol = Var(time,
                             initialize=2,
                             domain=NonNegativeReals,
                             doc='m3 of regen solution per m3 resin')

        self.regen_soln_per_column = Var(time,
                                         initialize=50,
                                         domain=NonNegativeReals,
                                         units=pyunits.m ** 3,
                                         doc='Regen solution used per column [m3/column]')

        self.regen_soln_per_column_annual = Var(time,
                                                initialize=1E3,
                                                domain=NonNegativeReals,
                                                units=pyunits.m ** 3 / pyunits.year,
                                                doc='Annual regen used per column [m3/year]')

        self.regen_soln_annual = Var(time,
                                     initialize=1E5,
                                     domain=NonNegativeReals,
                                     units=pyunits.m ** 3 / pyunits.year,
                                     doc='Total volume regen solution used [m3/year]')

        self.regen_time_per_column = Var(time,
                                         initialize=5,
                                         domain=NonNegativeReals,
                                         units=pyunits.min,
                                         doc='Regen time per column [min]')

        self.regen_flow = Var(time,
                              initialize=10,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 3 / pyunits.min,
                              doc='Regeneration flow rate [m3/min]')

        self.num_regen_per_column_annual = Var(time,
                                               initialize=200,
                                               domain=NonNegativeReals,
                                               doc='Number of regen cycles per year')

        self.salt_per_regen_per_column = Var(time,
                                             initialize=5E3,
                                             domain=NonNegativeReals,
                                             doc='Number of regen cycles per year')

        self.salt_per_column_annual = Var(time,
                                          initialize=1E5,
                                          domain=NonNegativeReals,
                                          units=pyunits.kg / pyunits.year,
                                          doc='Mass of salt per column per year [kg/yr]')

        self.salt_total_annual = Var(time,
                                     initialize=1E6,
                                     domain=NonNegativeReals,
                                     units=pyunits.kg / pyunits.year,
                                     doc='Mass of salt per year [kg/yr]')

        self.salt_dose = Var(time,
                             initialize=0.1,
                             domain=NonNegativeReals,
                             units=pyunits.kg / pyunits.m ** 3,
                             doc='Salt dose for system [kg/m3]')

        self.total_regen_time = Var(time,
                                    initialize=30,
                                    units=pyunits.min,
                                    domain=NonNegativeReals,
                                    doc='Total regeneration cycle time [min]')

        self.regen_dose.fix(300)

        try:
            self.regen_ww.fix(unit_params['regen_ww'])
        except KeyError:
            self.regen_ww.fix(0.1)

        ### BACKWASH VARIABLES

        self.bw_rate = Var(time,
                           initialize=5,
                           domain=NonNegativeReals,
                           units=pyunits.m / pyunits.hour,
                           bounds=(4.5, 6.5),
                           doc='Backwash rate [m/hr]')

        self.bw_time = Var(time,
                           initialize=6,
                           domain=NonNegativeReals,
                           units=pyunits.minute,
                           bounds=(4, 15),
                           doc='Backwash time [min]')

        self.bw_flow = Var(time,
                           initialize=5,
                           domain=NonNegativeReals,
                           units=pyunits.m ** 3 / pyunits.minute,
                           doc='Backwash flow rate [m3/min]')

        self.bed_expansion = Var(time,
                                 initialize=0.5,
                                 domain=NonNegativeReals,
                                 units=pyunits.dimensionless,
                                 bounds=(0.4, 0.6),
                                 doc='Resin bed expansion during backwash [%]')

        self.bed_expansion_h = Var(time,
                                   # initialize=0.5,
                                   domain=NonNegativeReals,
                                   units=pyunits.m,
                                   bounds=(0.1, 3),
                                   doc='Resin bed expansion during backwash [m]')

        self.bw_time.fix(6)

        ### RINSE VARIABLES

        self.rinse_bv = Var(time,
                            initialize=5,
                            domain=NonNegativeReals,
                            bounds=(2, 5),
                            doc='Number of bed volumes for rinse step [BV]')

        self.rinse_vol_per_column = Var(time,
                                        initialize=150,
                                        domain=NonNegativeReals,
                                        units=pyunits.m ** 3,
                                        doc='Rinse volume per column [m3/col]')

        self.rinse_vol_per_column_annual = Var(time,
                                               initialize=5E3,
                                               domain=NonNegativeReals,
                                               units=pyunits.m ** 3 / pyunits.year,
                                               doc='Rinse volume per column [m3/yr]')

        self.rinse_time_per_column = Var(time,
                                         initialize=4,
                                         domain=NonNegativeReals,
                                         units=pyunits.min,
                                         doc='Rinse time per column [min]')

        self.rinse_flow = Var(time,
                              initialize=2,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 3 / pyunits.min,
                              doc='Rinse step flow rate [m3/min]')

        self.rinse_bv.fix(3)

        ### RESIN AND FLOW VARIABLES

        ix_df = self.ix_df = pd.read_csv('data/ix_sac.csv', index_col='constituent')
        self.cons = [c for c in self.config.property_package.component_list if c in ix_df.index]
        ix_df = self.ix_df = ix_df.loc[self.cons].copy()
        self.sep_factor_dict = ix_df.to_dict()['sep_factor']
        self.meq_conv_dict = ix_df.to_dict()['meq']

        try:
            self.target = unit_params['target']
        except KeyError:
            self.cons_df = self.source_df.loc[[c for c in self.cons if c != 'sodium']].copy()
            self.cons_df['meq_L'] = [(self.cons_df.loc[c].value * 1E3) / self.meq_conv_dict[c] for c in self.cons if c != 'sodium']
            self.target = self.cons_df.meq_L.idxmax()

        for k, v in self.sep_factor_dict.items():
            if v > self.sep_factor_dict[self.target]:
                self.sep_factor_dict[k] = 0.99 * self.sep_factor_dict[self.target]

        self.sep_factor = Param(self.cons,
                                initialize=self.sep_factor_dict)

        self.meq_conv = Param(self.cons,
                              initialize=self.meq_conv_dict)

        self.target_removal = Var(time,
                                  initialize=1,
                                  domain=NonNegativeReals,
                                  bounds=(0.0001, 1),
                                  doc='Removal fraction for target compound')

        self.sfr = Var(time,
                       initialize=30,
                       domain=NonNegativeReals,
                       bounds=(6, 50),
                       doc='Service flow rate [BV/hr]')

        self.loading_rate = Var(time,
                                initialize=20,
                                domain=NonNegativeReals,
                                bounds=(10, 40),
                                units=pyunits.m / pyunits.hr,
                                doc='Column loading rate (superficial velocity) [m/hr]')

        self.cycle_time = Var(time,
                              initialize=100,
                              domain=NonNegativeReals,
                              units=pyunits.hr,
                              doc='Service cycle time [hr]')

        self.ebct = Var(time,
                        initialize=1.1,
                        domain=NonNegativeReals,
                        units=pyunits.min,
                        doc='Empty Bed Contact Time [min]')

        self.mg_L = Var(time,
                        self.cons,
                        initialize=1,
                        domain=NonNegativeReals,
                        doc='Influent concentration in mg/L')

        self.meq_L = Var(time,
                         self.cons,
                         initialize=0.1,
                         domain=NonNegativeReals,
                         doc='Influent concentration in meq/L')

        self.mass_in = Var(time,
                           self.cons,
                           initialize=200,
                           domain=NonNegativeReals,
                           doc='Influent mass [eq]')

        self.mass_removed = Var(time,
                                self.cons,
                                initialize=10,
                                domain=NonNegativeReals,
                                doc='Mass removed [eq]')

        self.frac_removed = Var(time,
                                self.cons,
                                initialize=0.8,
                                domain=NonNegativeReals,
                                doc='Fraction removed [%]')

        self.denom_resin = Var(time,
                               initialize=1,
                               domain=NonNegativeReals)

        self.denom_aq = Var(time,
                            initialize=1,
                            domain=NonNegativeReals)

        self.resin_conc = Var(time,
                              self.cons,
                              initialize=0.1,
                              domain=NonNegativeReals,
                              doc='Resin phase concentration of each ion [eq/L resin]')

        self.max_vol_treated = Var(time,
                                   initialize=5E3,
                                   domain=NonNegativeReals,
                                   bounds=(100, 1E6),
                                   units=pyunits.L / pyunits.L,
                                   doc='Max volume of water treated before breakthrough [L water/L resin]')

        self.resin_capacity = Var(time,
                                  initialize=1.7,
                                  domain=NonNegativeReals,
                                  bounds=(1.6, 2.2),
                                  doc='Resin capacity [eq/L]')

        self.resin_vol = Var(time,
                             # initialize=100,
                             domain=NonNegativeReals,
                             units=pyunits.m ** 3,
                             doc='Resin volume needed [m3]')

        self.resin_area = Var(time,
                              initialize=100,
                              domain=NonNegativeReals,
                              units=pyunits.m ** 2,
                              doc='Resin cross-sectional area needed [m2]')

        self.resin_depth = Var(time,
                               initialize=1.5,
                               domain=NonNegativeReals,
                               bounds=(0.75, 3),
                               units=pyunits.m,
                               doc='Resin bed depth [m]')

        self.resin_depth_to_column_diam_ratio = Var(time,
                                                    initialize=1,
                                                    domain=NonNegativeReals,
                                                    bounds=(0.6, 1.6),
                                                    units=pyunits.dimensionless,
                                                    doc='Ratio of resin depth to column height')

        self.resin_per_column = Var(time,
                                    initialize=15,
                                    domain=NonNegativeReals,
                                    units=pyunits.m ** 3,
                                    doc='Resin per column [m3]')

        self.resin_loss_frac_annual = Var(time,
                                          initialize=0.045,
                                          domain=NonNegativeReals,
                                          bounds=(3.75, 5.25),
                                          doc='Fraction of resin replaced per year [%]')

        self.resin_loss_annual = Var(time,
                                     initialize=20,
                                     domain=NonNegativeReals,
                                     units=pyunits.m ** 3,
                                     doc='Resin replaced per year [m3]')

        #### COLUMN VARIABLES

        self.column_h = Var(time,
                            initialize=2,
                            domain=NonNegativeReals,
                            units=pyunits.m,
                            bounds=(1, 16),
                            doc='Column height [m]')

        self.column_diam = Var(time,
                               initialize=2,
                               domain=NonNegativeReals,
                               units=pyunits.m,
                               bounds=(1, 4),
                               doc='Column diameter [m]')

        self.column_area = Var(time,
                               initialize=15,
                               domain=NonNegativeReals,
                               units=pyunits.m ** 2,
                               doc='Column cross-sectional area [m2]')

        if self.pv_material == 'fiberglass':
            self.column_vol = Var(time,
                                  initialize=2,
                                  domain=NonNegativeReals,
                                  bounds=(0.5, 4),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        else:
            self.column_vol = Var(time,
                                  initialize=35,
                                  domain=NonNegativeReals,
                                  bounds=(0.5, 25),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        self.num_columns = Var(time,
                               initialize=2,
                               domain=NonNegativeReals,
                               bounds=(1, 1E5),
                               units=pyunits.dimensionless,
                               doc='Number of columns in parallel')

        self.underdrain_h = Var(time,
                                initialize=0.5,
                                domain=NonNegativeReals,
                                units=pyunits.m,
                                doc='Underdrain height [m]')

        self.distributor_h = Var(time,
                                 initialize=1,
                                 domain=NonNegativeReals,
                                 units=pyunits.m,
                                 doc='Distributor height [m]')

        self.flow_per_column = Var(time,
                                   initialize=250,
                                   domain=NonNegativeReals,
                                   units=pyunits.m ** 3 / pyunits.hr,
                                   doc='Flow per column [m3/hr]')

        self.pressure_drop = Var(time,
                                 initialize=14,
                                 domain=NonNegativeReals,
                                 units=pyunits.psi,
                                 bounds=(0, 25),
                                 doc='Pressure drop across column [psi]')

        self.resin_capacity.fix(1.7)
        # self.sfr.fix(30)
        self.loading_rate.fix(20)
        self.underdrain_h.fix(0.5)
        self.distributor_h.fix(1)
        self.resin_loss_frac_annual.fix(0.045)
        # self.column_diam.fix(2.5)

        try:
            self.target_removal = unit_params['target_removal']
        except KeyError:
            self.target_removal.fix(1)

        flow_out_m3_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_out_m3_yr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.year)
        flow_out_L_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.L / pyunits.hr)

        ############################# CONSTRAINTS START
        #### RESIN AND PERFORMANCE CONSTRAINTS

        self.mg_L_constr = ConstraintList()
        self.meq_L_constr = ConstraintList()
        self.resin_conc_constr = ConstraintList()
        self.mass_in_constr = ConstraintList()
        self.mass_removed_constr = ConstraintList()
        self.frac_removed_constr = ConstraintList()

        for c in self.cons:
            self.mg_L_constr.add(self.mg_L[self.t, c] == (self.conc_mass_in[self.t, c] * 1E3))
            self.meq_L_constr.add(self.meq_L[self.t, c] == self.mg_L[self.t, c] / self.meq_conv[c])
            self.resin_conc_constr.add(self.resin_conc[self.t, c] == (self.resin_capacity[self.t] * self.sep_factor[c] * self.meq_L[self.t, c]) /
                                       self.denom_resin[self.t])
            self.mass_in_constr.add(self.mass_in[self.t, c] == self.meq_L[self.t, c] * flow_out_m3_hr * self.cycle_time[self.t] * 1E-3)
            self.mass_removed_constr.add(self.mass_removed[self.t, c] == (self.resin_conc[self.t, c] / self.max_vol_treated[self.t]) * flow_out_m3_hr * self.cycle_time[self.t])
            self.frac_removed_constr.add(self.frac_removed[self.t, c] == 0.99 * (self.mass_removed[self.t, c] / self.mass_in[self.t, c]))

        self.denom_resin_constr = Constraint(expr=self.denom_resin[self.t] == sum(self.meq_L[self.t, c] * self.sep_factor[c] for c in self.cons))
        self.denom_aq_constr = Constraint(expr=self.denom_aq[self.t] == sum(self.resin_conc[self.t, c] / self.sep_factor[c] for c in self.cons))

        self.max_vol_treated_constr = Constraint(expr=self.max_vol_treated[self.t] == (self.resin_conc[self.t, self.target] * 1E3) /
                                                      (self.meq_L[self.t, self.target] * self.target_removal[self.t]))

        self.resin_vol_constr = Constraint(expr=self.resin_vol[self.t] == flow_out_m3_hr / self.sfr[self.t])
        resin_vol_L = pyunits.convert(self.resin_vol[self.t], to_units=pyunits.L)

        self.resin_depth_to_column_diam_ratio_constr = Constraint(expr=self.resin_depth_to_column_diam_ratio[self.t] == self.resin_depth[self.t] / self.column_diam[self.t])

        self.resin_loss_annual_constr = Constraint(expr=self.resin_loss_annual[self.t] == self.resin_vol[self.t] * self.resin_loss_frac_annual[self.t])

        self.cycle_time_constr = Constraint(expr=self.cycle_time[self.t] == (self.max_vol_treated[self.t] * resin_vol_L) / flow_out_L_hr)

        self.resin_area_constr = Constraint(expr=self.resin_area[self.t] == self.resin_vol[self.t] / self.resin_depth[self.t])

        self.column_area_constr = Constraint(expr=self.column_area[self.t] == 3.141592 * (self.column_diam[self.t] / 2) ** 2)

        self.num_columns_constr = Constraint(expr=self.num_columns[self.t] == self.resin_area[self.t] / self.column_area[self.t])

        self.flow_per_col_constr = Constraint(expr=self.flow_per_column[self.t] == flow_out_m3_hr / self.num_columns[self.t])

        self.resin_per_col_constr = Constraint(expr=self.resin_per_column[self.t] == self.resin_vol[self.t] / self.num_columns[self.t])

        self.loading_rate_constr1 = Constraint(expr=self.loading_rate[self.t] == self.flow_per_column[self.t] / self.column_area[self.t])
        self.loading_rate_constr2 = Constraint(expr=self.loading_rate[self.t] == self.sfr[self.t] * self.resin_depth[self.t])

        self.pressure_drop_constr = Constraint(expr=self.pressure_drop[self.t] == (8.28E-04 * self.loading_rate[self.t] ** 2 + 0.173 * self.loading_rate[self.t] + 0.609) * self.resin_depth[self.t])  # Curve for 20C temperatuer

        self.column_h_constr = Constraint(expr=self.column_h[self.t] == self.resin_depth[self.t] + self.bed_expansion_h[self.t] + self.distributor_h[self.t] + self.underdrain_h[self.t])

        self.column_vol_constr = Constraint(expr=self.column_vol[self.t] == 3.14159 * (self.column_diam[self.t] / 2) ** 2 * self.column_h[self.t])

        self.ebct_constr = Constraint(expr=self.ebct[self.t] == (self.resin_depth[self.t] / self.loading_rate[self.t]) * 60)

        #### REGEN CONSTRAINTS

        self.regen_density_constr = Constraint(expr=self.regen_density[self.t] == 994.34 + 761.65 * self.regen_ww[self.t])  # kg Nacl / m3 resin

        self.regen_conc_constr = Constraint(expr=self.regen_conc[self.t] == self.regen_ww[self.t] * self.regen_density[self.t])

        self.regen_vol_constr = Constraint(expr=self.regen_vol[self.t] == self.regen_dose[self.t] / self.regen_conc[self.t])  # m3 regen soln / m3 resin

        self.num_regen_per_column_annual_constr = Constraint(expr=self.num_regen_per_column_annual[self.t] == 8760 / self.cycle_time[self.t])  # numerator is hours per year

        self.salt_per_regen_per_column_constr = Constraint(expr=self.salt_per_regen_per_column[self.t] == self.resin_per_column[self.t] * self.regen_dose[self.t])

        self.salt_per_col_annual_constr = Constraint(expr=self.salt_per_column_annual[self.t] == self.num_regen_per_column_annual[self.t] * self.salt_per_regen_per_column[self.t])  # kg / year per column

        self.salt_total_annual_constr = Constraint(expr=self.salt_total_annual[self.t] == self.salt_per_column_annual[self.t] * self.num_columns[self.t])  # kg / year

        self.salt_dose_constr = Constraint(expr=self.salt_dose[self.t] == self.salt_total_annual[self.t] / flow_out_m3_yr)

        self.regen_soln_per_col_constr = Constraint(expr=self.regen_soln_per_column[self.t] == self.resin_per_column[self.t] * self.regen_vol[self.t])

        self.regen_soln_per_col_annual_constr = Constraint(expr=self.regen_soln_per_column_annual[self.t] == self.regen_soln_per_column[self.t] * self.num_regen_per_column_annual[self.t])

        self.regen_soln_annual_constr = Constraint(expr=self.regen_soln_annual[self.t] == self.regen_soln_per_column_annual[self.t] * self.num_columns[self.t])

        self.regen_time_per_col_constr = Constraint(expr=self.regen_time_per_column[self.t] == self.ebct[self.t] * self.regen_vol[self.t])

        self.total_regen_time_constr = Constraint(expr=self.total_regen_time[self.t] == self.regen_time_per_column[self.t] + self.rinse_time_per_column[self.t] + self.bw_time[self.t])

        self.regen_flow_constr = Constraint(expr=self.regen_flow[self.t] == self.column_vol[self.t] / self.regen_time_per_column[self.t])

        ##### BW CONSTRAINTS

        self.bed_exp_constr = Constraint(expr=self.bed_expansion[self.t] == -1.35E-3 * self.bw_rate[self.t] ** 2 + 1.02E-1 * self.bw_rate[self.t] - 1.23E-2)

        self.bed_exp_h_constr = Constraint(expr=self.bed_expansion_h[self.t] == self.resin_depth[self.t] * self.bed_expansion[self.t])

        self.bw_flow_constr = Constraint(expr=self.bw_flow[self.t] == self.column_vol[self.t] / self.bw_time[self.t])

        ##### RINSE CONSTRAINTS

        self.rinse_vol_per_column_constr = Constraint(expr=self.rinse_vol_per_column[self.t] == self.resin_per_column[self.t] * self.rinse_bv[self.t])

        self.rinse_vol_per_col_annual_constr = Constraint(expr=self.rinse_vol_per_column_annual[self.t] == self.rinse_vol_per_column[self.t] * self.num_regen_per_column_annual[self.t])

        self.rinse_time_per_col_constr = Constraint(expr=self.rinse_time_per_column[self.t] == self.ebct[self.t] * self.rinse_bv[self.t])

        self.rinse_flow_constr = Constraint(expr=self.rinse_flow[self.t] == self.column_vol[self.t] / self.rinse_time_per_column[self.t])

        ##### WATER RECOVERY, CHEM DICT, AND CONSTITUENT REMOVAL

        self.wr_constr = Constraint(expr=self.water_recovery[self.t] == 1 - (self.total_regen_time[self.t] / ((self.cycle_time[self.t] * 60) + self.total_regen_time[self.t])))

        self.chem_dict = {
                'Sodium_Chloride': self.salt_dose[self.t]
                }

        self.del_component(self.component_removal_equation)

        self.ix_component_removal = ConstraintList()
        for c in self.config.property_package.component_list:
            if c in self.cons:
                self.ix_component_removal.add(self.frac_removed[self.t, c] * self.flow_vol_in[self.t] * self.conc_mass_in[self.t, c] ==
                                              self.flow_vol_waste[self.t] * self.conc_mass_waste[self.t, c])
            else:
                self.ix_component_removal.add(self.removal_fraction[self.t, c] * self.flow_vol_in[self.t] * self.conc_mass_in[self.t, c] ==
                                              self.flow_vol_waste[self.t] * self.conc_mass_waste[self.t, c])

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        time = self.flowsheet().config.time
        self.t = time.first()
        self.units_meta = self.config.property_package.get_metadata().get_derived_units

        self.mode = unit_params['mode']
        self.source_df = self.parent_block().source_df
        self.parent_block().has_ix = True
        try:
            self.pv_material = unit_params['pv_material']
        except KeyError:
            self.pv_material = 'carbon_w_plastic_internals'



        if self.mode == 'sac':
            self.resin_dict = {
                    'polystyrenic_macro': 3680,
                    'polystyrenic_gel': 6240,
                    } # cost of resin per m3, adapted to $/m3 from EPA models

            try:
                self.resin_type = unit_params['resin_type']
            except KeyError:
                self.resin_type = 'polystyrenic_macro'
            self.sac(unit_params)

        if self.mode == 'sba':
            self.resin_dict = {
                    'styrenic_gel_1': 5214,
                    'styrenic_gel_2': 6116,
                    'styrenic_macro_1': 7298,
                    'styrenic_macro_2': 7810,
                    'polyacrylic': 8658,
                    'nitrate': 6116
                    } # cost of resin per m3, adapted to $/m3 from EPA models
            try:
                self.resin_type = unit_params['resin_type']
            except KeyError:
                self.resin_type = 'styrenic_gel_1'
            self.sba(unit_params)



        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')

        self.costing.other_var_cost = (self.resin_unit_cap[self.t] * self.resin_loss_annual[self.t]) * 1E-6
        financials.get_complete_costing(self.costing)