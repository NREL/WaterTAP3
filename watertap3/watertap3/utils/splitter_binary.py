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
from pyomo.environ import Binary, Constraint, ConstraintList, NonNegativeReals, Set, Var, units as pyunits
from pyomo.network import Port
from pyomo.gdp import Disjunct, Disjunction

module_name = 'splitter_binary'

__all__ = ['SplitterBinary']


@declare_process_block_class('SplitterBinary')
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

    def get_split(self, split_dict=None):
        time = self.flowsheet().config.time
        t = time.first()
        units_meta = self.config.property_package.get_metadata().get_derived_units
        self.outlet_list = outlet_list = [f'outlet_{i}' for i, _ in enumerate(split_dict.keys(), 1)]
        self.to_units = to_units = list(split_dict.keys())
        self.disj_list = []
        self.flow_outlets = []

        # Add ports
        self.inlet = Port(noruleinit=True, doc='Inlet Port')

        self.flow_vol_in = Var(time,
                               initialize=1,
                            #    domain=NonNegativeReals,
                               bounds=(-1E2, 1E2),
                               units=units_meta('volume') / units_meta('time'),
                               doc='Volumetric flowrate of water in to splitter [m3/s]')
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                initialize=1E-3,
                                bounds=(-1E5, 1E5),
                                units=units_meta('mass') / units_meta('volume'),
                                doc='Mass concentration of species at outlet')
        self.temperature_in = Var(time,
                                  initialize=300,
                                  bounds=(-400, 400), 
                                  units=units_meta('temperature'),
                                  doc='Temperature at outlet')
        self.pressure_in = Var(time,
                               initialize=1E5,
                               bounds=(-1E6, 1E6),
                               units=units_meta('pressure'),
                               doc='Pressure at outlet')

        self.inlet.add(self.flow_vol_in, 'flow_vol')
        self.inlet.add(self.conc_mass_in, 'conc_mass')
        self.inlet.add(self.temperature_in, 'temperature')
        self.inlet.add(self.pressure_in, 'pressure')

        self.temp_constr = ConstraintList()
        self.press_constr = ConstraintList()
        self.conc_constr = ConstraintList()
        self.flow_constr = ConstraintList()

        for (outlet, to_unit) in zip(outlet_list, to_units):
            setattr(self, outlet, Port(noruleinit=True, doc=f'Outlet Port {outlet}\nFlows to {to_unit}'))
            
            port_outlet = getattr(self, outlet)
            port_outlet.to_unit = to_unit

            setattr(self, f'flow_vol_{outlet}', Var(time,
                                                   initialize=0.5,
                                                #    domain=NonNegativeReals,
                                                   bounds=(0, 1E2),
                                                   units=units_meta('volume') / units_meta('time'),
                                                   doc='Volumetric flowrate of water out of splitter'))

            flow_outlet = getattr(self, f'flow_vol_{outlet}')

            setattr(self, f'conc_mass_{outlet}', Var(time,
                                                    self.config.property_package.component_list,
                                                    initialize=1E-3,
                                                    # domain=NonNegativeReals,
                                                    bounds=(-1E5, 1E5),
                                                    units=units_meta('mass') / units_meta('volume'),
                                                    doc='Mass concentration of species at outlet'))
            
            conc_mass_outlet  = getattr(self, f'conc_mass_{outlet}')

            setattr(self, f'pressure_{outlet}', Var(time,
                                                   initialize=1E5,
                                                #    domain=NonNegativeReals,
                                                   bounds=(-1E6, 1E6),
                                                   units=units_meta('pressure'),
                                                   doc='Pressure at outlet'))

            pressure_outlet = getattr(self, f'pressure_{outlet}')

            setattr(self, f'temperature_{outlet}', Var(time,
                                                      initialize=300,
                                                    #   domain=NonNegativeReals,
                                                      bounds=(-400, 400), 
                                                      units=units_meta('temperature'),
                                                      doc='Temperature at outlet'))

            temperature_outlet = getattr(self, f'temperature_{outlet}')

            setattr(self, f'disjunct_{outlet}', Disjunct())
            
            disj_outlet = getattr(self, f'disjunct_{outlet}')
            self.disj_list.append(disj_outlet)
            
            disj_outlet.flow = Constraint(expr=self.flow_vol_in[t] == flow_outlet[t])
            disj_outlet.pressure = Constraint(expr=self.pressure_in[t] == pressure_outlet[t])
            disj_outlet.temperature = Constraint(expr=self.temperature_in[t] == temperature_outlet[t])

            disj_outlet.conc_mass_out = ConstraintList()

            for c in self.config.property_package.component_list:
                disj_outlet.conc_mass_out.add(self.conc_mass_in[t, c] * self.flow_vol_in[t] == conc_mass_outlet[t, c] * flow_outlet[t])
            
            port_outlet.add(flow_outlet, 'flow_vol')
            port_outlet.add(conc_mass_outlet, 'conc_mass')
            port_outlet.add(pressure_outlet, 'pressure')
            port_outlet.add(temperature_outlet, 'temperature')

            # self.press_constr.add(self.pressure_in[t] == pressure_outlet[t])
            # self.temp_constr.add(self.temperature_in[t] == temperature_outlet[t])
            # self.flow_constr.add(self.flow_vol_in[t] == 1 / len(outlet_list) * flow_outlet[t])
            # for c in self.config.property_package.component_list:
            #     self.conc_constr.add(self.conc_mass_in[t, c] == conc_mass_outlet[t, c])

        for i, outlet in enumerate(outlet_list):
            disj_outlet = getattr(self, f'disjunct_{outlet}')
            other_outlets = [x for x in outlet_list if x != outlet]
            for other_outlet in other_outlets:
                other_outlet_flow = getattr(self, f'flow_vol_{other_outlet}')
                other_outlet_pressure = getattr(self, f'pressure_{other_outlet}')
                other_outlet_temperature = getattr(self, f'temperature_{other_outlet}')
                other_outlet_conc_mass = getattr(self, f'conc_mass_{other_outlet}')
                # disj_outlet.noflow = Constraint(expr=other_outlet_flow[t] == 0)
                # disj_outlet.nopress = Constraint(expr=other_outlet_pressure[t] == 0)
                # disj_outlet.notemp = Constraint(expr=other_outlet_temperature[t] == 0)

                setattr(disj_outlet, f'no_flow_{other_outlet}', Constraint(expr=other_outlet_flow[t] == 1E-16 * self.flow_vol_in[t]))
                setattr(disj_outlet, f'no_press_{other_outlet}', Constraint(expr=other_outlet_pressure[t] == 1E-12 * self.pressure_in[t]))
                setattr(disj_outlet, f'no_temp_{other_outlet}', Constraint(expr=other_outlet_temperature[t] == 1E-12 * self.temperature_in[t]))
                # disj_outlet.no_conc_mass_out = ConstraintList()
                # for c in self.config.property_package.component_list:
                    
                #     disj_outlet.no_conc_mass_out.add(other_outlet_conc_mass[t, c] * other_outlet_flow[t]== 1E-16 * self.conc_mass_in[t, c] * self.flow_vol_in[t])
                
        self.splitter_disjunction = Disjunction(expr=self.disj_list, xor=True)