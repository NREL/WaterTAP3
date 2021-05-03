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
Demonstration property package for WaterTAP3

For WaterTAP3 models, this package primarily needs to define the following:
    - a trivial phase list
    - components in the system for removal
    - base units of measurement
"""

# Import Pyomo libraries
from pyomo.environ import units as pyunits
# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        MaterialFlowBasis,
                        PhysicalParameterBlock,
                        StateBlockData,
                        StateBlock,
                        MaterialBalanceType,
                        EnergyBalanceType)
from idaes.core.phases import LiquidPhase
from idaes.core.components import Component

__all__ = ['WaterParameterBlock',
           'WaterStateBlock']

# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("WaterParameterBlock")
class WaterParameterData(PhysicalParameterBlock):
    CONFIG = PhysicalParameterBlock.CONFIG()
    """
    Property Parameter Block Class

    Define component and phase lists, along with base units
    """

    def build(self):
        '''
        Callable method for Block construction.
        '''
        super(WaterParameterData, self).build()

        self._state_block_class = WaterStateBlock

        # Add Phase objects
        self.Liq = LiquidPhase()
        self.tds = Component()
        self.tss = Component()
        self.toc = Component()

        # Add Component objects - only include contaminants, etc here
        # Water is assumed to always be present
        
        ### MAKE THIS BASED ON THE DATA INPUT?!?! ###
        # import generate_constituent_list
        # train_constituent_list = generate_constituent_list.run(self.parent_block())
        #
        # for constituent_name in train_constituent_list:
        # #for constituent_name in ["TOC", "nitrates", "TDS"]:
        #     setattr(self, constituent_name, Component())

    @classmethod
    def define_metadata(cls, obj):
        """Define properties supported and units."""
        obj.add_properties(
            {'flow_vol_in': {'method': None, 'units': pyunits.m**3/pyunits.s},
             'conc_mass_in': {'method': None, 'units': pyunits.kg/pyunits.m**3},
             'temperature_in': {'method': None, 'units': pyunits.degK},
             'pressure_in': {'method': None, 'units': pyunits.bar},
             'flow_vol_out': {'method': None, 'units': pyunits.m**3/pyunits.s},
             'conc_mass_out': {'method': None, 'units': pyunits.kg/pyunits.m**3},
             'temperature_out': {'method': None, 'units': pyunits.degK},
             'pressure_out': {'method': None, 'units': pyunits.bar},
             'flow_vol_waste': {'method': None, 'units': pyunits.m**3/pyunits.s},
             'conc_mass_waste': {'method': None, 'units': pyunits.kg/pyunits.m**3},
             'temperature_waste': {'method': None, 'units': pyunits.degK},
             'pressure_waste': {'method': None, 'units': pyunits.bar},
             'deltaP_outlet': {'method': None, 'units': pyunits.bar},
             'deltaP_waste': {'method': None, 'units': pyunits.bar},
             'water_recovery':{'method': None, 'units': pyunits.dimensionless},
             'removal_fraction': {'method': None, 'units': pyunits.dimensionless}
             })


        obj.add_default_units({'time': pyunits.s,
                               'length': pyunits.m,
                               'mass': pyunits.kg,
                               'amount': pyunits.mol,
                               'temperature': pyunits.degK})

class _WaterStateBlock(StateBlock):
    """
    This Class contains methods which should be applied to Property Blocks as a
    whole, rather than individual elements of indexed Property Blocks.
    """

    def initialize(blk, state_args={}, state_vars_fixed=False,
                   hold_state=False, outlvl=1,
                   solver='ipopt', optarg={'tol': 1e-8}):
        """
        Initialization routine for property package.
        Keyword Arguments:
            state_args : Dictionary with initial guesses for the state vars
                         chosen. Note that if this method is triggered
                         through the control volume, and if initial guesses
                         were not provied at the unit model level, the
                         control volume passes the inlet values as initial
                         guess.The keys for the state_args dictionary are:

                         flow_mol_phase_comp : value at which to initialize
                                               phase component flows
                         pressure : value at which to initialize pressure
                         temperature : value at which to initialize temperature
            outlvl : sets output level of initialization routine
                     * 0 = no output (default)
                     * 1 = return solver state for each step in routine
                     * 2 = include solver output infomation (tee=True)
            optarg : solver options dictionary object (default=None)
            state_vars_fixed: Flag to denote if state vars have already been
                              fixed.
                              - True - states have already been fixed by the
                                       control volume 1D. Control volume 0D
                                       does not fix the state vars, so will
                                       be False if this state block is used
                                       with 0D blocks.
                             - False - states have not been fixed. The state
                                       block will deal with fixing/unfixing.
            solver : str indicating whcih solver to use during
                     initialization (default = 'ipopt')
            hold_state : flag indicating whether the initialization routine
                         should unfix any state variables fixed during
                         initialization (default=False).
                         - True - states varaibles are not unfixed, and
                                 a dict of returned containing flags for
                                 which states were fixed during
                                 initialization.
                        - False - state variables are unfixed after
                                 initialization by calling the
                                 relase_state method
        Returns:
            If hold_states is True, returns a dict containing flags for
            which states were fixed during initialization.
        """

        _log.info('Starting {} initialization'.format(blk.name))

        # Fix state variables if not already fixed
        if state_vars_fixed is False:
            flags = fix_state_vars(blk, state_args)

        else:
            # Check when the state vars are fixed already result in dof 0
            for k in blk.keys():
                if degrees_of_freedom(blk[k]) != 0:
                    raise Exception("State vars fixed but degrees of freedom "
                                    "for state block is not zero during "
                                    "initialization.")
        # Set solver options
        if outlvl > 1:
            stee = True
        else:
            stee = False

        if optarg is None:
            sopt = {'tol': 1e-8}
        else:
            sopt = optarg

        opt = SolverFactory('ipopt')
        opt.options = sopt
        # ---------------------------------------------------------------------
        # Initialize flow rates and compositions

        free_vars = 0
        for k in blk.keys():
            free_vars += number_unfixed_variables(blk[k])
        if free_vars > 0:
            try:
                results = solve_indexed_blocks(opt, [blk], tee=stee)
            except:
                results = None
        else:
            results = None

        if outlvl > 0:
            if results is None or results.solver.termination_condition \
                    == TerminationCondition.optimal:
                _log.info("Property initialization for "
                          "{} completed".format(blk.name))
            else:
                _log.warning("Property initialization for "
                             "{} failed".format(blk.name))

        # ---------------------------------------------------------------------
        # Return state to initial conditions
        if state_vars_fixed is False:
            if hold_state is True:
                return flags
            else:
                blk.release_state(flags)

        if outlvl > 0:
            _log.info("Initialization completed for {}".format(blk.name))

    def release_state(blk, flags, outlvl=0):
        '''
        Method to relase state variables fixed during initialization.
        Keyword Arguments:
            flags : dict containing information of which state variables
                    were fixed during initialization, and should now be
                    unfixed. This dict is returned by initialize if
                    hold_state=True.
            outlvl : sets output level of of logging
        '''
        if flags is None:
            return

        # Unfix state variables
        revert_state_vars(blk, flags)

        if outlvl > 0:
            if outlvl > 0:
                _log.info('{} states released.'.format(blk.name))

@declare_process_block_class("WaterStateBlock",
                             block_class=_WaterStateBlock)
# @declare_process_block_class("WaterStateBlock")
class WaterStateBlockData(StateBlockData):
    """
    This won;t actually be used for most WaterTAP3 models, but is included to
    allow for future integration with ProteusLib and IDAES
    """

    def build(self):
        """
        Callable method for Block construction
        """
        super(WaterStateBlockData, self).build()
        self.scaling_factor = Suffix(direction=Suffix.EXPORT)

        # Next, get the base units of measurement from the property definition
        units_meta = self.config.property_package.get_metadata().get_derived_units

        # Also need to get time domain
        # This will not be used for WaterTAP3, but will be needed to integrate
        # with ProteusLib dynamic models
        time = self.flowsheet().config.time

        # Add variables representing flow at inlet
        # Note that Vars are indexed by time and have units derived from
        # property package
        # Property metadata does not currently support concentration or volumetric
        # flow, but I will fix that.
        # Note that the concentration variable is indexed by components
        # I included temperature and pressure as these would commonly be used
        # in ProteusLib
        if unit_name == "chlorination":
            unit_process_model.get_additional_variables(self, units_meta, time)
        if unit_name == "ro_deep":
            unit_process_model.get_additional_variables(self, units_meta, time)
        if unit_name == "ro_deep_scnd_pass":
            unit_process_model.get_additional_variables(self, units_meta, time)
        # if unit_name == "uv_aop":
        #     unit_process_model.get_additional_variables(self, units_meta, time)

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

        # Add similar variables for outlet and waste stream
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

        self.flow_vol_waste = Var(
                time,
                initialize=1,
                domain=NonNegativeReals,
                units=units_meta("volume") / units_meta("time"),
                doc="Volumetric flowrate of water in waste")
        self.conc_mass_waste = Var(
                time,
                self.config.property_package.component_list,
                # domain=NonNegativeReals,
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

        # Next, add additional variables for unit performance
        self.deltaP_outlet = Var(time,
                                 initialize=1e-6,
                                 # domain=NonNegativeReals,
                                 units=units_meta("pressure"),
                                 doc="Pressure change between inlet and outlet")
        self.deltaP_waste = Var(time,
                                initialize=1e-6,
                                # domain=NonNegativeReals,
                                units=units_meta("pressure"),
                                doc="Pressure change between inlet and waste")

        # Then, recovery and removal variables

        self.water_recovery = Var(time,
                                  initialize=0.8,  # TODO: NEEDS TO BE DIFFERENT?
                                  domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  bounds=(1e-8, 1.0000001),
                                  doc="Water recovery fraction")
        self.removal_fraction = Var(time,
                                    self.config.property_package.component_list,
                                    domain=NonNegativeReals,
                                    initialize=0.01,  # TODO: NEEDS TO BE DIFFERENT?
                                    units=pyunits.dimensionless,
                                    doc="Component removal fraction")

        special_list = ["reverse_osmosis"]  # , "anion_exchange_epa"]
        if unit_name not in special_list:

            if unit_name != "ro_deep":

                # print("includes pressure constraint in equations")

                @self.Constraint(time, doc="Outlet pressure equation")
                def outlet_pressure_constraint(b, t):
                    return (b.pressure_in[t] + b.deltaP_outlet[t] ==
                            b.pressure_out[t])

                @self.Constraint(time, doc="Waste pressure equation")
                def waste_pressure_constraint(b, t):
                    return (b.pressure_in[t] + b.deltaP_waste[t] ==
                            b.pressure_waste[t])

            if unit_name != "anion_exchange_epa":

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
        # self.inlet = Port(noruleinit=True, doc="Inlet Port")

        # Populate Port with inlet variables
        # self.inlet.add(self.flow_vol_in, "flow_vol")
        # self.inlet.add(self.conc_mass_in, "conc_mass")
        # self.inlet.add(self.temperature_in, "temperature")
        # self.inlet.add(self.pressure_in, "pressure")
        #
        # # Add Ports for outlet and waste streams
        # self.outlet = Port(noruleinit=True, doc="Outlet Port")
        # self.outlet.add(self.flow_vol_out, "flow_vol")
        # self.outlet.add(self.conc_mass_out, "conc_mass")
        # self.outlet.add(self.temperature_out, "temperature")
        # self.outlet.add(self.pressure_out, "pressure")
        #
        # self.waste = Port(noruleinit=True, doc="Waste Port")
        # self.waste.add(self.flow_vol_waste, "flow_vol")
        # self.waste.add(self.conc_mass_waste, "conc_mass")
        # self.waste.add(self.temperature_waste, "temperature")
        # self.waste.add(self.pressure_waste, "pressure")
        #


    def define_state_vars(self):
        return {
                "flow_vol_in": self.flow_mass_comp,
                "flow_vol_out": self.temperature,
                "flow_vol_waste": self.pressure,
                "conc_mass_in": self.conc_mass_in,
                "conc_mass_out": self.conc_mass_out,
                "conc_mass_waste": self.conc_mass_waste,
                "temperature_in": self.temperature_in,
                "temperature_out": self.temperature_out,
                "temperature_waste": self.temperature_waste,
                "pressure_in": self.pressure_in,
                "pressure_out": self.pressure_out,
                "pressure_waste": self.pressure_waste,
                "water_recovery": self.water_recovery,
                "removal_fraction": self.removal_fraction,
                "deltaP_outlet": self.deltaP_outlet,
                "deltaP_waste": self.deltaP_waste

                }

    def define_port_members(self):
        return self.define_state_vars()