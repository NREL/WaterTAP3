.. _backwash_solids_handling_unit:

Backwash Solids Handling
============================================================

The backwash solids handling unit model represents the handling of the waste/backwash streams
from  filtration processes (e.g. tri-media filtration). It is typically recycled back into  the
treatment train or sent to a final waste unit.

Unit Parameters
--------------------

There is one parameter for backwash solids handling:

* ``"recovery"`` - proportion of flow recycled back to treatment technology

    * Required parameter
    * Value between 0 and 1
|
Capital Costs
---------------

The capital costs are a function of mass flow [kg/hr] from Figure 5.7.1 in in McGivney & Kawamura
(2008):

    .. math::

        C_{bw} = 9.76 \frac{M_{in}}{1577255} ^ {0.918}
|
The mass flow in is the sum of all the constituents flowing into the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i
|
Then, the density of the solution is [kg/m3]:

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86
|
And mass flow is determined with [kg/hr]:

    .. math::

        M_{in} = \rho_{in} Q_{in}
|

Electricity Intensity
------------------------

Electricity intensity for backwash solids handling is based off the pump used. The
calculation includes:

* Lift height [ft]:

    .. math::

        h
|
* The pump and motor efficiencies:

    .. math::

        \eta_{pump}, \eta_{motor}
|
* And the influent flow in [gal/min] and [m3/hr]:

    .. math::

        Q_{gpm}, Q_{m3hr}
|
Then the electricity intensity is calculated as:

    .. math::

        E_{bw} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{m3hr}}
|

Assumptions
------------------------

* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

References
-------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Backwash Solids Handling Module
----------------------------------------

.. autoclass:: watertap3.wt_units.backwash_solids_handling.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak