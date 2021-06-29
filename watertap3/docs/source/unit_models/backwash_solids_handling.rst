Backwash Solids Handling
============================================================

Unit Basics
--------------

Backwash handling is a separate unit in WaterTAP3 and can be used to handle the waste/backwash
stream from filtration units (e.g. tri-media filtration).

Unit Parameters
--------------------

There is one parameter for backwash solids handling:

*``"recovery"`` - ???

Capital Costs
---------------

The capital costs are a function of mass flow [kg/hr] from Figure 5.7.1 in the below reference:

    .. math::

        C_{bw} = 9.76 M_{in} ^ {0.918}

The mass flow in is the sum of all the constituents flowing into the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i

Then, we estimate the density of the solution [kg/m3]:

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86

And mass flow [kg/hr] is determined with:

    .. math::

        M_{in} = \rho_{in} Q_{in}


Assumptions
--------------

Several aspects of the unit are assumed.

The lift height is 100 ft:

    .. math::

        h = 100

The pump and motor efficiency are 90%:

    .. math::

        \eta_{pump} = \eta_{motor} = 0.9


Electricity Intensity
------------------------

Electricity intensity for onshore intake in WaterTAP3 is based off the pump used,
the pump/motor efficiencies, lift height, and the influent flow rate.

References
-------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.backwash_solids_handling.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak