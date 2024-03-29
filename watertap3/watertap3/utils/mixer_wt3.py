##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
##############################################################################
'''
General purpose mixer block for IDAES models
'''
from __future__ import absolute_import, division, print_function  # disable implicit relative imports

import logging
from enum import Enum

from pyomo.environ import (Reals, SolverFactory, TerminationCondition, Var)
from pyomo.common.config import ConfigBlock, ConfigValue, In
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import (is_physical_parameter_block, is_state_block, list_of_strings)
from idaes.core.util.exceptions import (BurntToast, ConfigurationError, PropertyNotSupportedError)
from idaes.core.util.misc import add_object_reference
from pyomo.network import Port

__author__ = 'Andrew Lee'

__all__ = ['Mixer']
# Set up logger
_log = logging.getLogger(__name__)


# Enumerate options for balances
class MixingType(Enum):
    none = 0
    extensive = 1



class MomentumMixingType(Enum):
    none = 0
    minimize = 1
    equality = 2
    minimize_and_equality = 3



@declare_process_block_class('Mixer')
class Mixer1Data(UnitModelBlockData):
    '''
    This is a general purpose model for a Mixer1 block with the IDAES modeling
    framework. This block can be used either as a stand-alone Mixer1 unit
    operation, or as a sub-model within another unit operation.

    This model creates a number of StateBlocks to represent the incoming
    streams, then writes a set of phase-component material balances, an
    overall enthalpy balance and a momentum balance (2 options) linked to a
    mixed-state StateBlock. The mixed-state StateBlock can either be specified
    by the user (allowing use as a sub-model), or created by the Mixer1.

    When being used as a sub-model, Mixer1 should only be used when a set
    of new StateBlocks are required for the streams to be mixed. It should not
    be used to mix streams from mutiple ControlVolumes in a single unit model -
    in these cases the unit model developer should write their own mixing
    equations.
    '''
    CONFIG = ConfigBlock()
    CONFIG.declare('dynamic', ConfigValue(
        domain=In([False]),
        default=False,
        description='Dynamic model flag - must be False',
        doc='''Indicates whether this model will be dynamic or not,
**default** = False. Mixer1 blocks are always steady-state.'''))
    CONFIG.declare('has_holdup', ConfigValue(
        default=False,
        domain=In([False]),
        description='Holdup construction flag - must be False',
        doc='''Mixer1 blocks do not contain holdup, thus this must be
False.'''))
    CONFIG.declare('property_package', ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description='Property package to use for mixer',
        doc='''Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PropertyParameterObject** - a PropertyParameterBlock object.}'''))
    CONFIG.declare('property_package_args', ConfigBlock(
        implicit=True,
        description='Arguments to use for constructing property packages',
        doc='''A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}'''))
    CONFIG.declare('inlet_list', ConfigValue(
        domain=list_of_strings,
        description='List of inlet names',
        doc='''A list containing names of inlets,
**default** - None.
**Valid values:** {
**None** - use num_inlets argument,
**list** - a list of names to use for inlets.}'''))
    CONFIG.declare('num_inlets', ConfigValue(
        domain=int,
        description='Number of inlets to unit',
        doc='''Argument indicating number (int) of inlets to construct, not
used if inlet_list arg is provided,
**default** - None.
**Valid values:** {
**None** - use inlet_list arg instead, or default to 2 if neither argument
provided,
**int** - number of inlets to create (will be named with sequential integers
from 1 to num_inlets).}'''))
    CONFIG.declare('has_phase_equilibrium', ConfigValue(
        default=False,
        domain=In([True, False]),
        description='Calculate phase equilibrium in mixed stream',
        doc='''Argument indicating whether phase equilibrium should be
calculated for the resulting mixed stream,
**default** - False.
**Valid values:** {
**True** - calculate phase equilibrium in mixed stream,
**False** - do not calculate equilibrium in mixed stream.}'''))
    CONFIG.declare('material_mixing_type', ConfigValue(
        default=MixingType.extensive,
        domain=MixingType,
        description='Method to use when mixing material flows',
        doc='''Argument indicating what method to use when mixing material
flows of incoming streams,
**default** - MixingType.extensive.
**Valid values:** {
**MixingType.none** - do not include material mixing equations,
**MixingType.extensive** - mix total flows of each phase-component pair.}'''))
    CONFIG.declare('energy_mixing_type', ConfigValue(
        default=MixingType.extensive,
        domain=MixingType,
        description='Method to use when mixing energy flows',
        doc='''Argument indicating what method to use when mixing energy
flows of incoming streams,
**default** - MixingType.extensive.
**Valid values:** {
**MixingType.none** - do not include energy mixing equations,
**MixingType.extensive** - mix total enthalpy flows of each phase.}'''))
    CONFIG.declare('momentum_mixing_type', ConfigValue(
        default=MomentumMixingType.minimize,
        domain=MomentumMixingType,
        description='Method to use when mixing momentum/pressure',
        doc='''Argument indicating what method to use when mixing momentum/
pressure of incoming streams,
**default** - MomentumMixingType.minimize.
**Valid values:** {
**MomentumMixingType.none** - do not include momentum mixing equations,
**MomentumMixingType.minimize** - mixed stream has pressure equal to the
minimimum pressure of the incoming streams (uses smoothMin operator),
**MomentumMixingType.equality** - enforces equality of pressure in mixed and
all incoming streams.,
**MomentumMixingType.minimize_and_equality** - add constraints for pressure
equal to the minimum pressure of the inlets and constraints for equality of
pressure in mixed and all incoming streams. When the model is initially built,
the equality constraints are deactivated.  This option is useful for switching
between flow and pressure driven simulations.}'''))
    CONFIG.declare('mixed_state_block', ConfigValue(
        default=None,
        domain=is_state_block,
        description='Existing StateBlock to use as mixed stream',
        doc='''An existing state block to use as the outlet stream from the
Mixer1 block,
**default** - None.
**Valid values:** {
**None** - create a new StateBlock for the mixed stream,
**StateBlock** - a StateBock to use as the destination for the mixed stream.}
'''))
    CONFIG.declare('construct_ports', ConfigValue(
        default=True,
        domain=In([True, False]),
        description='Construct inlet and outlet Port objects',
        doc='''Argument indicating whether model should construct Port objects
linked to all inlet states and the mixed state,
**default** - True.
**Valid values:** {
**True** - construct Ports for all states,
**False** - do not construct Ports.'''))

    def build(self):
        '''
        General build method for Mixer1Data. This method calls a number
        of sub-methods which automate the construction of expected attributes
        of unit models.

        Inheriting models should call `super().build`.

        Args:
            None

        Returns:
            None
        '''
        # Call super.build()
        super(Mixer1Data, self).build()

        # Call setup methods from ControlVolumeBlockData
        self._get_property_package()
        self._get_indexing_sets()
        
        # Create list of inlet names
        inlet_list = self.create_inlet_list()

        # Build StateBlocks
        inlet_blocks = self.add_inlet_state_blocks(inlet_list)

        if self.config.mixed_state_block is None:
            mixed_block = self.add_mixed_state_block()
        else:
            mixed_block = self.get_mixed_state_block()

        if self.config.material_mixing_type == MixingType.extensive:
            self.add_material_mixing_equations(inlet_blocks=inlet_blocks,
                                               mixed_block=mixed_block)
        elif self.config.material_mixing_type == MixingType.none:
            pass
        else:
            raise ConfigurationError('{} received unrecognised value for '
                                     'material_mixing_type argument. This '
                                     'should not occur, so please contact '
                                     'the IDAES developers with this bug.'
                                     .format(self.name))
            
        self.add_port_objects(inlet_list, inlet_blocks, mixed_block)#ARIEL

        units_meta = self.config.property_package.get_metadata().get_derived_units #ARIEL
        time = self.flowsheet().config.time #ARIEL  
        
       
        # Next, add constraints linking these
        @self.Constraint(time, doc='Overall flow balance')
        def flow_balance(b, t):
            flow_vol_sum = 0 
            for p in inlet_list:
                flow_vol_sum = getattr(b, ('flow_vol_%s' % p))[t] + flow_vol_sum
            
            return flow_vol_sum == b.flow_vol_out[t] #b.flow_vol_in[t] == b.flow_vol_out[t]
        
        
        @self.Constraint(time,
                         self.config.property_package.component_list,
                         doc='Component mass balances')
        def component_mass_balance(b, t, j):
            
            component_sum = 0
            for p in inlet_list:
                component_sum = getattr(b, ('flow_vol_%s' % p))[t] * getattr(b, ('conc_mass_%s' % p))[t, j] + component_sum
                
            return component_sum == b.flow_vol_out[t] * b.conc_mass_out[t, j]
        
        @self.Constraint(time, doc='Outlet temperature equation')
        def outlet_temperature_constraint(b, t):
            
            temperature_sum = 0 
            for p in inlet_list:
                temperature_sum = getattr(b, ('temperature_%s' % p))[t] + temperature_sum
            
            return temperature_sum / len(inlet_list) == b.temperature_out[t] #+ 1e-4
        
        
        @self.Constraint(time, doc='Outlet pressure equation')
        def outlet_pressure_constraint(b, t):
            
            pressure_sum = 0 
            for p in inlet_list:
                pressure_sum = getattr(b, ('pressure_%s' % p))[t] + pressure_sum            
            
            return pressure_sum / len(inlet_list) == b.pressure_out[t] #+ 1e-4


    def create_inlet_list(self):
        '''
        Create list of inlet stream names based on config arguments.

        Returns:
            list of strings
        '''
        if (self.config.inlet_list is not None and
                self.config.num_inlets is not None):
            # If both arguments provided and not consistent, raise Exception
            if len(self.config.inlet_list) != self.config.num_inlets:
                raise ConfigurationError(
                        '{} Mixer1 provided with both inlet_list and '
                        'num_inlets arguments, which were not consistent ('
                        'length of inlet_list was not equal to num_inlets). '
                        'PLease check your arguments for consistency, and '
                        'note that it is only necessary to provide one of '
                        'these arguments.'.format(self.name))
        elif self.config.inlet_list is None and self.config.num_inlets is None:
            # If no arguments provided for inlets, default to num_inlets = 2
            self.config.num_inlets = 2

        # Create a list of names for inlet StateBlocks
        if self.config.inlet_list is not None:
            inlet_list = self.config.inlet_list
        else:
            inlet_list = ['inlet_' + str(n)
                          for n in range(1, self.config.num_inlets+1)]

        return inlet_list


    def add_inlet_state_blocks(self, inlet_list):
        '''
        Construct StateBlocks for all inlet streams.

        Args:
            list of strings to use as StateBlock names

        Returns:
            list of StateBlocks
        '''
        # Setup StateBlock argument dict
        tmp_dict = dict(**self.config.property_package_args)
        tmp_dict['has_phase_equilibrium'] = False
        tmp_dict['parameters'] = self.config.property_package
        tmp_dict['defined_state'] = True

        # Create empty list to hold StateBlocks for return
        inlet_blocks = []

        # Create an instance of StateBlock for all inlets
        for i in inlet_list:
            i_obj = self.config.property_package.state_block_class(
                        self.flowsheet().config.time,
                        doc='Material properties at inlet',
                        default=tmp_dict)

            setattr(self, i+'_state', i_obj)

            inlet_blocks.append(getattr(self, i+'_state'))

        return inlet_blocks


    def add_mixed_state_block(self):
        '''
        Constructs StateBlock to represent mixed stream.

        Returns:
            New StateBlock object
        '''
        # Setup StateBlock argument dict
        tmp_dict = dict(**self.config.property_package_args)
        tmp_dict['has_phase_equilibrium'] = \
            self.config.has_phase_equilibrium
        tmp_dict['parameters'] = self.config.property_package
        tmp_dict['defined_state'] = False

        self.mixed_state = self.config.property_package.state_block_class(
                                self.flowsheet().config.time,
                                doc='Material properties of mixed stream',
                                default=tmp_dict)

        return self.mixed_state


    def get_mixed_state_block(self):
        '''
        Validates StateBlock provided in user arguments for mixed stream.

        Returns:
            The user-provided StateBlock or an Exception
        '''
        # Sanity check to make sure method is not called when arg missing
        if self.config.mixed_state_block is None:
            raise BurntToast('{} get_mixed_state_block method called when '
                             'mixed_state_block argument is None. This should '
                             'not happen.'.format(self.name))

        # Check that the user-provided StateBlock uses the same prop pack
        if (self.config.mixed_state_block[
                self.flowsheet().config.time.first()].config.parameters
                != self.config.property_package):
            raise ConfigurationError(
                    '{} StateBlock provided in mixed_state_block argument '
                    ' does not come from the same property package as '
                    'provided in the property_package argument. All '
                    'StateBlocks within a Mixer1 must use the same '
                    'property package.'.format(self.name))

        return self.config.mixed_state_block


    def add_material_mixing_equations(self, inlet_blocks, mixed_block):
        '''
        Add material mixing equations (phase-component balances).
        '''
        # Create equilibrium generation term and constraints if required
        if self.config.has_phase_equilibrium is True:
            # Get units from property package
            units = {}
            for u in ['holdup', 'time']:
                try:
                    units[u] = (self.config.property_package
                                .get_metadata().default_units[u])
                except KeyError:
                    units[u] = '-'

            try:
                add_object_reference(
                    self,
                    'phase_equilibrium_idx_ref',
                    self.config.property_package.phase_equilibrium_idx)
            except AttributeError:
                raise PropertyNotSupportedError(
                    '{} Property package does not contain a list of phase '
                    'equilibrium reactions (phase_equilibrium_idx), thus does '
                    'not support phase equilibrium.'.format(self.name))
            self.phase_equilibrium_generation = Var(
                        self.flowsheet().config.time,
                        self.phase_equilibrium_idx_ref,
                        domain=Reals,
                        doc='Amount of generation in unit by phase '
                            'equilibria [{}/{}]'
                            .format(units['holdup'], units['time']))

        # Define terms to use in mixing equation
        def phase_equilibrium_term(b, t, p, j):
            if self.config.has_phase_equilibrium:
                sd = {}
                sblock = mixed_block[t]
                for r in b.phase_equilibrium_idx_ref:
                    if sblock.phase_equilibrium_list[r][0] == j:
                        if sblock.phase_equilibrium_list[r][1][0] == p:
                            sd[r] = 1
                        elif sblock.phase_equilibrium_list[r][1][1] == p:
                            sd[r] = -1
                        else:
                            sd[r] = 0
                    else:
                        sd[r] = 0

                return sum(b.phase_equilibrium_generation[t, r]*sd[r]
                           for r in b.phase_equilibrium_idx_ref)
            else:
                return 0
#ARIEL
#         # Get phase component list(s)
#         phase_component_list = self._get_phase_comp_list()

#         # Write phase-component balances
#         @self.Constraint(self.flowsheet().config.time,
#                          self.config.property_package.phase_list,
#                          self.config.property_package.component_list,
#                          doc='Material mixing equations')
#         def material_mixing_equations(b, t, p, j):
#             if j in phase_component_list[p]:
#                 return 0 == (
#                         sum(inlet_blocks[i][t].get_material_flow_terms(p, j)
#                             for i in range(len(inlet_blocks))) -
#                         mixed_block[t].get_material_flow_terms(p, j) +
#                         phase_equilibrium_term(b, t, p, j))
#             else:
#                 return Constraint.Skip

#     def add_energy_mixing_equations(self, inlet_blocks, mixed_block):
#         '''
#         Add energy mixing equations (total enthalpy balance).
#         '''
#         self.scaling_factor_energy = Param(
#                         default=1e-6,
#                         mutable=True,
#                         doc='Energy balance scaling parameter')

#         @self.Constraint(self.flowsheet().config.time, doc='Energy balances')
#         def enthalpy_mixing_equations(b, t):
#             return 0 == self.scaling_factor_energy*(
#                 sum(sum(inlet_blocks[i][t].get_enthalpy_flow_terms(p)
#                     for p in b.config.property_package.phase_list)
#                     for i in range(len(inlet_blocks))) -
#                 sum(mixed_block[t].get_enthalpy_flow_terms(p)
#                     for p in b.config.property_package.phase_list))


#     def add_pressure_minimization_equations(self, inlet_blocks, mixed_block):
#         '''
#         Add pressure minimization equations. This is done by sequential
#         comparisons of each inlet to the minimum pressure so far, using
#         the IDAES smooth minimum fuction.
#         '''
#         if not hasattr(self, 'inlet_idx'):
#             self.inlet_idx = RangeSet(len(inlet_blocks))
#         # Add variables
#         self.minimum_pressure = Var(self.flowsheet().config.time,
#                                     self.inlet_idx,
#                                     doc='Variable for calculating '
#                                         'minimum inlet pressure')

#         self.eps_pressure = Param(mutable=True,
#                                   initialize=1e-3,
#                                   domain=PositiveReals,
#                                   doc='Smoothing term for '
#                                       'minimum inlet pressure')

#         # Calculate minimum inlet pressure
#         @self.Constraint(self.flowsheet().config.time,
#                          self.inlet_idx,
#                          doc='Calculation for minimum inlet pressure')
#         def minimum_pressure_constraint(b, t, i):
#             if i == self.inlet_idx.first():
#                 return self.minimum_pressure[t, i] == (
#                            inlet_blocks[i-1][t].pressure)
#             else:
#                 return self.minimum_pressure[t, i] == (
#                         smooth_min(self.minimum_pressure[t, i-1],
#                                    inlet_blocks[i-1][t].pressure,
#                                    self.eps_pressure))

#         # Set inlet pressure to minimum pressure
#         @self.Constraint(self.flowsheet().config.time,
#                          doc='Link pressure to control volume')
#         def mixture_pressure(b, t):
#             return mixed_block[t].pressure == (
#                        self.minimum_pressure[t,
#                                              self.inlet_idx.last()])


#     def add_pressure_equality_equations(self, inlet_blocks, mixed_block):
#         '''
#         Add pressure equality equations. Note that this writes a number of
#         constraints equal to the number of inlets, enforcing equality between
#         all inlets and the mixed stream.
#         '''
#         if not hasattr(self, 'inlet_idx'):
#             self.inlet_idx = RangeSet(len(inlet_blocks))

#         # Create equality constraints
#         @self.Constraint(self.flowsheet().config.time,
#                          self.inlet_idx,
#                          doc='Calculation for minimum inlet pressure')
#         def pressure_equality_constraints(b, t, i):
#             return mixed_block[t].pressure == inlet_blocks[i-1][t].pressure
#ARIEL


    def add_port_objects(self, inlet_list, inlet_blocks, mixed_block):
        '''
        Adds Port objects if required.

        Args:
            a list of inlet StateBlock objects
            a mixed state StateBlock object

        Returns:
            None
        '''
        if self.config.construct_ports is True:
            
            # Add ports and variables for outlets and inlets
            time = self.flowsheet().config.time
            units_meta = self.config.property_package.get_metadata().get_derived_units
            # Add ports
            for p in inlet_list:
                setattr(self, p, Port(noruleinit=True, doc='Inlet Port')) #ARIEL  

                setattr(self, ('flow_vol_%s' % p), Var(time,
                                        initialize=1,
                                        units=units_meta('volume')/units_meta('time'),
                                        doc='Volumetric flowrate of water out of unit'))

                setattr(self, ('conc_mass_%s' % p), Var(time,
                                         self.config.property_package.component_list,
                                         initialize=0,
                                         units=units_meta('mass')/units_meta('volume'),
                                         doc='Mass concentration of species at outlet'))
                
                setattr(self, ('pressure_%s' % p), Var(time,
                                        initialize=1e5,
                                        units=units_meta('pressure'),
                                        doc='Pressure at outlet'))
                
                setattr(self, ('temperature_%s' % p), Var(time,
                                           initialize=300,
                                           units=units_meta('temperature'),
                                           doc='Temperature at outlet'))
                    
                getattr(self, p).add(getattr(self, ('temperature_%s' % p)), 'temperature')
                getattr(self, p).add(getattr(self, ('pressure_%s' % p)), 'pressure')
                getattr(self, p).add(getattr(self, ('conc_mass_%s' % p)), 'conc_mass')
                getattr(self, p).add(getattr(self, ('flow_vol_%s' % p)), 'flow_vol')
                #i_state = getattr(self, p+'_state') #ARIEL
                #self.add_port(name=p, block=i_state, doc='Inlet Port') #ARIEL
            #self.add_port(name='outlet', block=mixed_block, doc='Outlet Port') #ARIEL
            
            self.outlet = Port(noruleinit=True, doc='Outlet Port') #ARIEL

            self.flow_vol_out = Var(time,
                                    initialize=1,
                                    units=units_meta('volume')/units_meta('time'),
                                    doc='Volumetric flowrate of water out of unit')
            self.conc_mass_out = Var(time,
                                     self.config.property_package.component_list,
                                     initialize=0,
                                     units=units_meta('mass')/units_meta('volume'),
                                     doc='Mass concentration of species at outlet')
            self.temperature_out = Var(time,
                                       initialize=300,
                                       units=units_meta('temperature'),
                                       doc='Temperature at outlet')
            self.pressure_out = Var(time,
                                    initialize=1e5,
                                    units=units_meta('pressure'),
                                    doc='Pressure at outlet')

            self.outlet.add(self.flow_vol_out, 'flow_vol')
            self.outlet.add(self.conc_mass_out, 'conc_mass')
            self.outlet.add(self.temperature_out, 'temperature')
            self.outlet.add(self.pressure_out, 'pressure')

    def model_check(blk):
        '''
        This method executes the model_check methods on the associated state
        blocks (if they exist). This method is generally called by a unit model
        as part of the unit's model_check method.

        Args:
            None

        Returns:
            None
        '''
        # Try property block model check
        for t in blk.flowsheet().config.time:
            try:
                inlet_list = blk.create_inlet_list()
                for i in inlet_list:
                    i_block = getattr(blk, i+'_state')
                    i_block[t].model_check()
            except AttributeError:
                _log.warning('{} Mixer1 inlet property block has no model '
                             'checks. To correct this, add a model_check '
                             'method to the associated StateBlock class.'
                             .format(blk.name))
            try:
                if blk.config.mixed_state_block is None:
                    blk.mixed_state[t].model_check()
                else:
                    blk.config.mixed_state_block.model_check()
            except AttributeError:
                _log.warning('{} Mixer1 outlet property block has no '
                             'model checks. To correct this, add a '
                             'model_check method to the associated '
                             'StateBlock class.'.format(blk.name))


    def use_minimum_inlet_pressure_constraint(self):
        '''Activate the mixer pressure = mimimum inlet pressure constraint and
        deactivate the mixer pressure and all inlet pressures are equal
        constraints. This should only be used when momentum_mixing_type ==
        MomentumMixingType.minimize_and_equality.
        '''
        if self.config.momentum_mixing_type != \
                MomentumMixingType.minimize_and_equality:
            _log.warning(
                '''use_minimum_inlet_pressure_constraint() can only be used
                when momentum_mixing_type ==
                MomentumMixingType.minimize_and_equality''')
            return
        self.minimum_pressure_constraint.activate()
        self.pressure_equality_constraints.deactivate()


    def use_equal_pressure_constraint(self):
        '''Deactivate the mixer pressure = mimimum inlet pressure constraint
        and activate the mixer pressure and all inlet pressures are equal
        constraints. This should only be used when momentum_mixing_type ==
        MomentumMixingType.minimize_and_equality.
        '''
        if self.config.momentum_mixing_type != \
                MomentumMixingType.minimize_and_equality:
            _log.warning(
                '''use_equal_pressure_constraint() can only be used when
                momentum_mixing_type ==
                MomentumMixingType.minimize_and_equality''')
            return
        self.minimum_pressure_constraint.deactivate()
        self.pressure_equality_constraints.activate()


    def initialize(blk, outlvl=0, optarg={},
                   solver='ipopt', hold_state=False):
        '''
        Initialisation routine for mixer (default solver ipopt)

        Keyword Arguments:
            outlvl : sets output level of initialisation routine. **Valid
                     values:** **0** - no output (default), **1** - return
                     solver state for each step in routine, **2** - include
                     solver output infomation (tee=True)
            optarg : solver options dictionary object (default={})
            solver : str indicating whcih solver to use during
                     initialization (default = 'ipopt')
            hold_state : flag indicating whether the initialization routine
                     should unfix any state variables fixed during
                     initialization, **default** - False. **Valid values:**
                     **True** - states variables are not unfixed, and a dict of
                     returned containing flags for which states were fixed
                     during initialization, **False** - state variables are
                     unfixed after initialization by calling the release_state
                     method.

        Returns:
            If hold_states is True, returns a dict containing flags for which
            states were fixed during initialization.
        '''
        # Set solver options
        if outlvl > 1:
            stee = True
        else:
            stee = False

        opt = SolverFactory(solver)
        opt.options = optarg

        # Initialize inlet state blocks
        flags = {}
        inlet_list = blk.create_inlet_list()
        i_block_list = []
        for i in inlet_list:
            i_block = getattr(blk, i+'_state')
            i_block_list.append(i_block)
            flags[i] = {}
            flags[i] = i_block.initialize(outlvl=outlvl-1,
                                          optarg=optarg,
                                          solver=solver,
                                          hold_state=True)

        # Initialize mixed state block
        if blk.config.mixed_state_block is None:
            mblock = blk.mixed_state
        else:
            mblock = blk.config.mixed_state_block

        # Calculate initial guesses for mixed stream state
        for t in blk.flowsheet().config.time:
            # Iterate over state vars as defined by property package
            s_vars = mblock[t].define_state_vars()
            for s in s_vars:
                i_vars = []
                for i in range(len(i_block_list)):
                    i_vars.append(getattr(i_block_list[i][t],
                                          s_vars[s].local_name))

                if s == 'pressure':
                    # If pressure, use minimum as initial guess
                    mblock[t].pressure.value = min(
                            i_block_list[i][t].pressure.value
                            for i in range(len(i_block_list)))
                elif 'flow' in s:
                    # If a 'flow' variable (i.e. extensive), sum inlets
                    for k in s_vars[s]:
                        s_vars[s][k].value = sum(i_vars[i][k].value
                                                 for i in range(
                                                         len(i_block_list)))
                else:
                    # Otherwise use average of inlets
                    for k in s_vars[s]:
                        s_vars[s][k].value = (sum(i_vars[i][k].value
                                                  for i in range(
                                                         len(i_block_list))) /
                                              len(i_block_list))

        mblock.initialize(outlvl=outlvl-1,
                          optarg=optarg,
                          solver=solver,
                          hold_state=False)

        if blk.config.mixed_state_block is None:
            if (hasattr(blk, 'pressure_equality_constraints') and
                    blk.pressure_equality_constraints.active is True):
                blk.pressure_equality_constraints.deactivate()
                for t in blk.flowsheet().config.time:
                    sys_press = getattr(
                            blk,
                            blk.create_inlet_list()[0]+'_state')[t].pressure
                    blk.mixed_state[t].pressure.fix(sys_press.value)

                results = opt.solve(blk, tee=stee)

                blk.pressure_equality_constraints.activate()
                for t in blk.flowsheet().config.time:
                    blk.mixed_state[t].pressure.unfix()

            else:
                results = opt.solve(blk, tee=stee)

            if outlvl > 0:
                if results.solver.termination_condition == \
                        TerminationCondition.optimal:
                    _log.info('{} Initialisation Complete.'.format(blk.name))
                else:
                    _log.warning('{} Initialisation Failed.'.format(blk.name))
        else:
            _log.info('{} Initialisation Complete.'.format(blk.name))

        if hold_state is True:
            return flags
        else:
            blk.release_state(flags, outlvl=outlvl-1)

