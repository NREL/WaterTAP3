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
from pyomo.environ import Constraint, NonNegativeReals, Var
from pyomo.network import Port

module_name = 'source_wt3'


@declare_process_block_class('Source')
class SourceData(UnitModelBlockData):
    '''
    This class describes the rules for a zeroth-order model for a source.
    '''
    # The Config Block is used to process arguments from when the model is
    # instantiated. In IDAES, this serves two purposes:
    #     1. Allows us to separate physical properties from unit models
    #     2. Lets us give users options for configuring complex units
    # For WaterTAP3, this will mainly be boilerplate to keep things consistent
    # with ProteusLib and IDAES.
    # The dynamic and has_holdup options are expected arguments which must exist
    # The property package arguments let us define different sets of contaminants
    # without needing to write a new model.
    CONFIG = ConfigBlock()
    CONFIG.declare('dynamic', ConfigValue(
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
        super(SourceData, self).build()
        
        return

    def set_source(self):
        units_meta = self.config.property_package.get_metadata().get_derived_units
        time = self.flowsheet().config.time

        self.inlet = Port(noruleinit=True, doc='Inlet Port')

        self.flow_vol_in = Var(time,
                               initialize=1,
                               domain=NonNegativeReals,
                               units=units_meta('volume') / units_meta('time'),
                               doc='Volumetric flowrate of water into unit')
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                domain=NonNegativeReals,
                                initialize=1e-5,
                                units=units_meta('mass') / units_meta('volume'),
                                doc='Mass concentration of species at inlet')
        self.temperature_in = Var(time,
                                  initialize=300,
                                  units=units_meta('temperature'),
                                  doc='Temperature at inlet')
        self.pressure_in = Var(time,
                               initialize=1e5,
                               units=units_meta('pressure'),
                               doc='Pressure at inlet')

        self.outlet = Port(noruleinit=True, doc='outlet Port')

        self.flow_vol_out = Var(time,
                                initialize=1,
                                domain=NonNegativeReals,
                                units=units_meta('volume') / units_meta('time'),
                                doc='Volumetric flowrate of water out of unit')
        self.conc_mass_out = Var(time,
                                 self.config.property_package.component_list,
                                 initialize=0,
                                 domain=NonNegativeReals,
                                 units=units_meta('mass') / units_meta('volume'),
                                 doc='Mass concentration of species at outlet')
        self.temperature_out = Var(time,
                                   initialize=300,
                                   units=units_meta('temperature'),
                                   doc='Temperature at outlet')
        self.pressure_out = Var(time,
                                initialize=1e5,
                                units=units_meta('pressure'),
                                doc='Pressure at outlet')

        self.inlet.add(self.flow_vol_in, 'flow_vol')
        self.inlet.add(self.conc_mass_in, 'conc_mass')
        self.inlet.add(self.temperature_in, 'temperature')
        self.inlet.add(self.pressure_in, 'pressure')

        self.outlet.add(self.flow_vol_out, 'flow_vol')
        self.outlet.add(self.conc_mass_out, 'conc_mass')
        self.outlet.add(self.temperature_out, 'temperature')
        self.outlet.add(self.pressure_out, 'pressure')

        t = self.flowsheet().config.time.first()

        self.temperature_in.fix(300)
        self.pressure_in.fix(1)

        for j in self.config.property_package.component_list:
            setattr(self, ('%s_eq' % j), Constraint(expr=self.conc_mass_in[t, j]
                                                         == self.conc_mass_out[t, j]))

        self.eq_flow = Constraint(expr=self.flow_vol_in[t] == self.flow_vol_out[t])

        self.eq_temp = Constraint(expr=self.temperature_in[t] == self.temperature_out[t])

        self.eq_pres = Constraint(expr=self.pressure_in[t] == self.pressure_out[t])