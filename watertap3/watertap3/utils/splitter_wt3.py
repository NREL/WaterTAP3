##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
##############################################################################


from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Binary, Constraint, NonNegativeReals, Var, units as pyunits
from pyomo.network import Port

module_name = 'splitter_wt3'

__all__ = ['Splitter']


@declare_process_block_class('Splitter')
class SplitterProcessData(UnitModelBlockData):
    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(
            domain=In([False]),
            default=False,
            description="Dynamic model flag - must be False",
            doc="""Indicates whether this model will be dynamic or not,
            **default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(
            default=False,
            domain=In([False]),
            description="Holdup construction flag - must be False",
            doc="""Indicates whether holdup terms should be constructed or not.
            **default** - False. Equilibrium reactors do not have defined volume, thus
            this must be False."""))
    CONFIG.declare("property_package", ConfigValue(
            default=useDefault,
            domain=is_physical_parameter_block,
            description="Property package to use for control volume",
            doc="""Property parameter object used to define property calculations,
            **default** - useDefault.
            **Valid values:** {
            **useDefault** - use default package from parent model or flowsheet,
            **PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
            implicit=True,
            description="Arguments to use for constructing property packages",
            doc="""A ConfigBlock with arguments to be passed to a property block(s)
            and used when constructing these,
            **default** - None.
            **Valid values:** {
            see property package for documentation.}"""))

    def build(self):
        super(SplitterProcessData, self).build()

    def get_split(self, outlet_list_up=None, unit_params=None):
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        units_meta = self.config.property_package.get_metadata().get_derived_units
        self.outlet_list = outlet_list = outlet_list_up.keys()
        self.decision = all(splits == 1 for splits in outlet_list_up.values())
        self.decision_vars = []
        self.split_fraction_vars = []
        self.flow_outlets = []
        # print(outlet_list)
        # Add ports
        self.inlet = Port(noruleinit=True, doc='Inlet Port')

        self.flow_vol_in = Var(time,
                               initialize=1,
                               domain=NonNegativeReals,
                               bounds=(1E-9, 1E2),
                               units=units_meta('volume') / units_meta('time'),
                               doc='Volumetric flowrate of water in to splitter [m3/s]')
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                initialize=1E-3,
                                units=units_meta('mass') / units_meta('volume'),
                                doc='Mass concentration of species at outlet')
        self.temperature_in = Var(time,
                                  initialize=300,
                                  units=units_meta('temperature'),
                                  doc='Temperature at outlet')
        self.pressure_in = Var(time,
                               initialize=1E5,
                               units=units_meta('pressure'),
                               doc='Pressure at outlet')

        self.inlet.add(self.flow_vol_in, 'flow_vol')
        self.inlet.add(self.conc_mass_in, 'conc_mass')
        self.inlet.add(self.temperature_in, 'temperature')
        self.inlet.add(self.pressure_in, 'pressure')

        for p in outlet_list:
            setattr(self, p, Port(noruleinit=True, doc='Outlet Port'))

            setattr(self, ('flow_vol_%s' % p), Var(time,
                                                   initialize=0.5,
                                                   domain=NonNegativeReals,
                                                   bounds=(1E-9, 1E2),
                                                   units=units_meta('volume') / units_meta('time'),
                                                   doc='Volumetric flowrate of water out of unit'))

            setattr(self, ('conc_mass_%s' % p), Var(time,
                                                    self.config.property_package.component_list,
                                                    initialize=1E-3,
                                                    units=units_meta('mass') / units_meta('volume'),
                                                    doc='Mass concentration of species at outlet'))

            setattr(self, ('pressure_%s' % p), Var(time,
                                                   initialize=1E5,
                                                   domain=NonNegativeReals,
                                                   units=units_meta('pressure'),
                                                   doc='Pressure at outlet'))

            setattr(self, ('temperature_%s' % p), Var(time,
                                                      initialize=300,
                                                      domain=NonNegativeReals,
                                                      units=units_meta('temperature'),
                                                      doc='Temperature at outlet'))
            if not self.decision:
                setattr(self, ('split_fraction_%s' % p), Var(time,
                                                             initialize=0.5,
                                                             domain=NonNegativeReals,
                                                             bounds=(0.01, 0.99),
                                                             units=pyunits.dimensionless,
                                                             doc='split fraction'))

            if self.decision:
                setattr(self, ('split_fraction_%s' % p), Var(time,
                                                             initialize=1,
                                                             domain=NonNegativeReals,
                                                             bounds=(0, 1),
                                                             units=pyunits.dimensionless,
                                                             doc='split fraction'))

                setattr(self, ('decision_var_%s' % p), Var(time,
                                                           initialize=1,
                                                           # bounds=(0, 1),
                                                           within=Binary,
                                                           units=pyunits.dimensionless,
                                                           doc='variable for directing flow'))
                decision_var_name = ('decision_var_%s' % p)
                # split_fraction_var_name = ('split_fraction_%s' % p)
                flow_outlet_name = ('flow_vol_%s' % p)
                self.decision_vars.append(getattr(self, decision_var_name)[t])
                # self.split_fraction_vars.append(getattr(self, split_fraction_var_name)[t])
                self.flow_outlets.append(getattr(self, flow_outlet_name)[t])
            split_fraction_var_name = ('split_fraction_%s' % p)
            self.split_fraction_vars.append(getattr(self, split_fraction_var_name)[t])
            getattr(self, p).add(getattr(self, ('temperature_%s' % p)), 'temperature')
            getattr(self, p).add(getattr(self, ('pressure_%s' % p)), 'pressure')
            getattr(self, p).add(getattr(self, ('conc_mass_%s' % p)), 'conc_mass')
            getattr(self, p).add(getattr(self, ('flow_vol_%s' % p)), 'flow_vol')


        i = 0
        # print(outlet_list)


        for p in outlet_list:
            if outlet_list_up[p] == 'NA':
                getattr(self, ('split_fraction_%s' % p)).unfix()
            elif self.decision:
                getattr(self, ('split_fraction_%s' % p)).fix(1)
            else:
                getattr(self, ('split_fraction_%s' % p)).fix(outlet_list_up[p])
            # if 'split_fraction' in unit_params.keys():
            #     getattr(self, ('split_fraction_%s' % p)).fix(unit_params['split_fraction'][i])
            # else:
            #     getattr(self, ('split_fraction_%s' % p)).fix(1 / len(outlet_list))
            # i += 1

        for p in outlet_list:
            for j in self.config.property_package.component_list:
                setattr(self, ('%s_%s_eq' % (p, j)), Constraint(expr=self.conc_mass_in[t, j]
                                                                     == getattr(self, ('conc_mass_%s' % p))[t, j]))

        if self.decision:
            self.big_m = 1000
            self.split_fraction_constr = Constraint(expr=sum(self.split_fraction_vars) == 1)
            self.decision_var_constr = Constraint(expr=sum(self.decision_vars) == 1)
            # for i, decision_var in enumerate(self.decision_vars, 1):
            #     setattr(self, f'decision_var_constr_A{i}', Constraint(expr=self.flow_vol_in[t] - self.flow_outlets[i - 1] <= self.big_m * (1 - decision_var)))
            #     setattr(self, f'decision_var_constr_B{i}', Constraint(expr=self.flow_vol_in[t] - self.flow_outlets[i - 1] <= self.big_m * (decision_var)))

            for p in outlet_list:
                setattr(self, ('%s_eq_flow' % p),
                        Constraint(
                                expr=getattr(self, ('split_fraction_%s' % p))[t] * getattr(self, ('decision_var_%s' % p))[t] * self.flow_vol_in[t]
                                     == getattr(self, ('flow_vol_%s' % p))[t]))
        else:
            self.split_fraction_constr = Constraint(expr=sum(self.split_fraction_vars) <= 1.025)
            self.split_fraction_constr2 = Constraint(expr=sum(self.split_fraction_vars) >= 0.975)
            for p in outlet_list:
                setattr(self, ('%s_eq_flow' % p),
                        Constraint(
                                expr=getattr(self, ('split_fraction_%s' % p))[t] * pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)
                                     == pyunits.convert(getattr(self, ('flow_vol_%s' % p))[t], to_units=pyunits.m ** 3 / pyunits.hr)))
        # self.sum_flow_out = 0
        # for p in outlet_list:
        #     self.sum_flow_out += getattr(self, 'split_fraction_%s' % p)[t] * self.flow_vol_in[t]
        # self.split_fraction_constr3 = Constraint(expr=self.sum_flow_out == self.flow_vol_in[t])

        for p in outlet_list:
            setattr(self, ('%s_eq_temp' % (p)), Constraint(expr=self.temperature_in[t] == getattr(self, ('temperature_%s' % p))[t]))
            setattr(self, ('%s_eq_pres' % (p)), Constraint(expr=self.pressure_in[t] == getattr(self, ('pressure_%s' % p))[t]))
