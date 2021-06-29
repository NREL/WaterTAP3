Deep Well Injection
==========================

Deep well injection is used to dispose of waste streams.

Unit Parameters
--------------------

Deep well injection has two parameters:

* ``"lift_height"`` - lift height for injection pump [ft]:

    * Optional parameter
    * Default value is 400 ft
|
* ``"pipe_distance"`` - pipe distance from facility to deep well injection site [mi]

    * Required parameter
|
Capital Costs
---------------

Capital costs for deep well injection are based off of the costs for the Kay Baily Hutchinson
(KBH) deep well injection site. Costing calculation is split into well construction and pipe
construction. From the KBH data, well construction is $16.9 MM. Piping
cost assumes an 8 in diameter pipe, and is calculated as:

    .. math::

        C_{pipe} = 0.28 x_{pipe}
|
The total fixed cost is then calculated by scaling with KBH flow according to:

    .. math::

        C_{dwi} = ( C_{well} + C_{pipe} ) \frac{Q_{in}}{Q_{KBH}} ^ {0.7}
|

Electricity Intensity
------------------------

Electricity intensity for deep well injection is based off the pump used. The
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
Then the electricity intensity is calculated as [kWh/m3]:

    .. math::

        E_{dwi} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{m3hr}}
|

Assumptions
------------------------

* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

Reference
---------------------


Module
----------------------------------------

.. autoclass:: watertap3.wt_units.deep_well_injection.UnitProcess
    :members: fixed_cap, elect
    :exclude-members: build


..  raw:: pdf

    PageBreak