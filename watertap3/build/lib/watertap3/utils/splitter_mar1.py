from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Constraint, NonNegativeReals, Var, units as pyunits
from pyomo.network import Port

module_name = "splitter_mar1"

__all__ = ['Splitter']


@declare_process_block_class("Splitter")
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

    def get_split(self, outlet_list=None, unit_params=None):
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        units_meta = self.config.property_package.get_metadata().get_derived_units

        # Add ports
        for p in outlet_list:
            setattr(self, p, Port(noruleinit=True, doc="Outlet Port"))  # ARIEL

            setattr(self, ("flow_vol_%s" % p), Var(time,
                                                   # initialize=0.5,
                                                   domain=NonNegativeReals,
                                                   bounds=(1e-9, 1e2),
                                                   units=units_meta("volume") / units_meta("time"),
                                                   doc="Volumetric flowrate of water out of unit"))

            setattr(self, ("conc_mass_%s" % p), Var(time,
                                                    self.config.property_package.component_list,
                                                    initialize=1e-3,
                                                    units=units_meta("mass") / units_meta("volume"),
                                                    doc="Mass concentration of species at outlet"))

            setattr(self, ("pressure_%s" % p), Var(time,
                                                   initialize=1e5,
                                                   domain=NonNegativeReals,
                                                   units=units_meta("pressure"),
                                                   doc="Pressure at outlet"))

            setattr(self, ("temperature_%s" % p), Var(time,
                                                      initialize=300,
                                                      domain=NonNegativeReals,
                                                      units=units_meta("temperature"),
                                                      doc="Temperature at outlet"))

            setattr(self, ("split_fraction_%s" % p), Var(time,
                                                         initialize=0.5,
                                                         domain=NonNegativeReals,
                                                         bounds=(0.01, 0.99),
                                                         # units=units_meta("pressure"),
                                                         doc="split fraction"))

            getattr(self, p).add(getattr(self, ("temperature_%s" % p)), "temperature")
            getattr(self, p).add(getattr(self, ("pressure_%s" % p)), "pressure")
            getattr(self, p).add(getattr(self, ("conc_mass_%s" % p)), "conc_mass")
            getattr(self, p).add(getattr(self, ("flow_vol_%s" % p)), "flow_vol")

        self.inlet = Port(noruleinit=True, doc="Inlet Port")

        self.flow_vol_in = Var(time,
                               # initialize=1,
                               domain=NonNegativeReals,
                               bounds=(1e-9, 1e2),
                               units=units_meta("volume") / units_meta("time"),
                               doc="Volumetric flowrate of water out of unit")
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                initialize=1e-3,
                                units=units_meta("mass") / units_meta("volume"),
                                doc="Mass concentration of species at outlet")
        self.temperature_in = Var(time,
                                  initialize=300,
                                  units=units_meta("temperature"),
                                  doc="Temperature at outlet")
        self.pressure_in = Var(time,
                               initialize=1e5,
                               units=units_meta("pressure"),
                               doc="Pressure at outlet")

        self.inlet.add(self.flow_vol_in, "flow_vol")
        self.inlet.add(self.conc_mass_in, "conc_mass")
        self.inlet.add(self.temperature_in, "temperature")
        self.inlet.add(self.pressure_in, "pressure")

        ## set the split fraction as equal unless, stated otherwise.

        for i, p in enumerate(outlet_list):
            # self.split_fraction.fix(1 / len(outlet_list))
            if "split_fraction" in unit_params.keys():
                getattr(self, ("split_fraction_%s" % p)).fix(unit_params["split_fraction"][i])
            else:
                getattr(self, ("split_fraction_%s" % p)).fix(1 / len(outlet_list))

        for p in outlet_list:
            for j in self.config.property_package.component_list:
                setattr(self, ("%s_%s_eq" % (p, j)), Constraint(expr=self.conc_mass_in[t, j]
                                                                     == getattr(self, ("conc_mass_%s" % p))[t, j]))

        for p in outlet_list:
            setattr(self, ("%s_eq_flow" % p),
                    Constraint(
                            expr=getattr(self, ("split_fraction_%s" % p))[t] * pyunits.convert(self.flow_vol_in[t],
                                                                                               to_units=pyunits.m ** 3 / pyunits.hr)
                                 == pyunits.convert(getattr(self, ("flow_vol_%s" % p))[t],
                                                    to_units=pyunits.m ** 3 / pyunits.hr)))

        for p in outlet_list:
            setattr(self, ("%s_eq_temp" % (p)), Constraint(expr=self.temperature_in[t]
                                                                == getattr(self, ("temperature_%s" % p))[t]))

        for p in outlet_list:
            setattr(self, ("%s_eq_pres" % (p)), Constraint(expr=self.pressure_in[t]
                                                                == getattr(self, ("pressure_%s" % p))[t]))