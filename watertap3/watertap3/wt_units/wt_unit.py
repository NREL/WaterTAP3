#!/usr/bin/env python3

##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Base IDAES unit for WaterTAP3
"""

import idaes.logger as idaeslog
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import NonNegativeReals, SolverFactory, Var, units as pyunits
from pyomo.network import Port


@declare_process_block_class("WT3UnitProcess")
class WT3UnitProcessData(UnitModelBlockData):
    """
    This class describes the rules for a zeroth-order model for a unit

    The Config Block is used tpo process arguments from when the model is
    instantiated. In IDAES, this serves two purposes:
         1. Allows us to separate physical properties from unit models
         2. Lets us give users options for configuring complex units
    The dynamic and has_holdup options are expected arguments which must exist
    The property package arguments let us define different sets of contaminants
    without needing to write a new model.
    """

    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(domain=In([False]), default=False,
                                          description="Dynamic model flag - must be False",
                                          doc="""Indicates whether this model will be dynamic or 
                                          not,
                                          **default** = False. Equilibrium Reactors do not 
                                          support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(default=False, domain=In([False]),
                                             description="Holdup construction flag - must be False",
                                             doc="""Indicates whether holdup terms should be 
                                             constructed or not.
                                            **default** - False. Equilibrium reactors do not have defined volume, thus
                                            this must be False."""))
    CONFIG.declare("property_package", ConfigValue(default=useDefault,
                                                   domain=is_physical_parameter_block,
                                                   description="Property package to use for control volume",
                                                   doc="""Property parameter object used to define property 
                                                   calculations,
                                                    **default** - useDefault.
                                                    **Valid values:** {
                                                    **useDefault** - use default package from parent model or flowsheet,
                                                    **PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(implicit=True,
                                                        description="Arguments to use for "
                                                                    "constructing property "
                                                                    "packages",
                                                        doc="""A ConfigBlock with arguments to be 
                                                        passed to a property block(s)
                                                        and used when constructing these,
                                                        **default** - None.
                                                        **Valid values:** {
                                                        see property package for documentation.}"""))

    def build(self):
        super(WT3UnitProcessData, self).build()
        units_meta = self.config.property_package.get_metadata().get_derived_units
        time = self.flowsheet().config.time

        ## INLET
        self.flow_vol_in = Var(time,
                               initialize=1,
                               domain=NonNegativeReals,
                               units=units_meta("volume") / units_meta("time"),
                               bounds=(1e-8, 1e2),
                               doc="Volumetric flowrate of water into unit")
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                initialize=1e-5,
                                # domain=NonNegativeReals,
                                units=units_meta("mass") / units_meta("volume"),
                                doc="Mass concentration of species at inlet")
        self.temperature_in = Var(time,
                                  initialize=300,
                                  units=units_meta("temperature"),
                                  doc="Temperature at inlet")
        self.pressure_in = Var(time,
                               initialize=1,
                               domain=NonNegativeReals,
                               units=units_meta("pressure"),
                               doc="Pressure at inlet")

        ## OUTLET
        self.flow_vol_out = Var(time,
                                initialize=1,
                                domain=NonNegativeReals,
                                units=units_meta("volume") / units_meta("time"),
                                doc="Volumetric flowrate of water out of unit")
        self.conc_mass_out = Var(time,
                                 self.config.property_package.component_list,
                                 initialize=0,
                                 # domain=NonNegativeReals,
                                 units=units_meta("mass") / units_meta("volume"),
                                 doc="Mass concentration of species at outlet")
        self.temperature_out = Var(time,
                                   initialize=300,
                                   units=units_meta("temperature"),
                                   doc="Temperature at outlet")
        self.pressure_out = Var(time,
                                initialize=1,
                                domain=NonNegativeReals,
                                units=units_meta("pressure"),
                                doc="Pressure at outlet")
        self.deltaP_outlet = Var(time,
                                 initialize=1e-6,
                                 # domain=NonNegativeReals,
                                 units=units_meta("pressure"),
                                 doc="Pressure change between inlet and outlet")

        self.deltaP_outlet.fix(1E-4)

        ## WASTE
        self.flow_vol_waste = Var(time,
                                  initialize=1,
                                  domain=NonNegativeReals,
                                  units=units_meta("volume") / units_meta("time"),
                                  doc="Volumetric flowrate of water in waste")
        self.conc_mass_waste = Var(time,
                                   self.config.property_package.component_list,
                                   initialize=0,
                                   units=units_meta("mass") / units_meta("volume"),
                                   doc="Mass concentration of species in waste")
        self.temperature_waste = Var(time,
                                     initialize=300,
                                     domain=NonNegativeReals,
                                     units=units_meta("temperature"),
                                     doc="Temperature of waste")
        self.pressure_waste = Var(time,
                                  initialize=1,
                                  domain=NonNegativeReals,
                                  units=units_meta("pressure"),
                                  doc="Pressure of waste")

        self.deltaP_waste = Var(time,
                                initialize=1e-6,
                                # domain=NonNegativeReals,
                                units=units_meta("pressure"),
                                doc="Pressure change between inlet and waste")

        self.deltaP_waste.fix(1E-4)

        ## WATER RECOVERY & REMOVAL FRACTION
        self.water_recovery = Var(time,
                                  initialize=0.8,
                                  domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  bounds=(1e-8, 1.0000001),
                                  doc="Water recovery fraction")
        self.removal_fraction = Var(time,
                                    self.config.property_package.component_list,
                                    domain=NonNegativeReals,
                                    initialize=0.01,
                                    units=pyunits.dimensionless,
                                    doc="Component removal fraction")

        @self.Constraint(time, doc="Outlet pressure equation")
        def outlet_pressure_constraint(b, t):
            return (b.pressure_in[t] + b.deltaP_outlet[t] ==
                    b.pressure_out[t])

        @self.Constraint(time, doc="Waste pressure equation")
        def waste_pressure_constraint(b, t):
            return (b.pressure_in[t] + b.deltaP_waste[t] ==
                    b.pressure_waste[t])

        @self.Constraint(time, doc="Water recovery equation")
        def recovery_equation(b, t):
            return b.water_recovery[t] * b.flow_vol_in[t] == b.flow_vol_out[t]

            # Next, add constraints linking these

        @self.Constraint(time, doc="Overall flow balance")
        def flow_balance(b, t):
            return b.flow_vol_in[t] == b.flow_vol_out[t] + b.flow_vol_waste[t]

        @self.Constraint(time,
                         self.config.property_package.component_list,
                         doc="Component removal equation")
        def component_removal_equation(b, t, j):
            return (b.removal_fraction[t, j] *
                    b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
                    b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

        @self.Constraint(time,
                         self.config.property_package.component_list,
                         doc="Component mass balances")
        def component_mass_balance(b, t, j):
            return (b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
                    b.flow_vol_out[t] * b.conc_mass_out[t, j] +
                    b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

        @self.Constraint(time, doc="Outlet temperature equation")
        def outlet_temperature_constraint(b, t):
            return b.temperature_in[t] == b.temperature_out[t]

        @self.Constraint(time, doc="Waste temperature equation")
        def waste_temperature_constraint(b, t):
            return b.temperature_in[t] == b.temperature_waste[t]

        # The last step is to create Ports representing the three streams
        # Add an empty Port for the inlet
        self.inlet = Port(noruleinit=True, doc="Inlet Port")

        # Populate Port with inlet variables
        self.inlet.add(self.flow_vol_in, "flow_vol")
        self.inlet.add(self.conc_mass_in, "conc_mass")
        self.inlet.add(self.temperature_in, "temperature")
        self.inlet.add(self.pressure_in, "pressure")

        # Add Ports for outlet and waste streams
        self.outlet = Port(noruleinit=True, doc="Outlet Port")
        self.outlet.add(self.flow_vol_out, "flow_vol")
        self.outlet.add(self.conc_mass_out, "conc_mass")
        self.outlet.add(self.temperature_out, "temperature")
        self.outlet.add(self.pressure_out, "pressure")

        self.waste = Port(noruleinit=True, doc="Waste Port")
        self.waste.add(self.flow_vol_waste, "flow_vol")
        self.waste.add(self.conc_mass_waste, "conc_mass")
        self.waste.add(self.temperature_waste, "temperature")
        self.waste.add(self.pressure_waste, "pressure")

    def initialize(
            blk,
            state_args=None,
            routine=None,
            outlvl=idaeslog.NOTSET,
            solver="ipopt",
            optarg={"tol": 1e-6}):
        """
        General wrapper for pressure changer initialization routines
        Keyword Arguments:
            routine : str stating which initialization routine to execute
                        * None - currently no specialized routine for RO unit
            state_args : a dict of arguments to be passed to the property
                         package(s) to provide an initial state for
                         initialization (see documentation of the specific
                         property package) (default = {}).
            outlvl : sets output level of initialization routine
            optarg : solver options dictionary object (default={'tol': 1e-6})
            solver : str indicating whcih solver to use during
                     initialization (default = 'ipopt')
        Returns:
            None
        """
        init_log = idaeslog.getInitLogger(blk.name, outlvl, tag="unit")
        solve_log = idaeslog.getSolveLogger(blk.name, outlvl, tag="unit")
        # Set solver options
        opt = SolverFactory(solver)
        opt.options = optarg

        # ---------------------------------------------------------------------
        # Initialize holdup block
        flags = blk.unit.initialize(
                outlvl=outlvl,
                optarg=optarg,
                solver=solver,
                state_args=state_args,
                )
        init_log.info_high("Initialization Step 1 Complete.")
        # ---------------------------------------------------------------------
        # Initialize permeate
        # Set state_args from inlet state
        if state_args is None:
            state_args = {}
            state_dict = blk.feed_side.properties_in[
                blk.flowsheet().config.time.first()].define_port_members()

            for k in state_dict.keys():
                if state_dict[k].is_indexed():
                    state_args[k] = {}
                    for m in state_dict[k].keys():
                        state_args[k][m] = state_dict[k][m].value
                else:
                    state_args[k] = state_dict[k].value

        blk.properties_permeate.initialize(
                outlvl=outlvl,
                optarg=optarg,
                solver=solver,
                state_args=state_args,
                )
        init_log.info_high("Initialization Step 2 Complete.")

        # ---------------------------------------------------------------------
        # Solve unit
        with idaeslog.solver_log(solve_log, idaeslog.DEBUG) as slc:
            res = opt.solve(blk, tee=slc.tee)
        init_log.info_high(
                "Initialization Step 3 {}.".format(idaeslog.condition(res)))

        # ---------------------------------------------------------------------
        # Release Inlet state
        blk.unit.release_state(flags, outlvl + 1)
        init_log.info(
                "Initialization Complete: {}".format(idaeslog.condition(res))
                )

    # def get_costing(self, tpec_or_tic=None, cost_method='wt', year=None,
    #                 unit_params=None, basis_year=2020):
    #     #
    #     # if not hasattr(self.flowsheet(), "costing"):
    #     #     self.flowsheet().get_costing(module=module, year=year)
    #     #
    #     self.costing = Block()
    #     #
    #     # time = self.flowsheet().config.time.first()
    #     # flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hour)
    #
    #     sys_cost_params = self.parent_block().costing_param
    #     self.tpec_or_tic = tpec_or_tic
    #     if self.tpec_or_tic == 'TPEC':
    #         self.costing.tpec_tic = sys_cost_params.tpec
    #     else:
    #         self.costing.tpec_tic = sys_cost_params.tic
    #
    #     self.costing.basis_year = basis_year
    #
    #     chem_dict = {}
    #     self.chem_dict = chem_dict
    #
    #
    #     self.costing.fixed_cap_inv_unadjusted = Expression(expr=0,
    #                                                        doc="Unadjusted fixed capital "
    #                                                            "investment")  # $MM
    #
    #     self.electricity = 0  # kwh/m3
    #
    #     financials.get_complete_costing(self.costing)